import zipfile
import io
import json
import os

xapk_path = 'Last+Green_+Tower+Defense_1.1.1_APKPure.xapk'

with zipfile.ZipFile(xapk_path) as xapk:
    apk_bytes = xapk.read('pad_install.apk')

localization_files = {}
all_text_assets = []

with zipfile.ZipFile(io.BytesIO(apk_bytes)) as apk:
    json_files = [n for n in apk.namelist() if n.endswith('.json') and 'import' in n]
    print(f"Total import JSON files: {len(json_files)}")
    
    for n in json_files:
        data = apk.read(n)
        try:
            content = data.decode('utf-8')
            if 'cc.TextAsset' in content:
                jdata = json.loads(content)
                # Cocos Creator text asset structure
                if len(jdata) >= 3 and isinstance(jdata[-1], list):
                    for item in jdata[-1]:
                        if isinstance(item, list) and len(item) >= 3:
                            asset_name = str(item[1])
                            asset_text = str(item[2])
                            all_text_assets.append((asset_name, n, len(asset_text)))
                            if any(k in asset_name.lower() for k in ['local', 'lang', 'string', 'text', 'xml', 'csv', 'i18n']):
                                localization_files[asset_name] = (n, asset_text)
        except Exception as e:
            pass

print(f"\nAll Text Assets found ({len(all_text_assets)}):")
for name, path, length in all_text_assets:
    print(f" - {name} ({length} bytes) -> {path}")

print(f"\nExtracted {len(localization_files)} matching localization files:")
os.makedirs('extracted_lang', exist_ok=True)
for name, (path, content) in localization_files.items():
    filename = name if any(name.endswith(ext) for ext in ['.xml', '.json', '.txt', '.csv', '.tsv', '.yaml']) else f"{name}.xml"
    out_path = os.path.join('extracted_lang', filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved: {out_path} ({len(content)} chars)")
