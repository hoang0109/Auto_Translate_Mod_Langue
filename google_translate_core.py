#!/usr/bin/env python3
"""
Google Translate Core Module
Thay thế DeepL API bằng Google Translate miễn phí
"""
import time
import random
from typing import List, Optional
import requests
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class GoogleTranslateAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://translate.googleapis.com/translate_a/single"
        self.rate_limit_delay = 0.1  # Giây giữa các request
        self.max_chunk_size = 4500  # Kích thước tối đa mỗi chunk
        self.lock = threading.Lock()
        
    def get_language_code(self, lang_code):
        """Chuyển đổi language code"""
        lang_map = {
            'VI': 'vi',
            'JA': 'ja', 
            'EN': 'en',
            'ZH': 'zh',
            'FR': 'fr',
            'DE': 'de',
            'ES': 'es'
        }
        return lang_map.get(lang_code.upper(), lang_code.lower())
    
    def split_text_into_chunks(self, texts, max_size=4500):
        """Chia danh sách text thành các chunks nhỏ hơn"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for text in texts:
            text_size = len(text.encode('utf-8'))
            
            # Nếu text quá lớn, chia nhỏ text đó
            if text_size > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_size = 0
                
                # Chia text lớn thành các phần nhỏ hơn
                words = text.split()
                temp_chunk = []
                temp_size = 0
                
                for word in words:
                    word_size = len(word.encode('utf-8')) + 1  # +1 cho space
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
    
    def translate_chunk(self, texts, target_lang, source_lang='en'):
        """Dịch một chunk văn bản"""
        if not texts:
            return []
            
        try:
            # Tạo request parameters
            combined_text = '\n'.join(texts)
            
            params = {
                'client': 'gtx',
                'sl': source_lang,
                'tl': target_lang,
                'dt': 't',
                'q': combined_text
            }
            
            # Rate limiting
            with self.lock:
                time.sleep(self.rate_limit_delay + random.uniform(0, 0.1))
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Parse JSON response
                result = response.json()
                
                if result and len(result) > 0 and result[0]:
                    # Ghép các phần đã dịch
                    translated_parts = []
                    for part in result[0]:
                        if part and len(part) > 0:
                            translated_parts.append(part[0])
                    
                    translated_text = ''.join(translated_parts)
                    
                    # Tách lại thành các phần riêng lẻ
                    translated_lines = translated_text.split('\n')
                    
                    # Đảm bảo số lượng kết quả khớp với input
                    if len(translated_lines) == len(texts):
                        return translated_lines
                    else:
                        # Nếu không khớp, trả về kết quả gộp cho từng text
                        return [translated_text] * len(texts)
                else:
                    return texts  # Trả về text gốc nếu không dịch được
            else:
                print(f"Google Translate Error: {response.status_code}")
                return texts
                
        except requests.exceptions.RequestException as e:
            print(f"Network error in Google Translate: {e}")
            return texts
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return texts
        except Exception as e:
            print(f"Unexpected error in Google Translate: {e}")
            return texts
    
    def translate_texts(self, texts, target_lang, source_lang='en', progress_callback=None):
        """
        Dịch danh sách văn bản sử dụng Google Translate
        
        Args:
            texts: List of strings to translate
            target_lang: Target language code (VI, JA, etc.)
            source_lang: Source language code (default: 'en')
            progress_callback: Optional callback function for progress updates
        
        Returns:
            List of translated strings
        """
        if not texts:
            return []
        
        # Chuyển đổi language codes
        target_lang = self.get_language_code(target_lang)
        source_lang = self.get_language_code(source_lang)
        
        print(f"🌐 Starting Google Translate: {len(texts)} texts from {source_lang} to {target_lang}")
        
        # Chia nhỏ texts thành chunks
        chunks = self.split_text_into_chunks(texts, self.max_chunk_size)
        print(f"📦 Split into {len(chunks)} chunks for processing")
        
        all_results = []
        processed_texts = 0
        
        # Xử lý từng chunk tuần tự để tránh rate limiting
        for i, chunk in enumerate(chunks):
            try:
                if progress_callback:
                    progress_callback(i, len(chunks), f"Translating chunk {i+1}/{len(chunks)}")
                
                chunk_results = self.translate_chunk(chunk, target_lang, source_lang)
                all_results.extend(chunk_results)
                processed_texts += len(chunk)
                
                print(f"✅ Chunk {i+1}/{len(chunks)}: Translated {len(chunk)} texts")
                
                # Thêm delay giữa các chunks để tránh rate limiting
                if i < len(chunks) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ Error processing chunk {i+1}: {e}")
                all_results.extend(chunk)  # Trả về text gốc nếu lỗi
        
        print(f"🎉 Google Translate completed: {len(all_results)} texts translated")
        return all_results

def test_google_translate():
    """Test function cho Google Translate"""
    translator = GoogleTranslateAPI()
    
    test_texts = [
        "Hello world",
        "This is a test",
        "Factorio is a great game",
        "Iron plate",
        "Copper wire"
    ]
    
    print("🧪 Testing Google Translate...")
    results = translator.translate_texts(test_texts, 'VI', 'en')
    
    print("\n📋 Results:")
    for original, translated in zip(test_texts, results):
        print(f"  EN: {original}")
        print(f"  VI: {translated}")
        print()

if __name__ == "__main__":
    test_google_translate()
