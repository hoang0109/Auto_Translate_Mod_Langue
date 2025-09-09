#!/usr/bin/env python3
"""
Phân tích cấu trúc các mod Factorio thực tế
Để hiểu cách các mod hoạt động và có thể Việt hóa
"""
import os
import zipfile
import json
from pathlib import Path
from collections import defaultdict
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mod_translate_core import find_locale_files, parse_cfg_lines, read_cfg_file

def analyze_mod_structure(mod_path):
    """Phân tích cấu trúc của một mod"""
    mod_info = {
        'name': os.path.basename(mod_path),
        'size_mb': round(os.path.getsize(mod_path) / (1024*1024), 2),
        'has_info_json': False,
        'has_locale_en': False,
        'has_locale_other': False,
        'locale_languages': [],
        'locale_file_count': 0,
        'translatable_strings': 0,
        'mod_data': {},
        'file_types': defaultdict(int),
        'error': None
    }
    
    try:
        with zipfile.ZipFile(mod_path, 'r') as zipf:
            file_list = zipf.namelist()
            
            # Count file types
            for file_name in file_list:
                ext = Path(file_name).suffix.lower()
                mod_info['file_types'][ext if ext else 'no_extension'] += 1
            
            # Check for info.json
            info_files = [f for f in file_list if f.endswith('info.json')]
            if info_files:
                mod_info['has_info_json'] = True
                try:
                    with zipf.open(info_files[0]) as f:
                        mod_data = json.load(f)
                        mod_info['mod_data'] = {
                            'name': mod_data.get('name', 'unknown'),
                            'version': mod_data.get('version', 'unknown'),
                            'title': mod_data.get('title', ''),
                            'author': mod_data.get('author', ''),
                            'factorio_version': mod_data.get('factorio_version', ''),
                            'dependencies': len(mod_data.get('dependencies', []))
                        }
                except Exception as e:
                    mod_info['error'] = f"Error reading info.json: {e}"
            
            # Check locale files
            locale_files = [f for f in file_list if 'locale/' in f and f.endswith('.cfg')]
            mod_info['locale_file_count'] = len(locale_files)
            
            # Find languages
            languages = set()
            for locale_file in locale_files:
                parts = locale_file.split('/')
                for i, part in enumerate(parts):
                    if part == 'locale' and i + 1 < len(parts):
                        languages.add(parts[i + 1])
            
            mod_info['locale_languages'] = list(languages)
            mod_info['has_locale_en'] = 'en' in languages
            mod_info['has_locale_other'] = len(languages) > 1 or ('en' not in languages and len(languages) > 0)
            
            # Count translatable strings (only from English)
            if mod_info['has_locale_en']:
                try:
                    en_files = [f for f in locale_files if '/en/' in f]
                    total_strings = 0
                    for en_file in en_files:
                        raw_content = read_cfg_file(zipf, en_file)
                        key_vals, _ = parse_cfg_lines(raw_content)
                        total_strings += len(key_vals)
                    mod_info['translatable_strings'] = total_strings
                except Exception as e:
                    mod_info['error'] = f"Error counting strings: {e}"
            
    except Exception as e:
        mod_info['error'] = f"Error opening zip: {e}"
    
    return mod_info

