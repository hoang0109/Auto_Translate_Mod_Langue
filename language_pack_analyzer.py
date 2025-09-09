"""
Language Pack Analyzer - Phân tích các language pack đã tạo
"""
import os
import json
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from file_utils import MemoryOptimizedZipHandler, FileError
from logger_config import get_logger


@dataclass
class LanguagePackInfo:
    """Thông tin về language pack"""
    zip_path: str
    name: str = ""
    version: str = ""
    title: str = ""
    author: str = ""
    description: str = ""
    factorio_version: str = ""
    dependencies: List[str] = None
    translated_mods: List[str] = None
    file_size: int = 0
    creation_date: Optional[datetime] = None
    locale_files_count: int = 0
    total_translations: int = 0
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.translated_mods is None:
            self.translated_mods = []


@dataclass 
class ModTranslationInfo:
    """Thông tin dịch thuật của một mod"""
    mod_name: str
    locale_file: str
    translations_count: int = 0
    sections: List[str] = None
    sample_translations: Dict[str, str] = None
    
    def __post_init__(self):
        if self.sections is None:
            self.sections = []
        if self.sample_translations is None:
            self.sample_translations = {}


class LanguagePackAnalyzer:
    """Analyzer cho language packs"""
    
    def __init__(self):
        self.logger = get_logger("LanguagePackAnalyzer")
        self.zip_handler = MemoryOptimizedZipHandler()
        
    def find_language_packs(self, search_dirs: List[str] = None) -> List[str]:
        """
        Tìm tất cả language pack files
        
        Args:
            search_dirs: List of directories to search in
            
        Returns:
            List of language pack zip file paths
        """
        if search_dirs is None:
            search_dirs = ["output", ".", "Code mau"]
            
        pack_files = []
        pattern = "Auto_Translate_Mod_Langue_Vietnamese_"
        
        for search_dir in search_dirs:
            search_path = Path(search_dir)
            if not search_path.exists():
                continue
                
            # Tìm zip files
            for zip_file in search_path.glob("*.zip"):
                if pattern in zip_file.name:
                    pack_files.append(str(zip_file.absolute()))
                    
        # Sort by version (newest first)
        pack_files.sort(key=self._extract_version_from_filename, reverse=True)
        
        self.logger.info(f"Found {len(pack_files)} language pack files")
        return pack_files
    
    def _extract_version_from_filename(self, filename: str) -> Tuple[int, int, int]:
        """Extract version từ filename để sort"""
        try:
            basename = Path(filename).stem
            # Extract version from "Auto_Translate_Mod_Langue_Vietnamese_x.y.z"
            parts = basename.split("_")
            if len(parts) >= 4:
                version_str = parts[-1]  # Get last part (version)
                version_parts = version_str.split(".")
                return tuple(int(p) for p in version_parts[:3])
        except Exception:
            pass
        return (0, 0, 0)
    
    def analyze_language_pack(self, zip_path: str) -> LanguagePackInfo:
        """
        Phân tích chi tiết một language pack
        
        Args:
            zip_path: Path to language pack zip file
            
        Returns:
            LanguagePackInfo object
        """
        self.logger.info(f"Analyzing language pack: {zip_path}")
        
        pack_info = LanguagePackInfo(zip_path=zip_path)
        
        try:
            # Get basic file info
            pack_info.file_size = Path(zip_path).stat().st_size
            pack_info.creation_date = datetime.fromtimestamp(Path(zip_path).stat().st_mtime)
            
            with self.zip_handler.open_zip(zip_path) as zipf:
                namelist = zipf.namelist()
                
                # Find and parse info.json
                info_json_path = self._find_info_json(namelist)
                if info_json_path:
                    info_data = self._parse_info_json(zipf, info_json_path)
                    self._populate_basic_info(pack_info, info_data)
                
                # Analyze locale files
                locale_files = self._find_locale_files(namelist)
                pack_info.locale_files_count = len(locale_files)
                pack_info.translated_mods = self._extract_mod_names_from_locale_files(locale_files)
                
                # Count total translations
                pack_info.total_translations = self._count_total_translations(zipf, locale_files)
                
        except Exception as e:
            self.logger.error(f"Failed to analyze language pack {zip_path}: {e}")
            pack_info.name = f"Error analyzing: {Path(zip_path).name}"
            
        return pack_info
    
    def _find_info_json(self, namelist: List[str]) -> Optional[str]:
        """Tìm info.json file trong zip"""
        for name in namelist:
            if name.endswith('info.json') and name.count('/') <= 1:
                return name
        return None
    
    def _parse_info_json(self, zipf: zipfile.ZipFile, info_path: str) -> Dict[str, Any]:
        """Parse info.json content"""
        try:
            content = self.zip_handler.read_text_from_zip(zipf.filename, info_path)
            return json.loads(content)
        except Exception as e:
            self.logger.warning(f"Failed to parse info.json: {e}")
            return {}
    
    def _populate_basic_info(self, pack_info: LanguagePackInfo, info_data: Dict[str, Any]):
        """Populate basic info from info.json data"""
        pack_info.name = info_data.get("name", "")
        pack_info.version = info_data.get("version", "")
        pack_info.title = info_data.get("title", "")
        pack_info.author = info_data.get("author", "")
        pack_info.description = info_data.get("description", "")
        pack_info.factorio_version = info_data.get("factorio_version", "")
        
        # Parse dependencies
        dependencies = info_data.get("dependencies", [])
        pack_info.dependencies = []
        for dep in dependencies:
            dep_name = dep.strip().lstrip('?').strip()
            if dep_name:
                pack_info.dependencies.append(dep_name)
    
    def _find_locale_files(self, namelist: List[str]) -> List[str]:
        """Tìm tất cả locale files trong zip"""
        locale_files = []
        for name in namelist:
            if '/locale/' in name and name.endswith('.cfg'):
                locale_files.append(name)
        return locale_files
    
    def _extract_mod_names_from_locale_files(self, locale_files: List[str]) -> List[str]:
        """Extract mod names từ locale file paths"""
        mod_names = set()
        for file_path in locale_files:
            # Extract mod name from path like "folder/locale/vi/mod_name.cfg"
            filename = Path(file_path).stem
            if filename:
                mod_names.add(filename)
        return sorted(list(mod_names))
    
    def _count_total_translations(self, zipf: zipfile.ZipFile, locale_files: List[str]) -> int:
        """Đếm tổng số translations trong tất cả locale files"""
        total_count = 0
        
        for locale_file in locale_files[:10]:  # Limit to first 10 files for performance
            try:
                content = self.zip_handler.read_text_from_zip(zipf.filename, locale_file)
                lines = content.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith(';') and not stripped.startswith('['):
                        total_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to count translations in {locale_file}: {e}")
                continue
                
        # Estimate for remaining files if there are more than 10
        if len(locale_files) > 10:
            avg_per_file = total_count / min(10, len(locale_files))
            total_count = int(avg_per_file * len(locale_files))
            
        return total_count
    
    def get_mod_translation_details(self, zip_path: str, mod_name: str) -> Optional[ModTranslationInfo]:
        """
        Lấy chi tiết translation của một mod cụ thể
        
        Args:
            zip_path: Path to language pack zip
            mod_name: Name of mod to analyze
            
        Returns:
            ModTranslationInfo object or None if not found
        """
        try:
            with self.zip_handler.open_zip(zip_path) as zipf:
                # Find locale file for this mod
                target_file = None
                for name in zipf.namelist():
                    if name.endswith(f'{mod_name}.cfg') and '/locale/' in name:
                        target_file = name
                        break
                
                if not target_file:
                    return None
                
                # Parse locale file
                content = self.zip_handler.read_text_from_zip(zip_path, target_file)
                
                mod_info = ModTranslationInfo(
                    mod_name=mod_name,
                    locale_file=target_file
                )
                
                # Parse content
                self._parse_locale_content(content, mod_info)
                
                return mod_info
                
        except Exception as e:
            self.logger.error(f"Failed to get mod translation details for {mod_name}: {e}")
            return None
    
    def _parse_locale_content(self, content: str, mod_info: ModTranslationInfo):
        """Parse locale file content và populate mod_info"""
        lines = content.split('\n')
        current_section = None
        translation_count = 0
        sections = set()
        sample_translations = {}
        
        for line in lines:
            stripped = line.strip()
            
            # Section headers
            if stripped.startswith('[') and stripped.endswith(']'):
                current_section = stripped[1:-1]
                sections.add(current_section)
                continue
            
            # Translation entries
            if '=' in stripped and not stripped.startswith(';'):
                try:
                    key, value = stripped.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key and value:
                        translation_count += 1
                        
                        # Store sample translations (max 5 per section)
                        section_key = current_section or 'unknown'
                        if section_key not in sample_translations:
                            sample_translations[section_key] = {}
                        
                        if len(sample_translations[section_key]) < 3:
                            sample_translations[section_key][key] = value
                            
                except ValueError:
                    continue
        
        mod_info.translations_count = translation_count
        mod_info.sections = sorted(list(sections))
        mod_info.sample_translations = sample_translations
    
    def compare_language_packs(self, pack1_path: str, pack2_path: str) -> Dict[str, Any]:
        """
        So sánh hai language packs
        
        Args:
            pack1_path: Path to first language pack
            pack2_path: Path to second language pack  
            
        Returns:
            Comparison results
        """
        try:
            pack1_info = self.analyze_language_pack(pack1_path)
            pack2_info = self.analyze_language_pack(pack2_path)
            
            # Compare mods
            mods1 = set(pack1_info.translated_mods)
            mods2 = set(pack2_info.translated_mods)
            
            added_mods = mods2 - mods1
            removed_mods = mods1 - mods2
            common_mods = mods1 & mods2
            
            return {
                'pack1': pack1_info,
                'pack2': pack2_info,
                'added_mods': sorted(list(added_mods)),
                'removed_mods': sorted(list(removed_mods)),
                'common_mods': sorted(list(common_mods)),
                'total_change': len(added_mods) - len(removed_mods),
                'translation_change': pack2_info.total_translations - pack1_info.total_translations
            }
            
        except Exception as e:
            self.logger.error(f"Failed to compare language packs: {e}")
            return {'error': str(e)}
    
    def generate_analysis_report(self, pack_info: LanguagePackInfo) -> str:
        """
        Tạo báo cáo phân tích chi tiết
        
        Args:
            pack_info: LanguagePackInfo object
            
        Returns:
            Formatted analysis report
        """
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append("LANGUAGE PACK ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Basic Info
        report_lines.append("📋 BASIC INFORMATION")
        report_lines.append("-" * 30)
        report_lines.append(f"Name: {pack_info.name}")
        report_lines.append(f"Version: {pack_info.version}")
        report_lines.append(f"Title: {pack_info.title}")
        report_lines.append(f"Author: {pack_info.author}")
        report_lines.append(f"Factorio Version: {pack_info.factorio_version}")
        report_lines.append(f"File Size: {pack_info.file_size / 1024 / 1024:.2f} MB")
        if pack_info.creation_date:
            report_lines.append(f"Created: {pack_info.creation_date.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Translation Stats
        report_lines.append("📊 TRANSLATION STATISTICS")
        report_lines.append("-" * 30)
        report_lines.append(f"Total Locale Files: {pack_info.locale_files_count}")
        report_lines.append(f"Translated Mods: {len(pack_info.translated_mods)}")
        report_lines.append(f"Total Translations: {pack_info.total_translations:,}")
        report_lines.append("")
        
        # Translated Mods
        if pack_info.translated_mods:
            report_lines.append("🎮 TRANSLATED MODS")
            report_lines.append("-" * 30)
            for i, mod_name in enumerate(pack_info.translated_mods[:20], 1):
                report_lines.append(f"{i:2d}. {mod_name}")
            
            if len(pack_info.translated_mods) > 20:
                report_lines.append(f"... and {len(pack_info.translated_mods) - 20} more mods")
            report_lines.append("")
        
        # Dependencies  
        if pack_info.dependencies:
            report_lines.append("🔗 DEPENDENCIES")
            report_lines.append("-" * 30)
            for i, dep in enumerate(pack_info.dependencies[:10], 1):
                report_lines.append(f"{i:2d}. {dep}")
            
            if len(pack_info.dependencies) > 10:
                report_lines.append(f"... and {len(pack_info.dependencies) - 10} more dependencies")
            report_lines.append("")
        
        # Description
        if pack_info.description:
            report_lines.append("📝 DESCRIPTION")
            report_lines.append("-" * 30)
            # Wrap long description
            desc_lines = pack_info.description.split('. ')
            for desc_line in desc_lines:
                if desc_line.strip():
                    report_lines.append(f"• {desc_line.strip()}")
            report_lines.append("")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


# Convenience functions
def find_language_packs(search_dirs: List[str] = None) -> List[str]:
    """Find all language pack files"""
    analyzer = LanguagePackAnalyzer()
    return analyzer.find_language_packs(search_dirs)


def analyze_language_pack(zip_path: str) -> LanguagePackInfo:
    """Analyze a specific language pack"""
    analyzer = LanguagePackAnalyzer()
    return analyzer.analyze_language_pack(zip_path)


def generate_pack_report(zip_path: str) -> str:
    """Generate analysis report for a language pack"""
    analyzer = LanguagePackAnalyzer()
    pack_info = analyzer.analyze_language_pack(zip_path)
    return analyzer.generate_analysis_report(pack_info)
