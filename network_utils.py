"""
Network utilities với retry mechanism và error handling cải tiến
"""
import time
import requests
from typing import List, Optional, Dict, Any
import logging


class APIError(Exception):
    """Custom exception cho API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class NetworkUtils:
    """Utility class cho network operations với retry mechanism"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, timeout: int = 30):
        self.max_retries = max_retries
        self.retry_delay = retry_delay  
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Factorio-Mod-Translator/2.0'
        })
        
    def make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Thực hiện request với retry mechanism
        
        Args:
            method: HTTP method ('GET', 'POST', etc.)
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response object
            
        Raises:
            APIError: If all retries fail
        """
        kwargs.setdefault('timeout', self.timeout)
        
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Kiểm tra rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    if attempt < self.max_retries:
                        logging.warning(f"Rate limited. Waiting {retry_after}s before retry {attempt + 1}")
                        time.sleep(retry_after)
                        continue
                        
                # Các status code có thể retry
                if response.status_code in [500, 502, 503, 504] and attempt < self.max_retries:
                    logging.warning(f"Server error {response.status_code}. Retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                    
                return response
                
            except (requests.exceptions.ConnectionError, 
                   requests.exceptions.Timeout,
                   requests.exceptions.RequestException) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logging.warning(f"Network error: {e}. Retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                    
        # Nếu tất cả retry đều fail
        if last_exception:
            raise APIError(f"Network request failed after {self.max_retries} retries: {last_exception}")
        else:
            raise APIError(f"Request failed with status {response.status_code}", response.status_code)


class DeepLAPI:
    """Optimized DeepL API client với batch processing và error handling"""
    
    def __init__(self, api_key: str, endpoint: str = "api-free.deepl.com", max_batch_size: int = 50):
        self.api_key = api_key
        self.endpoint = endpoint
        self.max_batch_size = max_batch_size
        self.network = NetworkUtils()
        self.base_url = f"https://{endpoint}/v2"
        
    def test_api_key(self) -> Dict[str, Any]:
        """
        Test API key và lấy thông tin usage
        
        Returns:
            Dict chứa usage information
            
        Raises:
            APIError: If API key is invalid
        """
        try:
            response = self.network.make_request_with_retry(
                'GET', 
                f"{self.base_url}/usage",
                params={"auth_key": self.api_key}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                raise APIError(
                    error_data.get("message", "Unknown API error"),
                    response.status_code,
                    error_data
                )
                
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to test API key: {str(e)}")
    
    def translate_texts_batch(self, texts: List[str], target_lang: str, 
                            glossary_id: Optional[str] = None,
                            progress_callback: Optional[callable] = None) -> List[str]:
        """
        Dịch danh sách texts với batch processing
        
        Args:
            texts: List of texts to translate
            target_lang: Target language code
            glossary_id: Optional glossary ID
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of translated texts
            
        Raises:
            APIError: If translation fails
        """
        if not texts:
            return []
            
        all_translations = []
        total_batches = (len(texts) + self.max_batch_size - 1) // self.max_batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.max_batch_size
            end_idx = min(start_idx + self.max_batch_size, len(texts))
            batch_texts = texts[start_idx:end_idx]
            
            try:
                translations = self._translate_batch(batch_texts, target_lang, glossary_id)
                all_translations.extend(translations)
                
                # Progress callback
                if progress_callback:
                    progress_callback(batch_idx + 1, total_batches, len(all_translations))
                    
            except Exception as e:
                logging.error(f"Failed to translate batch {batch_idx + 1}/{total_batches}: {e}")
                # Fallback: add original texts
                all_translations.extend(batch_texts)
                
        return all_translations
    
    def _translate_batch(self, texts: List[str], target_lang: str, 
                        glossary_id: Optional[str] = None) -> List[str]:
        """
        Dịch một batch texts
        
        Args:
            texts: List of texts to translate  
            target_lang: Target language code
            glossary_id: Optional glossary ID
            
        Returns:
            List of translated texts
            
        Raises:
            APIError: If translation fails
        """
        data = {
            "auth_key": self.api_key,
            "text": texts,
            "target_lang": target_lang,
            "tag_handling": "xml"
        }
        
        if glossary_id:
            data["glossary_id"] = glossary_id
            
        try:
            response = self.network.make_request_with_retry(
                'POST',
                f"{self.base_url}/translate", 
                data=data
            )
            
            if response.status_code == 200:
                response_data = response.json()
                translations = [item["text"] for item in response_data.get("translations", [])]
                
                if len(translations) != len(texts):
                    raise APIError(f"Translation count mismatch: expected {len(texts)}, got {len(translations)}")
                    
                return translations
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                raise APIError(
                    error_data.get("message", f"Translation failed with status {response.status_code}"),
                    response.status_code,
                    error_data
                )
                
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to translate batch: {str(e)}")
    
    def get_supported_languages(self) -> Dict[str, List[Dict]]:
        """
        Lấy danh sách ngôn ngữ được hỗ trợ
        
        Returns:
            Dict with source and target languages
        """
        try:
            response = self.network.make_request_with_retry(
                'GET',
                f"{self.base_url}/languages",
                params={"auth_key": self.api_key}
            )
            
            if response.status_code == 200:
                return {"languages": response.json()}
            else:
                logging.warning(f"Failed to get supported languages: {response.status_code}")
                return {"languages": []}
                
        except Exception as e:
            logging.warning(f"Failed to get supported languages: {e}")
            return {"languages": []}
