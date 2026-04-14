#!/usr/bin/env python3
import os
import json
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path


class ConfigReader:
    def __init__(self):
        self.supported_extensions = {'.xlsx', '.xls', '.csv'}
    
    def read_excel(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        file_path = Path(file_path)
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return {sheet_name: df}
        else:
            xl = pd.ExcelFile(file_path)
            sheets = {}
            for sheet in xl.sheet_names:
                sheets[sheet] = pd.read_excel(xl, sheet_name=sheet)
            return sheets
    
    def read_csv(self, file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        return pd.read_csv(file_path, encoding=encoding)
    
    def read_file(self, file_path: str, sheet_name: Optional[str] = None, encoding: str = 'utf-8') -> Dict[str, pd.DataFrame]:
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext in ['.xlsx', '.xls']:
            return self.read_excel(file_path, sheet_name)
        elif ext == '.csv':
            df = self.read_csv(file_path, encoding)
            return {file_path.stem: df}
        else:
            raise ValueError(f"Unsupported file format: {ext}")


class ConfigDiffer:
    def __init__(self, old_data: Dict[str, pd.DataFrame], new_data: Dict[str, pd.DataFrame]):
        self.old_data = old_data
        self.new_data = new_data
    
    def get_sheets_diff(self) -> Dict[str, Any]:
        old_sheets = set(self.old_data.keys())
        new_sheets = set(self.new_data.keys())
        
        return {
            'added': list(new_sheets - old_sheets),
            'removed': list(old_sheets - new_sheets),
            'common': list(old_sheets & new_sheets)
        }
    
    def compare_sheet(self, sheet_name: str) -> Dict[str, Any]:
        old_df = self.old_data[sheet_name]
        new_df = self.new_data[sheet_name]
        
        old_df = old_df.fillna('')
        new_df = new_df.fillna('')
        
        old_rows, old_cols = old_df.shape
        new_rows, new_cols = new_df.shape
        
        row_changes = []
        
        max_rows = max(old_rows, new_rows)
        for i in range(max_rows):
            if i >= old_rows:
                row_changes.append({
                    'row': i,
                    'type': 'added',
                    'data': new_df.iloc[i].to_dict()
                })
            elif i >= new_rows:
                row_changes.append({
                    'row': i,
                    'type': 'removed',
                    'data': old_df.iloc[i].to_dict()
                })
            else:
                old_row = old_df.iloc[i]
                new_row = new_df.iloc[i]
                
                if not old_row.equals(new_row):
                    changed_fields = {}
                    for col in old_df.columns:
                        if col in new_df.columns:
                            old_val = old_row[col]
                            new_val = new_row[col]
                            if old_val != new_val:
                                changed_fields[col] = {
                                    'old': old_val,
                                    'new': new_val
                                }
                    
                    if changed_fields:
                        row_changes.append({
                            'row': i,
                            'type': 'modified',
                            'data': {
                                'old': old_row.to_dict(),
                                'new': new_row.to_dict()
                            },
                            'changes': changed_fields
                        })
        
        added_cols = list(set(new_df.columns) - set(old_df.columns))
        removed_cols = list(set(old_df.columns) - set(new_df.columns))
        
        return {
            'sheet_name': sheet_name,
            'old_shape': (old_rows, old_cols),
            'new_shape': (new_rows, new_cols),
            'added_columns': added_cols,
            'removed_columns': removed_cols,
            'row_changes': row_changes,
            'has_changes': len(row_changes) > 0 or len(added_cols) > 0 or len(removed_cols) > 0
        }
    
    def compare_all(self) -> Dict[str, Any]:
        sheets_diff = self.get_sheets_diff()
        sheet_comparisons = {}
        
        for sheet in sheets_diff['common']:
            sheet_comparisons[sheet] = self.compare_sheet(sheet)
        
        return {
            'sheets': sheets_diff,
            'comparisons': sheet_comparisons
        }


class ReportGenerator:
    @staticmethod
    def to_json(diff_result: Dict[str, Any], output_path: str):
        def convert_df_data(obj):
            if isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif hasattr(obj, 'item'):
                return obj.item()
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            elif isinstance(obj, list):
                return [convert_df_data(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: convert_df_data(v) for k, v in obj.items()}
            else:
                return str(obj)
        
        def deep_convert(obj):
            if isinstance(obj, dict):
                return {k: deep_convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [deep_convert(x) for x in obj]
            else:
                return convert_df_data(obj)
        
        converted_result = deep_convert(diff_result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(converted_result, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def to_html(diff_result: Dict[str, Any], output_path: str):
        html_parts = []
        html_parts.append('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>配表差异报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary { background: #fff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .sheet-section { background: #fff; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .added { color: green; }
        .removed { color: red; }
        .modified { color: orange; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .change-old { background-color: #ffcccc; }
        .change-new { background-color: #ccffcc; }
    </style>
</head>
<body>
''')
        
        html_parts.append('<h1>配表差异报告</h1>')
        
        sheets = diff_result['sheets']
        html_parts.append('<div class="summary">')
        html_parts.append(f'<p><strong>新增工作表:</strong> {", ".join(sheets["added"]) if sheets["added"] else "无"}</p>')
        html_parts.append(f'<p><strong>删除工作表:</strong> {", ".join(sheets["removed"]) if sheets["removed"] else "无"}</p>')
        html_parts.append(f'<p><strong>修改工作表:</strong> {len(sheets["common"])} 个</p>')
        html_parts.append('</div>')
        
        for sheet_name, comparison in diff_result['comparisons'].items():
            if comparison['has_changes']:
                html_parts.append(f'<div class="sheet-section">')
                html_parts.append(f'<h2>{sheet_name}</h2>')
                
                html_parts.append(f'<p>旧表大小: {comparison["old_shape"][0]} 行 × {comparison["old_shape"][1]} 列</p>')
                html_parts.append(f'<p>新表大小: {comparison["new_shape"][0]} 行 × {comparison["new_shape"][1]} 列</p>')
                
                if comparison['added_columns']:
                    html_parts.append(f'<p class="added">新增列: {", ".join(comparison["added_columns"])}</p>')
                if comparison['removed_columns']:
                    html_parts.append(f'<p class="removed">删除列: {", ".join(comparison["removed_columns"])}</p>')
                
                if comparison['row_changes']:
                    html_parts.append('<table>')
                    html_parts.append('<tr><th>行号</th><th>变更类型</th><th>详情</th></tr>')
                    
                    for change in comparison['row_changes']:
                        change_type = change['type']
                        css_class = change_type
                        
                        details = ''
                        if change_type == 'added':
                            details = json.dumps(change['data'], ensure_ascii=False)
                        elif change_type == 'removed':
                            details = json.dumps(change['data'], ensure_ascii=False)
                        elif change_type == 'modified':
                            details = f"变更字段: {json.dumps(change['changes'], ensure_ascii=False)}"
                        
                        html_parts.append(f'<tr><td>{change["row"]}</td><td class="{css_class}">{change_type}</td><td>{details}</td></tr>')
                    
                    html_parts.append('</table>')
                
                html_parts.append('</div>')
        
        html_parts.append('''
</body>
</html>
''')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(html_parts))


def main(old_file: str, new_file: str, output_json: Optional[str] = None, output_html: Optional[str] = None):
    reader = ConfigReader()
    
    print(f"读取旧文件: {old_file}")
    old_data = reader.read_file(old_file)
    
    print(f"读取新文件: {new_file}")
    new_data = reader.read_file(new_file)
    
    print("比较差异...")
    differ = ConfigDiffer(old_data, new_data)
    diff_result = differ.compare_all()
    
    if output_json:
        print(f"生成JSON报告: {output_json}")
        ReportGenerator.to_json(diff_result, output_json)
    
    if output_html:
        print(f"生成HTML报告: {output_html}")
        ReportGenerator.to_html(diff_result, output_html)
    
    print("完成!")
    return diff_result


if __name__ == '__main__':
    import click
    
    @click.command()
    @click.argument('old_file', type=click.Path(exists=True))
    @click.argument('new_file', type=click.Path(exists=True))
    @click.option('--json', 'output_json', type=click.Path(), help='输出JSON报告路径')
    @click.option('--html', 'output_html', type=click.Path(), help='输出HTML报告路径')
    def cli(old_file, new_file, output_json, output_html):
        main(old_file, new_file, output_json, output_html)
    
    cli()
