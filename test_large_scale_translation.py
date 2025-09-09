#!/usr/bin/env python3
"""
Large Scale Translation Test
Test với 10 mod khác nhau sử dụng dịch miễn phí (Google Translate hoặc mock advanced)
"""
import os
import shutil
import sys
import json
import zipfile
import time
import hashlib
from pathlib import Path
import tempfile
from datetime import datetime
from collections import defaultdict

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mod_translate_core import find_locale_files, parse_cfg_lines, read_cfg_file

# Free translation alternatives
try:
    from googletrans import Translator as GoogleTranslator
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️ googletrans not available, using advanced mock translation")

class FreeTranslationEngine:
    """Engine dịch miễn phí với nhiều phương pháp"""
    
    def __init__(self):
        self.google_translator = GoogleTranslator() if GOOGLE_AVAILABLE else None
        self.translation_cache = {}
        
        # Vietnamese translation dictionary
        self.vietnamese_dict = {
            # Common game terms
            "speed": "tốc độ",
            "belt": "băng tải", 
            "conveyor": "băng chuyền",
            "multiplier": "hệ số nhân",
            "setting": "cài đặt",
            "language": "ngôn ngữ",
            "target": "mục tiêu",
            "size": "kích thước",
            "big": "lớn",
            "small": "nhỏ",
            "bag": "túi",
            "inventory": "kho đồ",
            "item": "vật phẩm",
            "recipe": "công thức",
            "technology": "công nghệ",
            "research": "nghiên cứu",
            "entity": "thực thể",
            "fluid": "chất lỏng",
            "tile": "ô đất",
            "signal": "tín hiệu",
            "virtual": "ảo",
            "translate": "dịch",
            "batch": "lô",
            "request": "yêu cầu",
            "how many": "bao nhiêu",
            "per": "mỗi",
            "electric": "điện",
            "pole": "cột",
            "range": "phạm vi",
            "machine": "máy móc",
            "mining": "khai thác",
            "drone": "máy bay không người lái",
            "calculator": "máy tính",
            "rate": "tỷ lệ",
            "hero": "anh hùng",
            "turret": "tháp pháo",
            "redux": "cải tiến",
            "monster": "quái vật",
            "biter": "côn trùng cắn",
            "cold": "lạnh",
            "frost": "băng giá",
            "explosive": "nổ",
            "armoured": "bọc thép",
            "armor": "giáp",
            "bot": "robot",
            "start": "bắt đầu",
            "mega": "siêu",
            "gun": "súng",
            "equipment": "trang bị",
            "burner": "đốt nhiên liệu",
            "alien": "người ngoài hành tinh",
            "chaos": "hỗn loạn",
            "modpack": "gói mod",
            "enemy": "kẻ thù",
            "arachnid": "nhện",
            "stack": "chồng",
            "infinite": "vô hạn",
            "battery": "pin",
            "powered": "được cung cấp điện",
            "delta": "delta",
            # Common interface terms
            "name": "tên",
            "description": "mô tả", 
            "mod": "mod",
            "category": "danh mục",
            "group": "nhóm",
            "subgroup": "nhóm con",
            "order": "thứ tự",
            "enabled": "bật",
            "disabled": "tắt",
            "default": "mặc định",
            "value": "giá trị",
            "option": "tùy chọn",
            "tooltip": "chú thích",
            "label": "nhãn"
        }
    
    def translate_with_google(self, text, target_lang='vi'):
        """Dịch bằng Google Translate (nếu có)"""
        if not self.google_translator:
            return None
        
        try:
            # Check cache first
            cache_key = f"{text}_{target_lang}"
            if cache_key in self.translation_cache:
                return self.translation_cache[cache_key]
            
            result = self.google_translator.translate(text, dest=target_lang)
            translated = result.text
            
            # Cache result
            self.translation_cache[cache_key] = translated
            return translated
            
        except Exception as e:
            print(f"  ⚠️ Google Translate error: {e}")
            return None
    
    def advanced_mock_translate(self, text):
        """Mock translation nâng cao với AI-like logic"""
        original_text = text
        translated = text.lower()
        
        # Apply dictionary replacements
        for en_term, vi_term in self.vietnamese_dict.items():
            translated = translated.replace(en_term, vi_term)
        
        # Handle common patterns
        if "how many" in original_text.lower():
            translated = translated.replace("how many", "bao nhiêu")
        
        if " per " in original_text.lower():
            translated = translated.replace(" per ", " mỗi ")
        
        if translated.startswith("translate ("):
            translated = translated.replace("translate (", "dịch (").replace(")", ")")
        
        # Capitalize first letter if original was capitalized
        if original_text and original_text[0].isupper():
            translated = translated.capitalize()
        
        # If no changes made, add [VI] prefix
        if translated.lower() == original_text.lower():
            translated = f"[VI] {original_text}"
        
        return translated
    
    def translate_text(self, text, use_google=True):
        """Translate text using available methods"""
        if use_google and GOOGLE_AVAILABLE:
            result = self.translate_with_google(text)
            if result:
                return result
        
        # Fallback to advanced mock
        return self.advanced_mock_translate(text)
    
    def translate_batch(self, texts, use_google=True):
        """Batch translate multiple texts"""
        results = []
        for text in texts:
            translated = self.translate_text(text, use_google)
            results.append(translated)
            
            # Add small delay to avoid rate limiting
            if use_google and GOOGLE_AVAILABLE:
                time.sleep(0.1)
        
        return results

