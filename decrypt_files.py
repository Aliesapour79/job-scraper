# decrypt_files.py
from utils.decrypt import decrypt_file_to_string
import os

files = [
    'config/settings.py.enc',
    'config/resume.py.enc', 
    'matcher/skill_groups.py.enc'
]

for enc_file in files:
    if os.path.exists(enc_file):
        content = decrypt_file_to_string(enc_file)
        if content:
            out_file = enc_file.replace('.enc', '')
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✅ Decrypted: {enc_file} -> {out_file}')
        else:
            print(f'❌ Failed to decrypt: {enc_file}')
    else:
        print(f'⚠️ File not found: {enc_file}')