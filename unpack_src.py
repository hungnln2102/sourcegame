import zipfile
import io
import json
import os
import re

xapk_path = 'Last+Green_+Tower+Defense_1.1.1_APKPure.xapk'

with zipfile.ZipFile(xapk_path) as xapk:
    main_apk_bytes = xapk.read('com.plantdefense.gp.apk')

print("Extracting source maps from com.plantdefense.gp.apk...")
os.makedirs('decompiled_src', exist_ok=True)
with zipfile.ZipFile(io.BytesIO(main_apk_bytes)) as apk:
    map_data = apk.read('assets/assets/main/index.js.map')
    sm = json.loads(map_data.decode('utf-8'))
    sources = sm.get('sources', [])
    sources_content = sm.get('sourcesContent', [])
    print(f"Found {len(sources)} source files in index.js.map!")
    
    success_count = 0
    for idx, src_path in enumerate(sources):
        # Sanitize Windows path
        clean_path = src_path
        clean_path = re.sub(r'^[a-zA-Z]+:///?', '', clean_path)
        clean_path = clean_path.replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        clean_path = clean_path.replace('../', '').replace('..\\', '')
        
        out_file = os.path.join('decompiled_src', clean_path)
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        content = sources_content[idx] if idx < len(sources_content) and sources_content[idx] else ''
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)
        success_count += 1
    print(f"Successfully wrote {success_count} source files into decompiled_src!")

