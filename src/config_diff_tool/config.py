import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path


class Config:
    def __init__(self):
        self.primary_keys: Dict[str, str] = {}
        self.ignore_columns: List[str] = []
        self.ignore_sheets: List[str] = []
        self.output_dir: str = '.'
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        config = cls()
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'primary_keys' in data:
            config.primary_keys = data['primary_keys']
        
        if 'ignore_columns' in data:
            config.ignore_columns = data['ignore_columns']
        
        if 'ignore_sheets' in data:
            config.ignore_sheets = data['ignore_sheets']
        
        if 'output_dir' in data:
            config.output_dir = data['output_dir']
        
        return config
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        config = cls()
        
        if 'primary_keys' in data:
            config.primary_keys = data['primary_keys']
        
        if 'ignore_columns' in data:
            config.ignore_columns = data['ignore_columns']
        
        if 'ignore_sheets' in data:
            config.ignore_sheets = data['ignore_sheets']
        
        if 'output_dir' in data:
            config.output_dir = data['output_dir']
        
        return config
