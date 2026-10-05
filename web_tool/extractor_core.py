import zipfile
import io
import json
import os
import re
import sys
import shutil
import texture2ddecoder
from PIL import Image

Base64KeyChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
hex_map = [None] * 128
for i, c in enumerate(Base64KeyChars): 
    hex_map[ord(c)] = i

def decode_uuid(b64):
    if not isinstance(b64, str) or len(b64) != 22: 
        return str(b64)
    res = list(b64[:2]) + [''] * 34
    res[8] = res[13] = res[18] = res[23] = '-'
    j = 2
    for i in range(2, 22, 2):
        lhs = hex_map[ord(b64[i])]
        rhs = hex_map[ord(b64[i+1])]
        res[j] = '0123456789abcdef'[lhs >> 2]
        j += 1; j += 1 if j < 36 and res[j] == '-' else 0
        res[j] = '0123456789abcdef'[((lhs & 3) << 2) | (rhs >> 4)]
        j += 1; j += 1 if j < 36 and res[j] == '-' else 0
        res[j] = '0123456789abcdef'[rhs & 0xF]
        j += 1; j += 1 if j < 36 and res[j] == '-' else 0
    return ''.join(res)

def decode_astc_to_png(data):
    if len(data) < 16 or data[:4].hex() != '13aba15c':
        return None
    bx = data[4]
    by = data[5]
    bz = data[6]
    width = data[7] | (data[8] << 8) | (data[9] << 16)
    height = data[10] | (data[11] << 8) | (data[12] << 16)
    
    if bx < 4 or bx > 12 or by < 4 or by > 12:
        return None
        
    raw_astc = data[16:]
    try:
        decoded = texture2ddecoder.decode_astc(raw_astc, width, height, bx, by)
        img = Image.frombytes('RGBA', (width, height), decoded, 'raw', 'BGRA')
        return img
    except Exception:
        return None

ASSET_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp3', '.wav', '.ogg', '.m4a', '.mp4', '.json', '.xml', '.csv', '.txt', '.yaml', '.yml', '.ini', '.atlas', '.skel', '.ttf', '.otf', '.woff', '.obj', '.fbx', '.gltf', '.glb', '.bin', '.astc', '.etc2', '.pvr', '.ktx', '.bytes', '.lua', '.db'}

def extract_file(file_bytes, ext, logical_path, temp_extract_dir):
    clean_rel_path = re.sub(r'[\\:*?"<>|]', '_', logical_path)
    dest_file = os.path.join(temp_extract_dir, clean_rel_path)
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    
    converted = False
    if ext == '.astc':
        img = decode_astc_to_png(file_bytes)
        if img:
            dest_file += '.png'
            try:
                img.save(dest_file)
                converted = True
                return True, converted
            except: pass
        dest_file += ext
    else:
        dest_file += ext
        
    with open(dest_file, 'wb') as f:
        f.write(file_bytes)
    return True, converted

