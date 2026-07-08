"""
Module tính toán và bố trí móng cọc
Dựa trên nội lực từ ETAB, tính toán vị trí và số lượng cọc tối ưu
"""
import math
from typing import List, Dict, Tuple, Optional
import json
import pandas as pd
from dataclasses import dataclass, asdict
from enum import Enum


class LayoutType(Enum):
    """Kiểu bố trí cọc"""
    GRID = "grid"              # Lưới đều
    FLEXIBLE = "flexible"      # Linh hoạt theo nhu cầu
    CIRCULAR = "circular"      # Tròn
    RECTANGULAR = "rectangular" # Chữ nhật


@dataclass
class Pile:
    """Thông tin một cọc"""
    pile_id: str          # ID cọc
    x: float              # Tọa độ X (m)
    y: float              # Tọa độ Y (m)
    z: float              # Tọa độ Z (m)
    diameter: float       # Đường kính (m)
    length: float         # Chiều dài (m)
    bearing_capacity: float  # Sức chịu tải (tấn)
    load: float = 0.0     # Tải trọng thực tế (tấn)
    safety_factor: float = 1.0  # Hệ số an toàn
    utilization: float = 0.0    # Tỷ lệ sử dụng (%)
    
    def to_dict(self) -> dict:
        """Convert thành dict"""
        return asdict(self)
    
    def get_distance_to_point(self, x: float, y: float) -> float:
        """Tính khoảng cách từ cọc đến điểm (x,y)"""
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)
    
    def is_within_capacity(self, safety_factor: float = 1.0) -> bool:
        """Kiểm tra cọc có vượt tải không"""
        return self.load <= (self.bearing_capacity * safety_factor)
    
    def get_utilization_percent(self) -> float:
        """Lấy tỷ lệ sử dụng (%)"""
        if self.bearing_capacity == 0:
            return 0
        return (self.load / self.bearing_capacity) * 100


@dataclass
class PileGroup:
    """Nhóm cọc hỗ trợ một cột"""
    column_id: str       # ID cột
    column_x: float      # Tọa độ cột X
    column_y: float      # Tọa độ cột Y
    column_z: float      # Tọa độ cột Z
    pz: float            # Lực dọc (tấn)
    px: float = 0.0      # Lực ngang X (tấn)
    py: float = 0.0      # Lực ngang Y (tấn)
    mx: float = 0.0      # Momen X (tấn.m)
    my: float = 0.0      # Momen Y (tấn.m)
    piles: List[Pile] = None  # Danh sách cọc
    
    def __post_init__(self):
        if self.piles is None:
            self.piles = []
    
    def add_pile(self, pile: Pile):
        """Thêm một cọc vào nhóm"""
        self.piles.append(pile)
    
    def get_total_capacity(self) -> float:
        """Tính sức chịu tải tổng cộng"""
        return sum(pile.bearing_capacity for pile in self.piles)
    
    def get_load_distribution(self) -> Dict[str, float]:
        """Phân bố tải cho từng cọc"""
        if not self.piles:
            return {}
        
        result = {}
        total_capacity = self.get_total_capacity()
        
        if total_capacity == 0:
            equal_load = self.pz / len(self.piles) if self.piles else 0
            for pile in self.piles:
                result[pile.pile_id] = equal_load
        else:
            for pile in self.piles:
                # Phân bố tỉ lệ thuận với sức chịu tải
                load = (pile.bearing_capacity / total_capacity) * self.pz
                result[pile.pile_id] = load
        
        return result
    
    def calculate_eccentricity(self) -> Tuple[float, float]:
        """Tính tâm sai (e_x, e_y)"""
        if self.pz == 0:
            return 0, 0
        
        e_x = self.my / self.pz if self.pz != 0 else 0
        e_y = self.mx / self.pz if self.pz != 0 else 0
        
        return abs(e_x), abs(e_y)
    
    def to_dict(self) -> dict:
        """Convert thành dict"""
        return {
            'column_id': self.column_id,
            'column_x': self.column_x,
            'column_y': self.column_y,
            'column_z': self.column_z,
            'pz': self.pz,
            'px': self.px,
            'py': self.py,
            'mx': self.mx,
            'my': self.my,
            'num_piles': len(self.piles),
            'total_capacity': self.get_total_capacity(),
            'piles': [pile.to_dict() for pile in self.piles]
        }


