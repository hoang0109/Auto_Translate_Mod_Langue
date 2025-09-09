# 📋 Hướng Dẫn Sử Dụng Template Mod Loader

## 🎯 Mục Đích
Template Mod Loader cho phép bạn:
1. **Chọn file mod mẫu** từ thư mục `Code mau`
2. **Ghi nhận thông tin mod mẫu** (tên, version, dependencies, v.v.)
3. **Việt hóa các mod khác** theo thông thường
4. **Tự động tạo version mới của mod mẫu** chứa các bản dịch mới

## 🚀 Workflow Sử Dụng

### Bước 1: Load Template Mod
1. Click nút **📋 Load Template** trong phần file selection
2. Chọn file zip mod mẫu từ thư mục `Code mau` (ví dụ: `Auto_Translate_Mod_Langue_Vietnamese_1.0.1.zip`)
3. Chương trình sẽ đọc và hiển thị thông tin mod:
   - Name (tên mod)
   - Version (phiên bản hiện tại)
   - Title (tiêu đề)
   - Số lượng locale files

### Bước 2: Chọn Mod Files Để Việt Hóa
1. Click **➕ Add Files** để chọn các file mod (.zip) muốn Việt hóa
2. Các file này sẽ được dịch từ tiếng Anh sang tiếng Việt
3. Có thể chọn nhiều file cùng lúc

### Bước 3: Cấu Hình Dịch Thuật
1. Nhập **DeepL API Key**
2. Chọn **Target Language** (thường là VI - Vietnamese)
3. Chọn **DeepL Endpoint** (free hoặc paid)

### Bước 4: Thực Hiện Việt Hóa
1. Click **🚀 Start Translation**
2. Chương trình sẽ:
   - Dịch các file mod đã chọn
   - Lưu bản dịch vào thư mục tạm `temp_translations`
   - Tự động tạo version mới của template mod

### Bước 5: Kết Quả
- **File mod mẫu mới** sẽ được tạo trong thư mục `output/` với:
  - Version tăng lên (ví dụ: 1.0.1 → 1.0.2)
  - Tên mới với version (ví dụ: `Auto_Translate_Mod_Langue_Vietnamese_102.zip`)
  - Dependencies được cập nhật với các mod vừa dịch
  - Locale files mới từ bản dịch

## 📁 Cấu Trúc Files

```
Auto_Translate_Mod_Langue/
├── Code mau/                          # Thư mục chứa mod mẫu
│   ├── Auto_Translate_Mod_Langue_Vietnamese_1.0.1.zip
│   └── ...
├── output/                            # Thư mục output cho mod mới
│   └── Auto_Translate_Mod_Langue_Vietnamese_102.zip
├── temp_translations/                 # Thư mục tạm (tự động cleanup)
│   ├── mod1.cfg
│   └── mod2.cfg
└── ...
```

## 🔄 Template Version Management

### Version Increment Logic:
- **Patch increment**: 1.0.1 → 1.0.2
- **Minor increment**: 1.0 → 1.1.0  
- **Fallback**: Tạo version 1.0.1 nếu parse lỗi

### Template Info Update:
- `name`: Thêm version suffix (ví dụ: `ModName_102`)
- `version`: Tăng version
- `dependencies`: Thêm các mod vừa dịch với prefix `? `
- `description`: Thêm timestamp "(Updated: YYYY-MM-DD)"

## 💡 Ví Dụ Sử Dụng

### Scenario: Việt hóa 3 mod mới
1. **Load template**: `Auto_Translate_Mod_Langue_Vietnamese_1.0.1.zip`
2. **Add mod files**: 
   - `advanced-logistics.zip`
   - `better-power.zip`
   - `improved-mining.zip`
3. **Start translation**
4. **Kết quả**: 
   - Template mới: `Auto_Translate_Mod_Langue_Vietnamese_102.zip` (version 1.0.2)
   - Chứa 3 file Việt hóa mới:
     - `advanced-logistics.cfg`
     - `better-power.cfg`  
     - `improved-mining.cfg`

## ⚠️ Lưu Ý Quan Trọng

### Requirements:
- File template phải có cấu trúc mod Factorio hợp lệ với `info.json`
- DeepL API key hợp lệ
- File mod để dịch phải có `locale/en/*.cfg`

### Error Handling:
- Nếu không load template: chương trình hoạt động như cũ
- Nếu translation fails: chỉ báo lỗi, không tạo template mới
- File corrupted: skip và log warning

### Best Practices:
- Load template trước khi add mod files
- Kiểm tra API key trước khi start
- Backup file template gốc
- Kiểm tra kết quả trong `output/` folder

## 🐛 Troubleshooting

### "No such file or directory" error:
- Đảm bảo đã load template trước
- Kiểm tra file template có tồn tại

### "Template creation failed":  
- Kiểm tra quyền write vào thư mục `output/`
- Đảm bảo template có cấu trúc hợp lệ

### "No translations created":
- Kiểm tra mod files có `locale/en/*.cfg`
- Verify API key và network connection

## 📞 Support
- Email: hoang0109@gmail.com
- Check logs trong thư mục `logs/` để debug
- Enable debug mode với `DEBUG=1` environment variable
