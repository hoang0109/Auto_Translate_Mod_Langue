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
from mod_translate_pack_core import process_mods_to_language_pack, find_locale_files
from mod_translate_core import read_cfg_file, translate_texts as core_translate_texts
from mod_translate_pack_core import translate_texts as pack_translate_texts

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
                api_key_enc = config['SETTINGS'].get('api_key', '')
                if api_key_enc:
                    try:
                        self.api_key_var.set(self.decrypt_api_key(api_key_enc))
                    except Exception:
                        self.api_key_var.set('')
        except Exception:
            messagebox.showwarning("Settings", "No settings found or failed to load.")
    def on_close(self):
        """Lưu thông tin trước khi thoát chương trình."""
        self.save_settings()  # Gọi hàm lưu settings hiện có
        self.destroy()  # Thoát chương trình

    def __init__(self):
        super().__init__()
        self.title("Factorio Mod Translator")
        self.geometry("600x400")
        self.resizable(False, False)
        self.selected_files = []
        self.glossary_path = None
        self.api_key_var = tk.StringVar(self)
        self.mod_name_var = tk.StringVar(self, value="Auto_Translate_Mod_Langue")
        self.protocol("WM_DELETE_WINDOW", self.on_close)  # Gắn sự kiện thoát chương trình
        self.create_widgets()
        self.load_settings()  # Tự động tải lại thiết lập từ file config.ini
        self.file_lock = Lock()

    def create_widgets(self):
        # Frame for file selection
        file_frame = tk.LabelFrame(self, text="Select Mod Files (.zip)")
        file_frame.pack(fill="x", padx=10, pady=10)

        self.file_listbox = tk.Listbox(file_frame, height=5)
        self.file_listbox.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        file_btn_frame = tk.Frame(file_frame)
        file_btn_frame.pack(side="right", fill="y")
        tk.Button(file_btn_frame, text="Add Files", command=self.add_files).pack(fill="x", pady=2)
        tk.Button(file_btn_frame, text="Remove Selected", command=self.remove_selected).pack(fill="x", pady=2)

        # Mod Name input
        name_frame = tk.Frame(self)
        name_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(name_frame, text="Custom Mod Name:").pack(side="left")
        name_entry = tk.Entry(name_frame, textvariable=self.mod_name_var, width=40)
        name_entry.pack(side="left", padx=5)

        # API Key input
        api_frame = tk.Frame(self)
        api_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(api_frame, text="DeepL API Key:").pack(side="left")
        api_entry = tk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=40)
        api_entry.pack(side="left", padx=5)
        # Test DeepL API button
        tk.Button(api_frame, text="Test DeepL API", command=self.test_deepl_api).pack(side="left", padx=5)

    # Language selection
        # Language selection
        lang_frame = tk.Frame(self)
        lang_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(lang_frame, text="Target Language:").pack(side="left")
        self.lang_var = tk.StringVar(value="VI")
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=["VI", "JA", "EN", "ZH", "FR", "DE", "ES"], state="readonly", width=10)
        self.lang_combo.pack(side="left", padx=5)

        # Endpoint selection
        endpoint_frame = tk.Frame(self)
        endpoint_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(endpoint_frame, text="DeepL Endpoint:").pack(side="left")
        self.endpoint_var = tk.StringVar(value="api.deepl.com")
        endpoint_combo = ttk.Combobox(endpoint_frame, textvariable=self.endpoint_var, values=["api.deepl.com", "api-free.deepl.com"], state="readonly", width=20)
        endpoint_combo.pack(side="left", padx=5)

        # Progress and status
        self.progress = ttk.Progressbar(self, orient="horizontal", length=580, mode="determinate")
        self.progress.pack(padx=10, pady=5)
        self.status_label = tk.Label(self, text="Ready.", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)

        # Start Translation button321
        tk.Button(self, text="Start Translation", command=self.start_translation, height=2, bg="#4CAF50", fg="white").pack(fill="x", padx=10, pady=10)

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
        deepl_api_key = self.api_key_var.get().strip()
        if not deepl_api_key:
            messagebox.showerror("DeepL API Key Missing", "Please enter your DeepL API Key.")
            return

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
        threading.Thread(target=self.run_translation, args=(mods_to_translate, deepl_api_key, output_dir)).start()

    def run_translation(self, mods_to_translate, deepl_api_key, output_dir):
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

                    # Find locale files in the zip
                    locale_files = [f for f in zipf.namelist() if f.startswith("locale/en/") and f.endswith(".cfg")]

                    # Translate locale/en/*.cfg files using key->value mapping
                    from mod_translate_core import parse_cfg_lines
                    all_values = []
                    file_entries = []  # list of (locale_file, key_vals, lines)
                    for locale_file in locale_files:
                        raw_text = read_cfg_file(zipf, locale_file)
                        key_vals, lines = parse_cfg_lines(raw_text)
                        file_entries.append((locale_file, key_vals, lines))
                        all_values.extend([item['val'] for item in key_vals])

                    translated_values = []
                    if all_values:
                        endpoint = self.endpoint_var.get()
                        translated_values = core_translate_texts(all_values, deepl_api_key, self.lang_var.get(), None, endpoint)

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

                    # Save translated file to locale/vi
                    mod_cfg_path = Path("Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0/locale/vi") / f"{mod_name}.cfg"
                    mod_cfg_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(mod_cfg_path, "w", encoding="utf-8") as f:
                        f.writelines(merged_lines)

                    # Update dependencies in info.json
                    program_info_path = "Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0/info.json"
                    with open(program_info_path, "r", encoding="utf-8") as f:
                        program_info = json.load(f)
                    dependencies = program_info.get("dependencies", [])
                    if mod_name not in dependencies:
                        dependencies.append(f"? {mod_name}")
                    program_info["dependencies"] = dependencies
                    with open(program_info_path, "w", encoding="utf-8") as f:
                        json.dump(program_info, f, ensure_ascii=False, indent=2)

                translated_mods.append(mod_name)

            # Update version in info.json if mods were translated
            if len(translated_mods) >= 1:
                program_info_path = "Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0/info.json"
                with open(program_info_path, "r", encoding="utf-8") as f:
                    program_info = json.load(f)

                # Increment version
                old_version = program_info.get("version", "1.0.0")
                # Normalize and increment semantic version safely
                parts = old_version.split('.')
                while len(parts) < 3:
                    parts.append('0')
                try:
                    version_parts = [int(p) for p in parts]
                except ValueError:
                    # fallback to timestamp-based version
                    new_version = datetime.now().strftime('%Y.%m.%d')
                else:
                    version_parts[-1] += 1
                    new_version = '.'.join(map(str, version_parts))
                program_info["version"] = new_version

                # Determine old and new folder paths BEFORE writing to them
                old_folder = Path("Code mau/Auto_Translate_Mod_Langue_Vietnamese_1.0.0")
                new_folder = Path(f"Code mau/Auto_Translate_Mod_Langue_Vietnamese_{new_version}")

                # Ensure old_folder exists
                if not old_folder.exists():
                    # create from template if missing or raise
                    messagebox.showwarning("Warning", f"Template folder {old_folder} not found.")
                    old_folder.mkdir(parents=True, exist_ok=True)

                # If destination exists, backup
                if new_folder.exists():
                    backup_folder = Path(f"{str(new_folder)}.backup_{int(time.time())}")
                    new_folder.rename(backup_folder)

                # Write updated program info into old folder before rename
                program_info_path_old = old_folder / 'info.json'
                with open(program_info_path_old, 'w', encoding='utf-8') as f:
                    json.dump(program_info, f, ensure_ascii=False, indent=2)

                changelog_path_old = old_folder / 'changelog.txt'
                with open(changelog_path_old, 'a', encoding='utf-8') as f:
                    f.write(f"\nVersion {new_version}:\n")
                    f.write("\n".join([f"- Translated mod: {mod}" for mod in translated_mods]))

                # Now rename
                old_folder.rename(new_folder)

                # Create zip file from new_folder
                zip_path = Path(f"Code mau/Auto_Translate_Mod_Langue_Vietnamese_{new_version}.zip")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for foldername, subfolders, filenames in os.walk(new_folder):
                        for filename in filenames:
                            file_path = Path(foldername) / filename
                            arcname = file_path.relative_to(new_folder.parent)
                            zipf.write(file_path, arcname)

                messagebox.showinfo("Mod Update", f"Mod updated to version {new_version} and zipped at: {zip_path}")

            # Display results
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

    def test_deepl_api(self):
        """Kiểm tra tính hợp lệ của mã DeepL API."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your DeepL API Key.")
            return
        try:
            # Sử dụng endpoint từ combobox
            endpoint = f"https://{self.endpoint_var.get()}/v2/usage"
            response = requests.get(endpoint, params={"auth_key": api_key})
            if response.status_code == 200:
                messagebox.showinfo("Success", "DeepL API Key is valid.")
            else:
                error_message = response.json().get("message", "Unknown error")
                messagebox.showerror("Error", f"Invalid DeepL API Key. Server response: {error_message}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Network error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    app = ModTranslatorApp()
    app.mainloop()
