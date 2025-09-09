#!/usr/bin/env python3
"""
Demo so sánh Safe vs Fast Google Translate
"""
import time
import os
from pathlib import Path
from google_translate_core import GoogleTranslateAPI
from google_translate_safe import SafeGoogleTranslateAPI

def demo_comparison():
    print("🎯 DEMO SO SÁNH SAFE VS FAST GOOGLE TRANSLATE")
    print("=" * 60)
    
    # Test texts (Factorio-like)
    test_texts = [
        "Iron plate",
        "Copper wire", 
        "Steam engine",
        "Electric furnace",
        "Advanced circuit",
        "Assembly machine",
        "Transport belt",
        "Inserter",
        "Solar panel",
        "Accumulator",
        "Oil refinery",
        "Chemical plant",
        "Research lab",
        "Science pack",
        "Underground belt"
    ]
    
    print(f"📋 Test data: {len(test_texts)} Factorio items")
    
    # Test Fast Google Translate
    print(f"\n⚡ TESTING FAST GOOGLE TRANSLATE:")
    print("-" * 40)
    
    start_time = time.time()
    fast_translator = GoogleTranslateAPI()
    fast_results = fast_translator.translate_texts(test_texts, 'VI', 'en')
    fast_duration = time.time() - start_time
    
    print(f"⏱️  Duration: {fast_duration:.1f}s")
    print(f"📊 Speed: {len(test_texts)/fast_duration:.1f} texts/second")
    print(f"🎯 Results: {len(fast_results)} texts translated")
    
    # Test Safe Google Translate
    print(f"\n🔒 TESTING SAFE GOOGLE TRANSLATE:")
    print("-" * 40)
    
    start_time = time.time()
    safe_translator = SafeGoogleTranslateAPI()
    safe_results = safe_translator.translate_texts(test_texts, 'VI', 'en')
    safe_duration = time.time() - start_time
    
    print(f"⏱️  Duration: {safe_duration:.1f}s")
    print(f"📊 Speed: {len(test_texts)/safe_duration:.1f} texts/second")
    print(f"🎯 Results: {len(safe_results)} texts translated")
    
    # Comparison
    print(f"\n📈 COMPARISON:")
    print("-" * 30)
    print(f"⚡ Fast: {fast_duration:.1f}s ({len(test_texts)/fast_duration:.1f} texts/s)")
    print(f"🔒 Safe: {safe_duration:.1f}s ({len(test_texts)/safe_duration:.1f} texts/s)")
    print(f"🔄 Speed difference: {safe_duration/fast_duration:.1f}x slower (but safer)")
    
    # Quality comparison (first few results)
    print(f"\n🔍 QUALITY COMPARISON (First 5 results):")
    print("-" * 50)
    for i in range(min(5, len(test_texts))):
        original = test_texts[i]
        fast_trans = fast_results[i] if i < len(fast_results) else "N/A"
        safe_trans = safe_results[i] if i < len(safe_results) else "N/A"
        
        print(f"\n{i+1}. Original: {original}")
        print(f"   ⚡ Fast: {fast_trans}")
        print(f"   🔒 Safe: {safe_trans}")
        print(f"   📊 Same: {'✅' if fast_trans == safe_trans else '❌'}")

def demo_caching_benefits():
    print(f"\n" + "=" * 60)
    print("💾 DEMO CACHING BENEFITS")
    print("=" * 60)
    
    # Test texts with duplicates
    test_texts_with_duplicates = [
        "Iron plate", "Copper wire", "Iron plate",  # Duplicate
        "Steam engine", "Copper wire",  # Another duplicate
        "Electric furnace", "Iron plate",  # More duplicates
        "Advanced circuit", "Steam engine",
    ]
    
    print(f"📋 Test with duplicates: {len(test_texts_with_duplicates)} texts")
    print(f"📊 Unique texts: {len(set(test_texts_with_duplicates))} unique")
    
    # Test Safe Google Translate with caching
    print(f"\n🔒 Safe Google Translate (with caching):")
    
    safe_translator = SafeGoogleTranslateAPI()
    start_time = time.time()
    results = safe_translator.translate_texts(test_texts_with_duplicates, 'VI', 'en')
    duration = time.time() - start_time
    
    print(f"⏱️  Duration: {duration:.1f}s")
    print(f"📊 Effective speed: {len(test_texts_with_duplicates)/duration:.1f} texts/s")
    
    # Show statistics
    stats = safe_translator.stats
    total_accesses = stats['cache_hits'] + stats['cache_misses']
    if total_accesses > 0:
        hit_rate = (stats['cache_hits'] / total_accesses) * 100
        print(f"💾 Cache hit rate: {hit_rate:.1f}%")
        print(f"🎯 Actual requests: {stats['total_requests']}")
        print(f"⚡ Requests saved: {stats['cache_hits']}")

def show_gui_demo():
    print(f"\n" + "=" * 60)
    print("🖥️  GUI DEMO INSTRUCTIONS")
    print("=" * 60)
    
    print("\n🚀 1. Chạy GUI:")
    print("   python mod_translator_gui.py")
    
    print("\n⚙️  2. Chọn Translation Service:")
    print("   • 🔒 'Safe Google Translate (Recommended)' - An toàn, có cache")
    print("   • ⚡ 'Google Translate (Fast)' - Nhanh hơn, rủi ro cao hơn")
    print("   • 🔑 'DeepL API' - Chất lượng cao nhưng cần API key")
    
    print("\n📊 3. Khi chọn Safe Google Translate:")
    print("   • Statistics panel sẽ hiện ra")
    print("   • Theo dõi Requests, Cache %, RPM, Errors")
    print("   • RPM màu xanh (<= 25), vàng (<= 50), đỏ (> 50)")
    
    print("\n🎯 4. Khuyến nghị:")
    print("   • Dùng Safe cho production")
    print("   • Dùng Fast cho testing nhanh")
    print("   • Monitor statistics trong quá trình dịch")

if __name__ == "__main__":
    demo_comparison()
    demo_caching_benefits()
    show_gui_demo()
