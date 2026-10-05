import zipfile
import io
import json
import os
import re
import sys
import texture2ddecoder
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

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
        return None # Avoid ASTC crash on invalid blocks
        
    raw_astc = data[16:]
    try:
        decoded = texture2ddecoder.decode_astc(raw_astc, width, height, bx, by)
        img = Image.frombytes('RGBA', (width, height), decoded, 'raw', 'BGRA')
        return img
    except Exception:
        return None

def main():
    xapk_path = 'Last+Green_+Tower+Defense_1.1.1_APKPure.xapk'
    out_dir = os.path.join('source', 'exported_assets_full')
    
    print(f"Bắt đầu giải nén TOÀN BỘ tài nguyên từ {xapk_path} vào thư mục {out_dir}/ ...")
    
    with zipfile.ZipFile(xapk_path) as xapk:
        apk_names = [n for n in xapk.namelist() if n.endswith('.apk')]
        
        path_mapping = {} 
        
        # 1. Đọc các file config.*.json để xây dựng sơ đồ UUID -> Logical Path
        for apk_name in apk_names:
            apk_bytes = xapk.read(apk_name)
            with zipfile.ZipFile(io.BytesIO(apk_bytes)) as apk:
                for n in apk.namelist():
                    if ('cc.config.' in n or 'config.' in n) and n.endswith('.json'):
                        try:
                            cfg = json.loads(apk.read(n).decode('utf-8'))
                            uuids = cfg.get('uuids', [])
                            paths = cfg.get('paths', {})
                            
                            for idx_str, val in paths.items():
                                p = val[0] # Original logical path like "ui/banner/banner1"
                                if int(idx_str) < len(uuids):
                                    raw_uid = uuids[int(idx_str)]
                                    dec_uid = decode_uuid(raw_uid).split('@')[0]
                                    path_mapping.setdefault(dec_uid, []).append(p)
                        except Exception:
                            pass
                            
        print(f"Đã lập bản đồ được {len(path_mapping)} UUID (Bao gồm UX/UI, Sound, Spine, v.v...)")
        
        exported_count = 0
        converted_astc = 0
        
        # 2. Extract 
        for apk_name in apk_names:
            apk_bytes = xapk.read(apk_name)
            with zipfile.ZipFile(io.BytesIO(apk_bytes)) as apk:
                for n in apk.namelist():
                    basename = os.path.basename(n)
                    if '.' not in basename: continue
                    uid = basename.split('.')[0].split('@')[0]
                    
                    if uid in path_mapping:
                        file_bytes = apk.read(n)
                        ext = os.path.splitext(n)[1].lower()
                        
                        for logical_path in path_mapping[uid]:
                            # Giữ nguyên cấu trúc thư mục của game
                            clean_rel_path = re.sub(r'[\\:*?"<>|]', '_', logical_path)
                            dest_file = os.path.join(out_dir, clean_rel_path)
                            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                            
                            if ext == '.astc':
                                img = decode_astc_to_png(file_bytes)
                                if img:
                                    dest_file += '.png'
                                    try:
                                        img.save(dest_file)
                                        converted_astc += 1
                                        exported_count += 1
                                        continue
                                    except:
                                        pass
                                dest_file += ext # Fallback to original
                                
                            else:
                                dest_file += ext
                                
                            with open(dest_file, 'wb') as f:
                                f.write(file_bytes)
                            exported_count += 1

    print(f"\nHoàn tất 100% trích xuất!")
    print(f"Tổng số files đã lấy: {exported_count}")
    print(f"Số lượng ảnh ASTC đã giải mã sang PNG: {converted_astc}")

if __name__ == '__main__':
    main()
