#!/usr/bin/env python3
"""
Kiểm tra info.json đã được cập nhật
"""
import zipfile
import json
from pathlib import Path

def check_updated_info_json():
    print("🔍 KIỂM TRA INFO.JSON ĐÃ CẬP NHẬT")
    print("=" * 50)
    
    output_dir = Path("output")
    zip_files = list(output_dir.glob("*.zip"))
    
    if not zip_files:
        print("❌ Không tìm thấy file zip nào!")
        return
    
    for zip_file in zip_files:
        print(f"\n📦 Checking: {zip_file.name}")
        
        try:
            with zipfile.ZipFile(zip_file, 'r') as zf:
                # Tìm info.json files
                info_files = [f for f in zf.namelist() if f.endswith('info.json')]
                
                if not info_files:
                    print("  ❌ No info.json found!")
                    continue
                
                print(f"  📄 Info.json files found: {len(info_files)}")
                
                for info_file in info_files:
                    print(f"\n  🔍 Reading: {info_file}")
                    
                    content = zf.read(info_file).decode('utf-8')
                    info = json.loads(content)
                    
                    print(f"    📋 Title: {info.get('title', 'N/A')}")
                    print(f"    🔢 Version: {info.get('version', 'N/A')}")
                    print(f"    👤 Author: {info.get('author', 'N/A')}")
                    
                    description = info.get('description', 'N/A')
                    if len(description) > 80:
                        description = description[:80] + "..."
                    print(f"    📝 Description: {description}")
                    
                    dependencies = info.get('dependencies', [])
                    print(f"    📦 Dependencies: {len(dependencies)} items")
                    
                    # Hiển thị một vài dependencies đầu
                    if dependencies:
                        print("    🔗 First 5 dependencies:")
                        for i, dep in enumerate(dependencies[:5]):
                            print(f"      {i+1}. {dep}")
                        if len(dependencies) > 5:
                            print(f"      ... and {len(dependencies) - 5} more")
                    
                    # Kiểm tra các cải tiến
                    improvements = []
                    if "SafeTranslate" in info.get('title', ''):
                        improvements.append("✅ SafeTranslate branding")
                    if "SafeGoogleTranslateAPI" in info.get('description', ''):
                        improvements.append("✅ Mentions SafeGoogleTranslateAPI")
                    if "99.2%" in info.get('description', ''):
                        improvements.append("✅ Includes accuracy metric")
                    if len(set(dependencies)) == len(dependencies):
                        improvements.append("✅ No duplicate dependencies")
                    
                    if improvements:
                        print("    🎯 Improvements detected:")
                        for imp in improvements:
                            print(f"      {imp}")
                    
        except Exception as e:
            print(f"  ❌ Error reading zip: {e}")

if __name__ == "__main__":
    check_updated_info_json()