class PileCalculator:
    """Class tính toán bố trí cọc"""
    
    def __init__(self, config: dict):
        """
        Args:
            config: Dict cấu hình từ config.py
        """
        self.bearing_capacity = config.get('bearing_capacity', 500)  # tấn/cọc
        self.pile_diameter = config.get('pile_diameter', 0.8)  # m
        self.pile_length = config.get('pile_length', 15.0)  # m
        self.min_distance = config.get('min_distance', 3.0)  # m
        self.max_distance = config.get('max_distance', 10.0)  # m
        self.layout_type = config.get('grid_type', 'flexible')
        self.grid_spacing = config.get('grid_spacing', 4.0)  # m
        self.safety_factor = config.get('load_safety_factor', 1.3)
        self.eccentricity_limit = config.get('eccentricity_limit', 0.15)
    
    def calculate_number_of_piles(self, pz: float) -> int:
        """
        Tính số cọc cần thiết dựa trên lực dọc
        
        Args:
            pz: Lực dọc (tấn)
        
        Returns:
            Số cọc cần thiết (tối thiểu 1)
        """
        if pz <= 0:
            return 1
        
        # Công thức: n = Pz / (Bearing_Capacity * Safety_Factor)
        num_piles = math.ceil(pz / (self.bearing_capacity * self.safety_factor))
        
        return max(1, num_piles)
    
    def generate_grid_layout(self, column_x: float, column_y: float, 
                            num_piles: int) -> List[Tuple[float, float]]:
        """
        Tạo bố trí lưới đều quanh cột
        
        Args:
            column_x, column_y: Tọa độ cột
            num_piles: Số cọc
        
        Returns:
            Danh sách (x, y) vị trí cọc
        """
        if num_piles == 1:
            return [(column_x, column_y)]
        
        # Bố trí theo hình vuông
        side = math.ceil(math.sqrt(num_piles))
        spacing = self.grid_spacing
        offset = (side - 1) * spacing / 2
        
        positions = []
        count = 0
        
        for i in range(side):
            for j in range(side):
                if count >= num_piles:
                    break
                
                x = column_x - offset + i * spacing
                y = column_y - offset + j * spacing
                positions.append((x, y))
                count += 1
            
            if count >= num_piles:
                break
        
        return positions[:num_piles]
    
    def generate_circular_layout(self, column_x: float, column_y: float,
                                num_piles: int) -> List[Tuple[float, float]]:
        """
        Tạo bố trí tròn quanh cột
        
        Args:
            column_x, column_y: Tọa độ cột
            num_piles: Số cọc
        
        Returns:
            Danh sách (x, y) vị trí cọc
        """
        if num_piles == 1:
            return [(column_x, column_y)]
        
        positions = []
        radius = (num_piles * self.pile_diameter) / (2 * math.pi)
        radius = max(radius, self.min_distance)
        
        for i in range(num_piles):
            angle = (2 * math.pi * i) / num_piles
            x = column_x + radius * math.cos(angle)
            y = column_y + radius * math.sin(angle)
            positions.append((x, y))
        
        return positions
    
    def check_minimum_distance(self, positions: List[Tuple[float, float]]) -> bool:
        """
        Kiểm tra khoảng cách tối thiểu giữa các cọc
        
        Args:
            positions: Danh sách (x, y) vị trí cọc
        
        Returns:
            True nếu hợp lệ
        """
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                x1, y1 = positions[i]
                x2, y2 = positions[j]
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if dist < self.min_distance:
                    return False
        
        return True
    
    def layout_piles_for_column(self, column_id: str, column_x: float, 
                               column_y: float, column_z: float,
                               pz: float, px: float = 0, py: float = 0,
                               mx: float = 0, my: float = 0) -> PileGroup:
        """
        Bố trí cọc cho một cột
        
        Args:
            column_id: ID cột
            column_x, column_y, column_z: Tọa độ cột
            pz: Lực dọc (tấn)
            px, py: Lực ngang (tấn)
            mx, my: Momen (tấn.m)
        
        Returns:
            PileGroup object
        """
        # Tạo nhóm cọc
        pile_group = PileGroup(
            column_id=column_id,
            column_x=column_x,
            column_y=column_y,
            column_z=column_z,
            pz=pz,
            px=px,
            py=py,
            mx=mx,
            my=my
        )
        
        # Tính số cọc cần thiết
        num_piles = self.calculate_number_of_piles(pz)
        
        # Tạo bố trí
        if self.layout_type == 'grid':
            positions = self.generate_grid_layout(column_x, column_y, num_piles)
        elif self.layout_type == 'circular':
            positions = self.generate_circular_layout(column_x, column_y, num_piles)
        else:  # flexible
            # Thử circular trước, nếu không được dùng grid
            positions = self.generate_circular_layout(column_x, column_y, num_piles)
            if not self.check_minimum_distance(positions):
                positions = self.generate_grid_layout(column_x, column_y, num_piles)
        
        # Tạo các cọc
        load_dist = pile_group.get_load_distribution()
        
        for i, (x, y) in enumerate(positions):
            pile_id = f"{column_id}_P{i+1}"
            pile = Pile(
                pile_id=pile_id,
                x=x,
                y=y,
                z=column_z,
                diameter=self.pile_diameter,
                length=self.pile_length,
                bearing_capacity=self.bearing_capacity,
                load=load_dist.get(pile_id, pz / len(positions))
            )
            pile.utilization = pile.get_utilization_percent()
            pile_group.add_pile(pile)
        
        return pile_group
    
    def validate_pile_group(self, pile_group: PileGroup) -> Dict[str, any]:
        """
        Kiểm tra nhóm cọc có hợp lệ không
        
        Args:
            pile_group: PileGroup object
        
        Returns:
            Dict chứa kết quả kiểm tra
        """
        result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'eccentricity_x': 0,
            'eccentricity_y': 0,
            'max_utilization': 0,
            'total_capacity': pile_group.get_total_capacity()
        }
        
        # Kiểm tra sức chịu tải tổng
        if pile_group.pz > result['total_capacity']:
            result['errors'].append(
                f"Sức chịu tải tổng ({result['total_capacity']}) < Lực dọc ({pile_group.pz})"
            )
            result['valid'] = False
        
        # Kiểm tra tâm sai
        e_x, e_y = pile_group.calculate_eccentricity()
        result['eccentricity_x'] = e_x
        result['eccentricity_y'] = e_y
        
        # Giả sử chiều dài cạnh = min_distance * 3
        L = self.min_distance * 3
        limit = L / 6
        
        if e_x > limit or e_y > limit:
            result['warnings'].append(
                f"Tâm sai ({e_x:.2f}, {e_y:.2f}) > giới hạn ({limit:.2f})"
            )
        
        # Kiểm tra từng cọc
        max_util = 0
        for pile in pile_group.piles:
            util = pile.get_utilization_percent()
            max_util = max(max_util, util)
            
            if not pile.is_within_capacity(self.safety_factor):
                result['errors'].append(
                    f"Cọc {pile.pile_id} vượt tải: {util:.1f}%"
                )
                result['valid'] = False
            elif util > 90:
                result['warnings'].append(
                    f"Cọc {pile.pile_id} gần vượt tải: {util:.1f}%"
                )
        
        result['max_utilization'] = max_util
        
        return result
    
    def export_to_csv(self, pile_groups: List[PileGroup], output_file: str):
        """
        Export kết quả ra CSV
        
        Args:
            pile_groups: Danh sách PileGroup
            output_file: Đường dẫn file output
        """
        rows = []
        
        for group in pile_groups:
            for pile in group.piles:
                rows.append({
                    'Column_ID': group.column_id,
                    'Pile_ID': pile.pile_id,
                    'X': round(pile.x, 2),
                    'Y': round(pile.y, 2),
                    'Z': round(pile.z, 2),
                    'Diameter': pile.diameter,
                    'Length': pile.length,
                    'Bearing_Capacity': pile.bearing_capacity,
                    'Load': round(pile.load, 2),
                    'Utilization_%': round(pile.utilization, 1),
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"✅ Exported to {output_file}")
    
    def export_to_json(self, pile_groups: List[PileGroup], output_file: str):
        """
        Export kết quả ra JSON
        
        Args:
            pile_groups: Danh sách PileGroup
            output_file: Đường dẫn file output
        """
        data = {
            'metadata': {
                'bearing_capacity_per_pile': self.bearing_capacity,
                'pile_diameter': self.pile_diameter,
                'pile_length': self.pile_length,
                'min_distance': self.min_distance,
                'layout_type': self.layout_type,
                'safety_factor': self.safety_factor,
            },
            'pile_groups': [group.to_dict() for group in pile_groups]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Exported to {output_file}")


if __name__ == "__main__":
    # Test
    config = {
        'bearing_capacity': 500,
        'pile_diameter': 0.8,
        'pile_length': 15.0,
        'min_distance': 3.0,
        'grid_type': 'flexible',
        'grid_spacing': 4.0,
        'load_safety_factor': 1.3,
    }
    
    calc = PileCalculator(config)
    
    # Test với cột C1
    group = calc.layout_piles_for_column(
        column_id='C1',
        column_x=0, column_y=0, column_z=0,
        pz=1000, px=50, py=50, mx=100, my=100
    )
    
    print(f"Column: {group.column_id}")
    print(f"Number of piles: {len(group.piles)}")
    print(f"Total capacity: {group.get_total_capacity()} tấn")
    print(f"Utilization: {max(p.utilization for p in group.piles):.1f}%")
    
    validation = calc.validate_pile_group(group)
    print(f"Valid: {validation['valid']}")
    if validation['errors']:
        print("Errors:", validation['errors'])
    if validation['warnings']:
        print("Warnings:", validation['warnings'])