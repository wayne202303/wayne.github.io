import json
from typing import Dict, Any


class ReportGenerator:
    @staticmethod
    def to_json(diff_result: Dict[str, Any], output_path: str):
        def convert_df_data(obj):
            if hasattr(obj, 'item'):
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
                
                if comparison.get('primary_key_used'):
                    html_parts.append(f'<p><strong>使用主键:</strong> {comparison["primary_key_used"]}</p>')
                
                if comparison['added_columns']:
                    html_parts.append(f'<p class="added">新增列: {", ".join(comparison["added_columns"])}</p>')
                if comparison['removed_columns']:
                    html_parts.append(f'<p class="removed">删除列: {", ".join(comparison["removed_columns"])}</p>')
                
                if comparison['row_changes']:
                    html_parts.append('<table>')
                    html_parts.append('<tr><th>行号/键</th><th>变更类型</th><th>详情</th></tr>')
                    
                    for change in comparison['row_changes']:
                        change_type = change['type']
                        css_class = change_type
                        
                        row_key = change.get('key', change.get('row', 'N/A'))
                        
                        details = ''
                        if change_type == 'added':
                            details = json.dumps(change['data'], ensure_ascii=False)
                        elif change_type == 'removed':
                            details = json.dumps(change['data'], ensure_ascii=False)
                        elif change_type == 'modified':
                            details = f"变更字段: {json.dumps(change['changes'], ensure_ascii=False)}"
                        
                        html_parts.append(f'<tr><td>{row_key}</td><td class="{css_class}">{change_type}</td><td>{details}</td></tr>')
                    
                    html_parts.append('</table>')
                
                html_parts.append('</div>')
        
        html_parts.append('''
</body>
</html>
''')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(html_parts))
    
    @staticmethod
    def to_console(diff_result: Dict[str, Any], verbose: bool = False):
        sheets = diff_result['sheets']
        
        print("\n" + "="*60)
        print("配表差异报告")
        print("="*60)
        
        if sheets['added']:
            print(f"\n新增工作表: {', '.join(sheets['added'])}")
        
        if sheets['removed']:
            print(f"\n删除工作表: {', '.join(sheets['removed'])}")
        
        for sheet_name, comparison in diff_result['comparisons'].items():
            if comparison['has_changes']:
                print(f"\n--- 工作表: {sheet_name} ---")
                
                if comparison.get('primary_key_used'):
                    print(f"  使用主键: {comparison['primary_key_used']}")
                
                if comparison['added_columns']:
                    print(f"  新增列: {', '.join(comparison['added_columns'])}")
                
                if comparison['removed_columns']:
                    print(f"  删除列: {', '.join(comparison['removed_columns'])}")
                
                added_count = sum(1 for c in comparison['row_changes'] if c['type'] == 'added')
                removed_count = sum(1 for c in comparison['row_changes'] if c['type'] == 'removed')
                modified_count = sum(1 for c in comparison['row_changes'] if c['type'] == 'modified')
                
                print(f"  新增行: {added_count}")
                print(f"  删除行: {removed_count}")
                print(f"  修改行: {modified_count}")
                
                if verbose and comparison['row_changes']:
                    print("\n  详细变更:")
                    for change in comparison['row_changes'][:10]:
                        row_key = change.get('key', change.get('row', 'N/A'))
                        print(f"    [{change['type'].upper()}] {row_key}")
                    if len(comparison['row_changes']) > 10:
                        print(f"    ... 还有 {len(comparison['row_changes']) - 10} 条变更")
        
        print("\n" + "="*60)