def select_test_mods():
    """Chọn 10 mod để test từ analysis trước"""
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    
    # Top 10 mod recommendations từ analysis trước
    target_mods = [
        "Babelfish_2.0.0.zip",           # 11 strings, 0.04 MB
        "BigBags_1.0.37.zip",            # 23 strings, 0.07 MB  
        "BeltSpeedMultiplier_1.0.3.zip", # 1 string, 0.02 MB
        "ElectricPoleRangeMultiplier_1.0.3.zip", # 1 string, 0.01 MB
        "MachineSpeedMultiplier_1.1.1.zip",      # 8 strings, 0.02 MB
        "BobsStackSize_1.0.0.zip",       # 1 string, 0.03 MB
        "GunEquipment_0.0.22.zip",       # 6 strings, 0.28 MB
        "Mining_Drones_2.0.2.zip",       # 7 strings, 3.88 MB
        "MegaBotStart_2.0.2.zip",        # 4 strings, 0.68 MB
        "RateCalculator_3.3.7.zip"       # 66 strings, 0.09 MB
    ]
    
    available_mods = []
    for mod_file in target_mods:
        mod_path = os.path.join(mods_dir, mod_file)
        if os.path.exists(mod_path):
            available_mods.append(mod_path)
    
    print(f"🎯 Selected {len(available_mods)} mods for large scale test:")
    for i, mod_path in enumerate(available_mods, 1):
        size_mb = os.path.getsize(mod_path) / (1024 * 1024)
        print(f"  {i}. {os.path.basename(mod_path)} ({size_mb:.3f} MB)")
    
    return available_mods

