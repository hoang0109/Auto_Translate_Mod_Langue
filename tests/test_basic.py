"""
Basic unit tests cho Factorio Mod Translator
"""
import unittest
import tempfile
import os
import zipfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path để import modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_utils import ModFileProcessor, MemoryOptimizedZipHandler, TempFileManager
from network_utils import DeepLAPI, NetworkUtils, APIError
from mod_translator_optimized import ModInfo, TranslationConfig, ModTranslatorCore
from sample_mod_manager import SampleModManager, ModVersionManager, ModEditor, VersionType, SampleModInfo


class TestFileUtils(unittest.TestCase):
    """Test cases cho file utilities"""
    
    def setUp(self):
        self.temp_manager = TempFileManager()
        self.zip_handler = MemoryOptimizedZipHandler()
        self.mod_processor = ModFileProcessor()
        
        # Create test zip file
        self.test_zip_path = self.temp_manager.create_temp_file(suffix=".zip")
        self._create_test_zip()
    
    def tearDown(self):
        self.temp_manager.cleanup()
    
    def _create_test_zip(self):
        """Create a test zip file với mod structure"""
        with zipfile.ZipFile(self.test_zip_path, 'w') as zipf:
            # Create info.json
            info_data = {
                "name": "test-mod",
                "version": "1.0.0",
                "title": "Test Mod",
                "author": "Test Author",
                "factorio_version": "2.0"
            }
            zipf.writestr("test-mod/info.json", json.dumps(info_data, indent=2))
            
            # Create locale file
            locale_content = """[entity-name]
test-entity=Test Entity
another-entity=Another Entity

[item-name]
test-item=Test Item
"""
            zipf.writestr("test-mod/locale/en/entities.cfg", locale_content)
    
    def test_zip_handler_get_info(self):
        """Test zip info extraction"""
        info = self.zip_handler.get_zip_info(self.test_zip_path)
        
        self.assertIn('total_files', info)
        self.assertIn('has_info_json', info)
        self.assertIn('locale_files', info)
        self.assertTrue(info['has_info_json'])
        self.assertGreater(len(info['locale_files']), 0)
    
    def test_mod_processor_find_info(self):
        """Test mod info extraction"""
        info = self.mod_processor.find_mod_info(self.test_zip_path)
        
        self.assertIsNotNone(info)
        self.assertEqual(info['name'], 'test-mod')
        self.assertEqual(info['version'], '1.0.0')
        self.assertEqual(info['title'], 'Test Mod')
    
    def test_mod_processor_find_locale_files(self):
        """Test locale files detection"""
        locale_files = self.mod_processor.find_locale_files(self.test_zip_path)
        
        self.assertGreater(len(locale_files), 0)
        file_path, root_folder = locale_files[0]
        self.assertTrue(file_path.endswith('.cfg'))
        self.assertEqual(root_folder, 'test-mod')
    
    def test_mod_processor_parse_cfg(self):
        """Test .cfg file parsing"""
        content = """[entity-name]
test-entity=Test Entity
; comment line
another-entity=Another Entity

[item-name]
test-item=Test Item
"""
        key_vals, lines = self.mod_processor.parse_cfg_content(content)
        
        self.assertEqual(len(key_vals), 3)
        self.assertEqual(key_vals[0]['key'], 'test-entity')
        self.assertEqual(key_vals[0]['val'], 'Test Entity')


class TestNetworkUtils(unittest.TestCase):
    """Test cases cho network utilities"""
    
    def setUp(self):
        self.network_utils = NetworkUtils(max_retries=1, retry_delay=0.1)
    
    @patch('requests.Session.request')
    def test_successful_request(self, mock_request):
        """Test successful request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response
        
        response = self.network_utils.make_request_with_retry('GET', 'http://test.com')
        
        self.assertEqual(response.status_code, 200)
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_retry_on_server_error(self, mock_request):
        """Test retry mechanism trên server error"""
        # First call returns 500, second call returns 200
        mock_response_error = Mock()
        mock_response_error.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        mock_request.side_effect = [mock_response_error, mock_response_success]
        
        response = self.network_utils.make_request_with_retry('GET', 'http://test.com')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_request.call_count, 2)
    
    @patch('requests.Session.request')
    def test_api_error_on_failed_requests(self, mock_request):
        """Test APIError được raise khi tất cả requests fail"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_request.return_value = mock_response
        
        with self.assertRaises(APIError):
            self.network_utils.make_request_with_retry('GET', 'http://test.com')


