#!/usr/bin/env python3
"""
Script kiểm tra kết quả dịch Google Translate
"""
import os
from pathlib import Path
import zipfile

def check_translation_results():
    """Kiểm tra kết quả dịch trong output directory"""
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("❌ Output directory không tồn tại!")
        return
    
    zip_files = list(output_dir.glob("*.zip"))
    if not zip_files:
        print("❌ Không có file zip nào trong output directory!")
        return
    
    print(f"🎯 Tìm thấy {len(zip_files)} file(s) trong output directory:")
    
    for zip_file in zip_files:
        print(f"\n📦 Kiểm tra file: {zip_file.name}")
        
        try:
            with zipfile.ZipFile(zip_file, 'r') as zipf:
                cfg_files = [f for f in zipf.namelist() if f.endswith('.cfg')]
                print(f"  • Số lượng .cfg files: {len(cfg_files)}")
                
                if cfg_files:
                    print("  • Một số file .cfg được dịch:")
                    for cfg_file in cfg_files[:5]:  # Hiển thị 5 file đầu
                        cfg_name = os.path.basename(cfg_file)
                        print(f"    - {cfg_name}")
                    
                    if len(cfg_files) > 5:
                        print(f"    ... và {len(cfg_files) - 5} files khác")
                        
                    # Đọc nội dung một file mẫu để kiểm tra chất lượng dịch
                    sample_file = cfg_files[0]
                    try:
                        content = zipf.read(sample_file).decode('utf-8')
                        lines = content.split('\n')[:10]  # 10 dòng đầu
                        
                        print(f"\n  📄 Nội dung mẫu từ {os.path.basename(sample_file)}:")
                        for line in lines:
                            if '=' in line and line.strip():
                                print(f"    {line.strip()}")
                        
                    except Exception as e:
                        print(f"    ❌ Không thể đọc file mẫu: {e}")
        
        except Exception as e:
            print(f"  ❌ Lỗi khi đọc zip file: {e}")

def check_temp_translations():
    """Kiểm tra thư mục temp_translations"""
    temp_dir = Path("temp_translations")
    
    if temp_dir.exists():
        cfg_files = list(temp_dir.glob("*.cfg"))
        print(f"\n🔧 Temp translations: {len(cfg_files)} files")
        
        for cfg_file in cfg_files[:3]:  # Hiển thị 3 file đầu
            print(f"  • {cfg_file.name}")
            try:
                with open(cfg_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]  # 5 dòng đầu
                    for line in lines:
                        if '=' in line and line.strip():
                            print(f"    {line.strip()}")
                    print()
            except Exception as e:
                print(f"    ❌ Lỗi đọc file: {e}")
    else:
        print("\n🔧 Không có thư mục temp_translations")

if __name__ == "__main__":
    print("🔍 KIỂM TRA KẾT QUẢ GOOGLE TRANSLATE")
    print("=" * 50)
    
    check_translation_results()
    check_temp_translations()
    
    print("\n✅ Hoàn thành kiểm tra!")
