import zipfile
import io
import json
import os

xapk_path = 'Last+Green_+Tower+Defense_1.1.1_APKPure.xapk'

# 1. Unpack source map from com.plantdefense.gp.apk
with zipfile.ZipFile(xapk_path) as xapk:
    main_apk_bytes = xapk.read('com.plantdefense.gp.apk')
    pad_bytes = xapk.read('pad_install.apk')

print("Extracting source maps from com.plantdefense.gp.apk...")
os.makedirs('decompiled_src', exist_ok=True)
with zipfile.ZipFile(io.BytesIO(main_apk_bytes)) as apk:
    map_data = apk.read('assets/assets/main/index.js.map')
    try:
        sm = json.loads(map_data.decode('utf-8'))
        sources = sm.get('sources', [])
        sources_content = sm.get('sourcesContent', [])
        print(f"Found {len(sources)} source files in index.js.map!")
        for idx, src_path in enumerate(sources):
            # Clean path
            clean_path = src_path.replace('db://assets/', '').replace('../', '')
            out_file = os.path.join('decompiled_src', clean_path)
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            content = sources_content[idx] if idx < len(sources_content) and sources_content[idx] else ''
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(content)
        print("Source files extracted successfully into decompiled_src!")
    except Exception as e:
        print(f"Error unpacking source map: {e}")

# 2. Search for Equipment JSON configs in pad_install.apk
print("\nSearching equipment configs in pad_install.apk...")
equip_configs = []

with zipfile.ZipFile(io.BytesIO(pad_bytes)) as apk:
    json_files = [n for n in apk.namelist() if n.endswith('.json') and 'import' in n]
    for n in json_files:
        try:
            data = apk.read(n).decode('utf-8')
            if any(k in data.lower() for k in ['equip', 'weapon', 'item', 'quality', 'atk', 'defense', 'rarity']):
                j = json.loads(data)
                def find_strings(obj):
                    if isinstance(obj, str):
                        yield obj
                    elif isinstance(obj, list):
                        for x in obj:
                            yield from find_strings(x)
                    elif isinstance(obj, dict):
                        for x in obj.values():
                            yield from find_strings(x)
                
                # Check string content or json object structure
                strs = list(find_strings(j))
                for s in strs:
                    if s.startswith('{') or s.startswith('['):
                        try:
                            parsed = json.loads(s)
                            if isinstance(parsed, (dict, list)) and any(k in str(parsed).lower() for k in ['equip', 'weapon', 'item_id', 'quality']):
                                equip_configs.append((n, len(data), parsed))
                        except:
                            pass
        except:
            pass

print(f"Found {len(equip_configs)} potential equipment JSON config files.")
os.makedirs('extracted_equipment', exist_ok=True)
for idx, (path, size, data) in enumerate(equip_configs[:20]):
    out_name = f"equip_config_{idx}.json"
    with open(os.path.join('extracted_equipment', out_name), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {out_name} (from {path}, {size} bytes)")
