import configparser
import uuid
import base64
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import os
import threading
from mod_translate_pack_core import process_mods_to_language_pack

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

        # Start Translation button
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
        target_lang = self.lang_var.get().upper()
        lang_code = target_lang.lower()
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        # Path to mod mẫu (Translate_planet_into_Japanese) do người dùng cung cấp
        mod_sample_dir = r"C:\\Users\\Acer\\Desktop\\Translate_planet_into_Japanese_1.2.5\\Translate_planet_into_Japanese\\Code mau\\Translate_planet_into_Japanese"
        glossary_id = None
        self.progress['value'] = 0
        self.status_label.config(text="Translating... Please wait.")
        self.update()
        def worker():
            try:
                total = len(self.selected_files)
                custom_mod_name = self.mod_name_var.get().strip() or "Auto_Translate_Mod_Langue"
                def progress_callback(current, total, mod_name):
                    percent = int((current/total)*100)
                    self.progress['value'] = percent
                    self.status_label.config(text=f"Translating: {mod_name} ({current}/{total})")
                    self.update_idletasks()
                from mod_translate_pack_core import process_mods_to_language_pack
                mod_out_dir = process_mods_to_language_pack(
                    self.selected_files,
                    mod_sample_dir,
                    output_dir,
                    deepl_api_key,
                    target_lang,
                    lang_code,
                    glossary_id,
                    progress_callback,
                    custom_mod_name
                )
                self.status_label.config(text=f"Done. Output: {mod_out_dir}")
                self.progress['value'] = 100
                messagebox.showinfo("Translation Finished", f"Language pack created: {mod_out_dir}")
            except Exception as e:
                self.status_label.config(text="Error!")
                messagebox.showerror("Error", str(e))
            self.progress['value'] = 0
        threading.Thread(target=worker, daemon=True).start()

    def test_deepl_api(self):
        """Kiểm tra tính hợp lệ của mã DeepL API."""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your DeepL API Key.")
            return
        try:
            import requests
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
