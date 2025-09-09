#!/usr/bin/env python3
"""
Improved Mod Finder
Thay thế logic find_locale_files cũ bằng improved scanning
"""
import os
import zipfile
from pathlib import Path

def find_locale_files_improved(zip_path):
    """
    Improved version of find_locale_files that can find cfg files in various structures
    Returns: (root_folder, locale_files_list)
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            all_files = zipf.namelist()
            
            if not all_files:
                return None, []
            
            # Find root folder (look for info.json)
            root_folder = None
            for file_path in all_files:
                if file_path.endswith('info.json'):
                    parts = file_path.split('/')
                    if len(parts) >= 2:
                        root_folder = parts[0]
                        break
            
            # If no info.json found, use first directory
            if root_folder is None:
                for file_path in all_files:
                    if '/' in file_path:
                        root_folder = file_path.split('/')[0]
                        break
            
            if root_folder is None:
                return None, []
            
            # Find ALL .cfg files first
            cfg_files = [f for f in all_files if f.endswith('.cfg')]
            
            if not cfg_files:
                return root_folder, []
            
            # Filter for English locale files using strict patterns
            en_locale_files = []
            
            for cfg_file in cfg_files:
                cfg_lower = cfg_file.lower()
                is_english = False
                
                # Strict Pattern 1: Must contain /en/ or \en\ (exact match)
                if '/en/' in cfg_lower or '\\en\\' in cfg_lower:
                    # Kiểm tra không phải ngôn ngữ khác
                    other_langs = ['cs', 'de', 'fr', 'es', 'it', 'pl', 'ru', 'ja', 'ko', 'zh', 'pt', 'nl']
                    has_other_lang = any(f'/{lang}/' in cfg_lower or f'\\{lang}\\' in cfg_lower for lang in other_langs)
                    if not has_other_lang:
                        is_english = True
                
                # Strict Pattern 2: Check directory structure parts - must be exactly 'en'
                parts = cfg_file.split('/')
                for i, part in enumerate(parts):
                    if part.lower() == 'en' and i > 0 and i < len(parts) - 1:  # 'en' không được ở đầu hoặc cuối
                        prev_part = parts[i-1].lower()
                        if prev_part in ['locale', 'locales', 'lang', 'langs', 'language', 'languages']:
                            # Kiểm tra file name không chứa ngôn ngữ khác
                            filename = parts[-1].lower()
                            if not any(lang in filename for lang in ['czech', 'german', 'french', 'spanish']):
                                is_english = True
                                break
                
                if is_english:
                    en_locale_files.append(cfg_file)
            
            return root_folder, en_locale_files
            
    except zipfile.BadZipFile:
        return None, []
    except Exception as e:
        print(f"Error in find_locale_files_improved: {e}")
        return None, []

def test_improved_finder():
    """Test the improved finder with known problematic mods"""
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    
    # Test mods that were showing as "skipped" before
    test_mods = [
        "aai-industry_0.6.10.zip",
        "HeroTurretRedux_1.0.30.zip",
        "BeltSpeedMultiplier_1.0.3.zip",
        "Babelfish_2.0.0.zip"
    ]
    
    print("🧪 Testing Improved Mod Finder")
    print("=" * 50)
    
    for mod_name in test_mods:
        mod_path = os.path.join(mods_dir, mod_name)
        if os.path.exists(mod_path):
            print(f"\n📦 Testing: {mod_name}")
            
            # Test old method (for comparison)
            try:
                from mod_translate_pack_core import find_locale_files as old_find
                old_root, old_files = old_find(mod_path)
                print(f"  🔸 Old method: {len(old_files)} files found")
                if old_files:
                    print(f"    First file: {old_files[0]}")
            except Exception as e:
                print(f"  ❌ Old method failed: {e}")
            
            # Test new method
            try:
                new_root, new_files = find_locale_files_improved(mod_path)
                print(f"  ✅ New method: {len(new_files)} files found")
                if new_files:
                    print(f"    Files found:")
                    for i, file_path in enumerate(new_files[:3]):  # Show first 3
                        print(f"      {i+1}. {file_path}")
                    if len(new_files) > 3:
                        print(f"      ... and {len(new_files) - 3} more")
            except Exception as e:
                print(f"  ❌ New method failed: {e}")
        else:
            print(f"❌ {mod_name} not found")

def scan_all_mods_with_improved_finder(mods_dir):
    """Scan all mods using improved finder"""
    if not os.path.exists(mods_dir):
        print(f"❌ Directory not found: {mods_dir}")
        return {}
    
    print(f"🔍 Scanning all mods with improved finder...")
    print(f"Directory: {mods_dir}")
    
    all_mods = [f for f in os.listdir(mods_dir) if f.endswith('.zip')]
    print(f"Found {len(all_mods)} zip files")
    
    results = {}
    translatable_count = 0
    
    for mod_file in all_mods:
        mod_path = os.path.join(mods_dir, mod_file)
        root_folder, locale_files = find_locale_files_improved(mod_path)
        
        if locale_files:
            results[mod_file] = {
                'root_folder': root_folder,
                'locale_files': locale_files,
                'file_count': len(locale_files)
            }
            translatable_count += 1
            print(f"  ✅ {mod_file}: {len(locale_files)} locale files")
        else:
            print(f"  ⚪ {mod_file}: No locale files found")
    
    print(f"\n📊 Summary:")
    print(f"  • Total mods scanned: {len(all_mods)}")
    print(f"  • Mods with locale files: {translatable_count}")
    print(f"  • Success rate: {translatable_count/len(all_mods)*100:.1f}%")
    
    return results

if __name__ == "__main__":
    # Run tests
    test_improved_finder()
    
    print("\n" + "=" * 60)
    print("🔍 SCANNING ALL MODS")
    print("=" * 60)
    
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    results = scan_all_mods_with_improved_finder(mods_dir)
    
    if results:
        print(f"\n🎯 TOP TRANSLATABLE MODS:")
        sorted_results = sorted(results.items(), key=lambda x: x[1]['file_count'], reverse=True)
        for mod_name, info in sorted_results[:10]:
            print(f"  • {mod_name}: {info['file_count']} files")
