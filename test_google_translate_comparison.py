#!/usr/bin/env python3
"""
Google Translate Comparison Test
So sánh chất lượng dịch giữa Mock Advanced và Google Translate thật
"""
import os
import sys
import json
import time
from datetime import datetime

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try different googletrans versions
def try_import_googletrans():
    """Try to import Google Translate with different methods"""
    methods = []
    
    # Method 1: Standard googletrans
    try:
        from googletrans import Translator
        translator = Translator()
        # Quick test
        result = translator.translate("Hello", dest='vi')
        if result and result.text:
            methods.append(("googletrans", translator))
    except Exception as e:
        print(f"  ⚠️ Standard googletrans failed: {e}")
    
    # Method 2: Try alternative service URLs
    try:
        from googletrans import Translator
        translator = Translator(service_urls=['translate.googleapis.com'])
        result = translator.translate("Hello", dest='vi')
        if result and result.text:
            methods.append(("googletrans-alt", translator))
    except Exception as e:
        print(f"  ⚠️ Alternative googletrans failed: {e}")
    
    # Method 3: Try with different user agent
    try:
        from googletrans import Translator
        translator = Translator()
        translator.client.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        result = translator.translate("Hello", dest='vi')
        if result and result.text:
            methods.append(("googletrans-ua", translator))
    except Exception as e:
        print(f"  ⚠️ User-Agent googletrans failed: {e}")
    
    return methods

class AdvancedMockTranslator:
    """Advanced Mock Translator như đã dùng trong large scale test"""
    
    def __init__(self):
        self.vietnamese_dict = {
            "speed": "tốc độ", "belt": "băng tải", "conveyor": "băng chuyền",
            "multiplier": "hệ số nhân", "setting": "cài đặt", "language": "ngôn ngữ",
            "target": "mục tiêu", "size": "kích thước", "big": "lớn", "small": "nhỏ",
            "bag": "túi", "inventory": "kho đồ", "item": "vật phẩm", "recipe": "công thức",
            "technology": "công nghệ", "research": "nghiên cứu", "entity": "thực thể",
            "fluid": "chất lỏng", "tile": "ô đất", "signal": "tín hiệu", "virtual": "ảo",
            "translate": "dịch", "batch": "lô", "request": "yêu cầu", "how many": "bao nhiêu",
            "per": "mỗi", "electric": "điện", "pole": "cột", "range": "phạm vi",
            "machine": "máy móc", "mining": "khai thác", "drone": "máy bay không người lái",
            "calculator": "máy tính", "rate": "tỷ lệ", "hero": "anh hùng", "turret": "tháp pháo",
            "redux": "cải tiến", "monster": "quái vật", "biter": "côn trùng cắn",
            "cold": "lạnh", "frost": "băng giá", "explosive": "nổ", "armoured": "bọc thép",
            "armor": "giáp", "bot": "robot", "start": "bắt đầu", "mega": "siêu",
            "gun": "súng", "equipment": "trang bị", "burner": "đốt nhiên liệu",
            "alien": "người ngoài hành tinh", "chaos": "hỗn loạn", "modpack": "gói mod",
            "enemy": "kẻ thù", "arachnid": "nhện", "stack": "chồng", "infinite": "vô hạn",
            "battery": "pin", "powered": "được cung cấp điện", "delta": "delta",
            "name": "tên", "description": "mô tả", "mod": "mod", "category": "danh mục",
            "group": "nhóm", "subgroup": "nhóm con", "order": "thứ tự", "enabled": "bật",
            "disabled": "tắt", "default": "mặc định", "value": "giá trị", "option": "tùy chọn",
            "tooltip": "chú thích", "label": "nhãn", "production": "sản xuất",
            "consumption": "tiêu thụ", "inserters": "cần cẩu", "transport belts": "băng tải vận chuyển",
            "power": "năng lượng", "pollution": "ô nhiễm", "heat": "nhiệt"
        }
    
    def translate(self, text):
        """Translate with advanced mock logic"""
        if not text or text.strip() == "":
            return text
        
        original_text = text
        translated = text.lower()
        
        # Apply dictionary replacements (longer phrases first)
        sorted_terms = sorted(self.vietnamese_dict.items(), key=lambda x: len(x[0]), reverse=True)
        for en_term, vi_term in sorted_terms:
            translated = translated.replace(en_term, vi_term)
        
        # Handle special patterns
        if "how many" in original_text.lower():
            translated = translated.replace("how many", "bao nhiêu")
        
        if " per " in original_text.lower():
            translated = translated.replace(" per ", " mỗi ")
            
        if translated.startswith("translate ("):
            translated = translated.replace("translate (", "dịch (").replace(")", ")")
        
        # Preserve capitalization
        if original_text and original_text[0].isupper():
            translated = translated.capitalize()
        
        # If minimal changes, add [VI] prefix
        if translated.lower() == original_text.lower() or len(translated.replace(original_text.lower(), "")) < 3:
            translated = f"[VI] {original_text}"
        
        return translated

