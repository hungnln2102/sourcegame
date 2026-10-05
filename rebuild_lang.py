import zipfile
import io
import json
import os
import shutil

# Files configuration
original_xapk = 'Last+Green_+Tower+Defense_1.1.1_APKPure.xapk'
modded_xapk = 'Last_Green_Tower_Defense_Modded.xapk'
lang_folder = os.path.join('source', 'extracted_lang')

print(f"Reading original XAPK: {original_xapk}")
with zipfile.ZipFile(original_xapk, 'r') as xapk:
    xapk_items = {item.filename: xapk.read(item.filename) for item in xapk.infolist()}

pad_install_bytes = xapk_items['pad_install.apk']
print(f"Loaded pad_install.apk ({len(pad_install_bytes)} bytes)")

# We will modify the pad_install in memory
new_pad_install = io.BytesIO()

with zipfile.ZipFile(io.BytesIO(pad_install_bytes), 'r') as apk_in:
    with zipfile.ZipFile(new_pad_install, 'w', zipfile.ZIP_DEFLATED) as apk_out:
        for item in apk_in.infolist():
            content = apk_in.read(item.filename)
            
            # Check if this file is one of the target localization json files
            if item.filename.endswith('.json') and 'import' in item.filename:
                try:
                    text_content = content.decode('utf-8')
                    if 'localization_' in text_content:
                        # Find which language it is
                        j = json.loads(text_content)
                        
                        def find_strings(obj):
                            if isinstance(obj, str):
                                yield obj
                            elif isinstance(obj, list):
                                for x in obj:
                                    yield from find_strings(x)
                            elif isinstance(obj, dict):
                                for x in obj.values():
                                    yield from find_strings(x)
                                    
                        all_strings = list(find_strings(j))
                        loc_name = next((s for s in all_strings if s.startswith('localization_')), None)
                        
                        # Check if we have an edited XML for this language
                        if loc_name:
                            xml_path = os.path.join(lang_folder, f'{loc_name}.xml')
                            if os.path.exists(xml_path):
                                print(f"Found modified XML for {loc_name}, injecting into {item.filename}...")
                                with open(xml_path, 'r', encoding='utf-8') as f:
                                    new_xml_str = f.read()
                                
                                # Replace the XML string in the JSON structure
                                # Cocos format: j[-1][0][2] is usually the text content.
                                # Let's dynamically find and replace it
                                if len(j) >= 3 and isinstance(j[-1], list) and isinstance(j[-1][0], list) and len(j[-1][0]) >= 3:
                                    if j[-1][0][1] == loc_name:
                                        j[-1][0][2] = new_xml_str
                                        # Re-encode JSON
                                        content = json.dumps(j, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
                                        print(f" -> Successfully replaced {loc_name}!")
                except Exception as e:
                    pass
            
            # Write out to new pad_install.apk
            apk_out.writestr(item, content)

# Update the pad_install.apk in the XAPK dictionary
xapk_items['pad_install.apk'] = new_pad_install.getvalue()

print(f"\nWriting new XAPK to {modded_xapk}...")
with zipfile.ZipFile(modded_xapk, 'w', zipfile.ZIP_DEFLATED) as xapk_out:
    for filename, filebytes in xapk_items.items():
        xapk_out.writestr(filename, filebytes)

print(f"Done! Modified XAPK saved as {modded_xapk}")
print("NOTE: You will need to extract the APKs and re-sign them (e.g. using Uber Apk Signer) before installing on an Android device!")