def analyze_mod_for_translation(mod_path):
    """Phân tích chi tiết một mod để dịch"""
    print(f"\n🔍 Analyzing {os.path.basename(mod_path)}...")
    
    mod_info = {
        'path': mod_path,
        'name': os.path.basename(mod_path),
        'size_mb': round(os.path.getsize(mod_path) / (1024*1024), 3),
        'translatable_strings': 0,
        'locale_files': [],
        'translation_data': {},
        'analysis_time': 0,
        'error': None
    }
    
    start_time = time.time()
    
    try:
        # Get mod metadata
        with zipfile.ZipFile(mod_path, 'r') as zipf:
            info_files = [f for f in zipf.namelist() if f.endswith('info.json')]
            if info_files:
                with zipf.open(info_files[0]) as f:
                    info_data = json.load(f)
                    mod_info['mod_name'] = info_data.get('name', 'unknown')
                    mod_info['version'] = info_data.get('version', 'unknown')
                    mod_info['title'] = info_data.get('title', '')
        
        # Find and analyze locale files
        root_folder, locale_files = find_locale_files(mod_path)
        mod_info['locale_files'] = locale_files
        
        if locale_files:
            with zipfile.ZipFile(mod_path, 'r') as zipf:
                for locale_file in locale_files:
                    raw_content = read_cfg_file(zipf, locale_file)
                    key_vals, original_lines = parse_cfg_lines(raw_content)
                    
                    if key_vals:
                        file_data = {
                            'key_vals': key_vals,
                            'original_lines': original_lines,
                            'string_count': len(key_vals)
                        }
                        mod_info['translation_data'][locale_file] = file_data
                        mod_info['translatable_strings'] += len(key_vals)
        
        mod_info['analysis_time'] = time.time() - start_time
        
        print(f"  ✅ {mod_info['mod_name']} v{mod_info['version']}")
        print(f"  📊 {mod_info['translatable_strings']} translatable strings")
        print(f"  📁 {len(locale_files)} locale files")
        print(f"  ⏱️ Analysis time: {mod_info['analysis_time']:.2f}s")
        
        return mod_info
        
    except Exception as e:
        mod_info['error'] = str(e)
        print(f"  ❌ Error: {e}")
        return mod_info

def translate_mod_content_large_scale(mod_info, translator, use_google=True):
    """Dịch nội dung mod với engine dịch miễn phí"""
    print(f"\n🌐 Translating {mod_info['mod_name']}...")
    
    if mod_info.get('error') or not mod_info['translation_data']:
        print("  ⚪ Skipping due to analysis error or no content")
        return None
    
    start_time = time.time()
    translation_results = {}
    total_translated = 0
    
    for locale_file, file_data in mod_info['translation_data'].items():
        print(f"  📄 Processing {os.path.basename(locale_file)}...")
        
        key_vals = file_data['key_vals']
        original_lines = file_data['original_lines']
        
        # Extract texts to translate
        texts_to_translate = [item['val'] for item in key_vals]
        
        if not texts_to_translate:
            continue
        
        # Batch translate
        try:
            translated_texts = translator.translate_batch(texts_to_translate, use_google)
            
            # Build translation pairs
            translation_pairs = []
            for i, item in enumerate(key_vals):
                translation_pairs.append({
                    'key': item['key'],
                    'original': item['val'],
                    'translated': translated_texts[i],
                    'line_index': item['index']
                })
            
            # Generate translated lines
            translated_lines = original_lines[:]
            for pair in translation_pairs:
                line_idx = pair['line_index']
                translated_lines[line_idx] = f"{pair['key']}={pair['translated']}\n"
            
            translation_results[os.path.basename(locale_file)] = {
                'original_lines': original_lines,
                'translated_lines': translated_lines,
                'translation_pairs': translation_pairs,
                'string_count': len(translation_pairs)
            }
            
            total_translated += len(translation_pairs)
            print(f"    ✅ {len(translation_pairs)} strings translated")
            
        except Exception as e:
            print(f"    ❌ Translation error: {e}")
            continue
    
    translation_time = time.time() - start_time
    
    print(f"  ✅ Total: {total_translated} strings translated in {translation_time:.2f}s")
    print(f"  ⚡ Speed: {total_translated/translation_time:.1f} strings/second")
    
    return {
        'mod_info': mod_info,
        'translation_results': translation_results,
        'total_strings': total_translated,
        'translation_time': translation_time,
        'translation_speed': total_translated / translation_time if translation_time > 0 else 0
    }

