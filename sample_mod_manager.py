"""
Sample Mod Manager cho Factorio Mod Translator
Quản lý các mod mẫu, version và chỉnh sửa mod
"""
import os
import re
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from file_utils import ModFileProcessor, temp_file_manager
from logger_config import get_logger


class VersionType(Enum):
    """Enum cho loại version update"""
    MAJOR = "major"      # 1.0.0 -> 2.0.0
    MINOR = "minor"      # 1.0.0 -> 1.1.0  
    PATCH = "patch"      # 1.0.0 -> 1.0.1


@dataclass
class SampleModInfo:
    """Thông tin về sample mod"""
    name: str
    version: str
    title: str
    author: str
    description: str
    zip_path: str
    factorio_version: str = "2.0"
    dependencies: List[str] = None
    locale_files: List[str] = None
    last_modified: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.locale_files is None:
            self.locale_files = []


class ModVersionManager:
    """Quản lý version của mod"""
    
    def __init__(self):
        self.logger = get_logger("ModVersionManager")
    
    def parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """
        Parse version string thành tuple (major, minor, patch)
        
        Args:
            version_str: Version string (e.g., "1.0.1")
            
        Returns:
            Tuple (major, minor, patch)
        """
        try:
            # Remove any non-digit characters except dots
            clean_version = re.sub(r'[^\d.]', '', version_str)
            parts = clean_version.split('.')
            
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            return (major, minor, patch)
        except (ValueError, IndexError):
            self.logger.warning(f"Invalid version format: {version_str}, defaulting to (1, 0, 0)")
            return (1, 0, 0)
    
    def version_to_string(self, major: int, minor: int, patch: int) -> str:
        """Chuyển tuple version thành string"""
        return f"{major}.{minor}.{patch}"
    
    def increment_version(self, version_str: str, version_type: VersionType) -> str:
        """
        Tăng version theo type
        
        Args:
            version_str: Version hiện tại
            version_type: Loại version update
            
        Returns:
            Version string mới
        """
        major, minor, patch = self.parse_version(version_str)
        
        if version_type == VersionType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif version_type == VersionType.MINOR:
            minor += 1
            patch = 0
        elif version_type == VersionType.PATCH:
            patch += 1
        
        new_version = self.version_to_string(major, minor, patch)
        self.logger.info(f"Incremented version: {version_str} -> {new_version} ({version_type.value})")
        return new_version
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        So sánh 2 versions
        
        Returns:
            1 if version1 > version2
            0 if version1 == version2  
            -1 if version1 < version2
        """
        v1_tuple = self.parse_version(version1)
        v2_tuple = self.parse_version(version2)
        
        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0
    
    def suggest_next_version(self, current_version: str, has_major_changes: bool = False, 
                           has_minor_changes: bool = True) -> str:
        """
        Gợi ý version tiếp theo dựa trên loại thay đổi
        
        Args:
            current_version: Version hiện tại
            has_major_changes: Có thay đổi major không
            has_minor_changes: Có thay đổi minor không
            
        Returns:
            Suggested version string
        """
        if has_major_changes:
            return self.increment_version(current_version, VersionType.MAJOR)
        elif has_minor_changes:
            return self.increment_version(current_version, VersionType.MINOR)
        else:
            return self.increment_version(current_version, VersionType.PATCH)


class ModEditor:
    """Class để chỉnh sửa mod files"""
    
    def __init__(self):
        self.logger = get_logger("ModEditor")
        self.file_processor = ModFileProcessor()
        self.version_manager = ModVersionManager()
    
    def update_info_json(self, info_data: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cập nhật info.json với thông tin mới
        
        Args:
            info_data: Current info.json data
            updates: Dictionary với thông tin cần update
            
        Returns:
            Updated info.json data
        """
        updated_info = info_data.copy()
        
        for key, value in updates.items():
            if key == "dependencies" and isinstance(value, list):
                # Merge dependencies, remove duplicates
                existing_deps = set(updated_info.get("dependencies", []))
                new_deps = set(value)
                updated_info["dependencies"] = list(existing_deps.union(new_deps))
            else:
                updated_info[key] = value
        
        # Update timestamp trong description nếu có
        if "description" in updated_info:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            if "updated" not in updated_info["description"].lower():
                updated_info["description"] += f" (Updated: {timestamp})"
        
        self.logger.info(f"Updated info.json: {list(updates.keys())}")
        return updated_info
    
    def add_locale_files(self, mod_zip_path: str, locale_files: Dict[str, str], 
                        target_language: str = "vi") -> str:
        """
        Thêm locale files vào mod
        
        Args:
            mod_zip_path: Path to original mod zip
            locale_files: Dict mapping filename -> content
            target_language: Target language code
            
        Returns:
            Path to new mod zip
        """
        with temp_file_manager() as temp_mgr:
            # Extract original mod
            extract_dir = temp_mgr.create_temp_dir()
            with zipfile.ZipFile(mod_zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # Find mod root directory
            mod_dirs = [d for d in os.listdir(extract_dir) 
                       if os.path.isdir(os.path.join(extract_dir, d))]
            if not mod_dirs:
                raise ValueError("No mod directory found in zip")
            
            mod_root = os.path.join(extract_dir, mod_dirs[0])
            locale_dir = os.path.join(mod_root, "locale", target_language)
            os.makedirs(locale_dir, exist_ok=True)
            
            # Add new locale files
            for filename, content in locale_files.items():
                if not filename.endswith('.cfg'):
                    filename += '.cfg'
                
                file_path = os.path.join(locale_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.info(f"Added locale file: {filename}")
            
            # Create new zip
            new_zip_path = temp_mgr.create_temp_file(suffix=".zip")
            with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, extract_dir)
                        zipf.write(file_path, arcname)
            
            return new_zip_path
    
    def create_new_mod_version(self, original_zip: str, updates: Dict[str, Any],
                              new_locale_files: Dict[str, str] = None,
                              version_type: VersionType = VersionType.MINOR) -> str:
        """
        Tạo phiên bản mới của mod
        
        Args:
            original_zip: Path to original mod zip
            updates: Updates for info.json
            new_locale_files: New locale files to add
            version_type: Type of version increment
            
        Returns:
            Path to new mod zip
        """
        with temp_file_manager() as temp_mgr:
            # Extract original mod
            extract_dir = temp_mgr.create_temp_dir()
            with zipfile.ZipFile(original_zip, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # Find mod root
            mod_dirs = [d for d in os.listdir(extract_dir) 
                       if os.path.isdir(os.path.join(extract_dir, d))]
            if not mod_dirs:
                raise ValueError("No mod directory found")
            
            mod_root = os.path.join(extract_dir, mod_dirs[0])
            info_path = os.path.join(mod_root, "info.json")
            
            # Load and update info.json
            with open(info_path, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
            
            # Increment version
            current_version = info_data.get('version', '1.0.0')
            new_version = self.version_manager.increment_version(current_version, version_type)
            updates['version'] = new_version
            
            # Update mod name to include new version
            old_name = info_data.get('name', 'mod')
            if '_' in old_name and old_name.split('_')[-1].replace('.', '').isdigit():
                # Remove old version from name
                base_name = '_'.join(old_name.split('_')[:-1])
            else:
                base_name = old_name
            
            new_name = f"{base_name}_{new_version.replace('.', '')}"
            updates['name'] = new_name
            
            # Apply updates
            updated_info = self.update_info_json(info_data, updates)
            
            # Write updated info.json
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(updated_info, f, indent=2, ensure_ascii=False)
            
            # Add new locale files if provided
            if new_locale_files:
                locale_dir = os.path.join(mod_root, "locale", "vi")
                os.makedirs(locale_dir, exist_ok=True)
                
                for filename, content in new_locale_files.items():
                    if not filename.endswith('.cfg'):
                        filename += '.cfg'
                    
                    file_path = os.path.join(locale_dir, filename)
                    
                    # If file exists, merge content
                    existing_content = ""
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing_content = f.read()
                    
                    # Merge content (simple append for now)
                    merged_content = existing_content
                    if content and content not in existing_content:
                        if existing_content and not existing_content.endswith('\n'):
                            merged_content += '\n'
                        merged_content += content
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(merged_content)
            
            # Rename mod directory to match new name
            new_mod_root = os.path.join(extract_dir, new_name)
            if mod_root != new_mod_root:
                os.rename(mod_root, new_mod_root)
            
            # Create new zip
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            
            new_zip_path = os.path.join(output_dir, f"{new_name}.zip")
            with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(new_mod_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, extract_dir)
                        zipf.write(file_path, arcname)
            
            self.logger.info(f"Created new mod version: {new_zip_path}")
            return new_zip_path


class SampleModManager:
    """Manager cho sample mods"""
    
    def __init__(self, sample_dir: str = "Code mau"):
        self.sample_dir = Path(sample_dir)
        self.logger = get_logger("SampleModManager")
        self.file_processor = ModFileProcessor()
        self.mod_editor = ModEditor()
        self.version_manager = ModVersionManager()
    
    def scan_sample_mods(self) -> List[SampleModInfo]:
        """
        Scan thư mục sample và trả về list các sample mods
        
        Returns:
            List of SampleModInfo objects
        """
        sample_mods = []
        
        if not self.sample_dir.exists():
            self.logger.warning(f"Sample directory not found: {self.sample_dir}")
            return sample_mods
        
        # Scan zip files
        zip_files = list(self.sample_dir.glob("*.zip"))
        
        for zip_path in zip_files:
            try:
                mod_info = self.analyze_sample_mod(str(zip_path))
                if mod_info:
                    sample_mods.append(mod_info)
            except Exception as e:
                self.logger.error(f"Failed to analyze sample mod {zip_path}: {e}")
        
        self.logger.info(f"Found {len(sample_mods)} sample mods")
        return sample_mods
    
    def analyze_sample_mod(self, zip_path: str) -> Optional[SampleModInfo]:
        """
        Phân tích sample mod và trả về thông tin
        
        Args:
            zip_path: Path to sample mod zip
            
        Returns:
            SampleModInfo object hoặc None nếu fail
        """
        try:
            # Get basic info
            info_data = self.file_processor.find_mod_info(zip_path)
            if not info_data:
                return None
            
            # Get locale files
            locale_files = self.file_processor.find_locale_files(zip_path)
            locale_file_names = [os.path.basename(file_path) for file_path, _ in locale_files]
            
            # Get file modification time
            stat_info = os.stat(zip_path)
            last_modified = datetime.fromtimestamp(stat_info.st_mtime)
            
            sample_mod = SampleModInfo(
                name=info_data.get('name', ''),
                version=info_data.get('version', '1.0.0'),
                title=info_data.get('title', ''),
                author=info_data.get('author', ''),
                description=info_data.get('description', ''),
                factorio_version=info_data.get('factorio_version', '2.0'),
                dependencies=info_data.get('dependencies', []),
                zip_path=zip_path,
                locale_files=locale_file_names,
                last_modified=last_modified
            )
            
            self.logger.debug(f"Analyzed sample mod: {sample_mod.name} v{sample_mod.version}")
            return sample_mod
            
        except Exception as e:
            self.logger.error(f"Failed to analyze sample mod {zip_path}: {e}")
            return None
    
    def get_latest_version_mod(self, name_pattern: str) -> Optional[SampleModInfo]:
        """
        Lấy mod với version cao nhất matching pattern
        
        Args:
            name_pattern: Pattern to match mod name
            
        Returns:
            SampleModInfo with highest version
        """
        sample_mods = self.scan_sample_mods()
        matching_mods = [mod for mod in sample_mods if name_pattern.lower() in mod.name.lower()]
        
        if not matching_mods:
            return None
        
        # Sort by version (descending)
        latest_mod = max(matching_mods, 
                        key=lambda mod: self.version_manager.parse_version(mod.version))
        
        self.logger.info(f"Latest version mod for '{name_pattern}': {latest_mod.name} v{latest_mod.version}")
        return latest_mod
    
    def create_enhanced_mod(self, base_mod_info: SampleModInfo, 
                          additional_translations: Dict[str, str] = None,
                          new_dependencies: List[str] = None,
                          version_type: VersionType = VersionType.MINOR) -> str:
        """
        Tạo enhanced version của sample mod
        
        Args:
            base_mod_info: Base sample mod info
            additional_translations: Additional locale files
            new_dependencies: New dependencies to add
            version_type: Version increment type
            
        Returns:
            Path to new enhanced mod zip
        """
        updates = {}
        
        # Add new dependencies if provided
        if new_dependencies:
            existing_deps = base_mod_info.dependencies.copy()
            for dep in new_dependencies:
                if dep not in existing_deps:
                    existing_deps.append(dep)
            updates['dependencies'] = existing_deps
        
        # Update description
        current_desc = base_mod_info.description
        timestamp = datetime.now().strftime("%Y-%m-%d")
        updates['description'] = f"{current_desc} (Enhanced: {timestamp})"
        
        # Create new version
        new_zip_path = self.mod_editor.create_new_mod_version(
            base_mod_info.zip_path,
            updates,
            additional_translations or {},
            version_type
        )
        
        self.logger.info(f"Created enhanced mod: {new_zip_path}")
        return new_zip_path
    
    def load_sample_translations(self, mod_info: SampleModInfo, 
                               target_language: str = "vi") -> Dict[str, str]:
        """
        Load existing translations từ sample mod
        
        Args:
            mod_info: Sample mod info
            target_language: Target language code
            
        Returns:
            Dict mapping filename -> content
        """
        translations = {}
        
        try:
            with zipfile.ZipFile(mod_info.zip_path, 'r') as zipf:
                # Find locale files for target language
                locale_pattern = f"locale/{target_language}/"
                
                for file_info in zipf.infolist():
                    if (file_info.filename.startswith(locale_pattern) and 
                        file_info.filename.endswith('.cfg')):
                        
                        filename = os.path.basename(file_info.filename)
                        content = zipf.read(file_info.filename).decode('utf-8')
                        translations[filename] = content
            
            self.logger.info(f"Loaded {len(translations)} translation files from {mod_info.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load translations from {mod_info.zip_path}: {e}")
        
        return translations
