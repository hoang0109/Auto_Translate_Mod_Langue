#!/usr/bin/env python3
"""
Tạo một mod test có locale/en/*.cfg để test translation
"""
import zipfile
import json
import os

def create_test_mod():
    # Tạo info.json
    info_data = {
        "name": "test-translation-mod",
        "version": "1.0.0",
        "title": "Test Translation Mod",
        "author": "Test Author",
        "factorio_version": "2.0",
        "description": "A test mod for translation testing"
    }
    
    # Tạo nội dung locale en
    locale_content = """[entity-name]
test-entity=Test Entity
sample-machine=Sample Machine
example-turret=Example Turret

[item-name]
test-item=Test Item
sample-tool=Sample Tool
example-weapon=Example Weapon

[technology-name]
test-tech=Test Technology
sample-research=Sample Research

[recipe-name]
test-recipe=Test Recipe
sample-crafting=Sample Crafting
"""
    
    # Tạo zip file
    with zipfile.ZipFile("test-mod.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        # Thêm info.json
        zipf.writestr("test-translation-mod/info.json", json.dumps(info_data, indent=2))
        
        # Thêm locale file
        zipf.writestr("test-translation-mod/locale/en/test.cfg", locale_content)
        
        # Thêm một file locale khác
        extra_locale = """[fluid-name]
test-fluid=Test Fluid
sample-gas=Sample Gas

[equipment-name]
test-equipment=Test Equipment
"""
        zipf.writestr("test-translation-mod/locale/en/extra.cfg", extra_locale)
    
    print("Created test-mod.zip with locale/en files")
    
    # Hiển thị nội dung để verify
    print("\nContents of test-mod.zip:")
    with zipfile.ZipFile("test-mod.zip", "r") as zipf:
        for filename in zipf.namelist():
            print(f"  {filename}")

if __name__ == "__main__":
    create_test_mod()