def create_test_environment_large():
    """Tạo môi trường test cho quy mô lớn"""
    base_dir = "large_scale_test"
    test_dirs = [
        f"{base_dir}/input_mods",
        f"{base_dir}/translation_results",
        f"{base_dir}/performance_data",
        f"{base_dir}/logs",
        f"{base_dir}/cache"
    ]
    
    for dir_path in test_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    return base_dir

def save_translation_results(test_dir, results_list):
    """Lưu kết quả dịch và thống kê hiệu năng"""
    results_dir = os.path.join(test_dir, "translation_results")
    performance_dir = os.path.join(test_dir, "performance_data")
    
    # Save individual translation results
    for i, result in enumerate(results_list):
        if result:
            mod_name = result['mod_info']['mod_name']
            
            # Save translation files
            mod_result_dir = os.path.join(results_dir, mod_name)
            os.makedirs(mod_result_dir, exist_ok=True)
            
            for filename, file_data in result['translation_results'].items():
                output_path = os.path.join(mod_result_dir, filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    for line in file_data['translated_lines']:
                        if not line.endswith('\n'):
                            f.write(line + '\n')
                        else:
                            f.write(line)
    
    # Save performance summary
    performance_summary = {
        'test_timestamp': datetime.now().isoformat(),
        'total_mods': len(results_list),
        'successful_mods': len([r for r in results_list if r]),
        'failed_mods': len([r for r in results_list if not r]),
        'total_strings': sum(r['total_strings'] for r in results_list if r),
        'total_translation_time': sum(r['translation_time'] for r in results_list if r),
        'average_speed': 0,
        'mod_details': []
    }
    
    # Calculate average speed
    successful_results = [r for r in results_list if r]
    if successful_results:
        performance_summary['average_speed'] = sum(r['translation_speed'] for r in successful_results) / len(successful_results)
    
    # Add mod details
    for result in results_list:
        if result:
            mod_detail = {
                'name': result['mod_info']['mod_name'],
                'size_mb': result['mod_info']['size_mb'],
                'strings': result['total_strings'],
                'time': result['translation_time'],
                'speed': result['translation_speed'],
                'files': len(result['translation_results'])
            }
            performance_summary['mod_details'].append(mod_detail)
    
    # Save performance data
    performance_file = os.path.join(performance_dir, f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(performance_file, 'w', encoding='utf-8') as f:
        json.dump(performance_summary, f, indent=2, ensure_ascii=False)
    
    return performance_summary

def print_performance_report(performance_summary):
    """In báo cáo hiệu năng chi tiết"""
    print(f"\n{'='*80}")
    print("📊 LARGE SCALE TRANSLATION PERFORMANCE REPORT")
    print(f"{'='*80}")
    
    print(f"\n📋 OVERVIEW:")
    print(f"  • Test Time: {performance_summary['test_timestamp']}")
    print(f"  • Total Mods: {performance_summary['total_mods']}")
    print(f"  • Successful: {performance_summary['successful_mods']}")
    print(f"  • Failed: {performance_summary['failed_mods']}")
    print(f"  • Success Rate: {performance_summary['successful_mods']/performance_summary['total_mods']*100:.1f}%")
    
    print(f"\n🎯 TRANSLATION METRICS:")
    print(f"  • Total Strings Translated: {performance_summary['total_strings']:,}")
    print(f"  • Total Translation Time: {performance_summary['total_translation_time']:.2f} seconds")
    print(f"  • Average Speed: {performance_summary['average_speed']:.1f} strings/second")
    print(f"  • Throughput: {performance_summary['total_strings']/performance_summary['total_translation_time']:.1f} strings/second overall")
    
    print(f"\n📈 MOD BREAKDOWN:")
    print(f"{'Mod Name':<30} {'Strings':>8} {'Time':>8} {'Speed':>10} {'Files':>6}")
    print("-" * 70)
    
    for mod in performance_summary['mod_details']:
        print(f"{mod['name']:<30} {mod['strings']:>8} {mod['time']:>8.2f} {mod['speed']:>10.1f} {mod['files']:>6}")
    
    # Performance categories
    high_perf = [m for m in performance_summary['mod_details'] if m['speed'] > 50]
    medium_perf = [m for m in performance_summary['mod_details'] if 10 <= m['speed'] <= 50]
    low_perf = [m for m in performance_summary['mod_details'] if m['speed'] < 10]
    
    print(f"\n⚡ PERFORMANCE CATEGORIES:")
    print(f"  • High Speed (>50 strings/s): {len(high_perf)} mods")
    print(f"  • Medium Speed (10-50 strings/s): {len(medium_perf)} mods")
    print(f"  • Low Speed (<10 strings/s): {len(low_perf)} mods")
    
    # Size vs Performance analysis
    small_mods = [m for m in performance_summary['mod_details'] if m['size_mb'] < 1.0]
    large_mods = [m for m in performance_summary['mod_details'] if m['size_mb'] >= 1.0]
    
    print(f"\n📦 SIZE VS PERFORMANCE:")
    if small_mods:
        avg_speed_small = sum(m['speed'] for m in small_mods) / len(small_mods)
        print(f"  • Small Mods (<1MB): {len(small_mods)} mods, avg speed {avg_speed_small:.1f} strings/s")
    if large_mods:
        avg_speed_large = sum(m['speed'] for m in large_mods) / len(large_mods)
        print(f"  • Large Mods (>=1MB): {len(large_mods)} mods, avg speed {avg_speed_large:.1f} strings/s")

def main():
    """Main function - Large Scale Translation Test"""
    print("🚀 LARGE SCALE TRANSLATION TEST")
    print("Testing with 10 different mods using FREE translation")
    print("=" * 80)
    
    # Setup
    test_env = create_test_environment_large()
    translator = FreeTranslationEngine()
    
    print(f"\n🔧 TRANSLATION ENGINE:")
    if GOOGLE_AVAILABLE:
        print("  ✅ Google Translate API available")
        print("  📝 Will use Google Translate + Advanced Mock fallback")
        use_google = True
    else:
        print("  ⚪ Google Translate not available")
        print("  📝 Will use Advanced Mock Translation only")
        use_google = False
    
    # Select mods
    print(f"\n📦 SELECTING TEST MODS...")
    test_mods = select_test_mods()
    
    if len(test_mods) < 5:
        print(f"⚠️ Only {len(test_mods)} mods available, need at least 5 for meaningful test")
        return
    
    # Analyze all mods
    print(f"\n🔍 ANALYZING {len(test_mods)} MODS...")
    mod_analyses = []
    total_analysis_time = 0
    
    for mod_path in test_mods:
        analysis = analyze_mod_for_translation(mod_path)
        mod_analyses.append(analysis)
        total_analysis_time += analysis.get('analysis_time', 0)
    
    print(f"\n📊 Analysis Complete: {total_analysis_time:.2f}s total")
    
    # Translation phase
    print(f"\n🌐 TRANSLATION PHASE...")
    print("=" * 50)
    
    translation_results = []
    start_translation_time = time.time()
    
    for analysis in mod_analyses:
        if not analysis.get('error') and analysis['translatable_strings'] > 0:
            result = translate_mod_content_large_scale(analysis, translator, use_google)
            translation_results.append(result)
        else:
            print(f"\n⚪ Skipping {analysis['name']} - no translatable content")
            translation_results.append(None)
    
    total_translation_time = time.time() - start_translation_time
    
    # Save results and generate report
    print(f"\n💾 SAVING RESULTS...")
    performance_summary = save_translation_results(test_env, translation_results)
    
    # Print comprehensive report
    print_performance_report(performance_summary)
    
    print(f"\n🎉 LARGE SCALE TEST COMPLETED!")
    print(f"📁 Results saved in: {test_env}")
    print(f"⏱️ Total test time: {total_translation_time:.2f} seconds")

if __name__ == "__main__":
    main()
