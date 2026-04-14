import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


def convert_to_python_type(obj):
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Series):
        return {k: convert_to_python_type(v) for k, v in obj.to_dict().items()}
    elif isinstance(obj, dict):
        return {k: convert_to_python_type(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_python_type(x) for x in obj]
    elif pd.isna(obj):
        return None
    else:
        return obj


class ConfigDiffer:
    def __init__(
        self, 
        old_data: Dict[str, pd.DataFrame], 
        new_data: Dict[str, pd.DataFrame],
        primary_keys: Optional[Dict[str, str]] = None,
        ignore_columns: Optional[List[str]] = None
    ):
        self.old_data = old_data
        self.new_data = new_data
        self.primary_keys = primary_keys or {}
        self.ignore_columns = ignore_columns or []
    
    def get_sheets_diff(self) -> Dict[str, Any]:
        old_sheets = set(self.old_data.keys())
        new_sheets = set(self.new_data.keys())
        
        return {
            'added': list(new_sheets - old_sheets),
            'removed': list(old_sheets - new_sheets),
            'common': list(old_sheets & new_sheets)
        }
    
    def _filter_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        columns_to_keep = [col for col in df.columns if col not in self.ignore_columns]
        return df[columns_to_keep]
    
    def compare_sheet(self, sheet_name: str) -> Dict[str, Any]:
        old_df = self.old_data[sheet_name].copy()
        new_df = self.new_data[sheet_name].copy()
        
        old_df = self._filter_columns(old_df)
        new_df = self._filter_columns(new_df)
        
        old_df = old_df.fillna('')
        new_df = new_df.fillna('')
        
        old_rows, old_cols = old_df.shape
        new_rows, new_cols = new_df.shape
        
        primary_key = self.primary_keys.get(sheet_name)
        
        if primary_key and primary_key in old_df.columns and primary_key in new_df.columns:
            row_changes = self._compare_by_primary_key(old_df, new_df, primary_key)
        else:
            row_changes = self._compare_by_row_index(old_df, new_df)
        
        added_cols = list(set(new_df.columns) - set(old_df.columns))
        removed_cols = list(set(old_df.columns) - set(new_df.columns))
        
        return {
            'sheet_name': sheet_name,
            'old_shape': (old_rows, old_cols),
            'new_shape': (new_rows, new_cols),
            'added_columns': added_cols,
            'removed_columns': removed_cols,
            'row_changes': row_changes,
            'has_changes': len(row_changes) > 0 or len(added_cols) > 0 or len(removed_cols) > 0,
            'primary_key_used': primary_key if primary_key in old_df.columns and primary_key in new_df.columns else None
        }
    
    def _compare_by_primary_key(self, old_df: pd.DataFrame, new_df: pd.DataFrame, primary_key: str) -> List[Dict[str, Any]]:
        row_changes = []
        
        old_dict = old_df.set_index(primary_key).to_dict('index')
        new_dict = new_df.set_index(primary_key).to_dict('index')
        
        old_keys = set(old_dict.keys())
        new_keys = set(new_dict.keys())
        
        for key in new_keys - old_keys:
            row_changes.append({
                'key': convert_to_python_type(key),
                'type': 'added',
                'data': convert_to_python_type(new_dict[key])
            })
        
        for key in old_keys - new_keys:
            row_changes.append({
                'key': convert_to_python_type(key),
                'type': 'removed',
                'data': convert_to_python_type(old_dict[key])
            })
        
        for key in old_keys & new_keys:
            old_row = old_dict[key]
            new_row = new_dict[key]
            
            changed_fields = {}
            for col in old_df.columns:
                if col != primary_key and col in new_df.columns:
                    old_val = old_row.get(col, '')
                    new_val = new_row.get(col, '')
                    if old_val != new_val:
                        changed_fields[col] = {
                            'old': convert_to_python_type(old_val),
                            'new': convert_to_python_type(new_val)
                        }
            
            if changed_fields:
                row_changes.append({
                    'key': convert_to_python_type(key),
                    'type': 'modified',
                    'data': {
                        'old': convert_to_python_type(old_row),
                        'new': convert_to_python_type(new_row)
                    },
                    'changes': convert_to_python_type(changed_fields)
                })
        
        return row_changes
    
    def _compare_by_row_index(self, old_df: pd.DataFrame, new_df: pd.DataFrame) -> List[Dict[str, Any]]:
        row_changes = []
        
        max_rows = max(len(old_df), len(new_df))
        for i in range(max_rows):
            if i >= len(old_df):
                row_changes.append({
                    'row': i,
                    'type': 'added',
                    'data': convert_to_python_type(new_df.iloc[i].to_dict())
                })
            elif i >= len(new_df):
                row_changes.append({
                    'row': i,
                    'type': 'removed',
                    'data': convert_to_python_type(old_df.iloc[i].to_dict())
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
                                    'old': convert_to_python_type(old_val),
                                    'new': convert_to_python_type(new_val)
                                }
                    
                    if changed_fields:
                        row_changes.append({
                            'row': i,
                            'type': 'modified',
                            'data': {
                                'old': convert_to_python_type(old_row.to_dict()),
                                'new': convert_to_python_type(new_row.to_dict())
                            },
                            'changes': convert_to_python_type(changed_fields)
                        })
        
        return row_changes
    
    def compare_all(self) -> Dict[str, Any]:
        sheets_diff = self.get_sheets_diff()
        sheet_comparisons = {}
        
        for sheet in sheets_diff['common']:
            sheet_comparisons[sheet] = self.compare_sheet(sheet)
        
        return {
            'sheets': sheets_diff,
            'comparisons': sheet_comparisons
        }
    
    def has_any_changes(self, diff_result: Dict[str, Any]) -> bool:
        sheets = diff_result['sheets']
        if sheets['added'] or sheets['removed']:
            return True
        
        for sheet_name, comparison in diff_result['comparisons'].items():
            if comparison['has_changes']:
                return True
        
        return False
