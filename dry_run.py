from pathlib import Path
import zipfile
import json

WORKSPACE = Path(__file__).parent
MODS_DIR = WORKSPACE / 'mods'
SAMPLE_DIR = WORKSPACE / 'Code mau' / 'Auto_Translate_Mod_Langue_Vietnamese_1.0.0'
SAMPLE_VI = SAMPLE_DIR / 'locale' / 'vi'

mods = []
if MODS_DIR.exists():
    mods = list(MODS_DIR.glob('*.zip'))
else:
    # also check root for zip files (excluding the sample zip)
    mods = [p for p in WORKSPACE.glob('*.zip') if 'Auto_Translate_Mod_Langue_Vietnamese' not in p.name]

if not mods:
    print('No mod .zip files found in mods/ or workspace root.')
    print('Place .zip files in the mods/ folder and run again.')
    exit(0)

would_translate = []
skipped_already = []
no_lang = []

for z in mods:
    try:
        with zipfile.ZipFile(z, 'r') as zf:
            namelist = zf.namelist()
            info_path = next((n for n in namelist if n.endswith('info.json')), None)
            if not info_path:
                print(f'{z.name}: no info.json found, skipping')
                continue
            with zf.open(info_path) as f:
                info = json.load(f)
            mod_name = info.get('name', z.stem)
            locale_files = [n for n in namelist if (n.startswith('locale/en/') or n.startswith('locale\\en\\')) and n.endswith('.cfg')]
            if not locale_files:
                no_lang.append(mod_name)
                print(f'{z.name}: no locale/en .cfg files found')
                continue
            target_cfg = SAMPLE_VI / f'{mod_name}.cfg'
            if target_cfg.exists():
                skipped_already.append(mod_name)
                print(f'{z.name}: already translated as {target_cfg}, will skip')
            else:
                would_translate.append(mod_name)
                print(f'{z.name}: would translate and produce {target_cfg.name}')
    except zipfile.BadZipFile:
        print(f'{z.name}: not a valid zip file')
        continue

print('\nSummary:')
print(f'  Found {len(mods)} zip(s)')
print(f'  Would translate: {len(would_translate)} -> {would_translate}')
print(f'  Skipped (already translated): {len(skipped_already)} -> {skipped_already}')
print(f'  No language files: {len(no_lang)} -> {no_lang}')

if len(would_translate) >= 1:
    print('\nNote: If this were a real run, program version WOULD be bumped and the sample folder would be renamed/packed.')
else:
    print('\nNo translations needed; version would NOT be changed.')