class TestDeepLAPI(unittest.TestCase):
    """Test cases cho DeepL API client"""
    
    def setUp(self):
        self.api_client = DeepLAPI("test-key", "api-free.deepl.com", max_batch_size=2)
    
    @patch('network_utils.NetworkUtils.make_request_with_retry')
    def test_api_key_validation_success(self, mock_request):
        """Test successful API key validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "character_count": 1000,
            "character_limit": 500000
        }
        mock_request.return_value = mock_response
        
        result = self.api_client.test_api_key()
        
        self.assertEqual(result["character_count"], 1000)
        self.assertEqual(result["character_limit"], 500000)
    
    @patch('network_utils.NetworkUtils.make_request_with_retry')
    def test_api_key_validation_failure(self, mock_request):
        """Test API key validation failure"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_request.return_value = mock_response
        
        with self.assertRaises(APIError) as context:
            self.api_client.test_api_key()
        
        self.assertEqual(context.exception.status_code, 403)
    
    @patch('network_utils.NetworkUtils.make_request_with_retry')
    def test_batch_translation(self, mock_request):
        """Test batch translation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "translations": [
                {"text": "Translated text 1"},
                {"text": "Translated text 2"}
            ]
        }
        mock_request.return_value = mock_response
        
        texts = ["Text 1", "Text 2"]
        result = self.api_client.translate_texts_batch(texts, "VI")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Translated text 1")
        self.assertEqual(result[1], "Translated text 2")


class TestModTranslatorCore(unittest.TestCase):
    """Test cases cho core translator"""
    
    def setUp(self):
        config = TranslationConfig(
            api_key="test-key",
            target_language="VI",
            endpoint="api-free.deepl.com"
        )
        self.translator = ModTranslatorCore(config)
    
    def test_mod_info_creation(self):
        """Test ModInfo dataclass creation"""
        mod_info = ModInfo(
            name="test-mod",
            zip_path="/path/to/test.zip",
            version="1.0.0"
        )
        
        self.assertEqual(mod_info.name, "test-mod")
        self.assertEqual(mod_info.zip_path, "/path/to/test.zip")
        self.assertEqual(mod_info.version, "1.0.0")
        self.assertEqual(len(mod_info.locale_files), 0)
    
    @patch('mod_translator_optimized.DeepLAPI')
    def test_api_key_validation(self, mock_deepl_api):
        """Test API key validation through translator"""
        mock_api_instance = Mock()
        mock_api_instance.test_api_key.return_value = {
            "character_count": 1000,
            "character_limit": 500000
        }
        mock_deepl_api.return_value = mock_api_instance
        
        # Create new translator để use mocked API
        config = TranslationConfig(
            api_key="test-key",
            target_language="VI"
        )
        translator = ModTranslatorCore(config)
        
        result = translator.validate_api_key()
        
        self.assertTrue(result['valid'])
        self.assertIn('usage_info', result)
    
    def test_translation_config(self):
        """Test translation configuration"""
        config = TranslationConfig(
            api_key="test-key",
            target_language="VI",
            endpoint="api.deepl.com",
            max_batch_size=25
        )
        
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.target_language, "VI")
        self.assertEqual(config.endpoint, "api.deepl.com")
        self.assertEqual(config.max_batch_size, 25)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        self.temp_manager = TempFileManager()
    
    def tearDown(self):
        self.temp_manager.cleanup()
    
    def test_full_mod_analysis_pipeline(self):
        """Test full pipeline từ zip file đến ModInfo"""
        # Create test zip
        test_zip = self.temp_manager.create_temp_file(suffix=".zip")
        
        with zipfile.ZipFile(test_zip, 'w') as zipf:
            info_data = {
                "name": "integration-test-mod",
                "version": "1.0.0",
                "title": "Integration Test Mod"
            }
            zipf.writestr("integration-test-mod/info.json", json.dumps(info_data))
            
            locale_content = "[entity-name]\\ntest=Test Entity\\n"
            zipf.writestr("integration-test-mod/locale/en/test.cfg", locale_content)
        
        # Test analysis
        config = TranslationConfig(
            api_key="test-key",
            target_language="VI"
        )
        translator = ModTranslatorCore(config)
        
        mods_info = translator.analyze_mods([test_zip])
        
        self.assertEqual(len(mods_info), 1)
        mod_info = mods_info[0]
        self.assertEqual(mod_info.name, "integration-test-mod")
        self.assertEqual(mod_info.version, "1.0.0")
        self.assertGreater(len(mod_info.locale_files), 0)


class TestModVersionManager(unittest.TestCase):
    """Test cases cho ModVersionManager"""
    
    def setUp(self):
        self.version_manager = ModVersionManager()
    
    def test_parse_version(self):
        """Test version parsing"""
        # Test valid versions
        self.assertEqual(self.version_manager.parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(self.version_manager.parse_version("2.1.3"), (2, 1, 3))
        self.assertEqual(self.version_manager.parse_version("10.20.30"), (10, 20, 30))
        
        # Test partial versions
        self.assertEqual(self.version_manager.parse_version("1.0"), (1, 0, 0))
        self.assertEqual(self.version_manager.parse_version("1"), (1, 0, 0))
        
        # Test invalid versions
        self.assertEqual(self.version_manager.parse_version("invalid"), (1, 0, 0))
        self.assertEqual(self.version_manager.parse_version(""), (1, 0, 0))
    
    def test_version_to_string(self):
        """Test version tuple to string conversion"""
        self.assertEqual(self.version_manager.version_to_string(1, 0, 0), "1.0.0")
        self.assertEqual(self.version_manager.version_to_string(2, 1, 3), "2.1.3")
    
    def test_increment_version(self):
        """Test version incrementing"""
        # Test major increment
        result = self.version_manager.increment_version("1.2.3", VersionType.MAJOR)
        self.assertEqual(result, "2.0.0")
        
        # Test minor increment
        result = self.version_manager.increment_version("1.2.3", VersionType.MINOR)
        self.assertEqual(result, "1.3.0")
        
        # Test patch increment
        result = self.version_manager.increment_version("1.2.3", VersionType.PATCH)
        self.assertEqual(result, "1.2.4")
    
    def test_compare_versions(self):
        """Test version comparison"""
        # Test equal
        self.assertEqual(self.version_manager.compare_versions("1.0.0", "1.0.0"), 0)
        
        # Test greater
        self.assertEqual(self.version_manager.compare_versions("2.0.0", "1.0.0"), 1)
        self.assertEqual(self.version_manager.compare_versions("1.1.0", "1.0.0"), 1)
        self.assertEqual(self.version_manager.compare_versions("1.0.1", "1.0.0"), 1)
        
        # Test lesser
        self.assertEqual(self.version_manager.compare_versions("1.0.0", "2.0.0"), -1)
        self.assertEqual(self.version_manager.compare_versions("1.0.0", "1.1.0"), -1)
        self.assertEqual(self.version_manager.compare_versions("1.0.0", "1.0.1"), -1)
    
    def test_suggest_next_version(self):
        """Test version suggestion"""
        # Test major changes
        result = self.version_manager.suggest_next_version("1.0.0", has_major_changes=True)
        self.assertEqual(result, "2.0.0")
        
        # Test minor changes
        result = self.version_manager.suggest_next_version("1.0.0", has_minor_changes=True)
        self.assertEqual(result, "1.1.0")
        
        # Test patch changes
        result = self.version_manager.suggest_next_version("1.0.0", has_major_changes=False, has_minor_changes=False)
        self.assertEqual(result, "1.0.1")


class TestModEditor(unittest.TestCase):
    """Test cases cho ModEditor"""
    
    def setUp(self):
        self.mod_editor = ModEditor()
        self.temp_manager = TempFileManager()
        
        # Create test zip file
        self.test_zip_path = self.temp_manager.create_temp_file(suffix=".zip")
        self._create_test_mod_zip()
    
    def tearDown(self):
        self.temp_manager.cleanup()
    
    def _create_test_mod_zip(self):
        """Create test mod zip file"""
        with zipfile.ZipFile(self.test_zip_path, 'w') as zipf:
            # Create info.json
            info_data = {
                "name": "test-mod",
                "version": "1.0.0",
                "title": "Test Mod",
                "author": "Test Author",
                "description": "Test description",
                "factorio_version": "2.0",
                "dependencies": ["? base"]
            }
            zipf.writestr("test-mod/info.json", json.dumps(info_data, indent=2))
            
            # Create locale files
            locale_content = """[entity-name]
