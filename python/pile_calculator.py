#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module: pile_calculator.py
Tính toán và bố trí cọc móng tối ưu
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import json
import csv


@dataclass
class Pile:
    """Lớp biểu diễn một cọc"""
    pile_id: str
    x: float
    y: float
    z: float = 0
    diameter: float = 0.8
    length: float = 15.0
    bearing_capacity: float = 500  # tấn
    load: float = 0  # Tải trọng (tấn)
    utilization: float = 0  # Tỷ lệ sử dụng (%)
    
    def get_eccentricity(self) -> float:
        """Tính tâm sai từ tâm cộc"""
        # Giả định tâm cộc là (0,0)
        return (self.x**2 + self.y**2)**0.5
    
    def __repr__(self):
        return f"Pile({self.pile_id}, ({self.x:.2f}, {self.y:.2f}), Load={self.load:.1f}t, Util={self.utilization:.1f}%)"


@dataclass
class PileGroup:
    """Lớp biểu diễn một nhóm cọc cho một cột"""
    column_id: str
    column_x: float
    column_y: float
    column_z: float
    pz: float  # Lực dọc (tấn)
    px: float = 0  # Lực ngang X (tấn)
    py: float = 0  # Lực ngang Y (tấn)
    mx: float = 0  # Momen quanh X (tấn.m)
    my: float = 0  # Momen quanh Y (tấn.m)
    piles: List[Pile] = field(default_factory=list)
    
    def get_total_capacity(self) -> float:
        """Tổng sức chịu tải của nhóm cọc"""
        return sum(p.bearing_capacity for p in self.piles)
    
    def get_total_load(self) -> float:
        """Tổng tải trọng trên nhóm cọc"""
        return sum(p.load for p in self.piles)
    
    def get_center_of_gravity(self) -> Tuple[float, float]:
        """Tính trọng tâm của nhóm cọc"""
        if not self.piles:
            return 0, 0
        
        sum_x = sum(p.x for p in self.piles)
        sum_y = sum(p.y for p in self.piles)
        n = len(self.piles)
        
        return sum_x / n, sum_y / n
    
    def __repr__(self):
        return f"PileGroup({self.column_id}, {len(self.piles)} piles, Total={self.get_total_load():.1f}t)"


