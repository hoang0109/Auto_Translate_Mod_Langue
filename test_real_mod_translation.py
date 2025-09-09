#!/usr/bin/env python3
"""
Test script để kiểm tra chức năng dịch với mod Factorio thực tế
Sử dụng mod Babelfish như một test case nhỏ
"""
import os
import shutil
import sys
from pathlib import Path

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mod_translate_core import find_locale_files, parse_cfg_lines, read_cfg_file
import zipfile
import json

def copy_test_mod():
    """Copy mod test từ thư mục Factorio về thư mục hiện tại"""
    source_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    target_dir = "test_mods"
    
    # Tạo thư mục test_mods nếu chưa có
    os.makedirs(target_dir, exist_ok=True)
    
    # Danh sách các mod để test (từ analysis)
    test_mods = [
        "Babelfish_2.0.0.zip",      # 11 strings, 0.04 MB - SMALL
        "BigBags_1.0.37.zip",       # 23 strings, 0.07 MB - SMALL  
        "RateCalculator_3.3.7.zip", # 66 strings, 0.09 MB - MEDIUM
        "HeroTurretRedux_1.0.30.zip" # 117 strings, 0.21 MB - MEDIUM
    ]
    
    copied_mods = []
    for mod_file in test_mods:
        source_path = os.path.join(source_dir, mod_file)
        target_path = os.path.join(target_dir, mod_file)
        
        if os.path.exists(source_path):
            if not os.path.exists(target_path):
                print(f"📥 Copying {mod_file}...")
                shutil.copy2(source_path, target_path)
            else:
                print(f"✅ {mod_file} already exists")
            copied_mods.append(target_path)
        else:
            print(f"❌ {mod_file} not found in source directory")
    
    return copied_mods

