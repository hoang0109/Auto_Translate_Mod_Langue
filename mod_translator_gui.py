import configparser
import uuid
import base64
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import zipfile
import json
import shutil
import requests
import time
from threading import Lock
from datetime import datetime

import os
import threading
from mod_translate_pack_core import process_mods_to_language_pack
from mod_translate_core import read_cfg_file, translate_texts as core_translate_texts
from mod_translate_pack_core import translate_texts as pack_translate_texts
from improved_mod_finder import find_locale_files_improved
from google_translate_core import GoogleTranslateAPI
from google_translate_safe import SafeGoogleTranslateAPI

# Import Sample Mod Manager
try:
    from sample_mod_dialog import show_sample_mod_dialog
except ImportError:
    show_sample_mod_dialog = None

class ModTranslatorApp(tk.Tk):
    def get_machine_key(self):
        mac = uuid.getnode()
        mac_bytes = mac.to_bytes(6, 'big')
        # Pad/truncate to 32 bytes for Fernet key
        key = base64.urlsafe_b64encode(mac_bytes.ljust(32, b'0'))
        return key

    def encrypt_api_key(self, api_key):
        key = self.get_machine_key()
        f = Fernet(key)
        return f.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, token):
        key = self.get_machine_key()
        f = Fernet(key)
        return f.decrypt(token.encode()).decode()

    def save_settings(self):
        config = configparser.ConfigParser()
        config['SETTINGS'] = {
            'mod_name': self.mod_name_var.get(),
            'lang': self.lang_var.get(),
            'api_key': self.encrypt_api_key(self.api_key_var.get()) if self.api_key_var.get() else '',
            'endpoint': self.endpoint_var.get(),
            'translation_service': self.translation_service_var.get(),
        }
        with open('config.ini', 'w', encoding='utf-8') as f:
            config.write(f)
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def load_settings(self):
        config = configparser.ConfigParser()
        try:
            config.read('config.ini', encoding='utf-8')
            if 'SETTINGS' in config:
                self.mod_name_var.set(config['SETTINGS'].get('mod_name', ''))
                self.lang_var.set(config['SETTINGS'].get('lang', 'VI'))
                self.endpoint_var.set(config['SETTINGS'].get('endpoint', 'api.deepl.com'))
                self.translation_service_var.set(config['SETTINGS'].get('translation_service', 'Safe Google Translate (Recommended)'))
                api_key_enc = config['SETTINGS'].get('api_key', '')
                if api_key_enc:
                    try:
                        self.api_key_var.set(self.decrypt_api_key(api_key_enc))
                    except Exception:
                        self.api_key_var.set('')
                # Trigger service change để cập nhật UI
                self.after(100, self.on_service_change)
        except Exception:
            messagebox.showwarning("Settings", "No settings found or failed to load.")
    def on_close(self):
        """Lưu thông tin trước khi thoát chương trình."""
        self.save_settings()  # Gọi hàm lưu settings hiện có
        self.destroy()  # Thoát chương trình

    def __init__(self):
        super().__init__()
        self.title("🎮 Factorio Mod Translator v2.0")
        self.geometry("700x500")
        self.resizable(True, True)  # Cho phép resize
        self.minsize(600, 400)  # Kích thước tối thiểu
        
        # Initialize variables
        self.selected_files = []
        self.glossary_path = None
        self.api_key_var = tk.StringVar(self)
        self.mod_name_var = tk.StringVar(self, value="Auto_Translate_Mod_Langue")
        self.is_translating = False  # Trạng thái đang dịch
        self.translation_cancelled = False  # Trạng thái hủy dịch
        self.translation_service_var = tk.StringVar(self, value="Safe Google Translate (Recommended)")
        
        # Template mod info
        self.template_info = None
        
        # Threading và synchronization
        self.file_lock = Lock()
        
        # UI Setup
        self.setup_styles()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.create_widgets()
        self.load_settings()
        
        # Center window
        self.center_window()

    def setup_styles(self):
        """Thiết lập styles cho ứng dụng"""
        self.configure(bg='#f0f0f0')
        
    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        # Main container với scrollable frame
        main_frame = tk.Frame(self, bg='#f0f0f0')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame for file selection với improved UI
        file_frame = tk.LabelFrame(main_frame, text="📁 Select Mod Files (.zip)", 
                                  font=('Arial', 10, 'bold'), fg='#2c3e50')
        file_frame.pack(fill="both", expand=True, pady=(0, 10))

        # File list với scrollbar
        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.file_listbox = tk.Listbox(list_frame, height=6, font=('Arial', 9),
                                      selectmode=tk.EXTENDED)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        self.file_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # File buttons với icons
        file_btn_frame = tk.Frame(file_frame)
        file_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        tk.Button(file_btn_frame, text="➕ Add Files", command=self.add_files,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold')).pack(side="left", padx=(0, 5))
        tk.Button(file_btn_frame, text="➖ Remove Selected", command=self.remove_selected,
                 bg='#e74c3c', fg='white', font=('Arial', 9, 'bold')).pack(side="left", padx=(0, 5))
        tk.Button(file_btn_frame, text="🗑️ Clear All", command=self.clear_all_files,
                 bg='#95a5a6', fg='white', font=('Arial', 9, 'bold')).pack(side="left", padx=(0, 10))
        
        # Load Template button
        tk.Button(file_btn_frame, text="📋 Load Template", command=self.load_template_mod,
                 bg='#8e44ad', fg='white', font=('Arial', 9, 'bold')).pack(side="left")

        # Settings frame
        settings_frame = tk.LabelFrame(main_frame, text="⚙️ Translation Settings", 
                                      font=('Arial', 10, 'bold'), fg='#2c3e50')
        settings_frame.pack(fill="x", pady=(0, 10))
        
        # Mod Name input
        name_frame = tk.Frame(settings_frame)
        name_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(name_frame, text="Custom Mod Name:", font=('Arial', 9, 'bold')).pack(side="left")
        name_entry = tk.Entry(name_frame, textvariable=self.mod_name_var, width=35, font=('Arial', 9))
        name_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Translation Service selection
        service_frame = tk.Frame(settings_frame)
        service_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(service_frame, text="🌐 Translation Service:", font=('Arial', 9, 'bold')).pack(side="left")
        self.service_combo = ttk.Combobox(service_frame, textvariable=self.translation_service_var,
                                        values=["Safe Google Translate (Recommended)", "Google Translate (Fast)", "DeepL API"],
                                        state="readonly", width=30, font=('Arial', 9))
        self.service_combo.pack(side="left", padx=5)
        self.service_combo.bind('<<ComboboxSelected>>', self.on_service_change)
        
        # API Key input với validation
        api_frame = tk.Frame(settings_frame)
        api_frame.pack(fill="x", padx=10, pady=5)
        self.api_label = tk.Label(api_frame, text="🔑 DeepL API Key:", font=('Arial', 9, 'bold'))
        self.api_label.pack(side="left")
        self.api_entry = tk.Entry(api_frame, textvariable=self.api_key_var, show="*", 
                                 width=35, font=('Arial', 9))
        self.api_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.api_entry.bind('<KeyRelease>', self.on_api_key_change)
        
        # API status và test button
        api_btn_frame = tk.Frame(api_frame)
        api_btn_frame.pack(side="right")
        self.test_api_btn = tk.Button(api_btn_frame, text="🧪 Test API", command=self.test_deepl_api,
                                     bg='#3498db', fg='white', font=('Arial', 8, 'bold'))
        self.test_api_btn.pack(side="left", padx=5)
        
        self.api_status_label = tk.Label(api_btn_frame, text="❓", font=('Arial', 12))
        self.api_status_label.pack(side="left", padx=5)

        # Language và Endpoint selection
        config_frame = tk.Frame(settings_frame)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # Language selection
        lang_subframe = tk.Frame(config_frame)
        lang_subframe.pack(side="left", fill="x", expand=True)
        tk.Label(lang_subframe, text="🌍 Target Language:", font=('Arial', 9, 'bold')).pack(side="left")
        self.lang_var = tk.StringVar(value="VI")
        self.lang_combo = ttk.Combobox(lang_subframe, textvariable=self.lang_var, 
                                      values=["VI", "JA", "EN", "ZH", "FR", "DE", "ES"], 
                                      state="readonly", width=8, font=('Arial', 9))
        self.lang_combo.pack(side="left", padx=5)

        # Endpoint selection
        endpoint_subframe = tk.Frame(config_frame)
        endpoint_subframe.pack(side="right")
        tk.Label(endpoint_subframe, text="🌐 DeepL Endpoint:", font=('Arial', 9, 'bold')).pack(side="left")
        self.endpoint_var = tk.StringVar(value="api.deepl.com")
        self.endpoint_combo = ttk.Combobox(endpoint_subframe, textvariable=self.endpoint_var, 
                                          values=["api.deepl.com", "api-free.deepl.com"], 
                                          state="readonly", width=15, font=('Arial', 9))
        self.endpoint_combo.pack(side="left", padx=5)

        # Translation Statistics (for Safe Google Translate)
        self.stats_frame = tk.LabelFrame(main_frame, text="📈 Translation Statistics", 
                                        font=('Arial', 10, 'bold'), fg='#2c3e50')
        
        stats_info_frame = tk.Frame(self.stats_frame)
        stats_info_frame.pack(fill="x", padx=10, pady=5)
        
        # Statistics labels
        self.stats_requests_label = tk.Label(stats_info_frame, text="Requests: 0", 
                                            font=('Arial', 8), anchor="w")
        self.stats_requests_label.pack(side="left")
        
        self.stats_cache_label = tk.Label(stats_info_frame, text="Cache: 0%", 
                                         font=('Arial', 8), anchor="w")
        self.stats_cache_label.pack(side="left", padx=(20, 0))
        
        self.stats_rpm_label = tk.Label(stats_info_frame, text="RPM: 0", 
                                       font=('Arial', 8), anchor="w")
        self.stats_rpm_label.pack(side="left", padx=(20, 0))
        
        self.stats_errors_label = tk.Label(stats_info_frame, text="Errors: 0", 
                                          font=('Arial', 8), anchor="w", fg='red')
        self.stats_errors_label.pack(side="right")
        
        # Hide stats frame initially
        # Will be shown when using Safe Google Translate
        
        # Progress and status
        progress_frame = tk.LabelFrame(main_frame, text="📊 Progress", 
                                      font=('Arial', 10, 'bold'), fg='#2c3e50')
        progress_frame.pack(fill="x", pady=(0, 10))
        
        # Progress bar với chi tiết
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", 
                                       length=580, mode="determinate")
        self.progress.pack(padx=10, pady=5, fill="x")
        
        # Progress info
        progress_info_frame = tk.Frame(progress_frame)
        progress_info_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.progress_label = tk.Label(progress_info_frame, text="Ready to start translation", 
                                      font=('Arial', 9), anchor="w")
        self.progress_label.pack(side="left")
        
        self.progress_percent = tk.Label(progress_info_frame, text="0%", 
                                        font=('Arial', 9, 'bold'), anchor="e")
        self.progress_percent.pack(side="right")
        
        # Status label
        self.status_label = tk.Label(progress_frame, text="🟢 Ready", anchor="w", 
                                    font=('Arial', 9), fg='#27ae60')
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

        # Control buttons frame
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Top row buttons
        top_buttons_frame = tk.Frame(control_frame)
        top_buttons_frame.pack(fill="x", pady=(0, 5))
        
        # Start/Cancel button
        self.start_btn = tk.Button(top_buttons_frame, text="🚀 Start Translation", 
                                  command=self.start_translation, height=2, 
                                  bg="#27ae60", fg="white", font=('Arial', 11, 'bold'))
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Save settings button
        tk.Button(top_buttons_frame, text="💾 Save Settings", command=self.save_settings,
                 height=2, bg="#3498db", fg="white", font=('Arial', 11, 'bold')).pack(side="right")
        
        # Bottom row buttons
        bottom_buttons_frame = tk.Frame(control_frame)
        bottom_buttons_frame.pack(fill="x")
        
        # Analyze Language Pack button
        tk.Button(bottom_buttons_frame, text="📋 Analyze Language Pack", 
                 command=self.analyze_language_pack, height=2, 
                 bg="#9b59b6", fg="white", font=('Arial', 11, 'bold')).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Compare Packs button 
        tk.Button(bottom_buttons_frame, text="🔄 Compare Packs", 
                 command=self.compare_language_packs, height=2,
                 bg="#e67e22", fg="white", font=('Arial', 11, 'bold')).pack(side="right")

    def add_files(self):
        files = filedialog.askopenfilenames(title="Select Mod Files", filetypes=[("Zip Files", "*.zip")])
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                self.file_listbox.insert(tk.END, os.path.basename(f))

    def remove_selected(self):
        selected_indices = list(self.file_listbox.curselection())
        for idx in reversed(selected_indices):
            self.file_listbox.delete(idx)
            del self.selected_files[idx]
            
    def clear_all_files(self):
        """Xóa tất cả file đã chọn"""
        if self.selected_files:
            result = messagebox.askyesno("Clear All", "Are you sure you want to clear all selected files?")
            if result:
                self.file_listbox.delete(0, tk.END)
                self.selected_files.clear()
    
    def load_template_mod(self):
        """Tải mod mẫu làm template"""
        try:
            # Chọn file zip template từ thư mục Code mau
            template_file = filedialog.askopenfilename(
                title="Chọn Mod Mẫu",
                initialdir="Code mau",
                filetypes=[("Zip Files", "*.zip")]
            )
            
            if not template_file:
                return
                
            # Đọc thông tin mod từ file zip
            template_info = self.extract_template_info(template_file)
            
            if template_info:
                # Lưu thông tin template
                self.template_info = template_info
                
                # Hiển thị thông tin đã tải
                messagebox.showinfo("Template Loaded", 
                    f"Template loaded successfully:\n"
                    f"Name: {template_info['name']}\n"
                    f"Version: {template_info['version']}\n"
                    f"Title: {template_info['title']}\n"
                    f"Locale files: {len(template_info['locale_files'])}")
                
                # Cập nhật mod name
                self.mod_name_var.set(template_info['name'])
            else:
                messagebox.showerror("Error", "Failed to read template information")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load template: {str(e)}")
    
    def extract_template_info(self, zip_path):
        """Trích xuất thông tin từ mod template"""
        try:
            template_info = {
                'zip_path': zip_path,
                'name': '',
                'version': '1.0.0',
                'title': '',
                'author': '',
                'description': '',
                'dependencies': [],
                'locale_files': []
            }
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Tìm info.json
                info_files = [name for name in zipf.namelist() if name.endswith('info.json')]
                
                if info_files:
                    with zipf.open(info_files[0]) as f:
                        info_data = json.load(f)
                        template_info.update({
                            'name': info_data.get('name', ''),
                            'version': info_data.get('version', '1.0.0'),
                            'title': info_data.get('title', ''),
                            'author': info_data.get('author', ''),
                            'description': info_data.get('description', ''),
                            'dependencies': info_data.get('dependencies', [])
                        })
                
                # Tìm locale files (tiếng Việt) - flexible pattern matching
                locale_files = [name for name in zipf.namelist() 
                              if (('locale/vi/' in name or 'locale\\vi\\' in name or '/vi/' in name) 
                                  and name.endswith('.cfg'))]
                template_info['locale_files'] = locale_files
                
            return template_info
            
        except Exception as e:
            print(f"Error extracting template info: {e}")
            return None
    
    def create_new_template_version(self, translated_mods):
        """Tạo phiên bản mới của template mod với các bản dịch mới"""
        if not self.template_info:
            return None
            
        try:
            # Tăng version của template
            current_version = self.template_info['version']
            new_version = self.increment_version(current_version)
            
            # Tạo tên mới cho template
            base_name = self.template_info['name']
            new_name = f"{base_name}_{new_version.replace('.', '')}"
            
            # Tạo thư mục tạm cho template mới
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                new_template_dir = os.path.join(temp_dir, new_name)
                
                # Giải nén template gốc
                with zipfile.ZipFile(self.template_info['zip_path'], 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Tìm thư mục gốc của template
                extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                if not extracted_dirs:
                    return None
                
                old_template_dir = os.path.join(temp_dir, extracted_dirs[0])
                
                # Đổi tên thư mục
                os.rename(old_template_dir, new_template_dir)
                
                # Cập nhật info.json
                info_json_path = os.path.join(new_template_dir, 'info.json')
                if os.path.exists(info_json_path):
                    with open(info_json_path, 'r', encoding='utf-8') as f:
                        info_data = json.load(f)
                    
                    # Cập nhật thông tin
                    info_data['name'] = new_name
                    info_data['version'] = new_version
                    
                    # Thêm các mod đã dịch vào dependencies
                    dependencies = info_data.get('dependencies', [])
                    for mod_name in translated_mods:
                        dep_entry = f"? {mod_name}"
                        if dep_entry not in dependencies:
                            dependencies.append(dep_entry)
                    info_data['dependencies'] = dependencies
                    
                    # Cập nhật mô tả
                    timestamp = datetime.now().strftime('%Y-%m-%d')
                    info_data['description'] = f"{info_data.get('description', '')} (Updated: {timestamp})"
                    
                    with open(info_json_path, 'w', encoding='utf-8') as f:
                        json.dump(info_data, f, ensure_ascii=False, indent=2)
                
                # Sao chép các file .cfg mới từ Code mau đến template
                self.copy_new_locale_files_to_template(new_template_dir, translated_mods)
                
                # Tạo file zip mới
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                new_zip_path = os.path.join(output_dir, f"{new_name}.zip")
                
                with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(new_template_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                return new_zip_path
                
        except Exception as e:
            print(f"Error creating new template version: {e}")
            return None
        finally:
            # Cleanup temp_translations directory
            try:
                temp_dir = Path("temp_translations")
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not cleanup temp directory: {e}")
    
    def increment_version(self, version_str):
        """Tăng version của mod"""
        try:
            parts = version_str.split('.')
            if len(parts) >= 3:
                major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
                patch += 1
                return f"{major}.{minor}.{patch}"
            elif len(parts) == 2:
                major, minor = int(parts[0]), int(parts[1])
                minor += 1
                return f"{major}.{minor}.0"
            else:
                return "1.0.1"
        except:
            return "1.0.1"
    
    def copy_new_locale_files_to_template(self, template_dir, translated_mods):
        """Sao chép các file locale mới vào template"""
        try:
            # Thư mục locale/vi trong template
            locale_vi_dir = os.path.join(template_dir, "locale", "vi")
            os.makedirs(locale_vi_dir, exist_ok=True)
            
            # Sao chép các file .cfg từ thư mục temp_translations
            temp_translations_dir = "temp_translations"
            if os.path.exists(temp_translations_dir):
                for cfg_file in os.listdir(temp_translations_dir):
                    if cfg_file.endswith('.cfg'):
                        mod_name = os.path.splitext(cfg_file)[0]
                        if mod_name in translated_mods:
                            source_file = os.path.join(temp_translations_dir, cfg_file)
                            dest_file = os.path.join(locale_vi_dir, cfg_file)
                            shutil.copy2(source_file, dest_file)
            
            # Sao chép các file .cfg cũ từ template gốc (nếu có)
            if self.template_info and self.template_info.get('locale_files'):
                with zipfile.ZipFile(self.template_info['zip_path'], 'r') as zipf:
                    for locale_file_path in self.template_info['locale_files']:
                        if (('locale/vi/' in locale_file_path or 'locale\\vi\\' in locale_file_path or '/vi/' in locale_file_path) 
                            and locale_file_path.endswith('.cfg')):
                            try:
                                # Đọc nội dung file từ zip
                                content = zipf.read(locale_file_path).decode('utf-8')
                                
                                # Tên file
                                cfg_filename = os.path.basename(locale_file_path)
                                dest_file = os.path.join(locale_vi_dir, cfg_filename)
                                
                                # Chỉ copy nếu chưa có file mới (không ghi đè file mới dịch)
                                if not os.path.exists(dest_file):
                                    with open(dest_file, 'w', encoding='utf-8') as f:
                                        f.write(content)
                            except Exception as e:
                                print(f"Error copying old locale file {locale_file_path}: {e}")
                        
        except Exception as e:
            print(f"Error copying locale files: {e}")
    
    def analyze_language_pack(self):
        """Phân tích language pack hiện tại"""
        try:
            # Import language pack analyzer
            from language_pack_analyzer import LanguagePackAnalyzer
            analyzer = LanguagePackAnalyzer()
            
            # Analyze current language packs
            results = analyzer.analyze_all_packs()
            
            # Show results in a new dialog
            messagebox.showinfo("Language Pack Analysis", 
                              f"Analysis completed.\nFound {len(results)} language packs.")
                              
        except ImportError:
            messagebox.showinfo("Language Pack Analysis", "Feature coming soon!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze language pack: {str(e)}")
    
    def compare_language_packs(self):
        """So sánh các language packs"""
        try:
            # Feature placeholder
            messagebox.showinfo("Compare Language Packs", "Feature coming soon!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to compare language packs: {str(e)}")
                
    def on_service_change(self, event=None):
        """Xử lý khi thay đổi translation service"""
        service = self.translation_service_var.get()
        
        if "Google" in service:
            # Ẩn API key controls cho Google Translate
            if "Safe" in service:
                self.api_label.config(text="🔒 Safe Google Translate (Miễn phí)")
                # Hiện statistics panel
                self.stats_frame.pack(fill="x", pady=(0, 10))
            else:
                self.api_label.config(text="⚡ Google Translate Fast (Miễn phí)")
                # Ẩn statistics panel
                self.stats_frame.pack_forget()
                
            self.api_entry.config(state='disabled')
            self.test_api_btn.config(state='disabled')
            self.api_status_label.config(text="✅", fg='green')
        else:
            # Hiện API key controls cho DeepL
            self.api_label.config(text="🔑 DeepL API Key:")
            self.api_entry.config(state='normal')
            # Ẩn statistics panel
            self.stats_frame.pack_forget()
            self.on_api_key_change()
            
    def on_api_key_change(self, event=None):
        """Xử lý khi API key thay đổi"""
        service = self.translation_service_var.get()
        if "Google" in service:
            return  # Không cần xử lý cho Google Translate
            
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self.api_status_label.config(text="❓", fg='gray')
            self.test_api_btn.config(state='disabled')
        else:
            self.api_status_label.config(text="❓", fg='orange')
            self.test_api_btn.config(state='normal')
            
    def update_progress(self, current, total, current_mod=""):
        """Cập nhật progress bar"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress["value"] = percentage
            self.progress_percent.config(text=f"{percentage:.1f}%")
            if current_mod:
                self.progress_label.config(text=f"Processing: {current_mod} ({current}/{total})")
            else:
                self.progress_label.config(text=f"Progress: {current}/{total}")
        self.update_idletasks()
        
    def update_progress_with_stats(self, current, total, message=""):
        """Cập nhật progress và statistics cho Safe Google Translate"""
        # Cập nhật progress thường
        self.update_progress(current, total, message)
        
        # Cập nhật statistics nếu có Safe Google Translate
        if hasattr(self, 'google_translator') and hasattr(self.google_translator, 'stats'):
            stats = self.google_translator.stats
            
            # Cập nhật requests
            self.stats_requests_label.config(text=f"Requests: {stats['total_requests']}")
            
            # Cập nhật cache hit rate
            total_accesses = stats['cache_hits'] + stats['cache_misses']
            if total_accesses > 0:
                hit_rate = (stats['cache_hits'] / total_accesses) * 100
                self.stats_cache_label.config(text=f"Cache: {hit_rate:.0f}%")
            
            # Cập nhật RPM (tính từ requests_this_minute)
            if hasattr(self.google_translator, 'requests_this_minute'):
                rpm = self.google_translator.requests_this_minute
                color = 'green' if rpm <= 25 else 'orange' if rpm <= 50 else 'red'
                self.stats_rpm_label.config(text=f"RPM: {rpm}", fg=color)
            
            # Cập nhật errors
            errors = stats['errors']
            error_color = 'green' if errors == 0 else 'orange' if errors < 5 else 'red'
            self.stats_errors_label.config(text=f"Errors: {errors}", fg=error_color)
        
    def set_translation_state(self, is_translating):
        """Thiết lập trạng thái đang dịch"""
        self.is_translating = is_translating
        if is_translating:
            self.start_btn.config(text="⏹️ Cancel Translation", bg="#e74c3c", 
                                 command=self.cancel_translation)
            self.status_label.config(text="🟡 Translating...", fg='#f39c12')
        else:
            self.start_btn.config(text="🚀 Start Translation", bg="#27ae60", 
                                 command=self.start_translation)
            self.status_label.config(text="🟢 Ready", fg='#27ae60')
            
    def cancel_translation(self):
        """Hủy quá trình dịch"""
        self.translation_cancelled = True
        self.status_label.config(text="🔴 Cancelling...", fg='#e74c3c')
        self.start_btn.config(state='disabled')

    def select_glossary(self):
        path = filedialog.askopenfilename(title="Select Glossary File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if path:
            self.glossary_path = path
            self.glossary_label.config(text=os.path.basename(path), fg="black")
        else:
            self.glossary_path = None
            self.glossary_label.config(text="None", fg="gray")


    def start_translation(self):
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please add at least one mod file to translate.")
            return
            
        # Kiểm tra translation service
        service = self.translation_service_var.get()
        if "DeepL" in service:
            deepl_api_key = self.api_key_var.get().strip()
            if not deepl_api_key:
                messagebox.showerror("DeepL API Key Missing", "Please enter your DeepL API Key.")
                return
        else:
            deepl_api_key = None  # Sử dụng Google Translate

        # Update logic to handle multiple zip files in the output directory
        output_dir = "output"  # Replace with actual output directory
        output_zip_files = list(Path(output_dir).glob("*.zip"))
        existing_mods = set()

        if output_zip_files:
            # Find the zip file with the highest version
            def extract_version(zip_name):
                try:
                    version_str = zip_name.stem.split("_")[-1]
                    return tuple(map(int, version_str.split(".")))
                except Exception:
                    return (0, 0, 0)  # Default version if parsing fails

            latest_zip = max(output_zip_files, key=lambda z: extract_version(z.name))

            with zipfile.ZipFile(latest_zip, 'r') as zipf:
                for name in zipf.namelist():
                    if name.endswith(".cfg"):
                        mod_name = Path(name).stem
                        existing_mods.add(mod_name)

        mods_to_translate = self.selected_files

        if not mods_to_translate:
            messagebox.showinfo("No Mods to Translate", "All selected mods are already translated.")
            return

        # Call the translation function (process_mods_to_language_pack)
        threading.Thread(target=self.run_translation, args=(mods_to_translate, deepl_api_key, output_dir, service)).start()

    def run_translation(self, mods_to_translate, deepl_api_key, output_dir, translation_service):
        self.progress["value"] = 0
        self.status_label.config(text="Translating mods...")
        translated_mods = []
        skipped_mods = []
        no_lang_mods = []

        try:
            # Process each mod zip file
            for mod_path in self.selected_files:
                with zipfile.ZipFile(mod_path, 'r') as zipf:
                    # Read info.json to get mod name
                    info_json_path = next((f for f in zipf.namelist() if f.endswith('info.json')), None)
                    if not info_json_path:
                        continue

                    with zipf.open(info_json_path) as f:
                        info = json.load(f)
                        mod_name = info.get("name", "unknown_mod")

                    # Find locale files in the zip using improved finder
                    root_folder, locale_files = find_locale_files_improved(mod_path)
                    
                    if not locale_files:
                        print(f"Warning: {mod_name} has no English locale *.cfg files, skipping...")
                        skipped_mods.append(mod_name)
                        continue

                    # Translate locale/en/*.cfg files using key->value mapping with English filtering
                    from mod_translate_core import parse_cfg_lines
                    all_values = []
                    file_entries = []  # list of (locale_file, key_vals, lines)
                    for locale_file in locale_files:
                        raw_text = read_cfg_file(zipf, locale_file)
                        key_vals, lines = parse_cfg_lines(raw_text)
                        
                        # Lọc chỉ nội dung tiếng Anh thực sự
                        if self.is_english_content(key_vals):
                            file_entries.append((locale_file, key_vals, lines))
                            all_values.extend([item['val'] for item in key_vals])
                            print(f"    ✅ Processed {len(key_vals)} English entries from {os.path.basename(locale_file)}")
                        else:
                            print(f"    ⚪ Skipped {os.path.basename(locale_file)} - not English content")

                    translated_values = []
                    if all_values:
                        # Lựa chọn translation service
                        if "Google" in translation_service:
                            if "Safe" in translation_service:
                                # Sử dụng Safe Google Translate
                                self.google_translator = SafeGoogleTranslateAPI()
                                print(f"    ⚙️ Using Safe Google Translate (Max 25 RPM, with caching)")
                            else:
                                # Sử dụng Fast Google Translate
                                self.google_translator = GoogleTranslateAPI()
                                print(f"    ⚡ Using Fast Google Translate (Higher speed, higher risk)")
                                
                            translated_values = self.google_translator.translate_texts(
                                all_values, 
                                self.lang_var.get(), 
                                'en',
                                progress_callback=lambda current, total, msg: self.update_progress_with_stats(current, total, msg)
                            )
                        else:
                            # Sử dụng DeepL API
                            endpoint = self.endpoint_var.get()
                            from mod_translate_core import translate_texts
                            translated_values = translate_texts(all_values, deepl_api_key, self.lang_var.get(), None, endpoint)
                    else:
                        no_lang_mods.append(mod_name)
                        continue

                    # Reconstruct files and merge into single mod cfg
                    merged_lines = []
                    tv_iter = iter(translated_values)
                    for locale_file, key_vals, lines in file_entries:
                        translated_lines = lines[:]
                        for item in key_vals:
                            try:
                                translated_val = next(tv_iter)
                            except StopIteration:
                                translated_val = item['val']
                            translated_lines[item['index']] = f"{item['key']}={translated_val}\n"
                        merged_lines.extend(translated_lines)

                    # Save translated file - chỉ lưu vào tạm thời nếu có template
                    if self.template_info:
                        # Lưu tạm file CFG để sau này copy vào template mới
                        temp_cfg_dir = Path("temp_translations")
                        temp_cfg_dir.mkdir(exist_ok=True)
                        mod_cfg_path = temp_cfg_dir / f"{mod_name}.cfg"
                        with open(mod_cfg_path, "w", encoding="utf-8") as f:
                            f.writelines(merged_lines)
                    else:
                        # Nếu không có template, lưu vào Code mau mặc định
                        mod_cfg_path = Path("Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0/locale/vi") / f"{mod_name}.cfg"
                        mod_cfg_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(mod_cfg_path, "w", encoding="utf-8") as f:
                            f.writelines(merged_lines)

                translated_mods.append(mod_name)

            # Tạo mod template mới nếu có template info
            if self.template_info and len(translated_mods) >= 1:
                try:
                    new_template_path = self.create_new_template_version(translated_mods)
                    if new_template_path:
                        result_message = (
                            f"Translation completed successfully!\n\n"
                            f"Translated Mods: {len(translated_mods)}\n"
                            f"Created new template: {os.path.basename(new_template_path)}\n\n"
                            f"Translated: {', '.join(translated_mods)}"
                        )
                    else:
                        result_message = (
                            f"Translation completed.\n\n"
                            f"Translated Mods: {len(translated_mods)}\n"
                            f"Note: Could not create new template version\n\n"
                            f"Translated: {', '.join(translated_mods)}"
                        )
                except Exception as e:
                    result_message = (
                        f"Translation completed with warning.\n\n"
                        f"Translated Mods: {len(translated_mods)}\n"
                        f"Template creation failed: {str(e)}\n\n"
                        f"Translated: {', '.join(translated_mods)}"
                    )
            else:
                # Hiển thị kết quả bình thường
                result_message = (
                    f"Translation completed.\n\n"
                    f"Translated Mods: {len(translated_mods)}\n"
                    f"Skipped Mods: {len(skipped_mods)}\n"
                    f"Mods without language files: {len(no_lang_mods)}\n\n"
                    f"Translated: {', '.join(translated_mods)}\n"
                    f"Skipped: {', '.join(skipped_mods)}\n"
                    f"No Language Files: {', '.join(no_lang_mods)}"
                )
            
            messagebox.showinfo("Translation Results", result_message)
            self.status_label.config(text="Translation completed.")
        except Exception as e:
            self.status_label.config(text=f"Error: {e}")

    def is_english_content(self, key_vals):
        """
        Kiểm tra nội dung có thực sự là tiếng Anh không
        Sử dụng thuật toán đơn giản: kiểm tra các từ thông dụng tiếng Anh
        """
        if not key_vals:
            return False
            
        # Các từ tiếng Anh thông dụng trong Factorio
        english_indicators = [
            'the', 'and', 'for', 'with', 'from', 'this', 'that', 'can', 'will', 'are', 'is',
            'iron', 'copper', 'steel', 'plate', 'gear', 'wire', 'engine', 'motor', 'belt',
            'inserter', 'assembling', 'machine', 'furnace', 'drill', 'mining', 'electric',
            'steam', 'boiler', 'generator', 'solar', 'panel', 'accumulator', 'lab',
            'science', 'pack', 'research', 'technology', 'recipe', 'item', 'entity'
        ]
        
        # Các ký tự ngôn ngữ khác
        non_english_chars = ['č', 'ř', 'ě', 'š', 'ž', 'ä', 'ö', 'ü', 'ß', 'à', 'â', 'ç', 'è', 'é', 'ê', 'ë', 'ñ']
        
        english_score = 0
        non_english_score = 0
        
        for item in key_vals:
            value = item['val'].strip().lower()
            if len(value) < 2:
                continue
                
            # Kiểm tra các từ tiếng Anh
            for indicator in english_indicators:
                if indicator in value:
                    english_score += 1
                    break
            
            # Kiểm tra các ký tự không phải tiếng Anh
            for char in non_english_chars:
                if char in value:
                    non_english_score += 2
                    break
        
        english_ratio = english_score / max(len(key_vals), 1)
        non_english_ratio = non_english_score / max(len(key_vals), 1)
        
        # Ít nhất 30% các entry có từ tiếng Anh và không quá 20% các entry có ký tự không phải tiếng Anh
        return english_ratio >= 0.3 and non_english_ratio <= 0.2
        
    def test_deepl_api(self):
        """Kiểm tra tính hợp lệ của mã DeepL API với UI feedback."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self.api_status_label.config(text="⚠️", fg='red')
            messagebox.showerror("Error", "Please enter your DeepL API Key.")
            return
            
        # Hiện thị trạng thái đang kiểm tra
        self.api_status_label.config(text="🔄", fg='blue')
        self.test_api_btn.config(state='disabled', text="Testing...")
        self.update_idletasks()
        
        def test_api_thread():
            try:
                # Sử dụng endpoint từ combobox
                endpoint = f"https://{self.endpoint_var.get()}/v2/usage"
                response = requests.get(endpoint, params={"auth_key": api_key}, timeout=10)
                
                if response.status_code == 200:
                    usage_data = response.json()
                    character_count = usage_data.get('character_count', 0)
                    character_limit = usage_data.get('character_limit', 0)
                    
                    # Cập nhật UI trên main thread
                    self.after(0, lambda: self.api_status_label.config(text="✅", fg='green'))
                    self.after(0, lambda: messagebox.showinfo("Success", 
                        f"DeepL API Key is valid!\n"
                        f"Usage: {character_count:,}/{character_limit:,} characters"))
                else:
                    error_message = "Unknown error"
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message", error_message)
                    except:
                        pass
                    
                    self.after(0, lambda: self.api_status_label.config(text="❌", fg='red'))
                    self.after(0, lambda: messagebox.showerror("Error", 
                        f"Invalid DeepL API Key.\nServer response: {error_message}"))
                        
            except requests.exceptions.Timeout:
                self.after(0, lambda: self.api_status_label.config(text="⏰", fg='orange'))
                self.after(0, lambda: messagebox.showerror("Error", "Request timeout. Please check your connection."))
            except requests.exceptions.RequestException as e:
                self.after(0, lambda: self.api_status_label.config(text="🌐", fg='red'))
                self.after(0, lambda: messagebox.showerror("Error", f"Network error: {str(e)}"))
            except Exception as e:
                self.after(0, lambda: self.api_status_label.config(text="⚠️", fg='red'))
                self.after(0, lambda: messagebox.showerror("Error", f"Unexpected error: {str(e)}"))
            finally:
                # Khôi phục trạng thái button
                self.after(0, lambda: self.test_api_btn.config(state='normal', text="🧪 Test API"))
                
        # Chạy test trên thread riêng
        threading.Thread(target=test_api_thread, daemon=True).start()

if __name__ == "__main__":
    app = ModTranslatorApp()
    app.mainloop()
