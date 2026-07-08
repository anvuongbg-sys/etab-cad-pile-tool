"""
Module đọc file ETAB (Etabs 2020-2023)
Hỗ trợ đọc nội lực tại chân cột (joint forces)
"""
import os
from typing import List, Dict, Tuple, Optional
import pandas as pd

class ColumnData:
    """Class lưu trữ dữ liệu một cột"""
    
    def __init__(self, col_id: str, x: float, y: float, z: float):
        """
        Args:
            col_id: ID của cột
            x, y, z: Tọa độ cột (m)
        """
        self.col_id = col_id
        self.x = x
        self.y = y
        self.z = z
        self.forces = {}  # {load_case: (Px, Py, Pz, Mx, My, Mz)}
    
    def add_force(self, load_case: str, px: float, py: float, pz: float, 
                  mx: float, my: float, mz: float):
        """Thêm nội lực cho load case"""
        self.forces[load_case] = {
            'Px': px, 'Py': py, 'Pz': pz,
            'Mx': mx, 'My': my, 'Mz': mz
        }
    
    def get_max_vertical_force(self) -> Tuple[str, float]:
        """
        Lấy lực dọc lớn nhất (để kiểm soát)
        
        Returns:
            (load_case, force_value)
        """
        max_pz = 0
        max_case = None
        
        for case, forces in self.forces.items():
            pz = abs(forces['Pz'])
            if pz > max_pz:
                max_pz = pz
                max_case = case
        
        return max_case, max_pz
    
    def get_max_horizontal_force(self) -> Tuple[str, float]:
        """Lấy lực ngang lớn nhất"""
        max_ph = 0
        max_case = None
        
        for case, forces in self.forces.items():
            ph = (forces['Px']**2 + forces['Py']**2)**0.5
            if ph > max_ph:
                max_ph = ph
                max_case = case
        
        return max_case, max_ph
    
    def get_max_moment(self) -> Tuple[str, float]:
        """Lấy momen lớn nhất"""
        max_m = 0
        max_case = None
        
        for case, forces in self.forces.items():
            m = (forces['Mx']**2 + forces['My']**2)**0.5
            if m > max_m:
                max_m = m
                max_case = case
        
        return max_case, max_m
    
    def to_dict(self) -> dict:
        """Convert thành dict"""
        case, pz_max = self.get_max_vertical_force()
        _, ph_max = self.get_max_horizontal_force()
        _, m_max = self.get_max_moment()
        
        return {
            'Column_ID': self.col_id,
            'X': self.x,
            'Y': self.y,
            'Z': self.z,
            'Pz_Max': pz_max,
            'Ph_Max': ph_max,
            'M_Max': m_max,
            'Load_Cases': len(self.forces)
        }


class ETABSReader:
    """Class đọc dữ liệu từ file ETAB"""
    
    def __init__(self, etab_file: str):
        """
        Args:
            etab_file: Đường dẫn file ETAB (.edb)
        """
        self.etab_file = etab_file
        self.columns = {}  # {col_id: ColumnData}
        self.load_cases = []
    
    def read_from_csv(self, csv_file: str) -> Dict[str, ColumnData]:
        """
        Đọc từ file CSV đã export từ ETAB
        
        Format CSV expected:
        Joint,X,Y,Z,LoadCase,Px,Py,Pz,Mx,My,Mz
        
        Args:
            csv_file: Đường dẫn file CSV
        
        Returns:
            Dict của ColumnData objects
        """
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        df = pd.read_csv(csv_file)
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.upper()
        
        print(f"📊 Reading ETAB data from {csv_file}")
        print(f"   Columns: {list(df.columns)}")
        
        # Đọc dữ liệu
        for _, row in df.iterrows():
            col_id = str(row.get('JOINT') or row.get('COL_ID') or row.get('COLUMN'))
            
            # Bỏ qua nếu không có ID
            if pd.isna(col_id) or col_id == '':
                continue
            
            x = float(row.get('X', 0))
            y = float(row.get('Y', 0))
            z = float(row.get('Z', 0))
            
            load_case = str(row.get('LOADCASE', row.get('CASE', 'DEFAULT')))
            
            px = float(row.get('PX', 0))
            py = float(row.get('PY', 0))
            pz = float(row.get('PZ', 0))
            mx = float(row.get('MX', 0))
            my = float(row.get('MY', 0))
            mz = float(row.get('MZ', 0))
            
            # Tạo hoặc cập nhật cột
            if col_id not in self.columns:
                self.columns[col_id] = ColumnData(col_id, x, y, z)
            
            self.columns[col_id].add_force(load_case, px, py, pz, mx, my, mz)
            
            # Lưu load cases
            if load_case not in self.load_cases:
                self.load_cases.append(load_case)
        
        print(f"✅ Read {len(self.columns)} columns")
        print(f"✅ Found {len(self.load_cases)} load cases")
        
        return self.columns
    
    def read_from_excel(self, excel_file: str, sheet_name: str = 0) -> Dict[str, ColumnData]:
        """
        Đọc từ file Excel
        
        Args:
            excel_file: Đường dẫn file Excel
            sheet_name: Tên sheet (default là sheet đầu tiên)
        
        Returns:
            Dict của ColumnData objects
        """
        if not os.path.exists(excel_file):
            raise FileNotFoundError(f"Excel file not found: {excel_file}")
        
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # Tạo CSV tạm và đọc
        temp_csv = "temp_etab_data.csv"
        df.to_csv(temp_csv, index=False)
        
        try:
            result = self.read_from_csv(temp_csv)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
        
        return result
    
    def get_column_summary(self) -> pd.DataFrame:
        """Lấy bảng tóm tắt nội lực các cột"""
        data = [col.to_dict() for col in self.columns.values()]
        df = pd.DataFrame(data)
        return df.sort_values('Pz_Max', ascending=False)
    
    def export_summary(self, output_file: str):
        """Export bảng tóm tắt ra CSV"""
        df = self.get_column_summary()
        df.to_csv(output_file, index=False)
        print(f"✅ Summary exported to {output_file}")
    
    def get_columns_by_load_range(self, pz_min: float, pz_max: float) -> List[ColumnData]:
        """Lấy các cột có nội lực dọc trong khoảng [pz_min, pz_max]"""
        result = []
        for col in self.columns.values():
            _, pz = col.get_max_vertical_force()
            if pz_min <= pz <= pz_max:
                result.append(col)
        return result
    
    def __len__(self):
        return len(self.columns)
    
    def __getitem__(self, col_id: str) -> Optional[ColumnData]:
        return self.columns.get(col_id)
    
    def __iter__(self):
        return iter(self.columns.values())


# Hàm helper
def load_etab_data(file_path: str) -> ETABSReader:
    """
    Helper function để tải dữ liệu ETAB
    
    Args:
        file_path: Đường dẫn file ETAB/CSV/Excel
    
    Returns:
        ETABSReader object
    """
    reader = ETABSReader(file_path)
    
    if file_path.endswith('.csv'):
        reader.read_from_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        reader.read_from_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")
    
    return reader


if __name__ == "__main__":
    # Test example
    import sys
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        reader = load_etab_data(data_file)
        
        print("\n📋 Column Summary:")
        print(reader.get_column_summary())
    else:
        print("Usage: python etab_reader.py <data_file.csv|xlsx>")