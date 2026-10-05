import glob, os, re, sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

def parse_ts_dict(text):
    text = re.sub(r'//.*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    start = text.find('{')
    if start == -1: return {}
    text = text[start:]
    
    result = {}
    path = []
    
    # Tokenize: match braces, keys (string or number), strings, and array bracket start/end
    # We will ignore array parsing for now and just treat array indices as keys if they appear as `[idx]:`
    # Wait, LanguageAutogen has actual string arrays: `FunNames: ["A", "B"]`
    # Let's handle arrays:
    tokens = re.finditer(r'(?P<brace>[\{\}\[\]])|(?P<key>[a-zA-Z0-9_]+)\s*:|\s*\[(?P<idx>\d+)\]\s*:|(?P<str>\"(?:\\.|[^\\\"])*\"|\'(?:\\.|[^\\\'])*\'|\`(?:\\.|[^\\\`])*\`)', text)
    
    current_key = None
    array_index = []
    
    for m in tokens:
        if m.group('brace') == '{':
            if current_key is not None:
                path.append(current_key)
                current_key = None
        elif m.group('brace') == '}':
            if path:
                path.pop()
        elif m.group('brace') == '[':
            # array start
            if current_key is not None:
                path.append(current_key)
                current_key = None
                array_index.append(0)
        elif m.group('brace') == ']':
            # array end
            if path:
                path.pop()
            if array_index:
                array_index.pop()
        elif m.group('key'):
            current_key = m.group('key')
        elif m.group('idx'):
            current_key = m.group('idx')
        elif m.group('str'):
            val = m.group('str')[1:-1] # strip quotes
            
            # handle escapes
            val = val.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
            
            if current_key is not None:
                full_key = '.'.join(path + [current_key])
                result[full_key] = val
                current_key = None
            elif array_index:
                full_key = '.'.join(path + [str(array_index[-1])])
                result[full_key] = val
                array_index[-1] += 1
            elif path:
                # trailing comma string or array?
                pass
    return result

files = glob.glob('source/decompiled_src/**/Language.autogen.*.ts', recursive=True)
all_data = {}
langs = []

for f in files:
    lang = os.path.basename(f).replace('Language.autogen.', '').replace('.ts', '')
    langs.append(lang)
    with open(f, 'r', encoding='utf-8') as fp:
        all_data[lang] = parse_ts_dict(fp.read())
        
print(f'Parsed vi: {len(all_data["vi"])} keys')
print(f'Parsed en: {len(all_data.get("en", []))} keys')

df_data = {}
for lang in langs:
    for k, v in all_data[lang].items():
        if k not in df_data:
            df_data[k] = {'Key': k}
        df_data[k][lang] = v

df = pd.DataFrame(list(df_data.values()))
preferred = ['Key', 'en', 'vi', 'zh-HK']
final_cols = [c for c in preferred if c in df.columns] + sorted([c for c in df.columns if c not in preferred])
df = df[final_cols]
df.to_excel('code_lang_export.xlsx', index=False)
print(f'Exported {len(df)} strings to code_lang_export.xlsx')
