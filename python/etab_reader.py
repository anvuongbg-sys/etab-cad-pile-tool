#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module: etab_reader.py
Đọc dữ liệu từ file ETAB (CSV/Excel) và xử lý thông tin cột
"""

import os
import csv
from pathlib import Path
from typing import List, Tuple, Dict, Optional

try:
    import pandas as pd
except ImportError:
    pd = None


class Column:
    """Lớp biểu diễn một cột trong ETAB"""
    
    def __init__(self, col_id: str, x: float = 0, y: float = 0, z: float = 0):
        """
        Khởi tạo cột
        
        Args:
            col_id: ID cột (J1, J2, ...)
            x, y, z: Tọa độ cột
        """
        self.col_id = col_id
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.load_cases = {}  # {load_case: {force_dict}}
    
    def add_force(self, load_case: str, px: float = 0, py: float = 0, pz: float = 0,
                  mx: float = 0, my: float = 0, mz: float = 0):
        """
        Thêm lực cho một load case
        
        Args:
            load_case: Tên load case (LC1, LC2, ...)
            px, py, pz: Lực ngang và dọc (tấn)
            mx, my, mz: Momen (tấn.m)
        """
        if load_case not in self.load_cases:
            self.load_cases[load_case] = {}
        
        self.load_cases[load_case]['Px'] = float(px)
        self.load_cases[load_case]['Py'] = float(py)
        self.load_cases[load_case]['Pz'] = float(pz)
        self.load_cases[load_case]['Mx'] = float(mx)
        self.load_cases[load_case]['My'] = float(my)
        self.load_cases[load_case]['Mz'] = float(mz)
    
    def get_max_vertical_force(self) -> Tuple[str, float]:
        """
        Lấy lực dọc lớn nhất (Pz âm = nén)
        
        Returns:
            (load_case, max_pz)
        """
        if not self.load_cases:
            return '', 0
        
        max_case = ''
        max_pz = 0
        
        for case, forces in self.load_cases.items():
            pz = abs(forces.get('Pz', 0))
            if pz > max_pz:
                max_pz = pz
                max_case = case
        
        # Trả về giá trị âm (theo quy ước ETAB)
        return max_case, -max_pz if max_pz > 0 else 0
    
    def get_max_horizontal_force(self) -> Tuple[str, float]:
        """
        Lấy lực ngang lớn nhất (kết hợp Px và Py)
        
        Returns:
            (load_case, max_ph)
        """
        if not self.load_cases:
            return '', 0
        
        max_case = ''
        max_ph = 0
        
        for case, forces in self.load_cases.items():
            px = forces.get('Px', 0)
            py = forces.get('Py', 0)
            ph = (px**2 + py**2)**0.5
            
            if ph > max_ph:
                max_ph = ph
                max_case = case
        
        return max_case, max_ph
    
    def get_max_moment(self) -> Tuple[str, float]:
        """
        Lấy momen lớn nhất (kết hợp Mx và My)
        
        Returns:
            (load_case, max_moment)
        """
        if not self.load_cases:
            return '', 0
        
        max_case = ''
        max_m = 0
        
        for case, forces in self.load_cases.items():
            mx = forces.get('Mx', 0)
            my = forces.get('My', 0)
            m = (mx**2 + my**2)**0.5
            
            if m > max_m:
                max_m = m
                max_case = case
        
        return max_case, max_m
    
    def __repr__(self):
        return f"Column({self.col_id}, {self.x}, {self.y}, {self.z})"


class ETABSReader:
    """Lớp đọc và xử lý dữ liệu từ file ETAB"""
    
    def __init__(self):
        self.columns: Dict[str, Column] = {}
        self.load_cases = set()
    
    def add_column(self, col_id: str, x: float, y: float, z: float) -> Column:
        """
        Thêm một cột mới
        
        Args:
            col_id: ID cột
            x, y, z: Tọa độ
        
        Returns:
            Đối tượng Column được tạo
        """
        if col_id not in self.columns:
            self.columns[col_id] = Column(col_id, x, y, z)
        return self.columns[col_id]
    
    def add_force_to_column(self, col_id: str, load_case: str, 
                           px: float = 0, py: float = 0, pz: float = 0,
                           mx: float = 0, my: float = 0, mz: float = 0):
        """
        Thêm lực vào một cột
        
        Args:
            col_id: ID cột
            load_case: Tên load case
            Lực và momen
        """
        if col_id not in self.columns:
            self.add_column(col_id, 0, 0, 0)
        
        self.columns[col_id].add_force(load_case, px, py, pz, mx, my, mz)
        self.load_cases.add(load_case)
    
    def get_column(self, col_id: str) -> Optional[Column]:
        """Lấy cột theo ID"""
        return self.columns.get(col_id)
    
    def get_all_columns(self) -> List[Column]:
        """Lấy tất cả cột"""
        return list(self.columns.values())
    
    def __len__(self):
        return len(self.columns)
    
    def __iter__(self):
        return iter(self.columns.values())
    
    def __repr__(self):
        return f"ETABSReader({len(self.columns)} columns, {len(self.load_cases)} load cases)"


def load_etab_data(file_path: str) -> ETABSReader:
    """
    Tải dữ liệu ETAB từ file CSV hoặc Excel
    
    Args:
        file_path: Đường dẫn file ETAB
    
    Returns:
        Đối tượng ETABSReader
    
    Raises:
        FileNotFoundError: Nếu file không tồn tại
        ValueError: Nếu format file không hợp lệ
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.csv':
        return _load_csv(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        return _load_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def _load_csv(file_path: str) -> ETABSReader:
    """
    Tải dữ liệu từ file CSV
    
    CSV format expected:
    Joint,X,Y,Z,LoadCase,Px,Py,Pz,Mx,My,Mz
    """
    reader = ETABSReader()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            
            if not csv_reader.fieldnames:
                raise ValueError("CSV file is empty")
            
            # Kiểm tra các cột bắt buộc
            required_cols = ['Joint', 'X', 'Y', 'Z', 'LoadCase', 'Px', 'Py', 'Pz']
            missing_cols = [col for col in required_cols if col not in csv_reader.fieldnames]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            for row in csv_reader:
                if not row['Joint'] or row['Joint'].strip() == '':
                    continue
                
                try:
                    joint_id = row['Joint'].strip()
                    x = float(row['X'])
                    y = float(row['Y'])
                    z = float(row['Z'])
                    load_case = row['LoadCase'].strip()
                    px = float(row['Px'])
                    py = float(row['Py'])
                    pz = float(row['Pz'])
                    mx = float(row.get('Mx', 0))
                    my = float(row.get('My', 0))
                    mz = float(row.get('Mz', 0))
                    
                    # Thêm/cập nhật cột
                    if joint_id not in reader.columns:
                        reader.add_column(joint_id, x, y, z)
                    
                    reader.add_force_to_column(joint_id, load_case, px, py, pz, mx, my, mz)
                
                except ValueError as e:
                    print(f"Warning: Skipped row {row} - {e}")
                    continue
        
        return reader
    
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")


def _load_excel(file_path: str) -> ETABSReader:
    """
    Tải dữ liệu từ file Excel
    """
    if pd is None:
        raise ImportError("pandas is required to read Excel files. Install with: pip install pandas openpyxl")
    
    reader = ETABSReader()
    
    try:
        # Đọc sheet đầu tiên
        df = pd.read_excel(file_path, sheet_name=0)
        
        # Kiểm tra các cột bắt buộc
        required_cols = ['Joint', 'X', 'Y', 'Z', 'LoadCase', 'Px', 'Py', 'Pz']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        for _, row in df.iterrows():
            if pd.isna(row['Joint']) or str(row['Joint']).strip() == '':
                continue
            
            try:
                joint_id = str(row['Joint']).strip()
                x = float(row['X'])
                y = float(row['Y'])
                z = float(row['Z'])
                load_case = str(row['LoadCase']).strip()
                px = float(row['Px'])
                py = float(row['Py'])
                pz = float(row['Pz'])
                mx = float(row.get('Mx', 0)) if 'Mx' in df.columns else 0
                my = float(row.get('My', 0)) if 'My' in df.columns else 0
                mz = float(row.get('Mz', 0)) if 'Mz' in df.columns else 0
                
                # Thêm/cập nhật cột
                if joint_id not in reader.columns:
                    reader.add_column(joint_id, x, y, z)
                
                reader.add_force_to_column(joint_id, load_case, px, py, pz, mx, my, mz)
            
            except (ValueError, TypeError) as e:
                print(f"Warning: Skipped row - {e}")
                continue
        
        return reader
    
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")
