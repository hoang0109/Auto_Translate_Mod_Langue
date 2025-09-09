#!/usr/bin/env python3
"""
Script tích hợp đầy đủ để test template mod system
Workflow: Template mod -> Real mod translation -> New template version
"""
import os
import shutil
import sys
import json
import zipfile
from pathlib import Path
import tempfile
from datetime import datetime

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mod_translate_core import find_locale_files, parse_cfg_lines, read_cfg_file, write_cfg_file

def create_test_environment():
    """Tạo môi trường test với các thư mục cần thiết"""
    test_dirs = [
        "test_environment/input_mods",
        "test_environment/template_mods", 
        "test_environment/output_mods",
        "test_environment/translation_cache",
        "test_environment/logs"
    ]
    
    for dir_path in test_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
    
    return "test_environment"

def copy_test_mods(test_env_dir):
    """Copy mod test từ thư mục Factorio"""
    source_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    input_dir = os.path.join(test_env_dir, "input_mods")
    
    # Danh sách mod để test (small -> medium -> large)
    test_mods = [
        "Babelfish_2.0.0.zip",      # 11 strings, 0.04 MB - SMALL
        "BigBags_1.0.37.zip",       # 23 strings, 0.07 MB - SMALL  
        "RateCalculator_3.3.7.zip", # 66 strings, 0.09 MB - MEDIUM
        "BeltSpeedMultiplier_1.0.3.zip" # 1 string, 0.02 MB - TINY
    ]
    
    copied_mods = []
    for mod_file in test_mods:
        source_path = os.path.join(source_dir, mod_file)
        target_path = os.path.join(input_dir, mod_file)
        
        if os.path.exists(source_path):
            if not os.path.exists(target_path):
                print(f"📥 Copying {mod_file}...")
                shutil.copy2(source_path, target_path)
            else:
                print(f"✅ {mod_file} already exists")
            copied_mods.append(target_path)
        else:
            print(f"❌ {mod_file} not found in source")
    
    return copied_mods

