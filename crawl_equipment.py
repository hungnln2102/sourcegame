import json
import os
import glob
import xml.etree.ElementTree as ET

# 1. Load Vietnamese localization for string resolution
vi_dict = {}

try:
    tree_vi = ET.parse('source/extracted_lang/localization_vi.xml')
    for elem in tree_vi.getroot().findall('string'):
        vi_dict[elem.attrib.get('name')] = elem.text or ''
except Exception as e:
    print(f"Error loading vi localization: {e}")

def resolve_text(text_val):
    if not text_val or not isinstance(text_val, str):
        return text_val
    return vi_dict.get(text_val, text_val)

# 2. Find the largest config JSON
files = glob.glob('source/extracted_equipment/*.json')
target_file = max(files, key=os.path.getsize)

with open(target_file, 'r', encoding='utf-8') as f:
    master_cfg = json.load(f)

# Extract Equipment Items
equipments = []

# Examine equip_item_auto
table_key = 'config/item/equip_item_auto'
table_data = master_cfg.get(table_key, {})

for item_id, item_info in table_data.items():
    if isinstance(item_info, dict):
        name = resolve_text(item_info.get('name', ''))
        desc = resolve_text(item_info.get('description', item_info.get('equip_dec', '')))
        
        entry = {
            "id": int(item_id),
            "name_raw": item_info.get('name', ''),
            "name": name,
            "rarity": item_info.get('color', 1),
            "part": item_info.get('part', 0),
            "atk_min": item_info.get('atk_min', 0),
            "atk_max": item_info.get('atk_max', 0),
            "hp_min": item_info.get('hp_min', 0),
            "hp_max": item_info.get('hp_max', 0),
            "description": desc.replace('\\n', '\n'),
            "icon_id": item_info.get('icon_id', 0)
        }
        equipments.append(entry)

# Sort by ID
equipments.sort(key=lambda x: x['id'])

print(f"Total extracted equipment items: {len(equipments)}")

out_file = 'equipments_crawled.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(equipments, f, indent=2, ensure_ascii=False)

# Export to CSV
import csv
csv_file = 'equipments_crawled.csv'
with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name", "rarity", "part", "atk_min", "atk_max", "hp_min", "hp_max", "description"])
    writer.writeheader()
    for eq in equipments:
        writer.writerow({
            "id": eq["id"],
            "name": eq["name"],
            "rarity": eq["rarity"],
            "part": eq["part"],
            "atk_min": eq["atk_min"],
            "atk_max": eq["atk_max"],
            "hp_min": eq["hp_min"],
            "hp_max": eq["hp_max"],
            "description": eq["description"].replace('\n', ' ')
        })

print(f"Saved crawled equipment data to {out_file} and {csv_file}!")

print(f"\nSample Equipment (First 15):")
for eq in equipments[:15]:
    print(f" - ID {eq['id']}: [{eq['name']}] (Rarity: {eq['rarity']}, Slot: {eq['part']}, ATK: {eq['atk_min']}-{eq['atk_max']}, HP: {eq['hp_min']}-{eq['hp_max']})")