def test_translation_pipeline(mod_path):
    """Test pipeline dịch cho một mod"""
    print(f"\\n{'='*60}")
    print(f"🧪 TESTING TRANSLATION PIPELINE")
    print(f"📦 Mod: {os.path.basename(mod_path)}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Analyze mod structure using mod_translate_core functions
        print("\\n🔍 Step 1: Analyzing mod structure...")
        
        # Get mod info from info.json
        mod_info = {}
        with zipfile.ZipFile(mod_path, 'r') as zipf:
            # Find info.json
            info_files = [f for f in zipf.namelist() if f.endswith('info.json')]
            if info_files:
                with zipf.open(info_files[0]) as f:
                    mod_data = json.load(f)
                    mod_info = {
                        'name': mod_data.get('name', 'Unknown'),
                        'version': mod_data.get('version', 'Unknown'),
                        'factorio_version': mod_data.get('factorio_version', 'Unknown'),
                        'title': mod_data.get('title', ''),
                        'author': mod_data.get('author', '')
                    }
        
        if mod_info:
            print(f"   ✅ Mod Name: {mod_info.get('name', 'Unknown')}")
            print(f"   ✅ Version: {mod_info.get('version', 'Unknown')}")
            print(f"   ✅ Factorio Version: {mod_info.get('factorio_version', 'Unknown')}")
            print(f"   ✅ Title: {mod_info.get('title', '')[:50]}...")
            print(f"   ✅ Author: {mod_info.get('author', '')}")
        else:
            print("   ❌ Failed to analyze mod")
            return False
        
        # Find locale files
        root_folder, locale_files = find_locale_files(mod_path)
        if not locale_files:
            print("   ❌ No locale files found")
            return False
            
        print(f"   ✅ Root folder: {root_folder}")
        print(f"   ✅ English locale files: {len(locale_files)}")
        for locale_file in locale_files:
            print(f"      📄 {locale_file}")
        
        # Step 2: Extract translatable content
        print("\\n📝 Step 2: Extracting translatable content...")
        translations_data = {}
        
        with zipfile.ZipFile(mod_path, 'r') as zipf:
            for locale_file in locale_files:
                # Read file content
                raw_content = read_cfg_file(zipf, locale_file)
                
                # Parse key-value pairs
                key_vals, original_lines = parse_cfg_lines(raw_content)
                
                if key_vals:
                    translations = {item['key']: item['val'] for item in key_vals}
                    translations_data[locale_file] = {
                        'translations': translations,
                        'original_lines': original_lines,
                        'key_vals': key_vals
                    }
        
        if translations_data:
            total_strings = sum(len(file_data.get('translations', {})) for file_data in translations_data.values())
            print(f"   ✅ Total translatable strings: {total_strings}")
            
            # Show sample content
            for file_path, file_data in list(translations_data.items())[:2]:  # Show first 2 files
                translations = file_data.get('translations', {})
                print(f"   📄 {file_path}: {len(translations)} strings")
                for i, (key, value) in enumerate(list(translations.items())[:3]):  # Show first 3 strings
                    print(f"      {i+1}. {key} = {value[:50]}...")
        else:
            print("   ❌ No translatable content found")
            return False
        
        # Step 3: Test translation (with mock API for now)
        print("\\n🌐 Step 3: Testing translation (MOCK MODE)...")
        
        # Create output directory
        output_dir = f"translated_{Path(mod_path).stem}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Mock translate each file
        translated_count = 0
        for file_path, file_data in translations_data.items():
            translations = file_data.get('translations', {})
            if translations:
                # Mock translation - just add [VI] prefix  
                mock_translations = {}
                for key, value in translations.items():
                    mock_translations[key] = f"[VI] {value}"
                
                # Generate output file content
                original_lines = file_data.get('original_lines', [])
                translated_lines = []
                
                for line in original_lines:
                    if '=' in line and not line.strip().startswith('#'):
                        # This is a translatable line
                        key = line.split('=', 1)[0].strip()
                        if key in mock_translations:
                            translated_lines.append(f"{key}={mock_translations[key]}")
                        else:
                            translated_lines.append(line)
                    else:
                        # Comment or section header
                        translated_lines.append(line)
                
                # Write translated file
                output_file = os.path.join(output_dir, os.path.basename(file_path))
                with open(output_file, 'w', encoding='utf-8') as f:
                    for line in translated_lines:
                        # Ensure line ends with newline if it doesn't already have one
                        if not line.endswith('\n'):
                            f.write(line + '\n')
                        else:
                            f.write(line)
                
                translated_count += len(mock_translations)
                print(f"   ✅ Translated {os.path.basename(file_path)}: {len(mock_translations)} strings")
        
        print(f"   ✅ Total translated strings: {translated_count}")
        print(f"   ✅ Output directory: {output_dir}")
        
        # Step 4: Verify output files
        print("\\n🔍 Step 4: Verifying output files...")
        if os.path.exists(output_dir):
            output_files = [f for f in os.listdir(output_dir) if f.endswith('.cfg')]
            print(f"   ✅ Generated files: {len(output_files)}")
            
            for output_file in output_files:
                file_path = os.path.join(output_dir, output_file)
                file_size = os.path.getsize(file_path)
                print(f"      📄 {output_file}: {file_size} bytes")
                
                # Show sample content
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]
                    print(f"         Sample content:")
                    for line in lines:
                        print(f"         {line.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 FACTORIO MOD TRANSLATION TESTER")
    print("="*60)
    
    # Step 1: Copy test mods
    print("\\n📥 Step 1: Copying test mods...")
    copied_mods = copy_test_mod()
    
    if not copied_mods:
        print("❌ No test mods available!")
        return
    
    # Step 2: Test translation pipeline with smallest mod
    test_mod = copied_mods[0]  # Babelfish_2.0.0.zip
    success = test_translation_pipeline(test_mod)
    
    if success:
        print("\\n" + "="*60)
        print("✅ TRANSLATION PIPELINE TEST COMPLETED SUCCESSFULLY!")
        print("\\n🎯 Next steps:")
        print("1. Review the translated files in the output directory")
        print("2. Compare with original content")
        print("3. Test with real DeepL API")
        print("4. Integrate with template mod system")
    else:
        print("\\n" + "="*60)
        print("❌ TRANSLATION PIPELINE TEST FAILED!")
        print("\\n🔧 Check the error messages above and fix issues")

if __name__ == "__main__":
    main()
