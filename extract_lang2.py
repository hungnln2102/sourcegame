import zipfile
import io
import json
import re
import os

xapk_path = 'Last+Green_+Tower+Defense_1.1.1_APKPure.xapk'
with zipfile.ZipFile(xapk_path) as xapk:
    apk_bytes = xapk.read('pad_install.apk')

os.makedirs('extracted_lang', exist_ok=True)

with zipfile.ZipFile(io.BytesIO(apk_bytes)) as apk:
    json_files = [n for n in apk.namelist() if n.endswith('.json') and 'import' in n]
    for n in json_files:
        data = apk.read(n)
        try:
            content = data.decode('utf-8')
            if 'localization_' in content:
                print(f'Found localization_ in {n}')
                try:
                    j = json.loads(content)
                    # Cocos structure: [1,0,0,[...],[[...]],[[0,"localization_en","<?xml ... "]]]
                    # Look for strings starting with <?xml
                    
                    def find_strings(obj):
                        if isinstance(obj, str):
                            yield obj
                        elif isinstance(obj, list):
                            for item in obj:
                                yield from find_strings(item)
                        elif isinstance(obj, dict):
                            for item in obj.values():
                                yield from find_strings(item)
                    
                    all_strings = list(find_strings(j))
                    loc_name = next((s for s in all_strings if s.startswith('localization_')), None)
                    xml_str = next((s for s in all_strings if s.startswith('<?xml')), None)
                    
                    if loc_name and xml_str:
                        with open(f'extracted_lang/{loc_name}.xml', 'w', encoding='utf-8') as f:
                            f.write(xml_str)
                        print(f'Extracted {loc_name}.xml ({len(xml_str)} bytes)')
                    
                except Exception as e:
                    print('JSON load error:', e)
        except Exception as e:
            pass
