#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ETAB to CAD Pile Layout Tool - Main Entry Point
Tích hợp đọc ETAB → tính toán bố trí cọc → export sang CAD
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Import modules
from etab_reader import load_etab_data, ETABSReader
from pile_calculator import PileCalculator, PileGroup
from config import Config


class ETABToCADPileTool:
    """Class chính điều phối toàn bộ quy trình"""
    
    def __init__(self, config_file: str = None):
        """
        Khởi tạo tool
        
        Args:
            config_file: Đường dẫn file cấu hình JSON
        """
        self.config = Config(config_file)
        self.etab_reader = None
        self.pile_calculator = None
        self.pile_groups = []
    
    def setup(self):
        """Khởi tạo các thành phần"""
        print("\n" + "="*60)
        print("🏗️  ETAB to CAD Pile Layout Tool")
        print("="*60)
        
        # Khởi tạo calculator
        pile_config = self.config.get('pile_configs', {})
        self.pile_calculator = PileCalculator(pile_config)
        
        print(f"\n📋 Configuration:")
        print(f"   Bearing Capacity: {self.pile_calculator.bearing_capacity} tấn/cọc")
        print(f"   Pile Diameter: {self.pile_calculator.pile_diameter} m")
        print(f"   Pile Length: {self.pile_calculator.pile_length} m")
        print(f"   Min Distance: {self.pile_calculator.min_distance} m")
        print(f"   Layout Type: {self.pile_calculator.layout_type}")
        print(f"   Safety Factor: {self.pile_calculator.safety_factor}")
    
    def load_etab_file(self, file_path: str) -> bool:
        """
        Tải file ETAB
        
        Args:
            file_path: Đường dẫn file ETAB/CSV/Excel
        
        Returns:
            True nếu thành công
        """
        try:
            print(f"\n📂 Loading ETAB file: {file_path}")
            self.etab_reader = load_etab_data(file_path)
            print(f"✅ Successfully loaded {len(self.etab_reader)} columns")
            return True
        except Exception as e:
            print(f"❌ Error loading ETAB file: {e}")
            return False
    
    def calculate_pile_layout(self) -> bool:
        """
        Tính toán bố trí cọc cho tất cả các cột
        
        Returns:
            True nếu thành công
        """
        if not self.etab_reader or not self.pile_calculator:
            print("❌ ETAB reader or calculator not initialized")
            return False
        
        try:
            print(f"\n🔧 Calculating pile layout for {len(self.etab_reader)} columns...")
            
            self.pile_groups = []
            
            for col in self.etab_reader:
                # Lấy nội lực lớn nhất
                load_case, pz = col.get_max_vertical_force()
                
                if pz <= 0:
                    print(f"   ⚠️  Column {col.col_id}: Pz = 0, skipping")
                    continue
                
                # Lấy lực ngang và momen
                _, ph = col.get_max_horizontal_force()
                _, m = col.get_max_moment()
                
                # Giả sử lực ngang phân bố đều
                px = ph / math.sqrt(2) if ph > 0 else 0
                py = ph / math.sqrt(2) if ph > 0 else 0
                mx = m / math.sqrt(2) if m > 0 else 0
                my = m / math.sqrt(2) if m > 0 else 0
                
                # Tính toán bố trí cọc
                pile_group = self.pile_calculator.layout_piles_for_column(
                    column_id=col.col_id,
                    column_x=col.x,
                    column_y=col.y,
                    column_z=col.z,
                    pz=abs(pz),
                    px=px,
                    py=py,
                    mx=mx,
                    my=my
                )
                
                # Kiểm tra tính hợp lệ
                validation = self.pile_calculator.validate_pile_group(pile_group)
                
                status = "✅" if validation['valid'] else "⚠️ "
                util = validation['max_utilization']
                print(f"   {status} Column {col.col_id}: {len(pile_group.piles)} piles, Utilization: {util:.1f}%")
                
                if validation['errors']:
                    for error in validation['errors']:
                        print(f"      ❌ {error}")
                
                if validation['warnings']:
                    for warning in validation['warnings']:
                        print(f"      ⚠️  {warning}")
                
                self.pile_groups.append(pile_group)
            
            print(f"\n✅ Calculated layout for {len(self.pile_groups)} columns")
            return True
        
        except Exception as e:
            print(f"❌ Error calculating pile layout: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def export_results(self) -> bool:
        """
        Export kết quả ra các file
        
        Returns:
            True nếu thành công
        """
        try:
            output_dir = self.config.get('output_directory', 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"\n💾 Exporting results to {output_dir}/")
            
            # Export CSV
            if self.config.get_nested('output_format.csv', True):
                csv_file = os.path.join(output_dir, 'pile_layout.csv')
                self.pile_calculator.export_to_csv(self.pile_groups, csv_file)
            
            # Export JSON
            if self.config.get_nested('output_format.json', True):
                json_file = os.path.join(output_dir, 'pile_layout.json')
                self.pile_calculator.export_to_json(self.pile_groups, json_file)
            
            # Export summary report
            self.export_summary_report(output_dir)
            
            print(f"✅ All results exported to {output_dir}/")
            return True
        
        except Exception as e:
            print(f"❌ Error exporting results: {e}")
            return False
    
    def export_summary_report(self, output_dir: str):
        """
        Xuất báo cáo tóm tắt
        
        Args:
            output_dir: Thư mục output
        """
        report_file = os.path.join(output_dir, 'pile_summary_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ETAB TO CAD PILE LAYOUT - SUMMARY REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write("CONFIGURATION:\n")
            f.write("-" * 70 + "\n")
            f.write(f"Bearing Capacity per Pile: {self.pile_calculator.bearing_capacity} tấn\n")
            f.write(f"Pile Diameter: {self.pile_calculator.pile_diameter} m\n")
            f.write(f"Pile Length: {self.pile_calculator.pile_length} m\n")
            f.write(f"Min Distance between Piles: {self.pile_calculator.min_distance} m\n")
            f.write(f"Layout Type: {self.pile_calculator.layout_type}\n")
            f.write(f"Safety Factor: {self.pile_calculator.safety_factor}\n\n")
            
            f.write("RESULTS:\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Columns: {len(self.pile_groups)}\n")
            f.write(f"Total Piles: {sum(len(g.piles) for g in self.pile_groups)}\n\n")
            
            f.write("COLUMN DETAILS:\n")
            f.write("-" * 70 + "\n")
            
            for group in self.pile_groups:
                f.write(f"\nColumn: {group.column_id}\n")
                f.write(f"  Location: ({group.column_x:.2f}, {group.column_y:.2f}, {group.column_z:.2f})\n")
                f.write(f"  Vertical Load (Pz): {group.pz:.2f} tấn\n")
                f.write(f"  Horizontal Load (Ph): {(group.px**2 + group.py**2)**0.5:.2f} tấn\n")
                f.write(f"  Number of Piles: {len(group.piles)}\n")
                f.write(f"  Total Capacity: {group.get_total_capacity():.2f} tấn\n")
                
                max_util = max(p.utilization for p in group.piles) if group.piles else 0
                f.write(f"  Max Utilization: {max_util:.1f}%\n")
                
                f.write(f"\n  Pile Details:\n")
                for pile in group.piles:
                    f.write(f"    {pile.pile_id}: ({pile.x:.2f}, {pile.y:.2f}) - Load: {pile.load:.2f}t ({pile.utilization:.1f}%)\n")
        
        print(f"✅ Summary report exported: {report_file}")
    
    def run(self, etab_file: str) -> bool:
        """
        Chạy toàn bộ quy trình
        
        Args:
            etab_file: Đường dẫn file ETAB
        
        Returns:
            True nếu thành công
        """
        self.setup()
        
        if not self.load_etab_file(etab_file):
            return False
        
        if not self.calculate_pile_layout():
            return False
        
        if not self.export_results():
            return False
        
        print("\n" + "="*60)
        print("✅ Process completed successfully!")
        print("="*60)
        print(f"\n📊 Next steps:")
        print(f"   1. Review pile_layout.csv in output/ folder")
        print(f"   2. Open AutoCAD and run the PileLayout macro")
        print(f"   3. Select the pile_layout.csv file to draw piles")
        print(f"   4. Verify the layout and adjust if needed\n")
        
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='ETAB to CAD Pile Layout Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python main.py data/etab_export.csv
  python main.py data/etab_export.xlsx -c config.json
  python main.py -h  # Show this help message
        '''
    )
    
    parser.add_argument(
        'etab_file',
        help='Path to ETAB export file (CSV or Excel)'
    )
    
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file (JSON)',
        default=None
    )
    
    parser.add_argument(
        '--create-template',
        action='store_true',
        help='Create a template configuration file'
    )
    
    args = parser.parse_args()
    
    # Tạo template config nếu yêu cầu
    if args.create_template:
        from config import create_template_config
        create_template_config('config_template.json')
        print("✅ Template config created. Edit it and use with -c option.")
        return 0
    
    # Kiểm tra file ETAB tồn tại
    if not os.path.exists(args.etab_file):
        print(f"❌ ETAB file not found: {args.etab_file}")
        return 1
    
    # Chạy tool
    tool = ETABToCADPileTool(args.config)
    success = tool.run(args.etab_file)
    
    return 0 if success else 1


if __name__ == '__main__':
    import math  # Import math cho hàm calculate_pile_layout
    sys.exit(main())