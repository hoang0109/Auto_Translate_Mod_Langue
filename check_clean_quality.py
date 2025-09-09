#!/usr/bin/env python3
"""
Kiểm tra chất lượng file clean translation
"""
from pathlib import Path
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import re

def check_clean_quality():
    clean_dir = Path("clean_output")
    
    if not clean_dir.exists():
        print("❌ clean_output directory không tồn tại!")
        return
    
    cfg_files = list(clean_dir.glob("*.cfg"))
    
    print("🔍 KIỂM TRA CHẤT LƯỢNG CLEAN TRANSLATION")
    print("=" * 50)
    
    for cfg_file in cfg_files:
        print(f"\n📄 Analyzing: {cfg_file.name}")
        
        try:
            with open(cfg_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = 0
            vietnamese_count = 0
            english_count = 0
            other_count = 0
            samples = []
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('['):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip()
                    
                    if len(value) < 2:
                        continue
                    
                    total_lines += 1
                    
                    try:
                        detected_lang = detect(value)
                        if detected_lang == 'vi':
                            vietnamese_count += 1
                        elif detected_lang == 'en':
                            english_count += 1
                        else:
                            other_count += 1
                            
                        # Lưu mẫu
                        if len(samples) < 10:
                            samples.append({
                                'line': line_num,
                                'key': key.strip(),
                                'value': value,
                                'lang': detected_lang
                            })
                            
                    except LangDetectException:
                        other_count += 1
            
            # Tính tỷ lệ
            vi_ratio = vietnamese_count / max(total_lines, 1)
            en_ratio = english_count / max(total_lines, 1)
            other_ratio = other_count / max(total_lines, 1)
            
            print(f"  📊 Thống kê ngôn ngữ:")
            print(f"    🇻🇳 Vietnamese: {vietnamese_count}/{total_lines} ({vi_ratio:.1%})")
            print(f"    🇺🇸 English: {english_count}/{total_lines} ({en_ratio:.1%})")
            print(f"    ❓ Other: {other_count}/{total_lines} ({other_ratio:.1%})")
            
            # Đánh giá chất lượng
            if vi_ratio >= 0.8:
                quality = "🟢 EXCELLENT"
            elif vi_ratio >= 0.6:
                quality = "🟡 GOOD"
            elif vi_ratio >= 0.4:
                quality = "🟠 FAIR"
            else:
                quality = "🔴 POOR"
            
            print(f"  🎯 Chất lượng dịch: {quality}")
            
            # Hiển thị mẫu
            print(f"  📋 Mẫu dịch:")
            for sample in samples[:5]:
                flag = "🇻🇳" if sample['lang'] == 'vi' else "🇺🇸" if sample['lang'] == 'en' else "❓"
                print(f"    {flag} {sample['key']} = {sample['value'][:60]}...")
                
        except Exception as e:
            print(f"  ❌ Error analyzing {cfg_file.name}: {e}")

if __name__ == "__main__":
    check_clean_quality()
