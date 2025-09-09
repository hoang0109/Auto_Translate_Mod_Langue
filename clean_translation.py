#!/usr/bin/env python3
"""
Tạo bản dịch sạch chỉ từ file locale/en
"""
import os
import zipfile
import json
from pathlib import Path
from improved_mod_finder import find_locale_files_improved
from mod_translate_core import read_cfg_file, parse_cfg_lines
from google_translate_core import GoogleTranslateAPI

def analyze_and_clean_translate(selected_files, target_lang='VI'):
    """
    Tạo bản dịch sạch với filtering tốt hơn
    """
    print("🧹 CLEAN TRANSLATION PROCESS")
    print("=" * 50)
    
    google_translator = GoogleTranslateAPI()
    translated_mods = []
    skipped_mods = []
    
    # Tạo thư mục output sạch
    clean_output_dir = Path("clean_output")
    clean_output_dir.mkdir(exist_ok=True)
    
    for mod_path in selected_files:
        print(f"\n📦 Processing: {os.path.basename(mod_path)}")
        
        try:
            with zipfile.ZipFile(mod_path, 'r') as zipf:
                # Đọc info.json
                info_json_path = next((f for f in zipf.namelist() if f.endswith('info.json')), None)
                if not info_json_path:
                    print("  ❌ No info.json found")
                    continue
                
                with zipf.open(info_json_path) as f:
                    info = json.load(f)
                    mod_name = info.get("name", "unknown_mod")
                
                print(f"  🏷️  Mod name: {mod_name}")
                
                # Tìm file locale/en với filter nghiêm ngặt
                root_folder, locale_files = find_locale_files_improved(mod_path)
                
                if not locale_files:
                    print(f"  ⚪ No English locale files found")
                    skipped_mods.append(mod_name)
                    continue
                
                print(f"  📄 Found {len(locale_files)} English locale files:")
                for lf in locale_files:
                    print(f"    - {lf}")
                
                # Kiểm tra từng file có thực sự là tiếng Anh không
                verified_english_files = []
                all_values = []
                file_entries = []
                
                for locale_file in locale_files:
                    print(f"  🔍 Analyzing: {os.path.basename(locale_file)}")
                    
                    raw_text = read_cfg_file(zipf, locale_file)
                    key_vals, lines = parse_cfg_lines(raw_text)
                    
                    # Kiểm tra nội dung có phải tiếng Anh không
                    english_content = verify_english_content(key_vals)
                    
                    if english_content['is_english']:
                        print(f"    ✅ Verified as English ({english_content['english_ratio']:.1%} English content)")
                        verified_english_files.append(locale_file)
                        file_entries.append((locale_file, key_vals, lines))
                        all_values.extend([item['val'] for item in key_vals])
                    else:
                        print(f"    ❌ Not English ({english_content['english_ratio']:.1%} English, detected: {english_content['detected_languages']})")
                
                if not all_values:
                    print(f"  ⚪ No verified English content to translate")
                    skipped_mods.append(mod_name)
                    continue
                
                print(f"  🌐 Translating {len(all_values)} text entries...")
                
                # Dịch với Google Translate
                translated_values = google_translator.translate_texts(
                    all_values,
                    target_lang,
                    'en',
                    progress_callback=lambda current, total, msg: print(f"    {msg}")
                )
                
                # Tạo file .cfg dịch
                merged_lines = []
                tv_iter = iter(translated_values)
                
                for locale_file, key_vals, lines in file_entries:
                    translated_lines = lines[:]
                    for item in key_vals:
                        try:
                            translated_val = next(tv_iter)
                            translated_lines[item['index']] = f"{item['key']}={translated_val}\n"
                        except StopIteration:
                            break
                    merged_lines.extend(translated_lines)
                
                # Lưu file kết quả
                output_file = clean_output_dir / f"{mod_name}_clean.cfg"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.writelines(merged_lines)
                
                print(f"  ✅ Saved clean translation: {output_file.name}")
                translated_mods.append(mod_name)
                
        except Exception as e:
            print(f"  ❌ Error processing {mod_path}: {e}")
            continue
    
    # Báo cáo kết quả
    print(f"\n📊 CLEAN TRANSLATION SUMMARY")
    print("=" * 30)
    print(f"✅ Successfully translated: {len(translated_mods)} mods")
    print(f"⚪ Skipped (no English content): {len(skipped_mods)} mods")
    
    if translated_mods:
        print(f"\n📋 Translated mods:")
        for mod in translated_mods:
            print(f"  • {mod}")
    
    if skipped_mods:
        print(f"\n📋 Skipped mods:")
        for mod in skipped_mods:
            print(f"  • {mod}")