def process_package(input_file, progress_callback=None):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    temp_extract_dir = os.path.join(os.path.dirname(input_file), f"extracted_{base_name}")
    output_zip = os.path.join(os.path.dirname(input_file), f"{base_name}_extracted_assets.zip")
    
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    if progress_callback:
        progress_callback("Đang đọc file APK/XAPK...", 10)
        
    exported_count = 0
    converted_astc = 0
    path_mapping = {}
    
    try:
        with zipfile.ZipFile(input_file) as package:
            all_files = package.namelist()
            apk_files = [f for f in all_files if f.endswith('.apk')]
            
            # Step 1: Scan for config (Cocos UUID mapping)
            scan_files = []
            if apk_files:
                for apk_name in apk_files:
                    apk_bytes = package.read(apk_name)
                    with zipfile.ZipFile(io.BytesIO(apk_bytes)) as apk:
                        for n in apk.namelist():
                            if ('cc.config.' in n or 'config.' in n) and n.endswith('.json'):
                                scan_files.append((apk, n))
            else:
                for n in all_files:
                    if ('cc.config.' in n or 'config.' in n) and n.endswith('.json'):
                        scan_files.append((package, n))

            for apk_obj, n in scan_files:
                try:
                    cfg = json.loads(apk_obj.read(n).decode('utf-8'))
                    uuids = cfg.get('uuids', [])
                    paths = cfg.get('paths', {})
                    for idx_str, val in paths.items():
                        p = val[0]
                        if int(idx_str) < len(uuids):
                            raw_uid = uuids[int(idx_str)]
                            dec_uid = decode_uuid(raw_uid).split('@')[0]
                            path_mapping.setdefault(dec_uid, []).append(p)
                except Exception:
                    pass
            
            is_cocos = len(path_mapping) > 0
            msg = f"Lập bản đồ thành công {len(path_mapping)} UUID assets." if is_cocos else "Không tìm thấy map Cocos, sẽ trích xuất Standard Assets."
            if progress_callback:
                progress_callback(f"{msg} Đang trích xuất...", 40)
                
            # Step 2: Extract
            if apk_files:
                for apk_name in apk_files:
                    apk_bytes = package.read(apk_name)
                    with zipfile.ZipFile(io.BytesIO(apk_bytes)) as apk:
                        for n in apk.namelist():
                            basename = os.path.basename(n)
                            if '.' not in basename: continue
                            ext = os.path.splitext(n)[1].lower()
                            
                            if is_cocos:
                                uid = basename.split('.')[0].split('@')[0]
                                if uid in path_mapping:
                                    file_bytes = apk.read(n)
                                    for logical_path in path_mapping[uid]:
                                        success, conv = extract_file(file_bytes, ext, logical_path, temp_extract_dir)
                                        if success: exported_count += 1
                                        if conv: converted_astc += 1
                            else:
                                # Trích xuất TOÀN BỘ file trong assets/ và res/ (không bỏ sót bất kỳ file hay extension nào)
                                if 'assets/' in n or 'res/' in n:
                                    file_bytes = apk.read(n)
                                    logical_path = n.replace('assets/', '').replace('res/', '')
                                    if logical_path.strip():
                                        clean_rel_path = re.sub(r'[\\:*?"<>|]', '_', logical_path)
                                        dest_file = os.path.join(temp_extract_dir, clean_rel_path)
                                        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                                        with open(dest_file, 'wb') as f:
                                            f.write(file_bytes)
                                        exported_count += 1
            else:
                for n in all_files:
                    basename = os.path.basename(n)
                    if not basename: continue
                    ext = os.path.splitext(n)[1].lower()
                    
                    if is_cocos:
                        uid = basename.split('.')[0].split('@')[0]
                        if uid in path_mapping:
                            file_bytes = package.read(n)
                            for logical_path in path_mapping[uid]:
                                success, conv = extract_file(file_bytes, ext, logical_path, temp_extract_dir)
                                if success: exported_count += 1
                                if conv: converted_astc += 1
                    else:
                        if 'assets/' in n or 'res/' in n:
                            file_bytes = package.read(n)
                            logical_path = n.replace('assets/', '').replace('res/', '')
                            if logical_path.strip():
                                clean_rel_path = re.sub(r'[\\:*?"<>|]', '_', logical_path)
                                dest_file = os.path.join(temp_extract_dir, clean_rel_path)
                                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                                with open(dest_file, 'wb') as f:
                                    f.write(file_bytes)
                                exported_count += 1

            if progress_callback:
                progress_callback("Đang nén kết quả thành file ZIP...", 85)

            if exported_count > 0:
                shutil.make_archive(output_zip.replace('.zip', ''), 'zip', temp_extract_dir)
            else:
                # Tạo file zip rỗng hoặc ném lỗi
                with zipfile.ZipFile(output_zip, 'w') as zip_empty:
                    pass
            shutil.rmtree(temp_extract_dir)
            
            if progress_callback:
                progress_callback("Hoàn tất giải nén 100%!", 100)
                
            return output_zip, exported_count, converted_astc

    except Exception as e:
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        raise e
