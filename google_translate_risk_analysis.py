#!/usr/bin/env python3
"""
Phân tích rủi ro khi gửi quá nhiều request đến Google Translate (Free)
"""
import time
import random
from collections import defaultdict
from datetime import datetime, timedelta

class GoogleTranslateRiskAnalyzer:
    def __init__(self):
        self.request_history = []
        self.blocked_periods = []
        
    def analyze_risks(self):
        """Phân tích các rủi ro khi sử dụng Google Translate Free"""
        print("⚠️ PHÂN TÍCH RỦI RO GOOGLE TRANSLATE (FREE)")
        print("=" * 60)
        
        print("\n🚨 CÁC RỦI RO CHÍNH:")
        print("1. 🔴 Rate Limiting (429 Too Many Requests)")
        print("   - Google có thể block IP tạm thời")
        print("   - Thời gian block: 1-24 giờ")
        print("   - Trigger: >100-200 requests/phút")
        
        print("\n2. 🔴 IP Blocking")
        print("   - Block IP dài hạn nếu abuse")
        print("   - Cần đổi IP hoặc chờ lâu")
        print("   - Trigger: Hàng nghìn requests liên tục")
        
        print("\n3. 🔴 Service Degradation")
        print("   - Chất lượng dịch giảm khi quá tải")
        print("   - Response time chậm")
        print("   - Timeout errors")
        
        print("\n4. 🔴 Detection & Captcha")
        print("   - Google phát hiện bot behavior")
        print("   - Yêu cầu giải captcha")
        print("   - Block automated access")
        
        self.estimate_current_usage()
        self.suggest_improvements()
    
    def estimate_current_usage(self):
        """Ước tính usage hiện tại của hệ thống"""
        print("\n📊 ƯỚC TÍNH USAGE HIỆN TẠI:")
        
        # Từ kết quả test trước đó
        mods_translated = 47  # Từ improved_mod_finder
        avg_texts_per_mod = 200  # Ước tính trung bình
        total_texts = mods_translated * avg_texts_per_mod
        
        # Ước tính chunks và requests
        max_chunk_size = 4500  # từ GoogleTranslateAPI
        avg_text_length = 50  # ký tự
        texts_per_chunk = max_chunk_size // avg_text_length  # ~90 texts/chunk
        
        total_chunks = total_texts // texts_per_chunk
        total_requests = total_chunks
        
        print(f"• Số mods có thể dịch: {mods_translated}")
        print(f"• Tổng văn bản ước tính: {total_texts:,}")
        print(f"• Số chunks: {total_chunks:,}")
        print(f"• Số requests: {total_requests:,}")
        
        # Ước tính thời gian với delay hiện tại
        current_delay = 0.6  # 0.1 + 0.5 từ code
        estimated_time = total_requests * current_delay
        
        print(f"• Thời gian ước tính: {estimated_time/3600:.1f} giờ")
        print(f"• Requests per hour: {total_requests/(estimated_time/3600):.0f}")
        
        # Đánh giá rủi ro
        requests_per_minute = (total_requests / (estimated_time/60))
        
        if requests_per_minute > 100:
            risk_level = "🔴 HIGH RISK"
        elif requests_per_minute > 50:
            risk_level = "🟡 MEDIUM RISK"
        else:
            risk_level = "🟢 LOW RISK"
        
        print(f"• Requests per minute: {requests_per_minute:.1f}")
        print(f"• Risk Level: {risk_level}")
    
    def suggest_improvements(self):
        """Đề xuất cải thiện"""
        print("\n💡 ĐỀ XUẤT GIẢI PHÁP:")
        
        print("1. 🛡️ ADVANCED RATE LIMITING:")
        print("   - Tăng delay giữa requests: 1-3 giây")
        print("   - Random delay để tránh pattern detection")
        print("   - Exponential backoff khi gặp lỗi")
        
        print("2. 🔄 REQUEST BATCHING:")
        print("   - Gom nhiều văn bản nhỏ thành batch lớn")
        print("   - Giảm số lượng requests tổng thể")
        print("   - Tối ưu chunk size")
        
        print("3. 📦 CACHING SYSTEM:")
        print("   - Cache kết quả dịch đã có")
        print("   - Tránh dịch lại văn bản giống nhau")
        print("   - Persistent cache cross-sessions")
        
        print("4. 🔀 MULTIPLE STRATEGIES:")
        print("   - Fallback sang offline translation")
        print("   - User Agent rotation")
        print("   - Session management")
        
        print("5. 🎯 SMART FILTERING:")
        print("   - Ưu tiên dịch văn bản quan trọng")
        print("   - Skip văn bản đã có sẵn tiếng Việt")
        print("   - Batch processing theo priority")

def demonstrate_improved_rate_limiting():
    """Demo cải thiện rate limiting"""
    print("\n🔧 DEMO IMPROVED RATE LIMITING:")
    print("=" * 40)
    
    # Simulate different strategies
    strategies = {
        "Current (0.6s delay)": {"delay": 0.6, "requests": 100},
        "Conservative (2s delay)": {"delay": 2.0, "requests": 100},
        "Smart Backoff": {"delay": 1.0, "requests": 100, "backoff": True},
        "Cached (50% hit rate)": {"delay": 1.0, "requests": 50}
    }
    
    for strategy, params in strategies.items():
        delay = params["delay"]
        requests = params["requests"]
        backoff = params.get("backoff", False)
        
        total_time = requests * delay
        if backoff:
            total_time *= 1.2  # 20% thêm cho backoff
        
        requests_per_minute = requests / (total_time / 60)
        
        risk = "🔴 HIGH" if requests_per_minute > 100 else "🟡 MED" if requests_per_minute > 50 else "🟢 LOW"
        
        print(f"• {strategy}:")
        print(f"  Time: {total_time/60:.1f} min, RPM: {requests_per_minute:.1f}, Risk: {risk}")

if __name__ == "__main__":
    analyzer = GoogleTranslateRiskAnalyzer()
    analyzer.analyze_risks()
    demonstrate_improved_rate_limiting()
