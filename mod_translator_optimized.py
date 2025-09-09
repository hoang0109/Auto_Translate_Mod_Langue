"""
Optimized Factorio Mod Translator với improved architecture
"""
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Import các modules đã tối ưu
from network_utils import DeepLAPI, APIError
from file_utils import ModFileProcessor, temp_file_manager, FileError
from logger_config import get_logger, get_logger_manager


class TranslationStatus(Enum):
    """Enum cho trạng thái dịch thuật"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ModInfo:
    """Dataclass cho thông tin mod"""
    name: str
    zip_path: str
    version: str = ""
    title: str = ""
    author: str = ""
    locale_files: List[str] = None
    status: TranslationStatus = TranslationStatus.PENDING
    error_message: str = ""
    
    def __post_init__(self):
        if self.locale_files is None:
            self.locale_files = []


@dataclass
class TranslationConfig:
    """Configuration cho translation process"""
    api_key: str
    target_language: str
    endpoint: str = "api-free.deepl.com"
    max_batch_size: int = 50
    max_retries: int = 3
    timeout: int = 30
    glossary_id: Optional[str] = None


@dataclass
class TranslationResult:
    """Kết quả của translation process"""
    total_mods: int = 0
    successful_mods: int = 0
    failed_mods: int = 0
    skipped_mods: int = 0
    duration: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ModTranslatorCore:
    """Core class cho mod translation với optimized architecture"""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.logger = get_logger("ModTranslatorCore")
        self.logger_manager = get_logger_manager()
        
        # Initialize components
        self.api_client = DeepLAPI(
            api_key=config.api_key,
            endpoint=config.endpoint,
            max_batch_size=config.max_batch_size
        )
        self.file_processor = ModFileProcessor()
        
        # Progress tracking
        self.progress_callback: Optional[Callable] = None
        self.should_cancel = False
        
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback function cho progress updates"""
        self.progress_callback = callback
    
    def cancel_translation(self):
        """Cancel translation process"""
        self.should_cancel = True
        self.logger.info("Translation cancellation requested")
    
    def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate DeepL API key và lấy usage info
        
        Returns:
            Dict chứa validation result và usage info
        
        Raises:
            APIError: If validation fails
        """
        try:
            self.logger.info("Validating DeepL API key...")
            usage_info = self.api_client.test_api_key()
            
            self.logger_manager.log_api_usage(
                usage_info.get('character_count', 0),
                usage_info.get('character_limit', 0)
            )
            
            self.logger.info("API key validation successful")
            return {
                'valid': True,
                'usage_info': usage_info
            }
            
        except APIError as e:
            self.logger.error(f"API key validation failed: {e}")
            return {
                'valid': False,
                'error': str(e),
                'status_code': getattr(e, 'status_code', None)
            }
    
    def analyze_mods(self, mod_paths: List[str]) -> List[ModInfo]:
        """
        Analyze danh sách mod files và trích xuất thông tin
        
        Args:
            mod_paths: List of paths to mod zip files
            
        Returns:
            List of ModInfo objects
        """
        self.logger.info(f"Analyzing {len(mod_paths)} mod files...")
        mods_info = []
        
        for mod_path in mod_paths:
            try:
                self.logger.debug(f"Analyzing mod: {mod_path}")
                
                # Get basic info
                mod_info_data = self.file_processor.find_mod_info(mod_path)
                if not mod_info_data:
                    self.logger.warning(f"No info.json found in {mod_path}")
                    continue
                
                # Find locale files
                locale_files = self.file_processor.find_locale_files(mod_path)
                if not locale_files:
                    self.logger.warning(f"No locale files found in {mod_path}")
                    continue
                
                # Create ModInfo
                mod_info = ModInfo(
                    name=mod_info_data.get('name', 'unknown'),
                    zip_path=mod_path,
                    version=mod_info_data.get('version', ''),
                    title=mod_info_data.get('title', ''),
                    author=mod_info_data.get('author', ''),
                    locale_files=[file_path for file_path, _ in locale_files]
                )
                
                mods_info.append(mod_info)
                self.logger.debug(f"Successfully analyzed mod: {mod_info.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to analyze mod {mod_path}: {e}")
                continue
        
        self.logger.info(f"Successfully analyzed {len(mods_info)} mods")
        return mods_info
    
    def translate_mods(self, mods_info: List[ModInfo]) -> TranslationResult:
        """
        Translate danh sách mods
        
        Args:
            mods_info: List of ModInfo objects to translate
            
        Returns:
            TranslationResult object
        """
        start_time = time.time()
        result = TranslationResult(total_mods=len(mods_info))
        
        self.logger_manager.log_translation_start(
            len(mods_info),
            self.config.target_language,
            self.config.endpoint
        )
        
        for i, mod_info in enumerate(mods_info):
            if self.should_cancel:
                self.logger.info("Translation cancelled by user")
                break
                
            try:
                # Update progress
                if self.progress_callback:
                    self.progress_callback(i + 1, len(mods_info), mod_info.name)
                
                self.logger_manager.log_translation_progress(i + 1, len(mods_info), mod_info.name)
                
                # Translate single mod
                success = self._translate_single_mod(mod_info)
                
                if success:
                    mod_info.status = TranslationStatus.SUCCESS
                    result.successful_mods += 1
                    self.logger.info(f"Successfully translated mod: {mod_info.name}")
                else:
                    mod_info.status = TranslationStatus.FAILED
                    result.failed_mods += 1
                    result.errors.append(f"{mod_info.name}: {mod_info.error_message}")
                    
            except Exception as e:
                mod_info.status = TranslationStatus.FAILED
                mod_info.error_message = str(e)
                result.failed_mods += 1
                result.errors.append(f"{mod_info.name}: {str(e)}")
                self.logger.error(f"Failed to translate mod {mod_info.name}: {e}")
        
        result.duration = time.time() - start_time
        
        self.logger_manager.log_translation_complete(
            result.successful_mods,
            result.failed_mods,
            result.duration
        )
        
        return result
    
    def _translate_single_mod(self, mod_info: ModInfo) -> bool:
        """
        Translate một mod duy nhất
        
        Args:
            mod_info: ModInfo object to translate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            mod_info.status = TranslationStatus.PROCESSING
            
            # Collect all texts từ tất cả locale files
            all_texts = []
            file_entries = []
            
            for locale_file in mod_info.locale_files:
                try:
                    key_vals, original_lines = self.file_processor.process_locale_file(
                        mod_info.zip_path, locale_file
                    )
                    
                    if key_vals:
                        file_entries.append((locale_file, key_vals, original_lines))
                        all_texts.extend([item['val'] for item in key_vals])
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process locale file {locale_file}: {e}")
                    continue
            
            if not all_texts:
                mod_info.error_message = "No texts found to translate"
                return False
            
            # Translate texts using optimized API client
            try:
                translated_texts = self.api_client.translate_texts_batch(
                    all_texts,
                    self.config.target_language,
                    self.config.glossary_id
                )
                
                if len(translated_texts) != len(all_texts):
                    mod_info.error_message = f"Translation count mismatch: {len(translated_texts)}/{len(all_texts)}"
                    return False
                    
            except APIError as e:
                mod_info.error_message = f"API Error: {str(e)}"
                return False
            
            # Save translated content
            return self._save_translated_mod(mod_info, file_entries, translated_texts)
            
        except Exception as e:
            mod_info.error_message = str(e)
            self.logger.error(f"Error translating mod {mod_info.name}: {e}")
            return False
    
    def _save_translated_mod(self, mod_info: ModInfo, file_entries: List, translated_texts: List[str]) -> bool:
        """
        Save translated mod content
        
        Args:
            mod_info: ModInfo object
            file_entries: List of (locale_file, key_vals, original_lines)
            translated_texts: List of translated texts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create output directory structure
            output_base = Path("Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0")
            output_locale_dir = output_base / "locale" / self.config.target_language.lower()
            output_locale_dir.mkdir(parents=True, exist_ok=True)
            
            # Combine all translated content into single file
            all_translated_lines = []
            translated_iter = iter(translated_texts)
            
            for locale_file, key_vals, original_lines in file_entries:
                translated_lines = original_lines[:]
                
                for item in key_vals:
                    try:
                        translated_val = next(translated_iter)
                        translated_lines[item['index']] = f"{item['key']}={translated_val}\\n"
                    except StopIteration:
                        break
                
                all_translated_lines.extend(translated_lines)
            
            # Save to output file
            output_file = output_locale_dir / f"{mod_info.name}.cfg"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(all_translated_lines)
            
            self.logger_manager.log_file_operation(
                "CREATE", str(output_file), True, f"Translated mod: {mod_info.name}"
            )
            
            return True
            
        except Exception as e:
            mod_info.error_message = f"Failed to save translated content: {str(e)}"
            self.logger_manager.log_file_operation(
                "CREATE", f"mod_{mod_info.name}.cfg", False, str(e)
            )
            return False
    
    def update_language_pack_info(self, successful_mods: List[str]) -> bool:
        """
        Update info.json của language pack với mods đã dịch
        
        Args:
            successful_mods: List of successfully translated mod names
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            from datetime import datetime
            
            info_path = Path("Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0/info.json")
            
            if info_path.exists():
                with open(info_path, 'r', encoding='utf-8') as f:
                    info_data = json.load(f)
            else:
                info_data = {}
            
            # Update version
            old_version = info_data.get("version", "1.0.0")
            version_parts = old_version.split('.')
            if len(version_parts) >= 3:
                try:
                    patch = int(version_parts[2]) + 1
                    new_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"
                except ValueError:
                    new_version = datetime.now().strftime('%Y.%m.%d')
            else:
                new_version = datetime.now().strftime('%Y.%m.%d')
            
            # Update info
            info_data.update({
                "name": f"Auto_Translate_Mod_Langue_Vietnamese_{new_version}",
                "version": new_version,
                "title": "Factorio Mods Vietnamese Language Pack",
                "author": "Hoang0109 - hoang0109@gmail.com",
                "description": f"Vietnamese translation pack for Factorio mods. Includes: {', '.join(successful_mods)}. Auto-translated using DeepL.",
                "factorio_version": "2.0"
            })
            
            # Update dependencies
            current_deps = set()
            for dep in info_data.get("dependencies", []):
                dep_name = dep.strip().lstrip('?').strip()
                current_deps.add(dep_name)
            
            for mod_name in successful_mods:
                current_deps.add(mod_name)
            
            info_data["dependencies"] = [f"? {mod}" for mod in sorted(current_deps)]
            
            # Save updated info
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, ensure_ascii=False, indent=2)
            
            self.logger_manager.log_file_operation("UPDATE", str(info_path), True)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update language pack info: {e}")
            return False
    
    def create_language_pack_zip(self, version: str) -> Optional[str]:
        """
        Create zip file của language pack
        
        Args:
            version: Version string for zip file
            
        Returns:
            Path to created zip file, None if failed
        """
        try:
            source_dir = Path("Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0")
            zip_path = f"output/Auto_Translate_Mod_Langue_Vietnamese_{version}.zip"
            
            Path("output").mkdir(exist_ok=True)
            
            created_zip = self.file_processor.create_optimized_zip(
                str(source_dir), zip_path
            )
            
            self.logger_manager.log_file_operation("CREATE", created_zip, True, f"Language pack v{version}")
            return created_zip
            
        except Exception as e:
            self.logger.error(f"Failed to create language pack zip: {e}")
            return None


# Factory function để tạo ModTranslatorCore instance
def create_translator(api_key: str, target_language: str, endpoint: str = "api-free.deepl.com", 
                     **kwargs) -> ModTranslatorCore:
    """
    Factory function để tạo ModTranslatorCore instance
    
    Args:
        api_key: DeepL API key
        target_language: Target language code
        endpoint: DeepL endpoint
        **kwargs: Additional config parameters
        
    Returns:
        ModTranslatorCore instance
    """
    config = TranslationConfig(
        api_key=api_key,
        target_language=target_language,
        endpoint=endpoint,
        **kwargs
    )
    return ModTranslatorCore(config)