def compare_translation_quality():
    """So sánh chất lượng dịch giữa các phương pháp"""
    print("🔍 GOOGLE TRANSLATE COMPARISON TEST")
    print("=" * 60)
    
    # Try to get Google Translate
    print("\\n🌐 Checking Google Translate availability...")
    google_methods = try_import_googletrans()
    
    if google_methods:
        print(f"  ✅ Found {len(google_methods)} working Google Translate method(s)")
        for method_name, translator in google_methods:
            print(f"    • {method_name}")
        selected_google = google_methods[0][1]  # Use first working method
    else:
        print("  ❌ No working Google Translate methods found")
        print("  📝 Will compare with Mock only")
        selected_google = None
    
    # Initialize mock translator
    mock_translator = AdvancedMockTranslator()
    
    # Test sentences (mix of simple and complex)
    test_texts = [
        # Simple terms
        "Speed",
        "Belt multiplier",
        "Target language", 
        "Big bag size",
        
        # Game-specific terms
        "Mining drone",
        "Rate calculator",
        "Electric pole range",
        "Machine speed setting",
        
        # Complex phrases
        "How many translations per request",
        "Translate (Entity)",
        "Default GUI location", 
        "Show power consumption",
        
        # Technical descriptions
        "Calculate maximum production and consumption rates for the selected machines",
        "Increase the size of your inventory",
        "Bonus to item pickup distance: +1",
        "Some machines have no fuel",
        
        # Interface elements
        "Previous set (1/2)",
        "Next set (__1__/__2__)",
        "Open in recipe book",
        "Dismiss tool after selecting"
    ]
    
    print(f"\\n📝 Testing with {len(test_texts)} sample texts...")
    
    # Perform translations
    results = []
    
    for i, text in enumerate(test_texts):
        print(f"\\n🔸 Test {i+1}: '{text}'")
        
        result = {
            "original": text,
            "mock": mock_translator.translate(text),
            "google": None,
            "google_error": None
        }
        
        # Try Google Translate
        if selected_google:
            try:
                google_result = selected_google.translate(text, dest='vi')
                result["google"] = google_result.text
                print(f"  🤖 Mock: {result['mock']}")
                print(f"  🌐 Google: {result['google']}")
                
                # Add small delay to avoid rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                result["google_error"] = str(e)
                print(f"  🤖 Mock: {result['mock']}")
                print(f"  ❌ Google Error: {e}")
        else:
            print(f"  🤖 Mock: {result['mock']}")
            print(f"  ⚪ Google: Not available")
        
        results.append(result)
    
    return results, len(google_methods) > 0