def analyze_mods_directory(mods_dir):
    """Phân tích toàn bộ thư mục mods"""
    print(f"🔍 Analyzing mods directory: {mods_dir}")
    print("=" * 60)
    
    if not os.path.exists(mods_dir):
        print(f"❌ Directory not found: {mods_dir}")
        return
    
    # Get all zip files
    mod_files = []
    for file in os.listdir(mods_dir):
        if file.endswith('.zip'):
            mod_files.append(os.path.join(mods_dir, file))
    
    print(f"Found {len(mod_files)} mod files")
    
    # Analyze each mod
    translatable_mods = []
    non_translatable_mods = []
    error_mods = []
    
    total_strings = 0
    total_size = 0
    
    for mod_path in sorted(mod_files)[:20]:  # Limit to first 20 for demo
        print(f"\\nAnalyzing: {os.path.basename(mod_path)}...")
        mod_info = analyze_mod_structure(mod_path)
        
        total_size += mod_info['size_mb']
        
        if mod_info['error']:
            error_mods.append(mod_info)
            print(f"  ❌ Error: {mod_info['error']}")
        elif mod_info['has_locale_en'] and mod_info['translatable_strings'] > 0:
            translatable_mods.append(mod_info)
            total_strings += mod_info['translatable_strings']
            print(f"  ✅ Translatable: {mod_info['translatable_strings']} strings")
            print(f"     Name: {mod_info['mod_data'].get('name', 'unknown')}")
            print(f"     Version: {mod_info['mod_data'].get('version', 'unknown')}")
            print(f"     Size: {mod_info['size_mb']} MB")
        else:
            non_translatable_mods.append(mod_info)
            reason = "No locale/en" if not mod_info['has_locale_en'] else "No translatable strings"
            print(f"  ⚪ Not translatable: {reason}")
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total mods analyzed: {len(translatable_mods) + len(non_translatable_mods) + len(error_mods)}")
    print(f"✅ Translatable mods: {len(translatable_mods)}")
    print(f"⚪ Non-translatable mods: {len(non_translatable_mods)}")
    print(f"❌ Error mods: {len(error_mods)}")
    print(f"💬 Total translatable strings: {total_strings:,}")
    print(f"💾 Total size analyzed: {total_size:.1f} MB")
    
    # Detailed analysis of translatable mods
    if translatable_mods:
        print("\\n" + "=" * 60)
        print("🌍 TRANSLATABLE MODS DETAILS")
        print("=" * 60)
        
        for mod in translatable_mods:
            print(f"\\n📦 {mod['mod_data'].get('title', mod['mod_data'].get('name', 'Unknown'))}")
            print(f"   Name: {mod['mod_data'].get('name')}")
            print(f"   Version: {mod['mod_data'].get('version')}")
            print(f"   Author: {mod['mod_data'].get('author', 'Unknown')}")
            print(f"   Factorio Version: {mod['mod_data'].get('factorio_version', 'Unknown')}")
            print(f"   Size: {mod['size_mb']} MB")
            print(f"   Translatable Strings: {mod['translatable_strings']}")
            print(f"   Languages: {', '.join(mod['locale_languages'])}")
            print(f"   Dependencies: {mod['mod_data'].get('dependencies', 0)}")
            
            # File types
            main_types = {k: v for k, v in mod['file_types'].items() if v > 5}
            if main_types:
                print(f"   Main File Types: {dict(main_types)}")
    
    # Analysis by categories
    print("\\n" + "=" * 60)
    print("📈 ANALYSIS BY CATEGORIES")
    print("=" * 60)
    
    # Group by string count
    string_ranges = {
        "1-10": [],
        "11-50": [],
        "51-200": [],
        "200+": []
    }
    
    for mod in translatable_mods:
        strings = mod['translatable_strings']
        if strings <= 10:
            string_ranges["1-10"].append(mod)
        elif strings <= 50:
            string_ranges["11-50"].append(mod)
        elif strings <= 200:
            string_ranges["51-200"].append(mod)
        else:
            string_ranges["200+"].append(mod)
    
    for range_name, mods in string_ranges.items():
        if mods:
            print(f"\\n📊 {range_name} strings: {len(mods)} mods")
            for mod in mods[:3]:  # Show top 3
                print(f"   • {mod['mod_data'].get('name')}: {mod['translatable_strings']} strings")
    
    return {
        'translatable': translatable_mods,
        'non_translatable': non_translatable_mods,
        'errors': error_mods,
        'total_strings': total_strings
    }

