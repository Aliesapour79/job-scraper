# encrypt_cache.py
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

# 🔑 بارگذاری کلید از local.env
load_dotenv('local.env')

key = os.environ.get('ENCRYPTION_KEY')
if not key:
    print("❌ ENCRYPTION_KEY not found in local.env!")
    exit(1)

cipher = Fernet(key.encode())

cache_dir = "cache"
os.makedirs(cache_dir, exist_ok=True)

for file in os.listdir(cache_dir):
    if file.endswith('.json') and not file.endswith('.enc'):
        file_path = os.path.join(cache_dir, file)
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted = cipher.encrypt(data)
        
        enc_path = os.path.join(cache_dir, f"{file}.enc")
        with open(enc_path, 'wb') as f:
            f.write(encrypted)
        
        print(f"✅ Encrypted: {file} -> {file}.enc")