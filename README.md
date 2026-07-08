# ETAB to CAD Pile Layout Tool

**Công cụ tự động chuyển đổi dữ liệu nội lực từ ETAB sang bố trí cọc móng trên AutoCAD**

## 🎯 Tính năng

✅ **Đọc dữ liệu ETAB**
- Hỗ trợ file CSV, Excel export từ ETAB 2020-2023
- Đọc tọa độ cột và nội lực (Px, Py, Pz, Mx, My, Mz)

✅ **Tính toán bố trí cọc**
- Tính số lượng cọc tối ưu dựa trên lực dọc
- Hỗ trợ 3 kiểu bố trí: **Grid, Circular, Flexible**
- Kiểm tra khoảng cách tối thiểu giữa cọc
- Phân bố tải theo tỷ lệ sức chịu tải

✅ **Kiểm tra và xác thực**
- Kiểm tra sức chịu tải từng cọc
- Cảnh báo tâm sai vượt giới hạn
- Báo cáo tỷ lệ sử dụng (%)

✅ **Vẽ trên AutoCAD**
- Tự động vẽ vòng tròn biểu thị cọc
- Màu sắc theo mức sử dụng (Đỏ/Xanh/Xanh dương)
- Ghi ID cọc tự động

## 📋 Cấu trúc Project

```
etab-cad-pile-tool/
├── python/
│   ├── main.py                  # Entry point chính
│   ├── etab_reader.py           # Đọc file ETAB
│   ├── pile_calculator.py       # Tính toán bố trí cọc
│   ├── config.py                # Quản lý cấu hình
│   ├── requirements.txt         # Python dependencies
│   └── config_template.json     # File cấu hình mẫu
├── vba/
│   ├── PileLayoutModule.bas     # VBA macro cho AutoCAD
│   └── README_VBA.md            # Hướng dẫn VBA
├── output/                      # Thư mục output
│   ├── pile_layout.csv          # Kết quả CSV
│   ├── pile_layout.json         # Kết quả JSON
│   └── pile_summary_report.txt  # Báo cáo tóm tắt
├── README.md                    # File này
└── LICENSE
```

## 🚀 Cài đặt

### Yêu cầu
- Python 3.8+
- AutoCAD 2020 hoặc cao hơn
- pip (Python package manager)

### Bước 1: Clone Repository

```bash
git clone https://github.com/anvuongbg-sys/etab-cad-pile-tool.git
cd etab-cad-pile-tool
```

### Bước 2: Cài đặt Python Dependencies

```bash
cd python
pip install -r requirements.txt
```

### Bước 3: Cài đặt VBA Module (cho AutoCAD)

Xem file `vba/README_VBA.md` để hướng dẫn chi tiết.

## 📖 Hướng dẫn sử dụng

### Bước 1: Chuẩn bị file ETAB

1. Mở file ETAB (.edb) của bạn
2. Chọn **File** → **Export** → **Results** → **Joint Forces**
3. Export thành file CSV hoặc Excel
   - Đảm bảo các cột: **Joint, X, Y, Z, LoadCase, Px, Py, Pz, Mx, My, Mz**

### Bước 2: Cấu hình Tool (tùy chọn)

Tạo file `config.json` trong thư mục `python/`:

```bash
cd python
python main.py --create-template
```

Sửa `config_template.json` theo nhu cầu của bạn:

```json
{
  "pile_configs": {
    "bearing_capacity": 500,      # Sức chịu tải/cọc (tấn)
    "pile_diameter": 0.8,         # Đường kính cọc (m)
    "pile_length": 15.0,          # Chiều dài cọc (m)
    "min_distance": 3.0,          # Khoảng cách tối thiểu (m)
    "grid_type": "flexible",      # "grid", "circular", hoặc "flexible"
    "load_safety_factor": 1.3     # Hệ số an toàn
  }
}
```

### Bước 3: Chạy Tool

```bash
# Sử dụng cấu hình mặc định
python main.py data/etab_export.csv

# Sử dụng file cấu hình tùy chỉnh
python main.py data/etab_export.csv -c config.json

# Sử dụng file Excel
python main.py data/etab_export.xlsx
```

**Kết quả sẽ được lưu trong thư mục `output/`:**
- `pile_layout.csv` - Danh sách chi tiết cọc (để vẽ trên CAD)
- `pile_layout.json` - Dữ liệu đầy đủ (JSON format)
- `pile_summary_report.txt` - Báo cáo tóm tắt

### Bước 4: Vẽ trên AutoCAD

1. Mở file DWG trong AutoCAD
2. Chạy VBA Macro `PileLayout`:
   - Nhấn `Alt + F8`
   - Chọn `PileLayout` → **Run**
3. Chọn file `output/pile_layout.csv`
4. Các cọc sẽ được vẽ tự động trên bản vẽ

## 📊 File đầu ra (Output)

### pile_layout.csv

