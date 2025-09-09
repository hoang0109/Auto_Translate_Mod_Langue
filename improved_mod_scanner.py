#!/usr/bin/env python3
"""
Improved Mod Scanner
Quét lại tất cả mod và phát hiện chính xác các file .cfg bất kể cấu trúc thư mục
"""
import os
import zipfile
import json
from pathlib import Path
import sys

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def deep_scan_mod_structure(mod_path):
    """Quét sâu cấu trúc mod để tìm tất cả file cfg"""
    print(f"\n🔍 Deep scanning: {os.path.basename(mod_path)}")
    
    mod_info = {
        'path': mod_path,
        'name': os.path.basename(mod_path),
        'size_mb': round(os.path.getsize(mod_path) / (1024*1024), 3),
        'all_files': [],
        'info_json': None,
        'locale_files': [],
        'en_locale_files': [],
        'other_locale_files': [],
        'cfg_files': [],
        'directory_structure': [],
        'error': None
    }
    
    try:
        with zipfile.ZipFile(mod_path, 'r') as zipf:
            all_files = zipf.namelist()
            mod_info['all_files'] = all_files
            
            print(f"  📁 Total files in zip: {len(all_files)}")
            
            # Analyze directory structure
            directories = set()
            for file_path in all_files:
                parts = file_path.split('/')
                for i in range(len(parts)):
                    if i > 0:  # Skip empty root
                        dir_path = '/'.join(parts[:i+1])
                        if dir_path.endswith('/') or i == len(parts) - 1:
                            directories.add(dir_path.rstrip('/'))
            
            mod_info['directory_structure'] = sorted(list(directories))
            
            # Find info.json
            info_files = [f for f in all_files if f.endswith('info.json')]
            if info_files:
                print(f"  📄 Found info.json: {info_files[0]}")
                try:
                    with zipf.open(info_files[0]) as f:
                        mod_info['info_json'] = json.load(f)
                except Exception as e:
                    print(f"    ⚠️ Error reading info.json: {e}")
            
            # Find ALL .cfg files (regardless of location)
            cfg_files = [f for f in all_files if f.endswith('.cfg')]
            mod_info['cfg_files'] = cfg_files
            
            if cfg_files:
                print(f"  📄 Found {len(cfg_files)} .cfg files:")
                for cfg_file in cfg_files:
                    print(f"    • {cfg_file}")
            
            # Categorize locale files
            locale_files = [f for f in cfg_files if 'locale' in f.lower()]
            mod_info['locale_files'] = locale_files
            
            # Find English locale files (more flexible search)
            en_patterns = ['/en/', '\\en\\', 'locale/en', 'locale\\en', 'strings.cfg', 'english.cfg']
            en_locale_files = []
            
            for cfg_file in cfg_files:
                cfg_lower = cfg_file.lower()
                # Check if it's an English locale file
                is_english = False
                
                # Pattern 1: Contains /en/ or \en\
                if '/en/' in cfg_lower or '\\en\\' in cfg_lower:
                    is_english = True
                
                # Pattern 2: Contains "locale" and "en" somehow
                elif 'locale' in cfg_lower and '/en' in cfg_lower:
                    is_english = True
                
                # Pattern 3: Common English file names
                elif any(pattern in cfg_lower for pattern in ['strings.cfg', 'english.cfg', 'en.cfg']):
                    # Make sure it's in a locale-like directory
                    if 'locale' in cfg_lower or 'lang' in cfg_lower:
                        is_english = True
                
                # Pattern 4: Check directory structure
                parts = cfg_file.split('/')
                for i, part in enumerate(parts):
                    if part.lower() == 'en' and i > 0:
                        # Check if previous part suggests locale directory
                        prev_part = parts[i-1].lower()
                        if prev_part in ['locale', 'locales', 'lang', 'langs', 'language', 'languages']:
                            is_english = True
                            break
                
                if is_english:
                    en_locale_files.append(cfg_file)
            
            mod_info['en_locale_files'] = en_locale_files
            
            # Find other language files
            other_locale_files = [f for f in locale_files if f not in en_locale_files]
            mod_info['other_locale_files'] = other_locale_files
            
            print(f"  🌍 English locale files: {len(en_locale_files)}")
            for en_file in en_locale_files:
                print(f"    📄 {en_file}")
            
            if other_locale_files:
                print(f"  🌐 Other locale files: {len(other_locale_files)}")
                for other_file in other_locale_files[:3]:  # Show first 3
                    print(f"    📄 {other_file}")
                if len(other_locale_files) > 3:
                    print(f"    ... and {len(other_locale_files) - 3} more")
            
            # Show directory structure if it has locale
            locale_dirs = [d for d in mod_info['directory_structure'] if 'locale' in d.lower()]
            if locale_dirs:
                print(f"  📂 Locale directories found:")
                for locale_dir in locale_dirs:
                    print(f"    📁 {locale_dir}")
            
    except Exception as e:
        mod_info['error'] = str(e)
        print(f"  ❌ Error: {e}")
    
    return mod_info