class PileCalculator:
    """Lớp tính toán bố trí cọc"""
    
    def __init__(self, config: Dict = None):
        """
        Khởi tạo calculator
        
        Args:
            config: Dictionary chứa cấu hình
                - bearing_capacity: Sức chịu tải/cọc (tấn)
                - pile_diameter: Đường kính cọc (m)
                - pile_length: Chiều dài cọc (m)
                - min_distance: Khoảng cách tối thiểu giữa cọc (m)
                - max_distance: Khoảng cách tối đa (m)
                - grid_type: Kiểu bố trí (grid/circular/flexible)
                - load_safety_factor: Hệ số an toàn
        """
        if config is None:
            config = {}
        
        self.bearing_capacity = config.get('bearing_capacity', 500)
        self.pile_diameter = config.get('pile_diameter', 0.8)
        self.pile_length = config.get('pile_length', 15.0)
        self.min_distance = config.get('min_distance', 3.0)
        self.max_distance = config.get('max_distance', 10.0)
        self.layout_type = config.get('grid_type', 'flexible')
        self.safety_factor = config.get('load_safety_factor', 1.3)
        self.eccentricity_limit = config.get('eccentricity_limit', 0.15)  # L/6
    
    def layout_piles_for_column(self, column_id: str, column_x: float, column_y: float,
                               column_z: float, pz: float, px: float = 0, py: float = 0,
                               mx: float = 0, my: float = 0) -> PileGroup:
        """
        Tính toán bố trí cọc cho một cột
        
        Args:
            column_id: ID cột
            column_x, column_y, column_z: Tọa độ cột
            pz: Lực dọc (tấn, giá trị dương)
            px, py: Lực ngang (tấn)
            mx, my: Momen (tấn.m)
        
        Returns:
            Đối tượng PileGroup chứa danh sách cọc
        """
        # Tạo pile group
        group = PileGroup(
            column_id=column_id,
            column_x=column_x,
            column_y=column_y,
            column_z=column_z,
            pz=abs(pz),
            px=px,
            py=py,
            mx=mx,
            my=my
        )
        
        # Tính số cọc cần thiết
        num_piles = self._calculate_number_of_piles(abs(pz))
        
        if num_piles == 0:
            return group
        
        # Bố trí cọc
        if self.layout_type == 'grid':
            pile_positions = self._layout_grid(num_piles)
        elif self.layout_type == 'circular':
            pile_positions = self._layout_circular(num_piles)
        else:  # flexible
            # Chọn loại bố trí tối ưu dựa trên số cọc
            if num_piles <= 4:
                pile_positions = self._layout_grid(num_piles)
            else:
                pile_positions = self._layout_circular(num_piles)
        
        # Tạo các cọc
        for i, (rel_x, rel_y) in enumerate(pile_positions):
            pile_x = column_x + rel_x
            pile_y = column_y + rel_y
            
            pile = Pile(
                pile_id=f"{column_id}_P{i+1}",
                x=pile_x,
                y=pile_y,
                z=column_z,
                diameter=self.pile_diameter,
                length=self.pile_length,
                bearing_capacity=self.bearing_capacity
            )
            
            group.piles.append(pile)
        
        # Phân bố tải trọng
        self._distribute_loads(group)
        
        return group
    
    def _calculate_number_of_piles(self, vertical_load: float) -> int:
        """
        Tính số cọc cần thiết dựa trên lực dọc
        
        Args:
            vertical_load: Lực dọc (tấn)
        
        Returns:
            Số cọc cần thiết
        """
        if vertical_load <= 0:
            return 0
        
        # Tính số cọc = Lực / (Sức chịu tải * Hệ số an toàn)
        required_capacity = vertical_load * self.safety_factor
        num_piles = int(math.ceil(required_capacity / self.bearing_capacity))
        
        # Tối thiểu 2 cọc
        return max(2, num_piles)
    
    def _layout_grid(self, num_piles: int) -> List[Tuple[float, float]]:
        """
        Bố trí cọc theo lưới hình vuông
        
        Args:
            num_piles: Số cọc
        
        Returns:
            Danh sách tọa độ tương đối (rel_x, rel_y)
        """
        positions = []
        
        # Tính grid size
        side = math.ceil(math.sqrt(num_piles))
        spacing = self.min_distance + self.pile_diameter
        
        # Bố trí từ tâm
        offset = (side - 1) * spacing / 2
        
        count = 0
        for i in range(side):
            for j in range(side):
                if count >= num_piles:
                    break
                
                x = i * spacing - offset
                y = j * spacing - offset
                positions.append((x, y))
                count += 1
            
            if count >= num_piles:
                break
        
        return positions
    
    def _layout_circular(self, num_piles: int) -> List[Tuple[float, float]]:
        """
        Bố trí cọc theo hình tròn
        
        Args:
            num_piles: Số cọc
        
        Returns:
            Danh sách tọa độ tương đối (rel_x, rel_y)
        """
        positions = []
        
        if num_piles == 1:
            return [(0, 0)]
        
        # Tính bán kính dựa trên khoảng cách tối thiểu
        min_arc_length = self.min_distance + self.pile_diameter
        radius = max(self.pile_diameter, min_arc_length / (2 * math.pi / num_piles))
        
        # Bố trí cọc trên vòng tròn
        for i in range(num_piles):
            angle = 2 * math.pi * i / num_piles
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions.append((x, y))
        
        return positions
    
    def _distribute_loads(self, group: PileGroup):
        """
        Phân bố tải trọng cho các cọc
        
        Args:
            group: Nhóm cọc
        """
        if not group.piles:
            return
        
        n = len(group.piles)
        
        # Tải trọng từ lực dọc (phân bố đều)
        vertical_load_per_pile = group.pz / n
        
        # Lực ngang và momen (giả định phân bố theo vị trí)
        for pile in group.piles:
            # Lực dọc
            pile.load = vertical_load_per_pile
            
            # Lực ngang (giả định phân bố đều)
            if group.px != 0 or group.py != 0:
                ph = (group.px**2 + group.py**2)**0.5
                # Giả định mỗi cọc chịu 1/n lực ngang
                pile.load += ph / n * 0.3  # Hệ số 0.3 cho lực ngang
            
            # Momen (giả định phân bố theo khoảng cách từ tâm)
            if group.mx != 0 or group.my != 0:
                distance = (pile.x - group.column_x)**2 + (pile.y - group.column_y)**2
                distance = math.sqrt(distance) if distance > 0 else 0.1
                # Tải từ momen
                moment_magnitude = (group.mx**2 + group.my**2)**0.5
                if distance > 0:
                    # Giả định tải momen tỷ lệ với khoảng cách
                    pile.load += moment_magnitude / distance / n * 0.2
            
            # Tính tỷ lệ sử dụng
            if pile.bearing_capacity > 0:
                pile.utilization = (pile.load / pile.bearing_capacity) * 100
            else:
                pile.utilization = 0
    
    def validate_pile_group(self, group: PileGroup) -> Dict:
        """
        Kiểm tra tính hợp lệ của nhóm cọc
        
        Args:
            group: Nhóm cọc cần kiểm tra
        
        Returns:
            Dictionary chứa thông tin kiểm tra:
            - valid: Boolean
            - errors: List lỗi
            - warnings: List cảnh báo
            - max_utilization: Tỷ lệ sử dụng tối đa
        """
        errors = []
        warnings = []
        max_utilization = 0
        
        if not group.piles:
            errors.append("No piles in group")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings,
                'max_utilization': 0
            }
        
        # Kiểm tra tổng sức chịu tải
        total_capacity = group.get_total_capacity()
        total_load = group.get_total_load()
        
        if total_load > total_capacity:
            errors.append(f"Total load ({total_load:.1f}t) exceeds total capacity ({total_capacity:.1f}t)")
        
        # Kiểm tra từng cọc
        for pile in group.piles:
            max_utilization = max(max_utilization, pile.utilization)
            
            if pile.utilization > 100:
                errors.append(f"Pile {pile.pile_id} overloaded ({pile.utilization:.1f}%)")
            elif pile.utilization > 90:
                warnings.append(f"Pile {pile.pile_id} heavily loaded ({pile.utilization:.1f}%)")
        
        # Kiểm tra tâm sai
        cog_x, cog_y = group.get_center_of_gravity()
        eccentricity = math.sqrt((cog_x - group.column_x)**2 + (cog_y - group.column_y)**2)
        max_eccentricity = group.column_z / 6 if group.column_z > 0 else self.pile_length / 6
        
        if eccentricity > max_eccentricity:
            warnings.append(f"Eccentricity ({eccentricity:.2f}m) exceeds limit ({max_eccentricity:.2f}m)")
        
        # Kiểm tra khoảng cách giữa cọc
        for i, pile1 in enumerate(group.piles):
            for pile2 in group.piles[i+1:]:
                distance = math.sqrt((pile1.x - pile2.x)**2 + (pile1.y - pile2.y)**2)
                if distance < self.min_distance:
                    warnings.append(f"Distance between {pile1.pile_id} and {pile2.pile_id} ({distance:.2f}m) less than minimum ({self.min_distance}m)")
        
        valid = len(errors) == 0
        
        return {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'max_utilization': max_utilization
        }
    
    def export_to_csv(self, pile_groups: List[PileGroup], file_path: str):
        """
        Export dữ liệu cọc ra CSV
        
        Args:
            pile_groups: Danh sách nhóm cọc
            file_path: Đường dẫn file output
        """
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Column_ID', 'Pile_ID', 'X', 'Y', 'Z', 'Diameter', 'Length',
                'Bearing_Capacity', 'Load', 'Utilization_%'
            ])
            
            # Dữ liệu
            for group in pile_groups:
                for pile in group.piles:
                    writer.writerow([
                        group.column_id,
                        pile.pile_id,
                        f"{pile.x:.2f}",
                        f"{pile.y:.2f}",
                        f"{pile.z:.2f}",
                        f"{pile.diameter:.2f}",
                        f"{pile.length:.2f}",
                        f"{pile.bearing_capacity:.2f}",
                        f"{pile.load:.2f}",
                        f"{pile.utilization:.1f}"
                    ])
    
    def export_to_json(self, pile_groups: List[PileGroup], file_path: str):
        """
        Export dữ liệu cọc ra JSON
        
        Args:
            pile_groups: Danh sách nhóm cọc
            file_path: Đường dẫn file output
        """
        data = {
            'metadata': {
                'bearing_capacity_per_pile': self.bearing_capacity,
                'pile_diameter': self.pile_diameter,
                'pile_length': self.pile_length,
                'min_distance': self.min_distance,
                'safety_factor': self.safety_factor
            },
            'pile_groups': []
        }
        
        for group in pile_groups:
            group_data = {
                'column_id': group.column_id,
                'column_location': {'x': group.column_x, 'y': group.column_y, 'z': group.column_z},
                'loads': {'pz': group.pz, 'px': group.px, 'py': group.py, 'mx': group.mx, 'my': group.my},
                'num_piles': len(group.piles),
                'total_capacity': group.get_total_capacity(),
                'total_load': group.get_total_load(),
                'piles': []
            }
            
            for pile in group.piles:
                pile_data = {
                    'pile_id': pile.pile_id,
                    'x': pile.x,
                    'y': pile.y,
                    'z': pile.z,
                    'diameter': pile.diameter,
                    'length': pile.length,
                    'bearing_capacity': pile.bearing_capacity,
                    'load': pile.load,
                    'utilization_percent': pile.utilization
                }
                group_data['piles'].append(pile_data)
            
            data['pile_groups'].append(group_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
