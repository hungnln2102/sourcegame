import pandas as pd
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

excel_path = 'lang_export.xlsx'
out_folder = 'extracted_lang'

if not os.path.exists(excel_path):
    print(f"Error: {excel_path} not found.")
    sys.exit(1)

print(f"Reading {excel_path}...")
df = pd.read_excel(excel_path)
df = df.fillna('')

# Identify language columns (exclude ID and mz)
ignore_cols = {'ID', 'mz'}
lang_cols = [c for c in df.columns if c not in ignore_cols]

os.makedirs(out_folder, exist_ok=True)

for lang in lang_cols:
    root = ET.Element('resources')
    
    for _, row in df.iterrows():
        id_str = str(row['ID']).strip()
        mz_str = str(row.get('mz', '')).strip()
        text_str = str(row.get(lang, ''))
        
        if not id_str:
            continue
            
        elem = ET.SubElement(root, 'string', name=id_str)
        if mz_str:
            elem.set('mz', mz_str)
        elem.text = text_str
        
    # Convert to formatted XML
    xml_bytes = ET.tostring(root, encoding='utf-8')
    dom = xml.dom.minidom.parseString(xml_bytes)
    pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')

    out_file = os.path.join(out_folder, f"localization_{lang}.xml")
    with open(out_file, 'wb') as f:
        f.write(pretty_xml)
        
    print(f"Updated {out_file}")

print("\nDone! All XML language files have been updated from Excel.")
