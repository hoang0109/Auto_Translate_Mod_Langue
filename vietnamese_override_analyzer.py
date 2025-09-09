#!/usr/bin/env python3
"""
Vietnamese Override Analyzer
Phân tích và ghi đè mod đã có sẵn bản dịch tiếng Việt với chất lượng cải tiến
"""
import os
import sys
import zipfile
import json
from datetime import datetime
from pathlib import Path
import difflib
from collections import defaultdict

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mod_translate_core import find_locale_files, parse_cfg_lines, read_cfg_file

class VietnameseQualityAnalyzer:
    """Phân tích chất lượng bản dịch tiếng Việt hiện có"""
    
    def __init__(self):
        self.quality_patterns = {
            # Patterns cho bản dịch chất lượng cao
            'high_quality': [
                'tốc độ', 'băng tải', 'khai thác', 'tỷ lệ', 'máy móc',
                'công thức', 'công nghệ', 'nghiên cứu', 'vật phẩm', 'chất lỏng',
                'kho đồ', 'cài đặt', 'mặc định', 'năng lượng', 'tiêu thụ'
            ],
            
            # Patterns cho bản dịch kém chất lượng
            'low_quality': [
                '[VI]', '(VI)', 'Google Translate', 'auto translate',
                'dịch tự động', 'chưa dịch', 'not translated'
            ],
            
            # Patterns cho bản dịch machine translation thô
            'machine_translation': [
                'máy tính dịch', 'bản dịch máy', 'tự động dịch',
                'google dịch', 'deepl translate'
            ],
            
            # Common English words left untranslated
            'untranslated_english': [
                'speed', 'belt', 'machine', 'item', 'recipe', 'technology',
                'research', 'entity', 'fluid', 'inventory', 'setting'
            ]
        }
    
    def analyze_vietnamese_quality(self, vietnamese_text):
        """Phân tích chất lượng bản dịch tiếng Việt"""
        if not vietnamese_text:
            return {
                'score': 0,
                'quality': 'missing',
                'issues': ['No Vietnamese text provided'],
                'suggestions': []
            }
        
        text_lower = vietnamese_text.lower()
        score = 50  # Base score
        issues = []
        suggestions = []
        
        # Check for high quality patterns
        high_quality_count = sum(1 for pattern in self.quality_patterns['high_quality'] 
                                if pattern in text_lower)
        if high_quality_count > 0:
            score += high_quality_count * 5
        
        # Penalize low quality patterns
        low_quality_count = sum(1 for pattern in self.quality_patterns['low_quality'] 
                               if pattern in text_lower)
        if low_quality_count > 0:
            score -= low_quality_count * 20
            issues.append(f"Contains {low_quality_count} low-quality translation markers")
        
        # Check for machine translation patterns
        machine_count = sum(1 for pattern in self.quality_patterns['machine_translation'] 
                           if pattern in text_lower)
        if machine_count > 0:
            score -= machine_count * 15
            issues.append("Shows signs of raw machine translation")
        
        # Check for untranslated English
        english_count = sum(1 for pattern in self.quality_patterns['untranslated_english'] 
                           if pattern in text_lower)
        if english_count > 0:
            score -= english_count * 10
            issues.append(f"Contains {english_count} untranslated English terms")
            suggestions.append("Translate remaining English terms to Vietnamese")
        
        # Check length (very short translations might be incomplete)
        if len(vietnamese_text.strip()) < 5:
            score -= 30
            issues.append("Translation too short, possibly incomplete")
        
        # Check for Vietnamese diacritics (proper Vietnamese should have them)
        vietnamese_chars = 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'
        has_diacritics = any(char in vietnamese_text for char in vietnamese_chars)
        if not has_diacritics and len(vietnamese_text) > 10:
            score -= 20
            issues.append("Missing Vietnamese diacritics, might be simplified or poor quality")
            suggestions.append("Add proper Vietnamese diacritics")
        
        # Determine quality level
        if score >= 80:
            quality = 'excellent'
        elif score >= 65:
            quality = 'good'
        elif score >= 50:
            quality = 'fair'
        elif score >= 30:
            quality = 'poor'
        else:
            quality = 'very_poor'
        
        return {
            'score': max(0, min(100, score)),
            'quality': quality,
            'issues': issues,
            'suggestions': suggestions,
            'has_diacritics': has_diacritics,
            'high_quality_terms': high_quality_count,
            'problematic_patterns': low_quality_count + machine_count + english_count
        }