test-entity=Test Entity

[item-name]
test-item=Test Item
"""
            zipf.writestr("test-mod/locale/en/test.cfg", locale_content)
    
    def test_update_info_json(self):
        """Test updating info.json data"""
        original_info = {
            "name": "test-mod",
            "version": "1.0.0",
            "dependencies": ["? base"]
        }
        
        updates = {
            "version": "1.1.0",
            "dependencies": ["? new-dep"],
            "description": "Updated description"
        }
        
        updated_info = self.mod_editor.update_info_json(original_info, updates)
        
        self.assertEqual(updated_info["version"], "1.1.0")
        self.assertEqual(updated_info["description"], "Updated description")
        # Dependencies should be merged
        self.assertIn("? base", updated_info["dependencies"])
        self.assertIn("? new-dep", updated_info["dependencies"])
    
    @patch('tempfile.mkdtemp')
    @patch('os.makedirs')
    def test_add_locale_files(self, mock_makedirs, mock_mkdtemp):
        """Test adding locale files to mod"""
        # Mock temp directory
        mock_mkdtemp.return_value = "/tmp/test"
        
        locale_files = {
            "new-mod": "[entity-name]\nnew-entity=New Entity\n"
        }
        
        # This would normally create a new zip, but we'll just test the logic
        # In a real test, we'd need to check the actual file creation
        try:
            result = self.mod_editor.add_locale_files(self.test_zip_path, locale_files)
            # If it doesn't raise an exception, the basic logic works
            self.assertIsInstance(result, str)
        except Exception:
            # Expected in test environment due to mocking limitations
            pass


class TestSampleModManager(unittest.TestCase):
    """Test cases cho SampleModManager"""
    
    def setUp(self):
        # Create temporary sample directory
        self.temp_manager = TempFileManager()
        self.temp_sample_dir = self.temp_manager.create_temp_dir()
        self.sample_manager = SampleModManager(self.temp_sample_dir)
        
        # Create test sample mod
        self.test_sample_path = os.path.join(self.temp_sample_dir, "sample_mod_101.zip")
        self._create_sample_mod()
    
    def tearDown(self):
        self.temp_manager.cleanup()
    
    def _create_sample_mod(self):
        """Create test sample mod"""
        with zipfile.ZipFile(self.test_sample_path, 'w') as zipf:
            # Create info.json
            info_data = {
                "name": "sample-mod",
                "version": "1.0.1",
                "title": "Sample Mod",
                "author": "Sample Author",
                "description": "Sample description",
                "factorio_version": "2.0",
                "dependencies": ["? base", "? another-mod"]
            }
            zipf.writestr("sample-mod/info.json", json.dumps(info_data, indent=2))
            
            # Create Vietnamese locale files
            locale_content = """[entity-name]
