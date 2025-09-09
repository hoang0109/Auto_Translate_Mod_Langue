# 🎮 Hướng Dẫn Sử Dụng Factorio Mod Translator

## ⚠️ **QUAN TRỌNG - Đọc Trước Khi Sử Dụng**

### 🔍 **Vấn Đề Phổ Biến**
Nhiều user thất bại vì chọn **file đã dịch** thay vì **file mod gốc**. Chương trình chỉ dịch được **mod gốc có `locale/en/*.cfg`**.

### ✅ **Cách Xác Định Mod Đúng**

#### **Mod ĐÚNG (có thể dịch)**:
```
mod-name.zip
├── mod-name/
│   ├── info.json
│   ├── locale/
│   │   └── en/           ← CÓ thư mục EN
│   │       ├── items.cfg
│   │       └── entities.cfg
│   └── ...
```

#### **Mod SAI (không thể dịch)**:
```
mod-name.zip
├── mod-name/
│   ├── info.json
│   ├── locale/
│   │   └── vi/           ← KHÔNG có thư mục EN  
│   │       └── items.cfg
│   └── ...
```

## 🚀 **Workflow Đúng**

### **Bước 1: Load Template Mod**
1. Click **📋 Load Template**
2. Chọn file template từ thư mục `Code mau` 
   - Ví dụ: `Auto_Translate_Mod_Langue_Vietnamese_1.0.1.zip`
3. Xem thông tin template đã load

### **Bước 2: Add Mod Files (Quan Trọng!)**
1. Click **➕ Add Files**
2. **CHỌN MOD GỐC** có `locale/en/*.cfg`, KHÔNG phải file output
3. Ví dụ mod hợp lệ:
   - `test-mod.zip` (đã tạo sẵn để test)
   - Mod từ Factorio Portal chưa được dịch
   - Mod có English locale files

### **Bước 3: Cấu Hình**
1. Nhập **DeepL API Key** hợp lệ
2. Chọn **Target Language**: VI (Vietnamese)
3. Chọn **Endpoint**: 
   - `api-free.deepl.com` (miễn phí, giới hạn 500k ký tự/tháng)
   - `api.deepl.com` (trả phí, không giới hạn)

### **Bước 4: Test API**
1. Click **🧪 Test API** để kiểm tra API key
2. Đợi status hiển thị ✅ (thành công) hoặc ❌ (lỗi)

### **Bước 5: Bắt Đầu Dịch**
1. Click **🚀 Start Translation**
2. Xem progress bar và status
3. Đợi kết quả

## 📂 **Kết Quả**

### **Thành Công:**
- Template mới trong `output/`: `ModName_VERSION.zip`
- Chứa tất cả locale files cũ + mới dịch
- Version tự động tăng (1.0.1 → 1.0.2)
- Dependencies updated

### **Thất Bại:**
- **"0 locale files found"** → Mod không có `locale/en/*.cfg`
- **"API error"** → API key sai hoặc hết quota
- **"No values to translate"** → Mod không có text để dịch

## 🧪 **Test với Mod Mẫu**

Tôi đã tạo sẵn `test-mod.zip` để test:

```bash
# Kiểm tra nội dung mod test
python -c "
import zipfile
with zipfile.ZipFile('test-mod.zip', 'r') as z:
    print('Test mod contents:')
    [print(f'  {f}') for f in z.namelist()]
    
    print('\nSample locale content:')
    with z.open('test-translation-mod/locale/en/test.cfg') as f:
        print(f.read().decode('utf-8')[:200])
"
```

## 🔧 **Troubleshooting**

### **Lỗi: "Found 0 locale files"**
- **Nguyên nhân**: Mod không có `locale/en/*.cfg`
- **Giải pháp**: Chọn mod gốc từ Factorio Portal

### **Lỗi: "API key invalid"**
- **Nguyên nhân**: API key sai hoặc endpoint sai
- **Giải pháp**: 
  1. Kiểm tra API key từ DeepL dashboard
  2. Chọn đúng endpoint (free vs paid)

### **File rỗng trong output**
- **Nguyên nhân**: Mod không có text để dịch
- **Giải pháp**: Kiểm tra mod có `locale/en/*.cfg` với content

## 📥 **Download Mod Để Test**

### **Từ Factorio Portal:**
1. Vào https://mods.factorio.com/
2. Download mod chưa có Vietnamese translation
3. Unzip và kiểm tra có `locale/en/` không

### **Mod Phổ Biến Có Locale EN:**
- `aai-loaders` (gốc, chưa dịch)
- `alien-biomes` (gốc)  
- `big-bags` (gốc)

## 💡 **Tips**

1. **Luôn load template trước** khi add mod files
2. **Test API key** trước khi start translation
3. **Backup template** gốc trước khi dùng
4. **Kiểm tra quota** DeepL để tránh hết limit
5. **Sử dụng test-mod.zip** để verify workflow

## 📞 **Support**

- **Email**: hoang0109@gmail.com
- **Debug**: Check console output cho error details
- **Logs**: Xem `logs/` folder cho detailed logging