def recommend_translation_targets(analysis_result):
    """Đề xuất các mod nên dịch trước"""
    print("\\n" + "=" * 60)
    print("🎯 TRANSLATION RECOMMENDATIONS")
    print("=" * 60)
    
    translatable = analysis_result['translatable']
    
    # Sort by different criteria
    by_strings = sorted(translatable, key=lambda x: x['translatable_strings'], reverse=True)
    by_size = sorted(translatable, key=lambda x: x['size_mb'])
    
    print("\\n🔥 TOP PRIORITY (Most translatable content):")
    for i, mod in enumerate(by_strings[:5], 1):
        print(f"{i}. {mod['mod_data'].get('name')} - {mod['translatable_strings']} strings ({mod['size_mb']} MB)")
    
    print("\\n⚡ EASY TARGETS (Small size, good content):")
    easy_targets = [mod for mod in by_size if mod['translatable_strings'] >= 10 and mod['size_mb'] < 5.0]
    for i, mod in enumerate(easy_targets[:5], 1):
        print(f"{i}. {mod['mod_data'].get('name')} - {mod['translatable_strings']} strings ({mod['size_mb']} MB)")
    
    print("\\n💎 QUALITY PICKS (Good balance):")
    quality_picks = [mod for mod in translatable if 20 <= mod['translatable_strings'] <= 100 and mod['size_mb'] < 10.0]
    quality_picks = sorted(quality_picks, key=lambda x: x['translatable_strings'] / max(mod['size_mb'], 0.1), reverse=True)
    for i, mod in enumerate(quality_picks[:5], 1):
        ratio = mod['translatable_strings'] / max(mod['size_mb'], 0.1)
        print(f"{i}. {mod['mod_data'].get('name')} - {mod['translatable_strings']} strings ({mod['size_mb']} MB) [Ratio: {ratio:.1f}]")

def create_test_batch(analysis_result):
    """Tạo batch test với các mod thực tế"""
    print("\\n" + "=" * 60)
    print("🧪 CREATE TEST BATCH")
    print("=" * 60)
    
    translatable = analysis_result['translatable']
    
    # Select diverse test set
    test_candidates = []
    
    # 1 mod nhỏ (< 1MB, < 20 strings)
    small_mods = [mod for mod in translatable if mod['size_mb'] < 1.0 and mod['translatable_strings'] < 20]
    if small_mods:
        test_candidates.append(("SMALL", small_mods[0]))
    
    # 1 mod trung bình (1-5MB, 20-100 strings) 
    medium_mods = [mod for mod in translatable if 1.0 <= mod['size_mb'] <= 5.0 and 20 <= mod['translatable_strings'] <= 100]
    if medium_mods:
        test_candidates.append(("MEDIUM", medium_mods[0]))
    
    # 1 mod lớn (>5MB, >100 strings)
    large_mods = [mod for mod in translatable if mod['size_mb'] > 5.0 and mod['translatable_strings'] > 100]
    if large_mods:
        test_candidates.append(("LARGE", large_mods[0]))
    
    print("Recommended test batch:")
    for category, mod in test_candidates:
        print(f"\\n{category} MOD:")
        print(f"  📦 Name: {mod['mod_data'].get('name')}")
        print(f"  📁 File: {mod['name']}")
        print(f"  💬 Strings: {mod['translatable_strings']}")
        print(f"  💾 Size: {mod['size_mb']} MB")
        print(f"  🌍 Languages: {', '.join(mod['locale_languages'])}")

def main():
    """Main function"""
    mods_dir = r"C:\\Users\\Acer\\AppData\\Roaming\\Factorio\\mods"
    
    print("🎮 FACTORIO MODS STRUCTURE ANALYZER")
    print("=" * 60)
    
    # Analyze all mods
    analysis_result = analyze_mods_directory(mods_dir)
    
    # Recommendations
    if analysis_result and analysis_result['translatable']:
        recommend_translation_targets(analysis_result)
        create_test_batch(analysis_result)
    
    print("\\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETED!")
    print("\\n🎯 Next steps:")
    print("1. Pick a small mod from recommendations")
    print("2. Copy to current directory")
    print("3. Test with our translator")
    print("4. Compare with real DeepL API")

if __name__ == "__main__":
    main()
