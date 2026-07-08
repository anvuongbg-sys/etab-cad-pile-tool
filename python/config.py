"""
Configuration module for ETAB to CAD Pile Layout Tool
"""
import json
import os
from typing import Dict, Any

DEFAULT_CONFIG = {
    "etab_file": "",
    "output_directory": "output",
    "pile_configs": {
        "bearing_capacity": 500,           # Sức chịu tải/cọc (tấn)
        "pile_diameter": 0.8,              # Đường kính cọc (m)
        "pile_length": 15.0,               # Chiều dài cọc (m)
        "min_distance": 3.0,               # Khoảng cách tối thiểu (m)
        "max_distance": 10.0,              # Khoảng cách tối đa (m)
        "grid_type": "flexible",           # "grid" hoặc "flexible"
        "grid_spacing": 4.0,               # Khoảng cách lưới (m) nếu chọn grid
        "load_safety_factor": 1.3,         # Hệ số an toàn nội lực
        "eccentricity_limit": 0.15,        # Giới hạn tâm sai (L/6 = 0.167)
    },
    "column_info": {
        "column_width": 0.5,               # Chiều rộng cột (m)
        "column_height": 0.5,              # Chiều cao cột (m)
        "foundation_depth": 1.5,           # Độ sâu móng (m)
    },
    "output_format": {
        "csv": True,
        "json": True,
        "dwg": False,  # Yêu cầu CAD
        "report": True,
    },
    "cad_settings": {
        "pile_layer": "PILE",
        "pile_color": 256,  # Màu BYCOLOR (1=Red, 256=ByLayer)
        "pile_linetype": "CONTINUOUS",
        "text_height": 0.3,
        "units": "Meters",
    }
}

class Config:
    """Class quản lý cấu hình"""
    
    def __init__(self, config_file: str = None):
        """
        Khởi tạo Config
        
        Args:
            config_file: Đường dẫn file cấu hình JSON
        """
        self.config = DEFAULT_CONFIG.copy()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        self._create_output_dirs()
    
    def load_from_file(self, config_file: str):
        """Tải cấu hình từ file JSON"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                self._merge_config(user_config)
            print(f"✅ Loaded config from {config_file}")
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """Merge user config with defaults"""
        for key, value in user_config.items():
            if key in self.config and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def _create_output_dirs(self):
        """Tạo thư mục output"""
        output_dir = self.config.get("output_directory", "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"✅ Created output directory: {output_dir}")
    
    def get(self, key: str, default=None):
        """Lấy giá trị cấu hình"""
        return self.config.get(key, default)
    
    def get_nested(self, keys: str, default=None):
        """
        Lấy giá trị nested (ví dụ: 'pile_configs.bearing_capacity')
        
        Args:
            keys: Chuỗi khóa lồng nhau cách bằng dấu chấm
            default: Giá trị mặc định
        
        Returns:
            Giá trị tìm được hoặc default
        """
        keys_list = keys.split('.')
        value = self.config
        
        for key in keys_list:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def save_to_file(self, output_file: str):
        """Lưu cấu hình hiện tại ra file"""
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved config to {output_file}")
    
    def __repr__(self):
        return json.dumps(self.config, indent=2, ensure_ascii=False)


def create_template_config(output_file: str = "config_template.json"):
    """Tạo file cấu hình mẫu"""
    config = Config()
    config.save_to_file(output_file)
    print(f"✅ Template config created: {output_file}")


if __name__ == "__main__":
    # Test
    cfg = Config()
    print("Default config:")
    print(cfg)
    print("\nBearing capacity:", cfg.get_nested("pile_configs.bearing_capacity"))