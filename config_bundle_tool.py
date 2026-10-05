import zipfile
import io
import json
import zlib
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

Base64KeyChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
hex_map = [None] * 128
for i, c in enumerate(Base64KeyChars): hex_map[ord(c)] = i

def decode_uuid(b64):
    if len(b64) != 22: return b64
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

def unpack_config_bundle(xapk_path, out_json_path, lang_idx=502):
    print(f"Extracting config bundle (Lang Index {lang_idx}) from {xapk_path}...")
    with zipfile.ZipFile(xapk_path) as x:
        pad_bytes = x.read('pad_install.apk')
        
    with zipfile.ZipFile(io.BytesIO(pad_bytes)) as apk:
        cfg = json.loads(apk.read('assets/assets/resources/cc.config.09ce3.json').decode('utf-8'))
        
        # 502 = config/l10n/vi/config_bundle (Vietnamese)
        # 5118 = en, 2060 = zh-HK, 1927 = Main base config
        uuid_raw = cfg['uuids'][lang_idx]
        uid = decode_uuid(uuid_raw)
        
        bin_file = [n for n in apk.namelist() if uid in n and n.endswith('.bin')]
        if not bin_file:
            print("Could not find the bin file in APK.")
            return
            
        data = apk.read(bin_file[0])
        
        magic = data[:4]
        version = data[4]
        if magic != b'CFGZ':
            print("Invalid Magic Header!")
            return
            
        raw_gz = data[5:]
        uncompressed = zlib.decompress(raw_gz, 16 + zlib.MAX_WBITS)
        parsed = json.loads(uncompressed.decode('utf-8'))
        
        with open(out_json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully unpacked {len(parsed)} tables to {out_json_path}")

def pack_config_bundle(in_json_path, out_bin_path):
    print(f"Packing {in_json_path} into binary {out_bin_path}...")
    with open(in_json_path, 'r', encoding='utf-8') as f:
        parsed = json.load(f)
        
    json_bytes = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    
    # Compress with gzip
    compressed = zlib.compress(json_bytes, level=9)
    # zlib.compress creates a zlib stream, but Cocos expects a raw gzip stream or zlib stream?
    # CfgBinCodec uses pako.ungzip or inflate.
    # To be safe and match gen_cfg_bin.py, let's use standard gzip format:
    compressor = zlib.compressobj(9, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    gz_data = compressor.compress(json_bytes) + compressor.flush()
    
    # Header: CFGZ (4 bytes) + version 1 (1 byte)
    header = b'CFGZ\x01'
    
    with open(out_bin_path, 'wb') as f:
        f.write(header + gz_data)
        
    print(f"Successfully packed {len(json_bytes)} bytes down to {len(header + gz_data)} bytes!")

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'unpack'
    xapk_file = 'Last+Green_+Tower+Defense_1.1.1_APKPure.xapk'
    json_file = 'config_bundle_vi.json'
    
    if action == 'unpack':
        unpack_config_bundle(xapk_file, json_file, lang_idx=502) # 502 = Tiếng Việt
    elif action == 'pack':
        pack_config_bundle(json_file, 'config_bundle_vi_repacked.bin')
    else:
        print("Usage: python config_bundle_tool.py [unpack|pack]")
