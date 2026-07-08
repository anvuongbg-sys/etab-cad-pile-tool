# Hướng dẫn nhanh - ETAB to CAD Pile Layout Tool

## ⚡ Bắt đầu nhanh (5 phút)

### 1️⃣ Chuẩn bị dữ liệu ETAB

**Trong ETAB:**
```
File → Export → Results → Joint Forces
→ Chọn output CSV/Excel
→ Lưu vào folder: data/etab_export.csv
```

**Cấu trúc file CSV:**
```
Joint,X,Y,Z,LoadCase,Px,Py,Pz,Mx,My,Mz
J1,0,0,0,LC1,10,10,-500,50,50,10
J2,5,0,0,LC1,15,15,-650,60,60,15
```

### 2️⃣ Chạy Python Tool

```bash
cd python
python main.py ../data/etab_export.csv
```

**Kết quả:**
- ✅ CSV file: `output/pile_layout.csv`
- ✅ JSON file: `output/pile_layout.json`
- ✅ Report: `output/pile_summary_report.txt`

### 3️⃣ Vẽ trên AutoCAD

**Bước 1:** Mở AutoCAD
```
Alt + F8 → PileLayout → Run
```

**Bước 2:** Chọn file CSV
```
Browse → output/pile_layout.csv → OK
```

**Bước 3:** Xem kết quả
- Các cọc sẽ được vẽ tự động
- Zoom fit: Ctrl + A → Z

## 📋 Tham số cấu hình chính

| Tham số | Giá trị | Ý nghĩa |
|---------|--------|----------|
| `bearing_capacity` | 500 | Sức chịu tải/cọc (tấn) |
| `pile_diameter` | 0.8 | Đường kính cọc (m) |
| `pile_length` | 15.0 | Chiều dài cọc (m) |
| `min_distance` | 3.0 | Khoảng cách tối thiểu (m) |
| `load_safety_factor` | 1.3 | Hệ số an toàn |
| `grid_type` | "flexible" | Kiểu bố trí |

## 🎯 Ví dụ cấu hình cho các loại công trình

### Cao ốc thương mại
```json
{
  "bearing_capacity": 800,
  "pile_diameter": 1.0,
  "pile_length": 25.0,
  "load_safety_factor": 1.5
}
```

### Nhà ở thấp
```json
{
  "bearing_capacity": 300,
  "pile_diameter": 0.6,
  "pile_length": 10.0,
  "load_safety_factor": 1.2
}
```

### Công trình công nghiệp
```json
{
  "bearing_capacity": 1000,
  "pile_diameter": 1.2,
  "pile_length": 30.0,
  "load_safety_factor": 1.4
}
```

## 📊 Hiểu kết quả output

### Column trong CSV:
```
Column_ID    → Tên cột (C1, C2, ...)
Pile_ID      → Tên cọc (C1_P1, C1_P2, ...)
X, Y         → Tọa độ cọc (m)
Diameter     → Đường kính cọc (m)
Bearing_Capacity → Sức chịu tải cọc (tấn)
Load         → Tải trọng thực tế (tấn)
Utilization_% → Tỷ lệ sử dụng (%)
```

### Cảnh báo trong báo cáo:
```
✓ Sử dụng < 70% → OK, có thể giảm cọc
⚠ Sử dụng 70-90% → Bình thường
✗ Sử dụng > 90% → Cần tăng cọc
```

## 🔧 Các lệnh hữu ích

### Tạo cấu hình mẫu
```bash
python main.py --create-template
```

### Sử dụng cấu hình tùy chỉnh
```bash
python main.py data.csv -c my_config.json
```

### Xem trợ giúp
```bash
python main.py -h
```

## ❌ Lỗi thường gặp

### "ModuleNotFoundError: No module named 'pandas'"
```bash
→ Cài lại: pip install -r requirements.txt
```

### "CSV file not found"
```bash
→ Kiểm tra đường dẫn file
→ Đảm bảo file CSV tồn tại
```

### "VBA Macro not running"
```bash
→ Tools → Macro Security → Set "Low"
→ Hoặc thêm vào Trusted Locations
```

## 🎨 Tùy chỉnh trên AutoCAD

### Thay đổi màu cọc
Edit `PileLayoutModule.bas`:
```vba
Color mapping:
  color_index = 1   ' Đỏ (nguy hiểm)
  color_index = 3   ' Xanh (bình thường)  
  color_index = 5   ' Xanh dương (OK)
```

### Thay đổi kích thước text
```vba
Const TEXT_HEIGHT = 0.5  ' Tăng từ 0.3
```

### Thay đổi bán kính vòng tròn
```vba
Const CIRCLE_RADIUS = 0.5  ' Tăng từ 0.4
```

## 💡 Mẹo sử dụng

1. **Kiểm tra trước**: Luôn kiểm tra báo cáo trước khi vẽ CAD
2. **Backup**: Lưu backup file DWG trước khi chạy VBA
3. **Zoom**: Sử dụng `OptimizeView` macro để chỉ hiển thị layer cọc
4. **Xóa lại**: Dùng `ClearPiles` macro để xóa tất cả cọc cũ

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra README.md chính
2. Xem VBA README: `vba/README_VBA.md`
3. Liên hệ: anvuongbg@gmail.com

---

**Chúc bạn thành công! 🚀**
