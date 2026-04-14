import sys
from pathlib import Path
from typing import Optional, Dict, Any
import click

from .reader import ConfigReader
from .differ import ConfigDiffer
from .reporter import ReportGenerator
from .config import Config
from . import __version__


def filter_sheets(data: Dict[str, Any], ignore_sheets: list) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k not in ignore_sheets}


@click.command()
@click.option('--version', '-V', is_flag=True, help='显示版本信息')
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径 (YAML格式)')
@click.option('--json', 'output_json', type=click.Path(), help='输出JSON报告路径')
@click.option('--html', 'output_html', type=click.Path(), help='输出HTML报告路径')
@click.option('--primary-key', '-k', multiple=True, help='指定主键，格式: sheet_name:column_name')
@click.option('--ignore-column', '-i', multiple=True, help='指定忽略的列名')
@click.option('--ignore-sheet', '-s', multiple=True, help='指定忽略的工作表名')
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
@click.option('--quiet', '-q', is_flag=True, help='静默模式，不输出到控制台')
@click.option('--fail-on-diff', '-f', is_flag=True, help='发现差异时返回非零退出码')
@click.argument('old_file', type=click.Path(exists=True), required=False)
@click.argument('new_file', type=click.Path(exists=True), required=False)
def main(
    old_file: Optional[str] = None,
    new_file: Optional[str] = None,
    config: Optional[str] = None,
    output_json: Optional[str] = None,
    output_html: Optional[str] = None,
    primary_key: tuple = (),
    ignore_column: tuple = (),
    ignore_sheet: tuple = (),
    verbose: bool = False,
    quiet: bool = False,
    fail_on_diff: bool = False,
    version: bool = False
):
    if version:
        click.echo(f"config-diff-tool version {__version__}")
        sys.exit(0)
    
    if not old_file or not new_file:
        click.echo("错误: 必须指定旧文件和新文件路径", err=True)
        click.echo("使用方法: config-diff [OPTIONS] OLD_FILE NEW_FILE", err=True)
        click.echo("使用 'config-diff --help' 查看更多信息", err=True)
        sys.exit(2)
    
    try:
        cfg = Config()
        
        if config:
            cfg = Config.from_file(config)
        
        primary_keys_dict = cfg.primary_keys.copy()
        for pk in primary_key:
            if ':' in pk:
                sheet, col = pk.split(':', 1)
                primary_keys_dict[sheet] = col
        
        ignore_columns_list = cfg.ignore_columns.copy()
        ignore_columns_list.extend(ignore_column)
        
        ignore_sheets_list = cfg.ignore_sheets.copy()
        ignore_sheets_list.extend(ignore_sheet)
        
        if not quiet:
            click.echo(f"读取旧文件: {old_file}")
        reader = ConfigReader()
        old_data = reader.read_file(old_file)
        old_data = filter_sheets(old_data, ignore_sheets_list)
        
        if not quiet:
            click.echo(f"读取新文件: {new_file}")
        new_data = reader.read_file(new_file)
        new_data = filter_sheets(new_data, ignore_sheets_list)
        
        if not quiet:
            click.echo("比较差异...")
        differ = ConfigDiffer(
            old_data,
            new_data,
            primary_keys=primary_keys_dict,
            ignore_columns=ignore_columns_list
        )
        diff_result = differ.compare_all()
        
        has_changes = differ.has_any_changes(diff_result)
        
        if not quiet:
            ReportGenerator.to_console(diff_result, verbose=verbose)
        
        if output_json:
            if not quiet:
                click.echo(f"生成JSON报告: {output_json}")
            ReportGenerator.to_json(diff_result, output_json)
        
        if output_html:
            if not quiet:
                click.echo(f"生成HTML报告: {output_html}")
            ReportGenerator.to_html(diff_result, output_html)
        
        if not quiet:
            if has_changes:
                click.echo("\n完成! 发现差异。")
            else:
                click.echo("\n完成! 未发现差异。")
        
        if fail_on_diff and has_changes:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        sys.exit(2)


if __name__ == '__main__':
    main()