| Column_ID | Pile_ID | X | Y | Z | Diameter | Length | Bearing_Capacity | Load | Utilization_% |
|-----------|---------|---|---|---|----------|--------|------------------|------|---------------|
| C1 | C1_P1 | 0.00 | 0.00 | 0 | 0.8 | 15.0 | 500 | 125.5 | 25.1 |
| C1 | C1_P2 | 2.00 | 0.00 | 0 | 0.8 | 15.0 | 500 | 125.5 | 25.1 |

### pile_layout.json

```json
{
  "metadata": {
    "bearing_capacity_per_pile": 500,
    "pile_diameter": 0.8,
    "pile_length": 15.0,
    "safety_factor": 1.3
  },
  "pile_groups": [
    {
      "column_id": "C1",
      "pz": 1000.0,
      "num_piles": 3,
      "piles": [...]
    }
  ]
}
```

### pile_summary_report.txt

Báo cáo văn bản tóm tắt với:
- Cấu hình sử dụng
- Số lượng cộng/cọc
- Chi tiết tải trọng từng cọc
- Cảnh báo/lỗi (nếu có)

## 🎨 Màu sắc trên AutoCAD

VBA Module sử dụng màu để biểu thị mức sử dụng cọc:

| Màu | Mức Sử dụng | Ý nghĩa |
|-----|-------------|----------|
| 🔴 Đỏ | ≥ 90% | **Nguy hiểm** - Cần tăng số cọc |
| 🟢 Xanh | 70-89% | **Bình thường** - Sử dụng tốt |
| 🔵 Xanh dương | < 70% | **Có dư địa** - Có thể giảm cọc |

## ⚙️ Các kiểu bố trí cọc

### 1. Grid Layout
Bố trí theo lưới hình vuông đều quanh cột
```
config: "grid_type": "grid"
        "grid_spacing": 4.0  # Khoảng cách giữa cọc
```

### 2. Circular Layout
Bố trí theo vòng tròn quanh cột
```
config: "grid_type": "circular"
```

### 3. Flexible Layout
Tự động chọn giữa circular hoặc grid tùy theo khoảng cách tối thiểu
```
config: "grid_type": "flexible"
```

## 🔍 Kiểm tra dữ liệu

Tool sẽ kiểm tra và cảnh báo:

✗ **Lỗi (Errors)**
- Sức chịu tải tổng < lực dọc
- Cọc vượt tải

⚠️ **Cảnh báo (Warnings)**
- Tâm sai vượt giới hạn L/6
- Cọc sử dụng > 90%

## 🐛 Khắc phục sự cố

### Vấn đề: ModuleNotFoundError
```
giải pháp: pip install -r requirements.txt
```

### Vấn đề: File CSV không được đọc
```
giải pháp: Kiểm tra header columns
          Đảm bảo encoding là UTF-8
```

### Vấn đề: VBA Macro không chạy trên AutoCAD
```
giải pháp: Tools → Macro Security → Set "Low"
          Hoặc thêm file vào Trusted Locations
```

## 📚 API Reference

### ETABSReader
```python
from etab_reader import load_etab_data

reader = load_etab_data('data.csv')
for col in reader:
    print(f"Column {col.col_id}: Pz={col.get_max_vertical_force()[1]}")
```

### PileCalculator
```python
from pile_calculator import PileCalculator

calc = PileCalculator(config)
group = calc.layout_piles_for_column(
    column_id='C1', 
    column_x=0, column_y=0, column_z=0,
    pz=1000  # Load in tons
)
print(f"Number of piles: {len(group.piles)}")
```

### Config Management
```python
from config import Config

cfg = Config('config.json')
print(cfg.get_nested('pile_configs.bearing_capacity'))
```

## 📝 Ví dụ hoàn chỉnh

```bash
# 1. Chuẩn bị file CSV từ ETAB
# 2. Tạo cấu hình
cd python
python main.py --create-template

# 3. Chỉnh sửa config_template.json
# 4. Chạy tool
python main.py ../data/my_etab_export.csv -c config_template.json

# 5. Mở AutoCAD và chạy VBA Macro
# Alt + F8 → PileLayout → Run
```

## 🤝 Đóng góp

Các pull request được chào đón! Vui lòng:
1. Fork repository
2. Tạo feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Mở Pull Request

## 📄 License

Project này được cấp phép dưới MIT License - xem file `LICENSE` để biết chi tiết.

## 💬 Hỗ trợ

- 📧 Email: anvuongbg@gmail.com
- 🐛 Issues: GitHub Issues
- 💡 Suggestions: GitHub Discussions

## 🙏 Lời cảm ơn

Cảm ơn mọi người đã sử dụng tool này. Feedback của bạn giúp chúng tôi cải thiện!

---

**Version**: 1.0.0  
**Last Updated**: 2024-07-08  
**Author**: ETAB to CAD Tool Team
