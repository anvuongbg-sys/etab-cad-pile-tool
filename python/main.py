#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module: main.py
Entry point chính của ETAB to CAD Pile Layout Tool

Cách sử dụng:
    python main.py <input_file> [--config <config_file>] [--output <output_dir>]
    python main.py --create-template
"""

import sys
import argparse
import os
from pathlib import Path

# Import các module
from etab_reader import load_etab_data
from pile_calculator import PileCalculator
from config import Config, create_template_config


def create_output_directory(output_dir: str):
    """
    Tạo thư mục output nếu chưa tồn tại
    
    Args:
        output_dir: Đường dẫn thư mục
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def generate_report(calculator: PileCalculator, pile_groups, config: Config, file_path: str):
    """
    Tạo báo cáo text tóm tắt
    
    Args:
        calculator: PileCalculator instance
        pile_groups: Danh sách PileGroup
        config: Config instance
        file_path: Đường dẫn file output
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("ETAB TO CAD PILE LAYOUT REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        # Cấu hình
        f.write("CONFIGURATION\n")
        f.write("-" * 80 + "\n")
        cfg = config.get('pile_configs', {})
        f.write(f"Bearing Capacity/Pile:  {cfg.get('bearing_capacity', 500):.1f} t\n")
        f.write(f"Pile Diameter:          {cfg.get('pile_diameter', 0.8):.2f} m\n")
        f.write(f"Pile Length:            {cfg.get('pile_length', 15.0):.2f} m\n")
        f.write(f"Minimum Distance:       {cfg.get('min_distance', 3.0):.2f} m\n")
        f.write(f"Layout Type:            {cfg.get('grid_type', 'flexible')}\n")
        f.write(f"Safety Factor:          {cfg.get('load_safety_factor', 1.3):.2f}\n")
        f.write("\n")
        
        # TẮ ngách
        f.write("PILE LAYOUT SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Column ID':<15} {'Num Piles':<12} {'Total Load (t)':<18} {'Capacity (t)':<15} {'Max Util (%)':<12}\n")
        f.write("-" * 80 + "\n")
        
        total_piles = 0
        total_load = 0
        max_util_overall = 0
        errors_list = []
        warnings_list = []
        
        for group in pile_groups:
            num_piles = len(group.piles)
            group_load = group.get_total_load()
            capacity = group.get_total_capacity()
            
            # Kiểm tra nhóm
            validation = calculator.validate_pile_group(group)
            
            max_util = validation['max_utilization']
            max_util_overall = max(max_util_overall, max_util)
            
            f.write(f"{group.column_id:<15} {num_piles:<12} {group_load:<18.2f} {capacity:<15.2f} {max_util:<12.1f}\n")
            
            total_piles += num_piles
            total_load += group_load
            
            # Thu thập lỗi và cảnh báo
            if validation['errors']:
                errors_list.extend([(group.column_id, e) for e in validation['errors']])
            if validation['warnings']:
                warnings_list.extend([(group.column_id, w) for w in validation['warnings']])
        
        f.write("-" * 80 + "\n")
        f.write(f"{'TOTAL':<15} {total_piles:<12} {total_load:<18.2f} {sum(g.get_total_capacity() for g in pile_groups):<15.2f} {max_util_overall:<12.1f}\n")
        f.write("\n")
        
        # Lỗi
        if errors_list:
            f.write("ERRORS\n")
            f.write("-" * 80 + "\n")
            for col_id, error in errors_list:
                f.write(f"  [{col_id}] {error}\n")
            f.write("\n")
        
        # Cảnh báo
        if warnings_list:
            f.write("WARNINGS\n")
            f.write("-" * 80 + "\n")
            for col_id, warning in warnings_list:
                f.write(f"  [{col_id}] {warning}\n")
            f.write("\n")
        
        # Chi tiết từng cọc
        f.write("PILE DETAILS\n")
        f.write("-" * 80 + "\n")
        for group in pile_groups:
            f.write(f"\nColumn: {group.column_id}\n")
            f.write(f"  Location: ({group.column_x:.2f}, {group.column_y:.2f}, {group.column_z:.2f})\n")
            f.write(f"  Loads: Pz={group.pz:.1f}t, Px={group.px:.1f}t, Py={group.py:.1f}t\n")
            f.write(f"  Moments: Mx={group.mx:.1f}t.m, My={group.my:.1f}t.m\n")
            f.write(f"\n  {'Pile ID':<15} {'X (m)':<12} {'Y (m)':<12} {'Load (t)':<12} {'Util (%)':<12}\n")
            f.write(f"  {'-'*63}\n")
            
            for pile in group.piles:
                f.write(f"  {pile.pile_id:<15} {pile.x:<12.2f} {pile.y:<12.2f} {pile.load:<12.2f} {pile.utilization:<12.1f}\n")


def main():
    """
    Hàm chính
    """
    parser = argparse.ArgumentParser(
        description='ETAB to CAD Pile Layout Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ví dụ:
  python main.py data/etab_export.csv
  python main.py data/etab_export.xlsx -c config.json
  python main.py --create-template
        '''
    )
    
    parser.add_argument('input_file', nargs='?', help='File ETAB (CSV hoặc Excel)')
    parser.add_argument('-c', '--config', help='File cấu hình JSON')
    parser.add_argument('-o', '--output', default='output', help='Thư mục output (mặc định: output)')
    parser.add_argument('--create-template', action='store_true', help='Tạo file template cấu hình')
    
    args = parser.parse_args()
    
    try:
        # Tạo template cấu hình
        if args.create_template:
            create_template_config(f"{args.output}/config_template.json")
            print(f"\u2705 Template config created at: {args.output}/config_template.json")
            return 0
        
        # Kiểm tra file input
        if not args.input_file:
            parser.print_help()
            return 1
        
        if not os.path.exists(args.input_file):
            print(f"\u274c Error: Input file not found: {args.input_file}")
            return 1
        
        print(f"\n{'='*60}")
        print(f"ETAB to CAD Pile Layout Tool")
        print(f"{'='*60}")
        
        # Tạo output directory
        create_output_directory(args.output)
        print(f"\n📁 Output directory: {os.path.abspath(args.output)}")
        
        # Tải cấu hình
        config = Config(args.config) if args.config else Config()
        print(f"\n⚡ Loading configuration...")
        print(f"  - Bearing capacity: {config.get('pile_configs.bearing_capacity')} t/pile")
        print(f"  - Pile diameter: {config.get('pile_configs.pile_diameter')} m")
        print(f"  - Layout type: {config.get('pile_configs.grid_type')}")
        
        # Đọc dữ liệu ETAB
        print(f"\n📄 Reading ETAB file: {args.input_file}")
        reader = load_etab_data(args.input_file)
        print(f"  - Found {len(reader)} columns")
        
        # Tạo calculator
        calculator = PileCalculator(config.get('pile_configs'))
        
        # Tạo bố trí cọc
        print(f"\n🔨 Calculating pile layouts...")
        pile_groups = []
        
        for column in reader:
            max_case, max_pz = column.get_max_vertical_force()
            max_case_h, max_ph = column.get_max_horizontal_force()
            max_case_m, max_m = column.get_max_moment()
            
            if max_pz > 0:
                group = calculator.layout_piles_for_column(
                    column_id=column.col_id,
                    column_x=column.x,
                    column_y=column.y,
                    column_z=0,
                    pz=max_pz,
                    px=max_ph,
                    py=0,
                    mx=max_m,
                    my=0
                )
                pile_groups.append(group)
                print(f"  - {column.col_id}: {len(group.piles)} piles, Load={group.pz:.1f}t")
        
        if not pile_groups:
            print(f"\n\u26a0 No valid columns found")
            return 1
        
        # Export CSV
        csv_path = os.path.join(args.output, 'pile_layout.csv')
        calculator.export_to_csv(pile_groups, csv_path)
        print(f"\n✅ CSV exported: {csv_path}")
        
        # Export JSON
        json_path = os.path.join(args.output, 'pile_layout.json')
        calculator.export_to_json(pile_groups, json_path)
        print(f"\u2705 JSON exported: {json_path}")
        
        # Tạo báo cáo
        report_path = os.path.join(args.output, 'pile_summary_report.txt')
        generate_report(calculator, pile_groups, config, report_path)
        print(f"\u2705 Report exported: {report_path}")
        
        # Kiểm tra tổng quát
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        
        total_piles = sum(len(g.piles) for g in pile_groups)
        total_load = sum(g.pz for g in pile_groups)
        total_capacity = sum(g.get_total_capacity() for g in pile_groups)
        
        print(f"Total columns: {len(pile_groups)}")
        print(f"Total piles: {total_piles}")
        print(f"Total load: {total_load:.1f} t")
        print(f"Total capacity: {total_capacity:.1f} t")
        print(f"Utilization: {(total_load/total_capacity)*100:.1f}%")
        
        errors_count = 0
        warnings_count = 0
        for group in pile_groups:
            validation = calculator.validate_pile_group(group)
            errors_count += len(validation['errors'])
            warnings_count += len(validation['warnings'])
        
        if errors_count > 0:
            print(f"\n\u274c Errors: {errors_count}")
        if warnings_count > 0:
            print(f"\u26a0 Warnings: {warnings_count}")
        
        print(f"\n✅ Done! Ready for CAD import.")
        print(f"\n📝 Next steps:")
        print(f"   1. Open AutoCAD")
        print(f"   2. Run VBA macro: PileLayout")
        print(f"   3. Select file: {csv_path}")
        print(f"\n{'='*60}\n")
        
        return 0
    
    except Exception as e:
        print(f"\n\u274c Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
