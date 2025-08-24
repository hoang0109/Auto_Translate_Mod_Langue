import os
import zipfile
import tempfile
import re
import requests
from pathlib import Path

def find_locale_files(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            namelist = zipf.namelist()
            if not namelist:
                return None, []
            root_folder = None
            for item in namelist:
                if 'info.json' in item and item.count('/') == 1:
                    root_folder = item.split('/')[0]
                    break
            if root_folder is None:
                for item in namelist:
                    if '/' in item:
                        root_folder = item.split('/')[0]
                        break
            if root_folder is None:
                return None, []
            search_prefix = f"{root_folder}/locale/en/"
            locale_files = [f for f in namelist if f.startswith(search_prefix) and f.endswith(".cfg")]
            return root_folder, locale_files
    except zipfile.BadZipFile:
        return None, []
    except Exception:
        return None, []

def read_cfg_file(zipf, file_path):
    with zipf.open(file_path) as f:
        content = f.read()
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content.decode('utf-8-sig')

def write_cfg_file(content_lines, dest_path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.writelines(content_lines)

def translate_texts(texts, deepl_api_key, target_lang, glossary_id=None):
    if not texts:
        return []
    data = {
        "auth_key": deepl_api_key,
        "text": texts,
        "target_lang": target_lang,
        "tag_handling": "xml"
    }
    if glossary_id:
        data["glossary_id"] = glossary_id
    response = requests.post(
        "https://api-free.deepl.com/v2/translate",
        data=data
    )
    response.raise_for_status()
    translated = [line["text"] for line in response.json()["translations"]]
    return translated

def parse_cfg_lines(raw_text):
    lines = raw_text.splitlines(keepends=True)
    key_val_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith(";"):
            key, val = re.split(r'=', stripped, 1)
            key_val_lines.append({'index': i, 'key': key.strip(), 'val': val.strip()})
    return key_val_lines, lines

def process_mod(zip_path, output_dir, deepl_api_key, target_lang, glossary_id=None):
    zip_name = os.path.basename(zip_path)
    root_folder, locale_files = find_locale_files(zip_path)
    if not root_folder or not locale_files:
        return False, f"No locale files found in {zip_name}"
    with zipfile.ZipFile(zip_path, 'r') as zipf, tempfile.TemporaryDirectory() as tmpdir:
        mod_root = Path(tmpdir) / root_folder
        zipf.extractall(tmpdir)
        all_key_vals = []
        file_structure = {}
        for locale_file in locale_files:
            raw_text = read_cfg_file(zipf, locale_file)
            key_vals, lines = parse_cfg_lines(raw_text)
            all_key_vals.extend(key_vals)
            file_structure[locale_file] = {'key_vals': key_vals, 'lines': lines}
        values_to_translate = [item['val'] for item in all_key_vals]
        if not values_to_translate:
            return False, f"No text to translate in {zip_name}"
        try:
            translated_texts = translate_texts(values_to_translate, deepl_api_key, target_lang, glossary_id)
            if len(translated_texts) != len(values_to_translate):
                return False, "Translation count mismatch"
        except Exception as e:
            return False, str(e)
        translated_iter = iter(translated_texts)
        for locale_file, data in file_structure.items():
            lines = data['lines']
            key_vals = data['key_vals']
            translated_lines = lines[:]
            for item in key_vals:
                translated_val = next(translated_iter)
                translated_lines[item['index']] = f"{item['key']}={translated_val}\n"
            src_path_rel = Path(locale_file).relative_to(root_folder)
            vi_path = mod_root / "locale" / target_lang.lower() / src_path_rel.name
            write_cfg_file(translated_lines, vi_path)
        output_zip = Path(output_dir) / zip_name
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zout:
            for folder_path, _, files in os.walk(mod_root):
                for file in files:
                    full_path = Path(folder_path) / file
                    rel_path = full_path.relative_to(mod_root.parent)
                    zout.write(full_path, rel_path)
    return True, str(output_zip)
