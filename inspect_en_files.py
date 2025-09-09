#!/usr/bin/env python3
"""
Kiểm tra nội dung thực tế các file locale/en
"""
import os
import zipfile
from improved_mod_finder import find_locale_files_improved
from mod_translate_core import read_cfg_file, parse_cfg_lines

def inspect_en_files():
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    
    # Kiểm tra một file cụ thể
    mod_path = os.path.join(mods_dir, "aai-industry_0.6.10.zip")
    
    if os.path.exists(mod_path):
        print(f"🔍 Inspecting: aai-industry_0.6.10.zip")
        
        root_folder, locale_files = find_locale_files_improved(mod_path)
        
        if locale_files:
            with zipfile.ZipFile(mod_path, 'r') as zipf:
                for locale_file in locale_files:
                    print(f"\n📄 File: {locale_file}")
                    
                    raw_text = read_cfg_file(zipf, locale_file)
                    key_vals, lines = parse_cfg_lines(raw_text)
                    
                    print(f"  • Total entries: {len(key_vals)}")
                    print(f"  • First 10 entries:")
                    
                    for i, item in enumerate(key_vals[:10]):
                        print(f"    {i+1}. {item['key']} = {item['val'][:50]}...")
                    
                    # Kiểm tra các section
                    sections = set()
                    current_section = "default"
                    for line in lines:
                        line = line.strip()
                        if line.startswith('[') and line.endswith(']'):
                            current_section = line[1:-1]
                            sections.add(current_section)
                    
                    print(f"  • Sections found: {list(sections)}")

if __name__ == "__main__":
    inspect_en_files()