class VietnameseOverrideManager:
    """Quản lý việc ghi đè bản dịch tiếng Việt"""
    
    def __init__(self):
        self.quality_analyzer = VietnameseQualityAnalyzer()
        self.advanced_dictionary = {
            # Game mechanics
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
            "electric": "điện",
            "pole": "cột điện",
            "range": "phạm vi",
            "machine": "máy móc",
            "mining": "khai thác",
            "drone": "máy bay không người lái",
            "calculator": "máy tính",
            "rate": "tỷ lệ",
            "hero": "anh hùng",
            "turret": "tháp pháo",
            "redux": "cải tiến",
            "shield": "khiên",
            "loader": "máy tải",
            "vanilla": "cơ bản",
            "construction": "xây dựng",
            "robot": "robot",
            "copper": "đồng",
            "magazine": "băng đạn",
            "adjustable": "có thể điều chỉnh",
            "instant": "tức thời",
            "plus": "nâng cao",
            "water": "nước",
            "pumpjack": "máy bơm dầu",
            "slot": "ô",
            "starter": "khởi đầu",
            "buff": "tăng cường",
            "updated": "cập nhật",
            "utils": "tiện ích",
            "spoilable": "có thể hỏng",
            "blueprint": "bản thiết kế",
            "book": "sách",
            "infinite": "vô hạn",
            "battery": "pin",
            "powered": "được cung cấp năng lượng",
            "delta": "delta",
            "burner": "đốt nhiên liệu",
            
            # Interface terms
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
            "label": "nhãn",
            "production": "sản xuất",
            "consumption": "tiêu thụ",
            "power": "năng lượng",
            "pollution": "ô nhiễm",
            "heat": "nhiệt",
            
            # Actions and states
            "increase": "tăng",
            "decrease": "giảm",
            "bonus": "thưởng",
            "distance": "khoảng cách",
            "pickup": "nhặt",
            "drop": "thả",
            "build": "xây dựng",
            "reach": "với tới",
            "loot": "chiến lợi phẩm",
            "resource": "tài nguyên",
            "stack": "chồng",
            "factor": "hệ số",
            "offset": "độ lệch",
            "amount": "số lượng",
            "running": "chạy",
            
            # Quality descriptors
            "maximum": "tối đa",
            "minimum": "tối thiểu",
            "average": "trung bình",
            "total": "tổng",
            "current": "hiện tại",
            "selected": "đã chọn",
            "available": "có sẵn",
            "required": "cần thiết",
            "optional": "tùy chọn"
        }
    
    def create_improved_translation(self, english_text, existing_vietnamese=None):
        """Tạo bản dịch cải tiến dựa trên từ điển advanced"""
        if not english_text:
            return existing_vietnamese or ""
        
        # Start with original English
        improved = english_text.lower()
        
        # Apply dictionary replacements (longer phrases first)
        sorted_terms = sorted(self.advanced_dictionary.items(), key=lambda x: len(x[0]), reverse=True)
        for en_term, vi_term in sorted_terms:
            improved = improved.replace(en_term, vi_term)
        
        # Handle common patterns
        improved = improved.replace("how many", "bao nhiêu")
        improved = improved.replace(" per ", " mỗi ")
        improved = improved.replace("translate (", "dịch (")
        
        # Preserve original capitalization
        if english_text and english_text[0].isupper():
            improved = improved.capitalize()
        
        # If no significant changes and no existing Vietnamese, add [VI] prefix
        if (improved.lower() == english_text.lower() and 
            (not existing_vietnamese or len(existing_vietnamese.strip()) < 3)):
            improved = f"[VI] {english_text}"
        
        return improved
    
    def analyze_mod_vietnamese_status(self, mod_path):
        """Phân tích trạng thái tiếng Việt của mod"""
        print(f"\n🔍 Analyzing Vietnamese status: {os.path.basename(mod_path)}")
        
        analysis = {
            'mod_path': mod_path,
            'mod_name': os.path.basename(mod_path),
            'has_vietnamese': False,
            'vietnamese_files': [],
            'english_files': [],
            'quality_analysis': {},
            'comparison_data': {},
            'recommendation': 'unknown',
            'improvement_potential': 0,
            'error': None
        }
        
        try:
            with zipfile.ZipFile(mod_path, 'r') as zipf:
                all_files = zipf.namelist()
                
                # Find Vietnamese files
                vi_files = [f for f in all_files if f.endswith('.cfg') and '/vi/' in f.lower()]
                analysis['vietnamese_files'] = vi_files
                analysis['has_vietnamese'] = len(vi_files) > 0
                
                # Find English files
                en_files = [f for f in all_files if f.endswith('.cfg') and '/en/' in f.lower()]
                analysis['english_files'] = en_files
                
                print(f"  🇻🇳 Vietnamese files: {len(vi_files)}")
                print(f"  🇺🇸 English files: {len(en_files)}")
                
                if not analysis['has_vietnamese']:
                    analysis['recommendation'] = 'create_new'
                    analysis['improvement_potential'] = 100
                    print(f"  💡 Recommendation: Create new Vietnamese translation")
                    return analysis
                
                # Analyze existing Vietnamese quality
                for vi_file in vi_files:
                    print(f"    📄 Analyzing: {vi_file}")
                    
                    # Read Vietnamese content
                    vi_content = read_cfg_file(zipf, vi_file)
                    vi_key_vals, vi_lines = parse_cfg_lines(vi_content)
                    
                    # Find corresponding English file
                    en_file = vi_file.replace('/vi/', '/en/')
                    if en_file in en_files:
                        en_content = read_cfg_file(zipf, en_file)
                        en_key_vals, en_lines = parse_cfg_lines(en_content)
                        
                        # Compare translations
                        comparison = self.compare_translations(en_key_vals, vi_key_vals)
                        analysis['comparison_data'][vi_file] = comparison
                        
                        # Analyze Vietnamese quality
                        quality_scores = []
                        detailed_analysis = {}
                        
                        for vi_item in vi_key_vals:
                            key = vi_item['key']
                            vi_text = vi_item['val']
                            
                            # Find corresponding English
                            en_text = None
                            for en_item in en_key_vals:
                                if en_item['key'] == key:
                                    en_text = en_item['val']
                                    break
                            
                            if en_text:
                                quality = self.quality_analyzer.analyze_vietnamese_quality(vi_text)
                                quality_scores.append(quality['score'])
                                
                                # Store detailed analysis for problematic entries
                                if quality['score'] < 60:
                                    detailed_analysis[key] = {
                                        'english': en_text,
                                        'vietnamese': vi_text,
                                        'quality': quality,
                                        'improved_suggestion': self.create_improved_translation(en_text, vi_text)
                                    }
                        
                        if quality_scores:
                            avg_quality = sum(quality_scores) / len(quality_scores)
                            analysis['quality_analysis'][vi_file] = {
                                'average_score': avg_quality,
                                'total_entries': len(quality_scores),
                                'low_quality_count': len([s for s in quality_scores if s < 60]),
                                'detailed_issues': detailed_analysis
                            }
                            
                            print(f"      📊 Average quality score: {avg_quality:.1f}/100")
                            print(f"      ⚠️ Low quality entries: {len(detailed_analysis)}")
                
                # Generate overall recommendation
                analysis['recommendation'], analysis['improvement_potential'] = self.generate_recommendation(analysis)
                
        except Exception as e:
            analysis['error'] = str(e)
            print(f"  ❌ Error: {e}")
        
        return analysis
    
    def compare_translations(self, en_key_vals, vi_key_vals):
        """So sánh bản dịch tiếng Anh và tiếng Việt"""
        en_dict = {item['key']: item['val'] for item in en_key_vals}
        vi_dict = {item['key']: item['val'] for item in vi_key_vals}
        
        comparison = {
            'total_english': len(en_dict),
            'total_vietnamese': len(vi_dict),
            'translated_count': 0,
            'untranslated_keys': [],
            'identical_translations': [],  # Same as English
            'quality_issues': []
        }
        
        for key, en_text in en_dict.items():
            if key in vi_dict:
                vi_text = vi_dict[key]
                comparison['translated_count'] += 1
                
                # Check if translation is identical to English (likely untranslated)
                if en_text.lower().strip() == vi_text.lower().strip():
                    comparison['identical_translations'].append(key)
                
                # Check for quality issues
                quality = self.quality_analyzer.analyze_vietnamese_quality(vi_text)
                if quality['score'] < 50:
                    comparison['quality_issues'].append({
                        'key': key,
                        'english': en_text,
                        'vietnamese': vi_text,
                        'quality': quality
                    })
            else:
                comparison['untranslated_keys'].append(key)
        
        return comparison
    
    def generate_recommendation(self, analysis):
        """Tạo khuyến nghị dựa trên phân tích"""
        if not analysis['has_vietnamese']:
            return 'create_new', 100
        
        # Calculate overall quality score
        quality_scores = []
        total_low_quality = 0
        total_entries = 0
        
        for file_analysis in analysis['quality_analysis'].values():
            quality_scores.append(file_analysis['average_score'])
            total_low_quality += file_analysis['low_quality_count']
            total_entries += file_analysis['total_entries']
        
        if not quality_scores:
            return 'analyze_manually', 50
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        low_quality_percentage = (total_low_quality / total_entries * 100) if total_entries > 0 else 0
        
        # Determine recommendation
        if avg_quality >= 80 and low_quality_percentage < 10:
            return 'keep_existing', max(0, 100 - avg_quality)
        elif avg_quality >= 60 and low_quality_percentage < 30:
            return 'selective_update', min(40, low_quality_percentage)
        else:
            return 'full_override', min(90, 100 - avg_quality)
    
    def create_override_package(self, analysis, output_dir):
        """Tạo gói override cho mod"""
        if analysis['recommendation'] == 'keep_existing':
            print(f"  ✅ Keeping existing high-quality Vietnamese translation")
            return None
        
        mod_name = analysis['mod_name'].replace('.zip', '')
        override_dir = os.path.join(output_dir, f"{mod_name}_vietnamese_override")
        os.makedirs(override_dir, exist_ok=True)
        
        # Create improved translations
        improved_files = {}
        
        with zipfile.ZipFile(analysis['mod_path'], 'r') as zipf:
            for en_file in analysis['english_files']:
                en_content = read_cfg_file(zipf, en_file)
                en_key_vals, en_lines = parse_cfg_lines(en_content)
                
                # Create improved Vietnamese version
                improved_lines = []
                for line in en_lines:
                    if '=' in line and not line.strip().startswith('#'):
                        # This is a translatable line
                        key = line.split('=', 1)[0].strip()
                        
                        # Find the English value
                        for en_item in en_key_vals:
                            if en_item['key'] == key:
                                en_value = en_item['val']
                                
                                # Check if we have existing Vietnamese for comparison
                                existing_vi = None
                                vi_file = en_file.replace('/en/', '/vi/')
                                if vi_file in analysis['vietnamese_files']:
                                    vi_content = read_cfg_file(zipf, vi_file)
                                    vi_key_vals, _ = parse_cfg_lines(vi_content)
                                    for vi_item in vi_key_vals:
                                        if vi_item['key'] == key:
                                            existing_vi = vi_item['val']
                                            break
                                
                                # Create improved translation
                                improved_value = self.create_improved_translation(en_value, existing_vi)
                                improved_lines.append(f"{key}={improved_value}\n")
                                break
                        else:
                            # Key not found, keep original line
                            improved_lines.append(line)
                    else:
                        # Comment or section header
                        improved_lines.append(line)
                
                # Save improved file
                vi_filename = os.path.basename(en_file)
                vi_file_path = os.path.join(override_dir, vi_filename)
                
                with open(vi_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(improved_lines)
                
                improved_files[vi_filename] = len([line for line in improved_lines if '=' in line and not line.strip().startswith('#')])
        
        # Create analysis report
        report = {
            'mod_name': mod_name,
            'analysis_date': datetime.now().isoformat(),
            'recommendation': analysis['recommendation'],
            'improvement_potential': analysis['improvement_potential'],
            'quality_analysis': analysis['quality_analysis'],
            'improved_files': improved_files,
            'summary': {
                'total_files': len(improved_files),
                'total_improved_entries': sum(improved_files.values())
            }
        }
        
        report_path = os.path.join(override_dir, 'analysis_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"  🎯 Override package created: {override_dir}")
        print(f"     📁 Files: {len(improved_files)}")
        print(f"     📝 Improved entries: {sum(improved_files.values())}")
        
        return override_dir

def test_vietnamese_override_system():
    """Test hệ thống override với các mod có sẵn tiếng Việt"""
    print("🇻🇳 VIETNAMESE OVERRIDE ANALYZER")
    print("=" * 70)
    
    # Find mods with existing Vietnamese translations
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    vietnamese_mods = []
    
    if os.path.exists(mods_dir):
        all_mods = [f for f in os.listdir(mods_dir) if f.endswith('.zip')]
        
        print(f"🔍 Scanning {len(all_mods)} mods for Vietnamese translations...")
        
        for mod_file in all_mods:
            mod_path = os.path.join(mods_dir, mod_file)
            try:
                with zipfile.ZipFile(mod_path, 'r') as zipf:
                    vi_files = [f for f in zipf.namelist() if f.endswith('.cfg') and '/vi/' in f.lower()]
                    if vi_files:
                        vietnamese_mods.append(mod_path)
                        print(f"  ✅ {mod_file}: {len(vi_files)} Vietnamese files")
            except:
                continue
    
    print(f"\n📊 Found {len(vietnamese_mods)} mods with Vietnamese translations")
    
    if not vietnamese_mods:
        print("❌ No mods with Vietnamese translations found!")
        return
    
    # Analyze top mods
    manager = VietnameseOverrideManager()
    output_dir = "vietnamese_override_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    for mod_path in vietnamese_mods[:5]:  # Analyze first 5 mods
        analysis = manager.analyze_mod_vietnamese_status(mod_path)
        results.append(analysis)
        
        if analysis['recommendation'] != 'keep_existing':
            override_dir = manager.create_override_package(analysis, output_dir)
    
    # Generate summary report
    generate_override_summary(results, output_dir)

def generate_override_summary(results, output_dir):
    """Tạo báo cáo tổng kết"""
    print("\n" + "=" * 70)
    print("📋 VIETNAMESE OVERRIDE SUMMARY")
    print("=" * 70)
    
    recommendations = defaultdict(int)
    total_improvement_potential = 0
    
    for result in results:
        recommendations[result['recommendation']] += 1
        total_improvement_potential += result['improvement_potential']
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"  • Total mods analyzed: {len(results)}")
    print(f"  • Average improvement potential: {total_improvement_potential/len(results):.1f}%")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    for recommendation, count in recommendations.items():
        print(f"  • {recommendation.replace('_', ' ').title()}: {count} mods")
    
    print(f"\n📁 Output directory: {output_dir}")
    
    # Save detailed report
    summary_report = {
        'analysis_date': datetime.now().isoformat(),
        'total_mods': len(results),
        'recommendations': dict(recommendations),
        'average_improvement_potential': total_improvement_potential / len(results),
        'detailed_results': results
    }
    
    summary_path = os.path.join(output_dir, 'override_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Summary report saved: {summary_path}")

def main():
    """Main function"""
    try:
        test_vietnamese_override_system()
        
        print("\n" + "=" * 70)
        print("🎉 VIETNAMESE OVERRIDE ANALYSIS COMPLETED!")
        print("\n💡 Next steps:")
        print("1. Review analysis reports in vietnamese_override_analysis/")
        print("2. Apply selective updates to mods with poor quality translations")
        print("3. Create full overrides for mods with very poor translations")
        print("4. Keep existing translations for high-quality mods")
        
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
