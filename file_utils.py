"""
File utilities với memory optimization và better error handling
"""
import os
import zipfile
import tempfile
import json
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Generator
import logging
from contextlib import contextmanager


class FileError(Exception):
    """Custom exception cho file operations"""
    pass


class MemoryOptimizedZipHandler:
    """Handler cho zip files với memory optimization"""
    
    def __init__(self, max_memory_usage: int = 100 * 1024 * 1024):  # 100MB
        self.max_memory_usage = max_memory_usage
        
    @contextmanager
    def open_zip(self, zip_path: str, mode: str = 'r'):
        """
        Context manager để mở zip file
        
        Args:
            zip_path: Path to zip file
            mode: Open mode ('r', 'w', 'a')
            
        Yields:
            ZipFile object
        """
        zip_file = None
        try:
            zip_file = zipfile.ZipFile(zip_path, mode)
            yield zip_file
        except zipfile.BadZipFile as e:
            raise FileError(f"Invalid zip file: {zip_path}") from e
        except Exception as e:
            raise FileError(f"Failed to open zip file {zip_path}: {str(e)}") from e
        finally:
            if zip_file:
                zip_file.close()
    
    def get_zip_info(self, zip_path: str) -> Dict[str, Any]:
        """
        Lấy thông tin về zip file mà không load toàn bộ vào memory
        
        Args:
            zip_path: Path to zip file
            
        Returns:
            Dict chứa thông tin zip file
        """
        try:
            with self.open_zip(zip_path) as zipf:
                info = {
                    'total_files': len(zipf.namelist()),
                    'total_size': sum(info.file_size for info in zipf.infolist()),
                    'compressed_size': sum(info.compress_size for info in zipf.infolist()),
                    'has_info_json': any(name.endswith('info.json') for name in zipf.namelist()),
                    'locale_files': [name for name in zipf.namelist() 
                                   if name.startswith('locale/en/') and name.endswith('.cfg')]
                }
                return info
        except Exception as e:
            raise FileError(f"Failed to get zip info for {zip_path}: {str(e)}")
    
    def extract_specific_files(self, zip_path: str, file_patterns: List[str], 
                              extract_to: Optional[str] = None) -> List[str]:
        """
        Giải nén chỉ những files cần thiết
        
        Args:
            zip_path: Path to zip file
            file_patterns: List of file patterns to extract
            extract_to: Directory to extract to (temp dir if None)
            
        Returns:
            List of extracted file paths
        """
        if extract_to is None:
            extract_to = tempfile.mkdtemp()
            
        extracted_files = []
        
        try:
            with self.open_zip(zip_path) as zipf:
                for name in zipf.namelist():
                    if any(pattern in name for pattern in file_patterns):
                        try:
                            zipf.extract(name, extract_to)
                            extracted_files.append(os.path.join(extract_to, name))
                        except Exception as e:
                            logging.warning(f"Failed to extract {name}: {e}")
                            
            return extracted_files
        except Exception as e:
            raise FileError(f"Failed to extract files from {zip_path}: {str(e)}")
    
    def read_text_from_zip(self, zip_path: str, file_path: str, 
                          encoding: str = 'utf-8') -> str:
        """
        Đọc text file từ trong zip mà không extract
        
        Args:
            zip_path: Path to zip file
            file_path: Path of file inside zip
            encoding: Text encoding
            
        Returns:
            File content as string
        """
        try:
            with self.open_zip(zip_path) as zipf:
                with zipf.open(file_path) as f:
                    content = f.read()
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        # Fallback encodings
                        for fallback_encoding in ['utf-8-sig', 'latin-1', 'cp1252']:
                            try:
                                return content.decode(fallback_encoding)
                            except UnicodeDecodeError:
                                continue
                        # Last resort
                        return content.decode('utf-8', errors='replace')
        except Exception as e:
            raise FileError(f"Failed to read {file_path} from {zip_path}: {str(e)}")
    
    def stream_zip_contents(self, zip_path: str) -> Generator[Tuple[str, str], None, None]:
        """
        Stream zip contents để tránh load toàn bộ vào memory
        
        Args:
            zip_path: Path to zip file
            
        Yields:
            Tuple of (filename, content)
        """
        try:
            with self.open_zip(zip_path) as zipf:
                for name in zipf.namelist():
                    if not zipf.getinfo(name).is_dir():
                        try:
                            content = self.read_text_from_zip(zip_path, name)
                            yield name, content
                        except Exception as e:
                            logging.warning(f"Failed to read {name}: {e}")
        except Exception as e:
            raise FileError(f"Failed to stream contents from {zip_path}: {str(e)}")