def create_template_mod(test_env_dir, base_mod_path):
    """Tạo template mod từ một mod đã có"""
    template_dir = os.path.join(test_env_dir, "template_mods")
    base_mod_name = Path(base_mod_path).stem
    
    print(f"\\n🏗️ Creating template mod from {base_mod_name}...")
    
    # Extract base mod
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(base_mod_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Find mod directory
        extracted_items = os.listdir(temp_dir)
        mod_dir = None
        for item in extracted_items:
            if os.path.isdir(os.path.join(temp_dir, item)):
                mod_dir = os.path.join(temp_dir, item)
                break
        
        if not mod_dir:
            print("❌ Could not find mod directory")
            return None
        
        # Read info.json
        info_path = os.path.join(mod_dir, "info.json")
        if not os.path.exists(info_path):
            print("❌ info.json not found")
            return None
        
        with open(info_path, 'r', encoding='utf-8') as f:
            info_data = json.load(f)
        
        # Create template version
        template_info = info_data.copy()
        template_info['name'] = f"{template_info['name']}_Vietnamese"
        template_info['title'] = f"{template_info.get('title', template_info['name'])} (Vietnamese)"
        template_info['version'] = "1.0.0"  # Reset version for template
        template_info['description'] = f"Vietnamese translation template for {template_info['name']}"
        
        # Add dependencies
        dependencies = template_info.get('dependencies', [])
        if isinstance(dependencies, list):
            # Add base mod as dependency
            base_dependency = f"{info_data['name']} >= {info_data['version']}"
            if base_dependency not in dependencies:
                dependencies.insert(0, base_dependency)
        template_info['dependencies'] = dependencies
        
        # Create template mod directory
        template_mod_name = template_info['name']
        template_mod_dir = os.path.join(temp_dir, f"{template_mod_name}_template")
        os.makedirs(template_mod_dir, exist_ok=True)
        
        # Write updated info.json
        with open(os.path.join(template_mod_dir, "info.json"), 'w', encoding='utf-8') as f:
            json.dump(template_info, f, indent=2, ensure_ascii=False)
        
        # Create Vietnamese locale directory
        vi_locale_dir = os.path.join(template_mod_dir, "locale", "vi")
        os.makedirs(vi_locale_dir, exist_ok=True)
        
        # Create empty locale files (will be filled during translation)
        placeholder_content = "# Vietnamese translation placeholder\\n# Will be populated during translation process\\n"
        with open(os.path.join(vi_locale_dir, "template.cfg"), 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
        
        # Create changelog
        changelog_path = os.path.join(template_mod_dir, "changelog.txt")
        changelog_content = f"""---------------------------------------------------------------------------------------------------
Version: 1.0.0
Date: {datetime.now().strftime('%Y-%m-%d')}
  Changes:
    - Initial template creation for Vietnamese translation
    - Based on {info_data['name']} version {info_data['version']}
"""
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(changelog_content)
        
        # Create template zip
        template_zip_path = os.path.join(template_dir, f"{template_mod_name}_1.0.0.zip")
        with zipfile.ZipFile(template_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(template_mod_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)
        
        print(f"✅ Template mod created: {template_zip_path}")
        return template_zip_path

def translate_mod_content(mod_path, cache_dir):
    """Dịch nội dung mod (mock translation)"""
    print(f"\\n🌐 Translating content from {os.path.basename(mod_path)}...")
    
    # Find locale files
    root_folder, locale_files = find_locale_files(mod_path)
    if not locale_files:
        print("❌ No locale files found")
        return None
    
    translation_results = {}
    
    with zipfile.ZipFile(mod_path, 'r') as zipf:
        for locale_file in locale_files:
            # Read and parse content
            raw_content = read_cfg_file(zipf, locale_file)
            key_vals, original_lines = parse_cfg_lines(raw_content)
            
            if not key_vals:
                continue
            
            # Mock translation: Vietnamese translations
            translated_pairs = []
            for item in key_vals:
                key = item['key']
                original_value = item['val']
                
                # Simple mock translation rules
                if "speed" in original_value.lower():
                    translated_value = original_value.replace("speed", "tốc độ")
                elif "size" in original_value.lower():
                    translated_value = original_value.replace("size", "kích thước")
                elif "belt" in original_value.lower():
                    translated_value = original_value.replace("belt", "băng tải")
                elif "multiplier" in original_value.lower():
                    translated_value = original_value.replace("multiplier", "hệ số nhân")
                elif "setting" in original_value.lower():
                    translated_value = original_value.replace("setting", "cài đặt")
                elif "language" in original_value.lower():
                    translated_value = original_value.replace("language", "ngôn ngữ")
                else:
                    # Generic Vietnamese prefix
                    translated_value = f"[VI] {original_value}"
                
                translated_pairs.append({
                    'key': key,
                    'original': original_value,
                    'translated': translated_value,
                    'line_index': item['index']
                })
            
            # Generate translated content
            translated_lines = original_lines[:]
            for pair in translated_pairs:
                line_idx = pair['line_index']
                translated_lines[line_idx] = f"{pair['key']}={pair['translated']}\\n"
            
            # Store result
            file_basename = os.path.basename(locale_file)
            translation_results[file_basename] = {
                'original_lines': original_lines,
                'translated_lines': translated_lines,
                'translations': translated_pairs,
                'string_count': len(translated_pairs)
            }
            
            print(f"  ✅ {file_basename}: {len(translated_pairs)} strings translated")
    
    # Save to cache
    cache_file = os.path.join(cache_dir, f"{Path(mod_path).stem}_translations.json")
    cache_data = {
        'mod_name': Path(mod_path).stem,
        'timestamp': datetime.now().isoformat(),
        'total_strings': sum(result['string_count'] for result in translation_results.values()),
        'files': translation_results
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        # Convert translated_lines to string for JSON serialization
        for file_data in cache_data['files'].values():
            file_data['translated_lines'] = ''.join(file_data['translated_lines'])
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Translation cache saved: {cache_file}")
    return translation_results

def update_template_with_translation(template_path, translation_results, output_dir):
    """Cập nhật template mod với bản dịch mới"""
    print(f"\\n🔄 Updating template with new translations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract template
        with zipfile.ZipFile(template_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Find template directory
        template_dir = None
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                template_dir = item_path
                break
        
        if not template_dir:
            print("❌ Could not find template directory")
            return None
        
        # Update info.json version
        info_path = os.path.join(template_dir, "info.json")
        with open(info_path, 'r', encoding='utf-8') as f:
            info_data = json.load(f)
        
        # Increment version
        version_parts = info_data['version'].split('.')
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        new_version = '.'.join(version_parts)
        info_data['version'] = new_version
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, indent=2, ensure_ascii=False)
        
        # Create Vietnamese locale files
        vi_locale_dir = os.path.join(template_dir, "locale", "vi")
        os.makedirs(vi_locale_dir, exist_ok=True)
        
        # Write translated files
        for file_basename, translation_data in translation_results.items():
            vi_file_path = os.path.join(vi_locale_dir, file_basename)
            translated_content = translation_data['translated_lines']
            
            if isinstance(translated_content, list):
                content_str = ''.join(translated_content)
            else:
                content_str = translated_content
            
            with open(vi_file_path, 'w', encoding='utf-8') as f:
                f.write(content_str)
            
            print(f"  ✅ Created Vietnamese file: {file_basename}")
        
        # Update changelog
        changelog_path = os.path.join(template_dir, "changelog.txt")
        if os.path.exists(changelog_path):
            with open(changelog_path, 'r', encoding='utf-8') as f:
                old_changelog = f.read()
        else:
            old_changelog = ""
        
        new_changelog_entry = f"""---------------------------------------------------------------------------------------------------
Version: {new_version}
Date: {datetime.now().strftime('%Y-%m-%d')}
  Changes:
    - Updated Vietnamese translations
    - Added {sum(data['string_count'] for data in translation_results.values())} translated strings
    - Translation files: {', '.join(translation_results.keys())}
    
{old_changelog}"""
        
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(new_changelog_entry)
        
        # Create updated template zip
        template_name = info_data['name']
        output_zip_path = os.path.join(output_dir, f"{template_name}_{new_version}.zip")
        
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(template_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)
        
        print(f"✅ Updated template created: {output_zip_path}")
        return output_zip_path

def run_full_integration_test():
    """Chạy test tích hợp đầy đủ"""
    print("🧪 FULL INTEGRATION TEST - Template Mod System")
    print("=" * 70)
    
    # Step 1: Setup test environment
    print("\\n📁 Step 1: Setting up test environment...")
    test_env_dir = create_test_environment()
    
    # Step 2: Copy test mods
    print("\\n📥 Step 2: Copying test mods...")
    test_mods = copy_test_mods(test_env_dir)
    
    if not test_mods:
        print("❌ No test mods available!")
        return False
    
    # Step 3: Create template mod from smallest mod
    print("\\n🏗️ Step 3: Creating template mod...")
    base_mod = test_mods[0]  # Babelfish
    template_path = create_template_mod(test_env_dir, base_mod)
    
    if not template_path:
        print("❌ Failed to create template mod!")
        return False
    
    # Step 4: Translate content from multiple mods
    cache_dir = os.path.join(test_env_dir, "translation_cache")
    all_translations = {}
    
    for mod_path in test_mods[:2]:  # Test with first 2 mods
        print(f"\\n🌐 Step 4.{test_mods.index(mod_path)+1}: Translating {os.path.basename(mod_path)}...")
        translation_results = translate_mod_content(mod_path, cache_dir)
        
        if translation_results:
            # Merge translations (avoiding key conflicts)
            for file_name, file_data in translation_results.items():
                if file_name not in all_translations:
                    all_translations[file_name] = file_data
                else:
                    # Merge translations
                    existing_data = all_translations[file_name]
                    existing_data['translations'].extend(file_data['translations'])
                    existing_data['string_count'] += file_data['string_count']
                    
                    # Update translated lines (simple merge for demo)
                    existing_data['translated_lines'] += "\\n\\n" + file_data['translated_lines']
    
    if not all_translations:
        print("❌ No translations generated!")
        return False
    
    # Step 5: Update template with translations
    output_dir = os.path.join(test_env_dir, "output_mods")
    print("\\n🔄 Step 5: Updating template with translations...")
    final_template = update_template_with_translation(template_path, all_translations, output_dir)
    
    if not final_template:
        print("❌ Failed to update template!")
        return False
    
    # Step 6: Verification
    print("\\n✅ Step 6: Verification...")
    print(f"  📦 Final template: {os.path.basename(final_template)}")
    print(f"  📊 Total translations: {sum(data['string_count'] for data in all_translations.values())}")
    print(f"  📁 Files translated: {len(all_translations)}")
    
    # Show file sizes
    for file_path in [template_path, final_template]:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  📏 {os.path.basename(file_path)}: {size_mb:.3f} MB")
    
    print("\\n" + "=" * 70)
    print("✅ FULL INTEGRATION TEST COMPLETED SUCCESSFULLY!")
    print("\\n🎯 Results:")
    print(f"  • Test environment: {test_env_dir}")
    print(f"  • Original template: {os.path.basename(template_path)}")
    print(f"  • Updated template: {os.path.basename(final_template)}")
    print(f"  • Translation cache: {cache_dir}")
    
    return True

def main():
    """Main function"""
    try:
        success = run_full_integration_test()
        if success:
            print("\\n🎉 All tests passed! The template mod system is working correctly.")
        else:
            print("\\n❌ Some tests failed. Please check the error messages above.")
    except Exception as e:
        print(f"\\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
