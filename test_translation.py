#!/usr/bin/env python3
"""
Test translation workflow programmatically
"""
import os
import sys
from pathlib import Path
import zipfile

# Add current directory to path để import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mod_translate_core import translate_texts, process_mod, find_locale_files, parse_cfg_lines, read_cfg_file

def test_basic_translation():
    """Test basic translation functionality"""
    print("🧪 Testing Basic Translation Functionality")
    print("=" * 50)
    
    # Test 1: Check if test mod has locale files
    print("1. Checking test-mod.zip structure...")
    root_folder, locale_files = find_locale_files("test-mod.zip")
    print(f"   Root folder: {root_folder}")
    print(f"   Locale files: {locale_files}")
    
    if not locale_files:
        print("❌ ERROR: No locale files found in test-mod.zip")
        return False
    
    # Test 2: Parse locale files
    print("\n2. Parsing locale content...")
    with zipfile.ZipFile("test-mod.zip", 'r') as zipf:
        all_texts = []
        for locale_file in locale_files:
            raw_content = read_cfg_file(zipf, locale_file)
            key_vals, lines = parse_cfg_lines(raw_content)
            texts = [item['val'] for item in key_vals]
            all_texts.extend(texts)
            print(f"   {locale_file}: {len(key_vals)} translatable strings")
    
    print(f"   Total texts to translate: {len(all_texts)}")
    print(f"   Sample texts: {all_texts[:3]}")
    
    return True

def test_with_mock_api():
    """Test translation with mock API (no real API call)"""
    print("\n🔧 Testing Translation Logic (Mock API)")
    print("=" * 50)
    
    # Mock translation function
    def mock_translate_texts(texts, api_key, target_lang, glossary_id=None, endpoint=None):
        """Mock translation - just add [VI] prefix"""
        return [f"[VI] {text}" for text in texts]
    
    # Test với mock translation
    sample_texts = ["Test Entity", "Sample Machine", "Example Turret"]
    mock_results = mock_translate_texts(sample_texts, "fake-key", "VI")
    
    print(f"Input texts: {sample_texts}")
    print(f"Mock translated: {mock_results}")
    
    # Test reconstruction logic
    print("\n3. Testing file reconstruction...")
    with zipfile.ZipFile("test-mod.zip", 'r') as zipf:
        locale_file = "test-translation-mod/locale/en/test.cfg"
        raw_content = read_cfg_file(zipf, locale_file)
        key_vals, lines = parse_cfg_lines(raw_content)
        
        print(f"   Original lines: {len(lines)}")
        print(f"   Key-value pairs: {len(key_vals)}")
        
        # Reconstruct with mock translations
        translated_lines = lines[:]
        mock_translations = [f"[VI] {item['val']}" for item in key_vals]
        
        for i, item in enumerate(key_vals):
            translated_lines[item['index']] = f"{item['key']}={mock_translations[i]}\n"
        
        print(f"   Reconstructed lines: {len(translated_lines)}")
        print("   Sample output:")
        for i, line in enumerate(translated_lines[:10]):
            print(f"     Line {i+1}: {line.strip()}")

def test_template_loading():
    """Test template loading functionality"""
    print("\n📋 Testing Template Loading")
    print("=" * 50)
    
    # Check available templates
    code_mau_dir = Path("Code mau")
    if not code_mau_dir.exists():
        print("❌ ERROR: Code mau directory not found")
        return False
    
    zip_files = list(code_mau_dir.glob("*.zip"))
    print(f"Available templates: {len(zip_files)}")
    
    for zip_file in zip_files:
        print(f"  - {zip_file.name}")
        
        # Try to extract info
        try:
            with zipfile.ZipFile(zip_file, 'r') as zipf:
                info_files = [name for name in zipf.namelist() if name.endswith('info.json')]
                if info_files:
                    import json
                    with zipf.open(info_files[0]) as f:
                        info_data = json.load(f)
                        print(f"    Name: {info_data.get('name', 'Unknown')}")
                        print(f"    Version: {info_data.get('version', 'Unknown')}")
                        print(f"    Dependencies: {len(info_data.get('dependencies', []))}")
        except Exception as e:
            print(f"    Error reading: {e}")
    
    return True

def test_full_workflow_simulation():
    """Test full workflow simulation without real API"""
    print("\n🎯 Testing Full Workflow Simulation")
    print("=" * 50)
    
    # Step 1: Load template info (simulate)
    template_info = {
        'name': 'Auto_Translate_Mod_Langue_Vietnamese',
        'version': '1.0.1',
        'title': 'Test Template',
        'author': 'Test',
        'dependencies': ['? base'],
        'zip_path': 'Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.1.zip'
    }
    print(f"1. Template loaded: {template_info['name']} v{template_info['version']}")
    
    # Step 2: Analyze mod to translate
    root_folder, locale_files = find_locale_files("test-mod.zip")
    print(f"2. Mod to translate: {root_folder}, {len(locale_files)} locale files")
    
    # Step 3: Extract texts
    with zipfile.ZipFile("test-mod.zip", 'r') as zipf:
        all_texts = []
        for locale_file in locale_files:
            raw_content = read_cfg_file(zipf, locale_file)
            key_vals, lines = parse_cfg_lines(raw_content)
            all_texts.extend([item['val'] for item in key_vals])
    
    print(f"3. Extracted {len(all_texts)} texts to translate")
    
    # Step 4: Simulate translation
    translated_texts = [f"[VI] {text}" for text in all_texts]
    print(f"4. Simulated translation: {len(translated_texts)} results")
    
    # Step 5: Create output cfg content
    with zipfile.ZipFile("test-mod.zip", 'r') as zipf:
        locale_file = locale_files[0]
        raw_content = read_cfg_file(zipf, locale_file)
        key_vals, lines = parse_cfg_lines(raw_content)
        
        # Reconstruct
        translated_lines = lines[:]
        trans_iter = iter(translated_texts)
        
        for item in key_vals:
            try:
                translated_val = next(trans_iter)
                translated_lines[item['index']] = f"{item['key']}={translated_val}\n"
            except StopIteration:
                break
    
    print(f"5. Created translated content: {len(translated_lines)} lines")
    
    # Step 6: Save to temp file to verify
    temp_output = Path("temp_test_output.cfg")
    with open(temp_output, 'w', encoding='utf-8') as f:
        f.writelines(translated_lines)
    
    print(f"6. Saved test output to: {temp_output}")
    print("   Sample translated content:")
    with open(temp_output, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:8]):
            if '=' in line and not line.strip().startswith(';'):
                print(f"     {line.strip()}")
    
    # Cleanup
    if temp_output.exists():
        temp_output.unlink()
    
    return True

def main():
    """Run all tests"""
    print("🎮 Factorio Mod Translator - Translation Test")
    print("=" * 60)
    
    # Test 1: Basic functionality
    if not test_basic_translation():
        print("❌ Basic translation test failed")
        return
    
    # Test 2: Mock translation
    test_with_mock_api()
    
    # Test 3: Template loading
    if not test_template_loading():
        print("❌ Template loading test failed")
        return
    
    # Test 4: Full workflow simulation
    if not test_full_workflow_simulation():
        print("❌ Full workflow test failed")
        return
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("\n🎯 Next Steps:")
    print("1. Get a valid DeepL API key")
    print("2. Run the GUI: python mod_translator_gui.py")
    print("3. Load template from Code mau/")
    print("4. Add test-mod.zip as mod to translate")
    print("5. Configure API key and start translation")

if __name__ == "__main__":
    main()