class ModFileProcessor:
    """Processor cho Factorio mod files với memory optimization"""
    
    def __init__(self):
        self.zip_handler = MemoryOptimizedZipHandler()
        
    def find_mod_info(self, zip_path: str) -> Optional[Dict[str, Any]]:
        """
        Tìm và parse info.json từ mod zip
        
        Args:
            zip_path: Path to mod zip file
            
        Returns:
            Dict chứa mod info hoặc None nếu không tìm thấy
        """
        try:
            with self.zip_handler.open_zip(zip_path) as zipf:
                info_files = [name for name in zipf.namelist() if name.endswith('info.json')]
                
                if not info_files:
                    return None
                    
                # Ưu tiên info.json ở root level
                info_file = None
                for name in info_files:
                    if name.count('/') <= 1:  # Root level or first subdirectory
                        info_file = name
                        break
                        
                if not info_file:
                    info_file = info_files[0]  # Fallback to first found
                    
                content = self.zip_handler.read_text_from_zip(zip_path, info_file)
                return json.loads(content)
                
        except Exception as e:
            logging.warning(f"Failed to find mod info in {zip_path}: {e}")
            return None
    
    def find_locale_files(self, zip_path: str) -> List[Tuple[str, str]]:
        """
        Tìm locale files trong mod zip
        
        Args:
            zip_path: Path to mod zip file
            
        Returns:
            List of (file_path, root_folder) tuples
        """
        try:
            with self.zip_handler.open_zip(zip_path) as zipf:
                namelist = zipf.namelist()
                
                # Tìm root folder
                root_folder = None
                for name in namelist:
                    if 'info.json' in name and name.count('/') == 1:
                        root_folder = name.split('/')[0]
                        break
                        
                if not root_folder:
                    # Fallback: tìm folder có chứa locale
                    for name in namelist:
                        if 'locale/' in name:
                            root_folder = name.split('/')[0]
                            break
                            
                if not root_folder:
                    return []
                    
                # Tìm locale files
                search_prefix = f"{root_folder}/locale/en/"
                locale_files = []
                
                for name in namelist:
                    if name.startswith(search_prefix) and name.endswith('.cfg'):
                        locale_files.append((name, root_folder))
                        
                return locale_files
                
        except Exception as e:
            logging.warning(f"Failed to find locale files in {zip_path}: {e}")
            return []
    
    def process_locale_file(self, zip_path: str, locale_file: str) -> Tuple[List[Dict], List[str]]:
        """
        Process một locale file và trích xuất key-value pairs
        
        Args:
            zip_path: Path to mod zip file
            locale_file: Path to locale file inside zip
            
        Returns:
            Tuple of (key_value_pairs, original_lines)
        """
        try:
            content = self.zip_handler.read_text_from_zip(zip_path, locale_file)
            return self.parse_cfg_content(content)
        except Exception as e:
            logging.warning(f"Failed to process locale file {locale_file}: {e}")
            return [], []
    
    def parse_cfg_content(self, content: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse nội dung file .cfg
        
        Args:
            content: File content as string
            
        Returns:
            Tuple of (key_value_pairs, original_lines)
        """
        lines = content.splitlines(keepends=True)
        key_val_pairs = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith(";"):
                try:
                    key, val = stripped.split('=', 1)
                    key_val_pairs.append({
                        'index': i,
                        'key': key.strip(),
                        'val': val.strip()
                    })
                except ValueError:
                    # Skip malformed lines
                    continue
                    
        return key_val_pairs, lines
    
    def create_optimized_zip(self, source_dir: str, output_path: str, 
                           compression_level: int = 6) -> str:
        """
        Tạo zip file với tối ưu compression
        
        Args:
            source_dir: Source directory to zip
            output_path: Output zip file path
            compression_level: Compression level (0-9)
            
        Returns:
            Path to created zip file
        """
        try:
            with zipfile.ZipFile(output_path, 'w', 
                               zipfile.ZIP_DEFLATED, 
                               compresslevel=compression_level) as zipf:
                
                source_path = Path(source_dir)
                for file_path in source_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_path.parent)
                        zipf.write(file_path, arcname)
                        
            return output_path
        except Exception as e:
            raise FileError(f"Failed to create zip {output_path}: {str(e)}")


class TempFileManager:
    """Manager cho temporary files và cleanup"""
    
    def __init__(self):
        self.temp_dirs = []
        self.temp_files = []
        
    def create_temp_dir(self, prefix: str = "factorio_mod_") -> str:
        """
        Tạo temporary directory
        
        Args:
            prefix: Prefix for temp directory name
            
        Returns:
            Path to temp directory
        """
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, suffix: str = ".tmp", prefix: str = "factorio_") -> str:
        """
        Tạo temporary file
        
        Args:
            suffix: File suffix
            prefix: File prefix
            
        Returns:
            Path to temp file
        """
        fd, temp_file = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)  # Close file descriptor
        self.temp_files.append(temp_file)
        return temp_file
    
    def cleanup(self):
        """Cleanup tất cả temporary files và directories"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logging.warning(f"Failed to cleanup temp file {temp_file}: {e}")
                
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logging.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")
                
        self.temp_files.clear()
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup khi object bị destroy"""
        self.cleanup()


# Context manager cho automatic cleanup
@contextmanager
def temp_file_manager():
    """Context manager cho TempFileManager với automatic cleanup"""
    manager = TempFileManager()
    try:
        yield manager
    finally:
        manager.cleanup()
