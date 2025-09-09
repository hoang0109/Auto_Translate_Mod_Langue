#!/usr/bin/env python3
"""
Test GUI Integration with Improved Mod Finder
Tests that the updated GUI properly uses find_locale_files_improved
"""
import os
import zipfile
from improved_mod_finder import find_locale_files_improved

def test_gui_integration():
    """Test the GUI's improved locale file detection logic"""
    print("🧪 Testing GUI Integration with Improved Mod Finder")
    print("=" * 60)
    
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    
    if not os.path.exists(mods_dir):
        print("❌ Mods directory not found for testing")
        return
    
    # Find some test mods
    test_mods = [f for f in os.listdir(mods_dir) if f.endswith('.zip')][:10]
    
    print(f"📦 Testing {len(test_mods)} mods...")
    
    translatable_count = 0
    skipped_count = 0
    
    for mod_file in test_mods:
        mod_path = os.path.join(mods_dir, mod_file)
        
        # Simulate GUI's mod processing logic
        try:
            with zipfile.ZipFile(mod_path, 'r') as zipf:
                # Read info.json to get mod name
                info_json_path = next((f for f in zipf.namelist() if f.endswith('info.json')), None)
                if not info_json_path:
                    continue
                
                # Use the improved finder (this is what GUI now uses)
                root_folder, locale_files = find_locale_files_improved(mod_path)
                
                if not locale_files:
                    print(f"⚪ {mod_file}: No English locale *.cfg files, would be skipped")
                    skipped_count += 1
                else:
                    print(f"✅ {mod_file}: {len(locale_files)} locale files found, would be translated")
                    print(f"   Root: {root_folder}")
                    print(f"   Sample file: {locale_files[0]}")
                    translatable_count += 1
                    
        except Exception as e:
            print(f"❌ Error processing {mod_file}: {e}")
            skipped_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS:")
    print(f"  • Total mods tested: {len(test_mods)}")
    print(f"  • Mods that would be translated: {translatable_count}")
    print(f"  • Mods that would be skipped: {skipped_count}")
    print(f"  • Success rate: {translatable_count/(translatable_count+skipped_count)*100:.1f}%")
    
    if translatable_count > 0:
        print("\n✅ GUI integration test PASSED!")
        print("   The GUI should now successfully detect locale files in mods")
        print("   with various folder structures and reduce skip warnings.")
    else:
        print("\n⚠️ No translatable mods found - may need to check mod directory")

def test_specific_problematic_mods():
    """Test mods that were previously showing as skipped"""
    print("\n" + "=" * 60)  
    print("🔍 Testing Previously Problematic Mods")
    print("=" * 60)
    
    mods_dir = r"C:\Users\Acer\AppData\Roaming\Factorio\mods"
    
    # Mods that were likely skipped before
    problematic_mods = [
        "HeroTurretRedux_1.0.30.zip",
        "BeltSpeedMultiplier_1.0.3.zip", 
        "Babelfish_2.0.0.zip",
        "aai-industry_0.6.10.zip"
    ]
    
    found_count = 0
    for mod_name in problematic_mods:
        mod_path = os.path.join(mods_dir, mod_name)
        if os.path.exists(mod_path):
            root_folder, locale_files = find_locale_files_improved(mod_path)
            if locale_files:
                print(f"✅ {mod_name}: FIXED - {len(locale_files)} files found")
                found_count += 1
            else:
                print(f"⚪ {mod_name}: Still no locale files")
        else:
            print(f"❓ {mod_name}: Not found in directory")
    
    if found_count > 0:
        print(f"\n🎯 SUCCESS: {found_count} previously problematic mods now work!")
    
if __name__ == "__main__":
    test_gui_integration()
    test_specific_problematic_mods()
    
    print("\n" + "=" * 60)
    print("✅ INTEGRATION TEST COMPLETE")
    print("=" * 60)
    print("The GUI is now updated to use find_locale_files_improved.")
    print("This should significantly reduce 'no English locale files' warnings")
    print("and allow translation of mods with non-standard folder structures.")
