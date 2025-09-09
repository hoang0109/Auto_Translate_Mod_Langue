#!/usr/bin/env python3
"""
Script chỉnh sửa file info.json sau khi việt hóa
"""
import json
import os
from pathlib import Path
from datetime import datetime
import zipfile
import tempfile
import shutil

class InfoJsonUpdater:
    def __init__(self):
        self.current_date = datetime.now().strftime('%Y-%m-%d')
    
    def read_current_info_json(self, file_path):
        """Đọc file info.json hiện tại"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return None
    
    def clean_dependencies(self, dependencies):
        """Loại bỏ các dependencies duplicate"""
        if not dependencies:
            return []
        
        # Loại bỏ duplicates nhưng giữ nguyên thứ tự
        seen = set()
        cleaned = []
        for dep in dependencies:
            if dep not in seen:
                seen.add(dep)
                cleaned.append(dep)
        
        return sorted(cleaned)  # Sắp xếp theo thứ tự alphabet
    
    def update_info_json_content(self, info_data, translated_mods=None):
        """Cập nhật nội dung info.json"""
        # Cập nhật version
        current_version = info_data.get('version', '1.0.0')
        version_parts = current_version.split('.')
        if len(version_parts) >= 3:
            # Tăng patch version
            patch = int(version_parts[2]) + 1
            new_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"
        else:
            new_version = "1.0.1"
        
        # Cập nhật thông tin cơ bản
        updated_info = {
            "name": info_data.get("name", "Auto_Translate_Mod_Langue_Vietnamese"),
            "version": new_version,
            "title": "Factorio Mods Vietnamese Language Pack (SafeTranslate)",
            "author": info_data.get("author", "Hoang0109"),
            "factorio_version": info_data.get("factorio_version", "2.0"),
            "description": f"Gói việt hóa cho các mod Factorio được dịch bằng SafeGoogleTranslateAPI - An toàn, chất lượng cao (Updated: {self.current_date})",
        }
        
        # Xử lý dependencies
        dependencies = info_data.get("dependencies", [])
        
        # Nếu có danh sách mods đã dịch, cập nhật dependencies
        if translated_mods:
            # Thêm các mods mới đã dịch
            for mod_name in translated_mods:
                dep_entry = f"? {mod_name}"
                if dep_entry not in dependencies:
                    dependencies.append(dep_entry)
        
        # Clean up dependencies
        cleaned_deps = self.clean_dependencies(dependencies)
        updated_info["dependencies"] = cleaned_deps
        
        return updated_info
    
    def update_info_json_file(self, file_path, translated_mods=None):
        """Cập nhật file info.json"""
        print(f"🔧 Updating {file_path}")
        
        # Đọc file hiện tại
        info_data = self.read_current_info_json(file_path)
        if not info_data:
            return False
        
        print(f"  📋 Current version: {info_data.get('version', 'unknown')}")
        print(f"  📦 Dependencies count: {len(info_data.get('dependencies', []))}")
        
        # Cập nhật nội dung
        updated_info = self.update_info_json_content(info_data, translated_mods)
        
        print(f"  ✅ New version: {updated_info['version']}")
        print(f"  🧹 Cleaned dependencies: {len(updated_info['dependencies'])}")
        
        # Backup file gốc
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        print(f"  💾 Backup created: {backup_path}")
        
        # Ghi file mới
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_info, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ Updated successfully!")
            return True
            
        except Exception as e:
            print(f"  ❌ Error writing file: {e}")
            # Restore backup nếu có lỗi
            shutil.copy2(backup_path, file_path)
            return False
    
    def update_zip_info_json(self, zip_path, translated_mods=None):
        """Cập nhật info.json trong file zip"""
        print(f"🗜️ Updating info.json in {os.path.basename(zip_path)}")
        
        try:
            # Tạo thư mục tạm
            with tempfile.TemporaryDirectory() as temp_dir:
                # Giải nén zip
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Tìm file info.json
                info_json_paths = []
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == 'info.json':
                            info_json_paths.append(os.path.join(root, file))
                
                if not info_json_paths:
                    print("  ❌ No info.json found in zip")
                    return False
                
                # Cập nhật từng info.json
                success = True
                for info_path in info_json_paths:
                    if not self.update_info_json_file(info_path, translated_mods):
                        success = False
                
                if not success:
                    return False
                
                # Tạo lại zip file
                backup_zip = f"{zip_path}.backup"
                shutil.copy2(zip_path, backup_zip)
                print(f"  💾 Zip backup: {backup_zip}")
                
                # Tạo zip mới
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                print(f"  ✅ Zip updated successfully!")
                return True
                
        except Exception as e:
            print(f"  ❌ Error updating zip: {e}")
            return False
    
    def scan_and_update_output_directory(self, output_dir="output"):
        """Quét và cập nhật tất cả file info.json trong thư mục output"""
        output_path = Path(output_dir)
        
        if not output_path.exists():
            print(f"❌ Directory {output_dir} không tồn tại!")
            return
        
        print(f"🔍 SCANNING OUTPUT DIRECTORY: {output_dir}")
        print("=" * 60)
        
        # Tìm tất cả file zip
        zip_files = list(output_path.glob("*.zip"))
        
        if not zip_files:
            print("❌ No zip files found!")
            return
        
        print(f"📦 Found {len(zip_files)} zip files")
        
        # Cập nhật từng file
        success_count = 0
        for zip_file in zip_files:
            print(f"\n📦 Processing: {zip_file.name}")
            if self.update_zip_info_json(zip_file):
                success_count += 1
        
        print(f"\n📊 SUMMARY:")
        print(f"✅ Successfully updated: {success_count}/{len(zip_files)} files")
        print(f"❌ Failed: {len(zip_files) - success_count} files")
    
    def create_updated_info_template(self, output_file="updated_info_template.json"):
        """Tạo template info.json mới với các cải tiến"""
        template = {
            "name": "Auto_Translate_Mod_Langue_Vietnamese",
            "version": "2.0.0",
            "title": "Factorio Mods Vietnamese Language Pack (SafeTranslate)",
            "author": "Hoang0109",
            "factorio_version": "2.0",
            "description": f"Gói việt hóa chất lượng cao cho các mod Factorio. Sử dụng SafeGoogleTranslateAPI với 99.2% độ chính xác tiếng Việt. Hỗ trợ 40+ mods phổ biến (Updated: {self.current_date})",
            "dependencies": [
                "? aai-industry",
                "? aai-loaders", 
                "? alien-biomes",
                "? Babelfish",
                "? BigBags",
                "? jetpack",
                "? RateCalculator"
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Template created: {output_file}")
        return template

def main():
    updater = InfoJsonUpdater()
    
    print("🎯 INFO.JSON UPDATER")
    print("=" * 40)
    
    # Tùy chọn 1: Cập nhật tất cả file trong output directory
    print("\n1. Updating all files in output directory:")
    updater.scan_and_update_output_directory()
    
    # Tùy chọn 2: Tạo template mới
    print("\n2. Creating updated template:")
    updater.create_updated_info_template()
    
    print("\n🎉 Info.json update completed!")

def update_specific_file(file_path, translated_mods=None):
    """Function để cập nhật file cụ thể từ bên ngoài"""
    updater = InfoJsonUpdater()
    
    if file_path.endswith('.zip'):
        return updater.update_zip_info_json(file_path, translated_mods)
    else:
        return updater.update_info_json_file(file_path, translated_mods)

if __name__ == "__main__":
    main()
