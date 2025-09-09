
# 🚀 DEPLOYMENT GUIDE - Auto Translate Mod Langue

## 📋 System Requirements
- Python 3.8+ (tested with 3.13)
- Windows/Linux/MacOS
- 50MB+ free disk space
- Internet connection (optional, for DeepL API)

## 🔧 Installation
1. Clone/download the project files
2. Install dependencies: `pip install -r requirements.txt`
3. Configure DeepL API key (optional): Edit config files
4. Run tests: `python test_large_scale_translation.py`

## 🎮 Usage
### For End Users:
1. Place Factorio mods in input directory
2. Run: `python main_gui.py`
3. Select mods to translate
4. Click "Translate" button
5. Find Vietnamese mods in output directory

### For Developers:
1. Extend `vietnamese_dict` for new terms
2. Add new translation engines in `translation_engines/`
3. Update test cases in `test_*` files
4. Run full test suite before deployment

## 📊 Monitoring
- Check `logs/` directory for execution logs
- Review `performance_data/` for metrics
- Monitor `cache/` directory size

## 🆘 Troubleshooting
- File access errors: Check directory permissions
- Memory issues: Process mods in smaller batches
- Network errors: Use offline mode (Mock translator)

## 🔄 Updates
- Backup translation cache before updates
- Test with small mod set after updates
- Update Vietnamese dictionary regularly