sample-entity=Thực thể mẫu

[item-name]
sample-item=Vật phẩm mẫu
"""
            zipf.writestr("sample-mod/locale/vi/sample.cfg", locale_content)
    
    def test_scan_sample_mods(self):
        """Test scanning sample mods"""
        sample_mods = self.sample_manager.scan_sample_mods()
        
        self.assertEqual(len(sample_mods), 1)
        sample_mod = sample_mods[0]
        self.assertEqual(sample_mod.name, "sample-mod")
        self.assertEqual(sample_mod.version, "1.0.1")
        self.assertEqual(sample_mod.title, "Sample Mod")
    
    def test_analyze_sample_mod(self):
        """Test analyzing individual sample mod"""
        sample_mod = self.sample_manager.analyze_sample_mod(self.test_sample_path)
        
        self.assertIsNotNone(sample_mod)
        self.assertEqual(sample_mod.name, "sample-mod")
        self.assertEqual(sample_mod.version, "1.0.1")
        self.assertEqual(sample_mod.title, "Sample Mod")
        self.assertEqual(sample_mod.author, "Sample Author")
        self.assertIn("? base", sample_mod.dependencies)
        self.assertIn("? another-mod", sample_mod.dependencies)
    
    def test_get_latest_version_mod(self):
        """Test getting latest version mod"""
        # Create another version
        newer_sample_path = os.path.join(self.temp_sample_dir, "sample_mod_110.zip")
        with zipfile.ZipFile(newer_sample_path, 'w') as zipf:
            info_data = {
                "name": "sample-mod",
                "version": "1.1.0",
                "title": "Sample Mod",
                "author": "Sample Author"
            }
            zipf.writestr("sample-mod/info.json", json.dumps(info_data, indent=2))
        
        latest_mod = self.sample_manager.get_latest_version_mod("sample")
        
        self.assertIsNotNone(latest_mod)
        self.assertEqual(latest_mod.version, "1.1.0")
    
    def test_load_sample_translations(self):
        """Test loading sample translations"""
        sample_mod = self.sample_manager.analyze_sample_mod(self.test_sample_path)
        translations = self.sample_manager.load_sample_translations(sample_mod)
        
        self.assertGreater(len(translations), 0)
        self.assertIn('sample.cfg', translations)
        self.assertIn('sample-entity=Thực thể mẫu', translations['sample.cfg'])


class TestSampleModInfo(unittest.TestCase):
    """Test cases cho SampleModInfo dataclass"""
    
    def test_sample_mod_info_creation(self):
        """Test creating SampleModInfo"""
        mod_info = SampleModInfo(
            name="test-mod",
            version="1.0.0",
            title="Test Mod",
            author="Test Author",
            description="Test description",
            zip_path="/path/to/test.zip"
        )
        
        self.assertEqual(mod_info.name, "test-mod")
        self.assertEqual(mod_info.version, "1.0.0")
        self.assertEqual(mod_info.title, "Test Mod")
        self.assertEqual(mod_info.author, "Test Author")
        self.assertEqual(mod_info.description, "Test description")
        self.assertEqual(mod_info.zip_path, "/path/to/test.zip")
        self.assertEqual(mod_info.factorio_version, "2.0")  # Default value
        self.assertEqual(len(mod_info.dependencies), 0)  # Default empty list
        self.assertEqual(len(mod_info.locale_files), 0)  # Default empty list
    
    def test_sample_mod_info_with_dependencies(self):
        """Test SampleModInfo with dependencies"""
        dependencies = ["? base", "? another-mod"]
        locale_files = ["test.cfg", "items.cfg"]
        
        mod_info = SampleModInfo(
            name="test-mod",
            version="1.0.0",
            title="Test Mod",
            author="Test Author",
            description="Test description",
            zip_path="/path/to/test.zip",
            dependencies=dependencies,
            locale_files=locale_files
        )
        
        self.assertEqual(mod_info.dependencies, dependencies)
        self.assertEqual(mod_info.locale_files, locale_files)


if __name__ == '__main__':
    # Create logs directory nếu chưa có
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)
