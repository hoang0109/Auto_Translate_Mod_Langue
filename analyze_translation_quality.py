#!/usr/bin/env python3
"""
Phân tích chi tiết chất lượng dịch trong output
"""
import os
import zipfile
from pathlib import Path
import re
from collections import defaultdict
import langdetect
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

class TranslationQualityAnalyzer:
    def __init__(self):
        self.language_stats = defaultdict(int)
        self.translation_issues = []
        self.duplicated_content = defaultdict(list)
        
    def detect_language(self, text):
        """Phát hiện ngôn ngữ của text"""
        try:
            if len(text.strip()) < 10:
                return "unknown"
            # Chỉ lấy phần value sau dấu =
            if '=' in text:
                value = text.split('=', 1)[1].strip()
                if len(value) < 5:
                    return "short"
                return detect(value)
            return detect(text)
        except (LangDetectException, Exception):
            return "unknown"
    
    def analyze_cfg_content(self, content, filename):
        """Phân tích nội dung file .cfg"""
        lines = content.split('\n')
        results = {
            'total_lines': len(lines),
            'translation_lines': 0,
            'languages': defaultdict(int),
            'issues': [],
            'samples': []
        }
        
        translation_lines = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('['):
                continue
                
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if len(value) > 0:
                    results['translation_lines'] += 1
                    translation_lines.append((line_num, key, value))
                    
                    # Phát hiện ngôn ngữ
                    lang = self.detect_language(value)
                    results['languages'][lang] += 1
                    
                    # Kiểm tra các vấn đề
                    issues = self.check_translation_issues(key, value, line_num)
                    results['issues'].extend(issues)
                    
                    # Lưu mẫu
                    if len(results['samples']) < 10:
                        results['samples'].append({
                            'line': line_num,
                            'key': key,
                            'value': value,
                            'language': lang
                        })
        
        return results
    
    def check_translation_issues(self, key, value, line_num):
        """Kiểm tra các vấn đề trong dịch"""
        issues = []
        
        # 1. Kiểm tra mixed languages (tiếng Việt lẫn tiếng khác)
        if self.has_mixed_languages(value):
            issues.append({
                'type': 'mixed_language',
                'line': line_num,
                'key': key,
                'value': value,
                'description': 'Mixed languages in translation'
            })
        
        # 2. Kiểm tra không dịch (vẫn là tiếng Anh)
        try:
            detected_lang = detect(value)
            if detected_lang == 'en' and len(value) > 10:
                issues.append({
                    'type': 'not_translated',
                    'line': line_num,
                    'key': key,
                    'value': value,
                    'description': 'Still in English'
                })
        except:
            pass
        
        # 3. Kiểm tra dịch sai (có ký tự lạ)
        if self.has_weird_characters(value):
            issues.append({
                'type': 'weird_characters',
                'line': line_num,
                'key': key,
                'value': value,
                'description': 'Contains unusual characters'
            })
        
        return issues
    
    def has_mixed_languages(self, text):
        """Kiểm tra text có trộn lẫn ngôn ngữ không"""
        # Kiểm tra có ký tự Việt Nam và Latin cùng lúc
        has_vietnamese = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]', text))
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        
        if has_vietnamese and has_latin:
            # Nếu có cả tiếng Việt và Latin, kiểm tra xem có phải mixed không
            vietnamese_words = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]\w*', text))
            total_words = len(text.split())
            return vietnamese_words < total_words * 0.7  # Nếu ít hơn 70% từ Việt
        
        return False
    
    def has_weird_characters(self, text):
        """Kiểm tra ký tự lạ"""
        # Kiểm tra ký tự không phải tiếng Việt, Anh, số, hoặc ký tự đặc biệt thông thường
        weird_chars = re.findall(r'[^\w\s\-\.\,\!\?\(\)\[\]àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐa-zA-Z0-9]', text)
        return len(weird_chars) > 0
    
    def analyze_output_directory(self, output_dir="output"):
        """Phân tích toàn bộ output directory"""
        output_path = Path(output_dir)
        if not output_path.exists():
            print(f"❌ Directory {output_dir} không tồn tại!")
            return
        
        zip_files = list(output_path.glob("*.zip"))
        if not zip_files:
            print(f"❌ Không có file zip nào trong {output_dir}!")
            return
        
        print(f"🔍 PHÂN TÍCH CHẤT LƯỢNG DỊCH")
        print("=" * 60)
        
        all_results = {}
        total_files = 0
        total_issues = 0
        language_summary = defaultdict(int)
        
        for zip_file in zip_files:
            print(f"\n📦 Analyzing: {zip_file.name}")
            
            try:
                with zipfile.ZipFile(zip_file, 'r') as zipf:
                    cfg_files = [f for f in zipf.namelist() if f.endswith('.cfg')]
                    print(f"  📄 Found {len(cfg_files)} .cfg files")
                    
                    file_results = {}
                    
                    for cfg_file in cfg_files:
                        try:
                            content = zipf.read(cfg_file).decode('utf-8')
                            result = self.analyze_cfg_content(content, cfg_file)
                            file_results[cfg_file] = result
                            total_files += 1
                            total_issues += len(result['issues'])
                            
                            # Cập nhật thống kê ngôn ngữ
                            for lang, count in result['languages'].items():
                                language_summary[lang] += count
                            
                        except Exception as e:
                            print(f"    ❌ Error reading {cfg_file}: {e}")
                    
                    all_results[zip_file.name] = file_results
                    
            except Exception as e:
                print(f"  ❌ Error processing zip: {e}")
        
        # Báo cáo tổng kết
        self.generate_summary_report(all_results, total_files, total_issues, language_summary)
        
        # Báo cáo chi tiết các vấn đề
        self.generate_detailed_issues_report(all_results)
        
        return all_results
    
    def generate_summary_report(self, all_results, total_files, total_issues, language_summary):
        """Tạo báo cáo tổng kết"""
        print(f"\n📊 BÁOM CÁO TỔNG KẾT")
        print("=" * 40)
        print(f"• Tổng số .cfg files: {total_files}")
        print(f"• Tổng số vấn đề: {total_issues}")
        
        print(f"\n🌍 Thống kê ngôn ngữ phát hiện:")
        for lang, count in sorted(language_summary.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / sum(language_summary.values())) * 100
            flag = self.get_language_flag(lang)
            print(f"  {flag} {lang}: {count} ({percentage:.1f}%)")
    
    def get_language_flag(self, lang):
        """Lấy flag cho ngôn ngữ"""
        flags = {
            'vi': '🇻🇳',
            'en': '🇺🇸', 
            'cs': '🇨🇿',
            'de': '🇩🇪',
            'fr': '🇫🇷',
            'unknown': '❓',
            'short': '📏'
        }
        return flags.get(lang, '❓')
    
    def generate_detailed_issues_report(self, all_results):
        """Tạo báo cáo chi tiết các vấn đề"""
        print(f"\n⚠️ CHI TIẾT CÁC VẤN ĐỀ")
        print("=" * 40)
        
        issue_types = defaultdict(list)
        
        for zip_name, file_results in all_results.items():
            for cfg_file, result in file_results.items():
                for issue in result['issues']:
                    issue['zip'] = zip_name
                    issue['file'] = cfg_file
                    issue_types[issue['type']].append(issue)
        
        for issue_type, issues in issue_types.items():
            print(f"\n🚨 {issue_type.upper()}: {len(issues)} cases")
            
            # Hiển thị một số ví dụ
            for i, issue in enumerate(issues[:5]):
                print(f"  {i+1}. {issue['file']}:{issue['line']}")
                print(f"     Key: {issue['key']}")
                print(f"     Value: {issue['value'][:100]}...")
                print(f"     Issue: {issue['description']}")
                print()
            
            if len(issues) > 5:
                print(f"     ... và {len(issues) - 5} cases khác")

def main():
    analyzer = TranslationQualityAnalyzer()
    analyzer.analyze_output_directory()

if __name__ == "__main__":
    main()