def scan_specific_mods():
    """Quét các mod cụ thể mà bạn đã đề cập"""
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    
    # Các mod được đề cập trong warning
    specific_mods = [
        "aai-industry_0.6.10.zip",
        "AAI-Burner-Bots",
        "adjustable-magazine-size", 
        "BeltSpeedMultiplier",
        "copper-construction-robots",
        "HeroTurretRedux",
        "InfiniteDroneBattery-PoweredByDelta",
        "instant-mining-plus",
        "loaders-utils",
        "MachineSpeedMultiplier",
        "spoilable-blueprint-books",
        "starter_turrets",
        "Turret_Range_Buff_Updated",
        "Turret-Shields",
        "vanilla-loaders-hd",
        "water-pumpjack",
        "YKR_inventory_500slot"
    ]
    
    print("🔍 IMPROVED MOD SCANNER")
    print("=" * 60)
    print(f"Scanning specific mods mentioned in warnings...")
    
    found_mods = []
    missing_mods = []
    
    # First, find all zip files in mods directory
    if os.path.exists(mods_dir):
        all_zip_files = [f for f in os.listdir(mods_dir) if f.endswith('.zip')]
        print(f"📦 Found {len(all_zip_files)} zip files in mods directory")
        
        # Try to match specific mods
        for target_mod in specific_mods:
            # Find matching files (exact match or contains target name)
            matches = []
            for zip_file in all_zip_files:
                if target_mod in zip_file or zip_file.startswith(target_mod):
                    matches.append(zip_file)
            
            if matches:
                # Use the first match (usually most recent version)
                selected_mod = matches[0]
                mod_path = os.path.join(mods_dir, selected_mod)
                found_mods.append(mod_path)
                print(f"✅ Found: {target_mod} -> {selected_mod}")
            else:
                missing_mods.append(target_mod)
                print(f"❌ Missing: {target_mod}")
    
    print(f"\n📊 Summary: {len(found_mods)} found, {len(missing_mods)} missing")
    
    return found_mods

def analyze_found_mods(mod_paths):
    """Phân tích chi tiết các mod đã tìm thấy"""
    print("\n" + "=" * 60)
    print("📋 DETAILED MOD ANALYSIS")
    print("=" * 60)
    
    results = []
    
    for mod_path in mod_paths:
        result = deep_scan_mod_structure(mod_path)
        results.append(result)
    
    return results

def generate_summary_report(results):
    """Tạo báo cáo tổng kết"""
    print("\n" + "=" * 60)
    print("📊 SUMMARY REPORT")
    print("=" * 60)
    
    total_mods = len(results)
    mods_with_cfg = len([r for r in results if r['cfg_files']])
    mods_with_en_locale = len([r for r in results if r['en_locale_files']])
    mods_with_other_locale = len([r for r in results if r['other_locale_files']])
    
    print(f"📋 OVERVIEW:")
    print(f"  • Total mods analyzed: {total_mods}")
    print(f"  • Mods with .cfg files: {mods_with_cfg}")
    print(f"  • Mods with English locale: {mods_with_en_locale}")
    print(f"  • Mods with other locales: {mods_with_other_locale}")
    
    print(f"\n✅ MODS WITH TRANSLATABLE CONTENT:")
    translatable_mods = [r for r in results if r['en_locale_files']]
    
    for mod in translatable_mods:
        print(f"\n📦 {mod['name']} ({mod['size_mb']} MB)")
        print(f"  📄 English files: {len(mod['en_locale_files'])}")
        for en_file in mod['en_locale_files']:
            print(f"    • {en_file}")
        
        if mod['other_locale_files']:
            print(f"  🌐 Other locales: {len(mod['other_locale_files'])}")
    
    print(f"\n⚠️ MODS WITHOUT ENGLISH LOCALE:")
    non_translatable = [r for r in results if not r['en_locale_files']]
    
    for mod in non_translatable:
        print(f"\n📦 {mod['name']}")
        if mod['cfg_files']:
            print(f"  📄 Has .cfg files but not English locale:")
            for cfg_file in mod['cfg_files'][:3]:  # Show first 3
                print(f"    • {cfg_file}")
            if len(mod['cfg_files']) > 3:
                print(f"    ... and {len(mod['cfg_files']) - 3} more")
        else:
            print(f"  ⚪ No .cfg files found")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if translatable_mods:
        print(f"  ✅ Ready to translate: {len(translatable_mods)} mods")
        print(f"  🎯 Recommended for immediate translation:")
        for mod in translatable_mods[:3]:  # Top 3
            print(f"    • {mod['name']}: {len(mod['en_locale_files'])} English files")
    
    if non_translatable:
        print(f"  🔍 Need manual inspection: {len(non_translatable)} mods")
        print(f"    (May have non-standard locale structure)")

def save_detailed_results(results):
    """Lưu kết quả chi tiết ra file"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"improved_mod_scan_{timestamp}.json"
    
    # Prepare data for JSON serialization
    json_data = {
        'timestamp': timestamp,
        'total_mods': len(results),
        'scan_results': results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    return filename

def main():
    """Main function"""
    print("🔧 Starting improved mod scanning...")
    
    # Scan specific mods mentioned in warnings
    found_mod_paths = scan_specific_mods()
    
    if not found_mod_paths:
        print("\n❌ No mods found to analyze!")
        return
    
    # Analyze found mods in detail
    results = analyze_found_mods(found_mod_paths)
    
    # Generate summary report
    generate_summary_report(results)
    
    # Save detailed results
    save_detailed_results(results)
    
    print(f"\n🎉 Improved scanning completed!")
    print(f"📈 This should find .cfg files that were missed before")

if __name__ == "__main__":
    main()