def verify_english_content(key_vals):
    """
    Kiểm tra nội dung có thực sự là tiếng Anh không
    Sử dụng thuật toán đơn giản hơn: kiểm tra các từ thông dụng tiếng Anh
    """
    
    total_entries = len(key_vals)
    if total_entries == 0:
        return {'is_english': False, 'english_ratio': 0, 'reason': 'No entries'}
    
    # Các từ tiếng Anh thông dụng trong Factorio
    english_indicators = [
        # Các từ thông dụng
        'the', 'and', 'for', 'with', 'from', 'this', 'that', 'can', 'will', 'are', 'is',
        # Các từ Factorio
        'iron', 'copper', 'steel', 'plate', 'gear', 'wire', 'engine', 'motor', 'belt',
        'inserter', 'assembling', 'machine', 'furnace', 'drill', 'mining', 'electric',
        'steam', 'boiler', 'generator', 'solar', 'panel', 'accumulator', 'lab',
        'science', 'pack', 'research', 'technology', 'recipe', 'item', 'entity'
    ]
    
    # Các chỉ số ngôn ngữ khác (ký tự đặc biệt)
    non_english_indicators = [
        # Tiếng Czech
        'č', 'ř', 'ě', 'š', 'ž', 'ý', 'á', 'í', 'é', 'ú', 'ů',
        # Tiếng Đức
        'ä', 'ö', 'ü', 'ß',
        # Tiếng Pháp  
        'à', 'â', 'ç', 'è', 'é', 'ê', 'ë', 'î', 'ï', 'ô', 'ù', 'û', 'ü',
        # Tiếng Tây Ban Nha
        'ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü'
    ]
    
    english_score = 0
    non_english_score = 0
    
    for item in key_vals:
        value = item['val'].strip().lower()
        if len(value) < 2:
            continue
            
        # Kiểm tra các từ tiếng Anh
        for indicator in english_indicators:
            if indicator in value:
                english_score += 1
                break  # Chỉ tính 1 lần cho mỗi entry
        
        # Kiểm tra các ký tự không phải tiếng Anh
        for char in non_english_indicators:
            if char in value:
                non_english_score += 2  # Trừng phạt nặng hơn
                break
    
    # Tính ratio tiếng Anh
    english_ratio = english_score / max(total_entries, 1)
    non_english_ratio = non_english_score / max(total_entries, 1)
    
    # Quyết định: ít nhất 30% các entry có từ tiếng Anh và không quá 20% các entry có ký tự không phải tiếng Anh
    is_english = english_ratio >= 0.3 and non_english_ratio <= 0.2
    
    return {
        'is_english': is_english,
        'english_ratio': english_ratio,
        'non_english_ratio': non_english_ratio,
        'english_score': english_score,
        'non_english_score': non_english_score,
        'total_entries': total_entries,
        'reason': f'English: {english_score}/{total_entries} ({english_ratio:.1%}), Non-English: {non_english_score}/{total_entries} ({non_english_ratio:.1%})'
    }

def test_clean_translation():
    """Test với một vài mod"""
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    
    # Test với một vài mod có tiếng Anh
    test_mods = [
        "aai-industry_0.6.10.zip",
        "alien-biomes_0.7.4.zip",
        "jetpack_0.4.12.zip"
    ]
    
    selected_files = []
    for mod_name in test_mods:
        mod_path = os.path.join(mods_dir, mod_name)
        if os.path.exists(mod_path):
            selected_files.append(mod_path)
    
    if selected_files:
        analyze_and_clean_translate(selected_files, 'VI')
    else:
        print("❌ No test mods found!")

if __name__ == "__main__":
    test_clean_translation()
