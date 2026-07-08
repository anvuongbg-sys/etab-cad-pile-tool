# Hướng dẫn cài đặt VBA Module cho AutoCAD

## 📌 Yêu cầu
- AutoCAD 2020 hoặc cao hơn
- Quyền chỉnh sửa drawings

## 🔧 Cách cài đặt

### Bước 1: Mở VBA Editor
1. Trong AutoCAD, nhấn `Alt + F11` để mở VBA Editor
2. Hoặc: **Tools** → **Macros** → **Edit Macros**

### Bước 2: Tạo Module mới
1. Trong VBA Editor, nhấp chuột phải vào `VBAProject`
2. Chọn **Insert** → **Module**

### Bước 3: Copy code
1. Mở file `PileLayoutModule.bas` trong text editor
2. Copy toàn bộ code
3. Paste vào Module mới trong VBA Editor

### Bước 4: Lưu Project
1. Nhấn `Ctrl + S` để lưu
2. Đóng VBA Editor

## 🚀 Cách sử dụng

### Chạy Macro
1. Trong AutoCAD, nhấn `Alt + F8` hoặc **Tools** → **Macros** → **Macros**
2. Chọn macro `PileLayout` từ danh sách
3. Nhấn **Run**

### Chọn file CSV
1. Macro sẽ yêu cầu chọn file `pile_layout.csv`
2. Duyệt đến thư mục `output/` từ tool Python
3. Chọn file `pile_layout.csv`

### Xem kết quả
- Các cọc sẽ được vẽ trên mặt bằng CAD
- Màu sắc biểu thị mức sử dụng:
  - **Đỏ**: Sử dụng ≥ 90% (nguy hiểm)
  - **Xanh**: Sử dụng 70-89% (bình thường)
  - **Xanh dương**: Sử dụng < 70% (có dư địa)

## 📋 Các Macro có sẵn

| Macro | Chức năng |
|-------|----------|
| `PileLayout` | Vẽ móng cọc từ file CSV |
| `ClearPiles` | Xóa tất cả cọc |
| `OptimizeView` | Tối ưu view, chỉ hiển thị layer PILE |
| `ShowPileInfo` | Hiển thị thông tin cọc được chọn |

## ⚙️ Tùy chỉnh

Sửa các hằng số ở đầu module để tùy chỉnh:

```vba
Const PILE_LAYER = "PILE"        ' Tên layer
Const PILE_COLOR = 256            ' Màu cọc (256 = ByLayer)
Const TEXT_HEIGHT = 0.3           ' Kích thước text ID cọc
Const CIRCLE_RADIUS = 0.4         ' Bán kính vòng tròn biểu thị cọc
```

## 🐛 Khắc phục sự cố

### Lỗi: "Subscript out of range"
- Kiểm tra format file CSV có đúng không
- Đảm bảo có ít nhất 11 cột dữ liệu

### Lỗi: "File not found"
- Kiểm tra đường dẫn file CSV
- Đảm bảo file tồn tại

### Macro không chạy
- Mở **Tools** → **Macro Security** → Set thành "Low"
- Hoặc thêm document vào Trusted Locations

## 📞 Hỗ trợ
Xem file `README.md` ở thư mục gốc để biết thêm chi tiết.
