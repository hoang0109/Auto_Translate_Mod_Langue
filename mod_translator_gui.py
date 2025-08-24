import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import os
import threading
from mod_translate_pack_core import process_mods_to_language_pack

class ModTranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Factorio Mod Translator")
        self.geometry("600x400")
        self.resizable(False, False)
        self.selected_files = []
        self.glossary_path = None
        self.create_widgets()

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

        # Language selection
        lang_frame = tk.Frame(self)
        lang_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(lang_frame, text="Target Language:").pack(side="left")
        self.lang_var = tk.StringVar(value="VI")
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=["VI", "JA", "EN", "ZH", "FR", "DE", "ES"], state="readonly", width=10)
        self.lang_combo.pack(side="left", padx=5)

        # Glossary selection (optional)
        glossary_frame = tk.Frame(self)
        glossary_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(glossary_frame, text="Glossary (optional):").pack(side="left")
        self.glossary_label = tk.Label(glossary_frame, text="None", fg="gray")
        self.glossary_label.pack(side="left", padx=5)
        tk.Button(glossary_frame, text="Select Glossary", command=self.select_glossary).pack(side="left")

        # Start button
        tk.Button(self, text="Start Translation", command=self.start_translation, height=2, bg="#4CAF50", fg="white").pack(fill="x", padx=10, pady=10)

        # Progress and status
        self.progress = ttk.Progressbar(self, orient="horizontal", length=580, mode="determinate")
        self.progress.pack(padx=10, pady=5)
        self.status_label = tk.Label(self, text="Ready.", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)

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
        deepl_api_key = os.environ.get("DEEPL_API_KEY")
        if not deepl_api_key:
            messagebox.showerror("DeepL API Key Missing", "Please set the DEEPL_API_KEY environment variable.")
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
                # Tạo hàm callback để cập nhật tiến độ
                def progress_callback(current, total, mod_name):
                    percent = int((current/total)*100)
                    self.progress['value'] = percent
                    self.status_label.config(text=f"Translating: {mod_name} ({current}/{total})")
                    self.update_idletasks()
                # Sửa hàm core để nhận callback
                from mod_translate_pack_core import process_mods_to_language_pack
                mod_out_dir = process_mods_to_language_pack(
                    self.selected_files,
                    mod_sample_dir,
                    output_dir,
                    deepl_api_key,
                    target_lang,
                    lang_code,
                    glossary_id,
                    progress_callback
                )
                self.status_label.config(text=f"Done. Output: {mod_out_dir}")
                self.progress['value'] = 100
                messagebox.showinfo("Translation Finished", f"Language pack created: {mod_out_dir}")
            except Exception as e:
                self.status_label.config(text="Error!")
                messagebox.showerror("Error", str(e))
            self.progress['value'] = 0
        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = ModTranslatorApp()
    app.mainloop()
