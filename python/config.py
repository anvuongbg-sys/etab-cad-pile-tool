#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module: config.py
Quản lý file cấu hình JSON cho tool
"""

import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """Lớp quản lý cấu hình từ file JSON"""
    
    # Cấu hình mặc định
    DEFAULT_CONFIG = {
        'etab_file': '',
        'output_directory': 'output',
        'pile_configs': {
            'bearing_capacity': 500,
            'pile_diameter': 0.8,
            'pile_length': 15.0,
            'min_distance': 3.0,
            'max_distance': 10.0,
            'grid_type': 'flexible',
            'grid_spacing': 4.0,
            'load_safety_factor': 1.3,
            'eccentricity_limit': 0.15
        },
        'column_info': {
            'column_width': 0.5,
            'column_height': 0.5,
            'foundation_depth': 1.5
        },
        'output_format': {
            'csv': True,
            'json': True,
            'dwg': False,
            'report': True
        },
        'cad_settings': {
            'pile_layer': 'PILE',
            'pile_color': 256,
            'pile_linetype': 'CONTINUOUS',
            'text_height': 0.3,
            'units': 'Meters'
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Khởi tạo Config
        
        Args:
            config_file: Đường dẫn file config JSON.
                         Nếu None, sử dụng cấu hình mặc định
        """
        # Bắt đầu với cấu hình mặc định
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file
        
        # Tải file config nếu được cung cấp
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
    
    def _load_from_file(self, file_path: str):
        """
        Tải cấu hình từ file JSON
        
        Args:
            file_path: Đường dẫn file config
        
        Raises:
            FileNotFoundError: Nếu file không tồn tại
            json.JSONDecodeError: Nếu JSON không hợp lệ
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Deep merge với cấu hình mặc định
            self._deep_merge(self.config, loaded_config)
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {file_path}")
    
    def _deep_merge(self, base: Dict, update: Dict):
        """
        Deep merge dictionary update vào base
        
        Args:
            base: Dictionary cơ sở
            update: Dictionary cần merge
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị cấu hình
        
        Args:
            key: Tên key (hỗ trợ nested keys như 'pile_configs.bearing_capacity')
            default: Giá trị mặc định nếu key không tồn tại
        
        Returns:
            Giá trị của key hoặc default
        """
        return self.get_nested(key, default)
    
    def get_nested(self, key_path: str, default: Any = None) -> Any:
        """
        Lấy giá trị từ nested keys
        
        Args:
            key_path: Đường dẫn key (ví dụ: 'pile_configs.bearing_capacity')
            default: Giá trị mặc định
        
        Returns:
            Giá trị của key
        """
        keys = key_path.split('.')
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any):
        """
        Đặt giá trị cấu hình
        
        Args:
            key: Tên key (hỗ trợ nested keys)
            value: Giá trị mới
        """
        self.set_nested(key, value)
    
    def set_nested(self, key_path: str, value: Any):
        """
        Đặt giá trị cho nested keys
        
        Args:
            key_path: Đường dẫn key
            value: Giá trị mới
        """
        keys = key_path.split('.')
        current = self.config
        
        # Tạo các key trung gian nếu cần
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Đặt giá trị cuối cùng
        current[keys[-1]] = value
    
    def save(self, file_path: Optional[str] = None):
        """
        Lưu cấu hình vào file JSON
        
        Args:
            file_path: Đường dẫn file output.
                      Nếu None, sử dụng file_path từ __init__
        """
        if file_path is None:
            file_path = self.config_file
        
        if file_path is None:
            raise ValueError("No file path specified")
        
        # Tạo thư mục nếu cần
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def to_dict(self) -> Dict:
        """Trả về toàn bộ cấu hình dưới dạng dictionary"""
        return self.config.copy()
    
    def __repr__(self):
        return f"Config(file={self.config_file}, sections={list(self.config.keys())})"
    
    def __str__(self):
        return json.dumps(self.config, indent=2, ensure_ascii=False)


def create_template_config(file_path: str = 'config_template.json'):
    """
    Tạo file template cấu hình
    
    Args:
        file_path: Đường dẫn file template
    """
    config = Config()
    config.save(file_path)
    print(f"Template config created at: {file_path}")


if __name__ == '__main__':
    # Test
    cfg = Config()
    print(f"Default bearing capacity: {cfg.get_nested('pile_configs.bearing_capacity')}")
    
    # Thay đổi giá trị
    cfg.set('pile_configs.bearing_capacity', 600)
    print(f"Updated bearing capacity: {cfg.get_nested('pile_configs.bearing_capacity')}")
    
    # Lưu
    cfg.save('test_config.json')
    print("Config saved to test_config.json")