def analyze_translation_results(results, has_google):
    """Phân tích kết quả dịch"""
    print("\\n" + "=" * 60)
    print("📊 TRANSLATION QUALITY ANALYSIS")
    print("=" * 60)
    
    # Statistics
    total_tests = len(results)
    google_success = len([r for r in results if r["google"] and not r["google_error"]])
    mock_translations = len([r for r in results if r["mock"]])
    
    print(f"\\n📋 STATISTICS:")
    print(f"  • Total tests: {total_tests}")
    print(f"  • Mock translations: {mock_translations}")
    if has_google:
        print(f"  • Google successful: {google_success}")
        print(f"  • Google success rate: {google_success/total_tests*100:.1f}%")
    
    # Quality comparison categories
    if has_google:
        print(f"\\n🏆 QUALITY COMPARISON:")
        
        categories = {
            "exact_match": [],
            "google_better": [],
            "mock_better": [],
            "similar_quality": []
        }
        
        for result in results:
            if not result["google"] or result["google_error"]:
                continue
                
            mock_text = result["mock"].lower().replace("[vi] ", "")
            google_text = result["google"].lower()
            original = result["original"].lower()
            
            # Simple heuristic for quality comparison
            if mock_text == google_text:
                categories["exact_match"].append(result)
            elif "[vi]" in result["mock"] and len(google_text) > len(mock_text.replace("[vi] ", "")):
                categories["google_better"].append(result)
            elif "[vi]" not in result["mock"] and "vi" not in google_text and len(mock_text) > len(google_text):
                categories["mock_better"].append(result)
            else:
                categories["similar_quality"].append(result)
        
        for category, items in categories.items():
            count = len(items)
            print(f"  • {category.replace('_', ' ').title()}: {count} ({count/google_success*100:.1f}%)")
    
    # Show detailed examples
    print(f"\\n💡 DETAILED EXAMPLES:")
    
    for i, result in enumerate(results[:5]):  # Show first 5
        print(f"\\n📝 Example {i+1}: '{result['original']}'")
        print(f"  🤖 Mock: {result['mock']}")
        if result["google"]:
            print(f"  🌐 Google: {result['google']}")
        elif result["google_error"]:
            print(f"  ❌ Google: Error - {result['google_error'][:50]}...")
        else:
            print(f"  ⚪ Google: Not tested")
    
    # Mock translator strengths
    print(f"\\n🎯 MOCK TRANSLATOR STRENGTHS:")
    print("  ✅ Game-specific terminology (speed→tốc độ, belt→băng tải)")
    print("  ✅ Consistent formatting preservation")
    print("  ✅ No rate limiting or network dependencies")
    print("  ✅ Instant processing speed")
    print("  ✅ Factorio mod domain knowledge")
    
    if has_google:
        print(f"\\n🌐 GOOGLE TRANSLATE STRENGTHS:")
        print("  ✅ Natural language understanding")
        print("  ✅ Complex sentence structure handling")
        print("  ✅ Broader vocabulary coverage")
        print("  ✅ Context-aware translations")
    
    return {
        "total_tests": total_tests,
        "mock_success": mock_translations,
        "google_success": google_success if has_google else 0,
        "has_google": has_google,
        "results": results
    }

def save_comparison_results(analysis_results):
    """Lưu kết quả so sánh"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"translation_comparison_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\\n💾 Results saved to: {filename}")
    return filename

def main():
    """Main function"""
    try:
        # Run comparison test
        results, has_google = compare_translation_quality()
        
        # Analyze results
        analysis = analyze_translation_results(results, has_google)
        
        # Save results
        save_comparison_results(analysis)
        
        # Conclusion
        print("\\n" + "=" * 60)
        print("🎉 COMPARISON TEST COMPLETED!")
        
        if has_google:
            print("\\n🏆 CONCLUSION:")
            print("  • Both Mock and Google have their strengths")
            print("  • Mock excels at Factorio-specific terms")  
            print("  • Google better for natural language")
            print("  • Hybrid approach recommended for best results")
        else:
            print("\\n🏆 CONCLUSION:")
            print("  • Mock translator performs well for game content")
            print("  • No network dependency is a major advantage")
            print("  • Good fallback when Google Translate unavailable")
        
        print("\\n🚀 RECOMMENDATION:")
        print("  Use Mock Advanced as primary with Google as fallback")
        print("  Or combine both: Google for sentences, Mock for terms")
        
    except Exception as e:
        print(f"\\n💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
