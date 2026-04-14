import pandas as pd
from typing import Dict, Optional
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
