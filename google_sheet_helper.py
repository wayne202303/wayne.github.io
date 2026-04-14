#!/usr/bin/env python3
"""
Google Sheet 下载助手
用于从Google Sheet下载配表文件
"""
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Optional


def download_google_sheet(
    sheet_url: str,
    output_path: str,
    sheet_name: Optional[str] = None,
    format: str = 'xlsx'
) -> str:
    """
    从Google Sheet URL下载文件
    
    Args:
        sheet_url: Google Sheet URL或文件ID
        output_path: 输出文件路径
        sheet_name: 工作表名称（仅xlsx格式支持）
        format: 输出格式 ('xlsx' 或 'csv')
    
    Returns:
        输出文件路径
    """
    try:
        import gdown
    except ImportError:
        print("错误: 需要安装gdown库")
        print("请运行: pip install gdown")
        sys.exit(1)
    
    # 解析文件ID
    file_id = extract_file_id(sheet_url)
    if not file_id:
        print("错误: 无法解析Google Sheet URL")
        sys.exit(1)
    
    print(f"正在下载Google Sheet (ID: {file_id})...")
    
    # 构建下载URL
    if format == 'xlsx':
        download_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    else:
        download_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
    
    # 下载文件
    gdown.download(download_url, output_path, quiet=False, fuzzy=True)
    
    print(f"文件已保存到: {output_path}")
    return output_path


def extract_file_id(url: str) -> Optional[str]:
    """从Google Sheet URL中提取文件ID"""
    import re
    
    # 尝试匹配标准URL格式
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
        r'^([a-zA-Z0-9-_]+)$'  # 直接是ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def compare_google_sheets(
    old_sheet_url: str,
    new_sheet_url: str,
    output_html: Optional[str] = None,
    output_json: Optional[str] = None,
    **kwargs
):
    """
    对比两个Google Sheet
    
    Args:
        old_sheet_url: 旧的Google Sheet URL或ID
        new_sheet_url: 新的Google Sheet URL或ID
        output_html: HTML报告输出路径
        output_json: JSON报告输出路径
        **kwargs: 传递给config-diff的其他参数
    """
    import tempfile
    from config_diff_tool.cli import main as config_diff_main
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 下载旧文件
        old_file = temp_path / "old_sheet.xlsx"
        download_google_sheet(old_sheet_url, str(old_file), format='xlsx')
        
        # 下载新文件
        new_file = temp_path / "new_sheet.xlsx"
        download_google_sheet(new_sheet_url, str(new_file), format='xlsx')
        
        # 调用config-diff进行对比
        print("\n开始对比配表...")
        
        # 这里需要重新组织参数调用config_diff_main
        # 为了简单，我们直接导入并使用内部API
        from config_diff_tool.reader import ConfigReader
        from config_diff_tool.differ import ConfigDiffer
        from config_diff_tool.reporter import ReportGenerator
        
        reader = ConfigReader()
        old_data = reader.read_file(str(old_file))
        new_data = reader.read_file(str(new_file))
        
        differ = ConfigDiffer(
            old_data,
            new_data,
            primary_keys=kwargs.get('primary_keys', {}),
            ignore_columns=kwargs.get('ignore_columns', [])
        )
        
        diff_result = differ.compare_all()
        
        ReportGenerator.to_console(diff_result, verbose=kwargs.get('verbose', False))
        
        if output_html:
            ReportGenerator.to_html(diff_result, output_html)
            print(f"HTML报告已生成: {output_html}")
        
        if output_json:
            ReportGenerator.to_json(diff_result, output_json)
            print(f"JSON报告已生成: {output_json}")
        
        return differ.has_any_changes(diff_result)


if __name__ == '__main__':
    import click
    
    @click.command()
    @click.argument('old_sheet')
    @click.argument('new_sheet')
    @click.option('--html', 'output_html', type=click.Path(), help='输出HTML报告路径')
    @click.option('--json', 'output_json', type=click.Path(), help='输出JSON报告路径')
    @click.option('--primary-key', '-k', multiple=True, help='指定主键，格式: sheet_name:column_name')
    @click.option('--ignore-column', '-i', multiple=True, help='指定忽略的列名')
    @click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
    def cli(old_sheet, new_sheet, output_html, output_json, primary_key, ignore_column, verbose):
        """对比两个Google Sheet配表"""
        
        # 解析主键
        primary_keys = {}
        for pk in primary_key:
            if ':' in pk:
                sheet, col = pk.split(':', 1)
                primary_keys[sheet] = col
        
        try:
            has_changes = compare_google_sheets(
                old_sheet,
                new_sheet,
                output_html=output_html,
                output_json=output_json,
                primary_keys=primary_keys,
                ignore_columns=list(ignore_column),
                verbose=verbose
            )
            
            sys.exit(1 if has_changes else 0)
            
        except Exception as e:
            print(f"错误: {str(e)}", file=sys.stderr)
            sys.exit(2)
    
    cli()
