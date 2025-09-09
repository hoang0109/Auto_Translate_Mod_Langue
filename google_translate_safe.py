#!/usr/bin/env python3
"""
Google Translate Safe Version
Cải tiến với advanced rate limiting, caching, và error handling
"""
import time
import random
import hashlib
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
import threading
from datetime import datetime, timedelta

class SafeGoogleTranslateAPI:
    def __init__(self, cache_dir="translation_cache"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.base_url = "https://translate.googleapis.com/translate_a/single"
        
        # Advanced rate limiting
        self.min_delay = 1.5  # Tăng delay tối thiểu
        self.max_delay = 3.0  # Delay tối đa
        self.current_delay = self.min_delay
        self.consecutive_errors = 0
        self.max_chunk_size = 3000  # Giảm chunk size để an toàn hơn
        
        # Request tracking
        self.requests_this_minute = 0
        self.requests_this_hour = 0
        self.last_minute_reset = datetime.now()
        self.last_hour_reset = datetime.now()
        self.max_requests_per_minute = 25  # Conservative limit
        self.max_requests_per_hour = 1000
        
        # Caching system
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache = {}
        self.load_cache()
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'blocked_periods': 0
        }
    
    def load_cache(self):
        """Tải cache từ file"""
        cache_file = self.cache_dir / "translation_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"📦 Loaded {len(self.cache)} cached translations")
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
                self.cache = {}
    
    def save_cache(self):
        """Lưu cache vào file"""
        cache_file = self.cache_dir / "translation_cache.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    def get_cache_key(self, text, target_lang, source_lang='en'):
        """Tạo cache key từ text và language"""
        combined = f"{source_lang}->{target_lang}:{text}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def get_cached_translation(self, text, target_lang, source_lang='en'):
        """Lấy bản dịch từ cache nếu có"""
        cache_key = self.get_cache_key(text, target_lang, source_lang)
        return self.cache.get(cache_key)
    
    def cache_translation(self, text, translation, target_lang, source_lang='en'):
        """Lưu bản dịch vào cache"""
        cache_key = self.get_cache_key(text, target_lang, source_lang)
        self.cache[cache_key] = translation
        
        # Định kỳ lưu cache (mỗi 50 translations)
        if len(self.cache) % 50 == 0:
            self.save_cache()
    
    def check_rate_limits(self):
        """Kiểm tra và reset rate limits"""
        now = datetime.now()
        
        # Reset minute counter
        if now - self.last_minute_reset > timedelta(minutes=1):
            self.requests_this_minute = 0
            self.last_minute_reset = now
        
        # Reset hour counter
        if now - self.last_hour_reset > timedelta(hours=1):
            self.requests_this_hour = 0
            self.last_hour_reset = now
        
        # Check limits
        if self.requests_this_minute >= self.max_requests_per_minute:
            wait_time = 60 - (now - self.last_minute_reset).seconds
            print(f"⏳ Rate limit reached, waiting {wait_time}s...")
            time.sleep(wait_time + 1)
            self.check_rate_limits()  # Recheck after waiting
        
        if self.requests_this_hour >= self.max_requests_per_hour:
            wait_time = 3600 - (now - self.last_hour_reset).seconds
            print(f"⏳ Hourly limit reached, waiting {wait_time/60:.1f} minutes...")
            self.stats['blocked_periods'] += 1
            time.sleep(wait_time + 1)
            self.check_rate_limits()
    
    def adaptive_delay(self, success=True):
        """Adaptive delay based on success/failure"""
        if success:
            # Giảm delay nếu thành công
            self.current_delay = max(self.min_delay, self.current_delay * 0.9)
            self.consecutive_errors = 0
        else:
            # Tăng delay nếu lỗi (exponential backoff)
            self.consecutive_errors += 1
            backoff_factor = min(2.0 ** self.consecutive_errors, 8.0)  # Cap at 8x
            self.current_delay = min(self.max_delay * backoff_factor, 30.0)  # Cap at 30s
        
        # Random jitter để tránh pattern detection
        jitter = random.uniform(0.8, 1.2)
        actual_delay = self.current_delay * jitter
        
        print(f"⏱️ Waiting {actual_delay:.1f}s (errors: {self.consecutive_errors})")
        time.sleep(actual_delay)
    
    def get_language_code(self, lang_code):
        """Chuyển đổi language code"""
        lang_map = {
            'VI': 'vi', 'JA': 'ja', 'EN': 'en', 'ZH': 'zh',
            'FR': 'fr', 'DE': 'de', 'ES': 'es'
        }
        return lang_map.get(lang_code.upper(), lang_code.lower())
    
    def split_text_into_chunks(self, texts, max_size=None):
        """Chia nhỏ texts với size adaptive"""
        if max_size is None:
            max_size = self.max_chunk_size
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for text in texts:
            text_size = len(text.encode('utf-8'))
            
            # Nếu text quá lớn, chia nhỏ
            if text_size > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_size = 0
                
                # Chia text lớn thành từng từ
                words = text.split()
                temp_chunk = []
                temp_size = 0
                
                for word in words:
                    word_size = len(word.encode('utf-8')) + 1
                    if temp_size + word_size > max_size and temp_chunk:
                        chunks.append([' '.join(temp_chunk)])
                        temp_chunk = [word]
                        temp_size = word_size
                    else:
                        temp_chunk.append(word)
                        temp_size += word_size
                
                if temp_chunk:
                    chunks.append([' '.join(temp_chunk)])
            else:
                # Kiểm tra xem có thể thêm vào chunk hiện tại không
                if current_size + text_size > max_size and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = [text]
                    current_size = text_size
                else:
                    current_chunk.append(text)
                    current_size += text_size
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def translate_chunk_with_cache(self, texts, target_lang, source_lang='en'):
        """Dịch chunk với cache support"""
        if not texts:
            return []
        
        # Kiểm tra cache cho từng text
        cached_results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached = self.get_cached_translation(text, target_lang, source_lang)
            if cached:
                cached_results.append((i, cached))
                self.stats['cache_hits'] += 1
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                self.stats['cache_misses'] += 1
        
        # Nếu tất cả đã có trong cache
        if not uncached_texts:
            result = [''] * len(texts)
            for i, translation in cached_results:
                result[i] = translation
            print(f"💾 All {len(texts)} texts from cache")
            return result
        
        # Dịch các text chưa có trong cache
        print(f"💾 {len(cached_results)} from cache, {len(uncached_texts)} need translation")
        
        try:
            with self.lock:
                self.check_rate_limits()
                self.stats['total_requests'] += 1
                self.requests_this_minute += 1
                self.requests_this_hour += 1
            
            translated_uncached = self.translate_chunk_direct(uncached_texts, target_lang, source_lang)
            
            # Cache các kết quả mới
            for text, translation in zip(uncached_texts, translated_uncached):
                self.cache_translation(text, translation, target_lang, source_lang)
            
            # Kết hợp kết quả
            result = [''] * len(texts)
            for i, translation in cached_results:
                result[i] = translation
            
            for i, translation in zip(uncached_indices, translated_uncached):
                result[i] = translation
            
            self.adaptive_delay(success=True)
            return result
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            self.stats['errors'] += 1
            self.adaptive_delay(success=False)
            return texts  # Trả về text gốc nếu lỗi
    
    def translate_chunk_direct(self, texts, target_lang, source_lang='en'):
        """Dịch chunk trực tiếp (không cache)"""
        try:
            combined_text = '\n'.join(texts)
            
            params = {
                'client': 'gtx',
                'sl': source_lang,
                'tl': target_lang,
                'dt': 't',
                'q': combined_text
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result and len(result) > 0 and result[0]:
                    translated_parts = []
                    for part in result[0]:
                        if part and len(part) > 0:
                            translated_parts.append(part[0])
                    
                    translated_text = ''.join(translated_parts)
                    translated_lines = translated_text.split('\n')
                    
                    if len(translated_lines) == len(texts):
                        return translated_lines
                    else:
                        # Fallback: chia đều
                        words_per_text = len(translated_text.split()) // len(texts)
                        words = translated_text.split()
                        result_texts = []
                        for i in range(len(texts)):
                            start_idx = i * words_per_text
                            end_idx = (i + 1) * words_per_text if i < len(texts) - 1 else len(words)
                            result_texts.append(' '.join(words[start_idx:end_idx]))
                        return result_texts
                else:
                    raise Exception("Empty response from Google Translate")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            raise e
    
    def translate_texts(self, texts, target_lang, source_lang='en', progress_callback=None):
        """Main translation method với all improvements"""
        if not texts:
            return []
        
        target_lang = self.get_language_code(target_lang)
        source_lang = self.get_language_code(source_lang)
        
        print(f"🔒 Safe Google Translate: {len(texts)} texts {source_lang} -> {target_lang}")
        print(f"📊 Cache: {len(self.cache)} entries, Max RPM: {self.max_requests_per_minute}")
        
        chunks = self.split_text_into_chunks(texts, self.max_chunk_size)
        print(f"📦 Split into {len(chunks)} chunks (max size: {self.max_chunk_size})")
        
        all_results = []
        
        for i, chunk in enumerate(chunks):
            try:
                if progress_callback:
                    progress_callback(i, len(chunks), f"Safe translate chunk {i+1}/{len(chunks)}")
                
                chunk_results = self.translate_chunk_with_cache(chunk, target_lang, source_lang)
                all_results.extend(chunk_results)
                
                print(f"✅ Chunk {i+1}/{len(chunks)}: {len(chunk)} texts")
                
            except Exception as e:
                print(f"❌ Chunk {i+1} failed: {e}")
                all_results.extend(chunk)  # Fallback to original
        
        # Lưu cache cuối cùng
        self.save_cache()
        
        # In thống kê
        self.print_statistics()
        
        return all_results
    
    def print_statistics(self):
        """In thống kê sử dụng"""
        print(f"\n📈 TRANSLATION STATISTICS:")
        print(f"• Total requests: {self.stats['total_requests']}")
        print(f"• Cache hits: {self.stats['cache_hits']}")
        print(f"• Cache misses: {self.stats['cache_misses']}")
        hit_rate = self.stats['cache_hits'] / max(self.stats['cache_hits'] + self.stats['cache_misses'], 1)
        print(f"• Cache hit rate: {hit_rate:.1%}")
        print(f"• Errors: {self.stats['errors']}")
        print(f"• Blocked periods: {self.stats['blocked_periods']}")
        print(f"• Current delay: {self.current_delay:.1f}s")

def test_safe_translation():
    """Test Safe Google Translate"""
    translator = SafeGoogleTranslateAPI()
    
    test_texts = [
        "Iron plate",
        "Copper wire", 
        "Steam engine",
        "Electric furnace",
        "Advanced circuit",
        "Iron plate",  # Duplicate để test cache
        "Assembly machine"
    ]
    
    print("🧪 Testing Safe Google Translate...")
    results = translator.translate_texts(test_texts, 'VI', 'en')
    
    print("\n📋 Results:")
    for orig, trans in zip(test_texts, results):
        print(f"  EN: {orig}")
        print(f"  VI: {trans}")
        print()

if __name__ == "__main__":
    test_safe_translation()
