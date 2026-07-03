# decrypt_all_files.py
"""
رمزگشایی همه فایل‌های .enc با استفاده از کلید local.env
"""

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

# =========================
# 🔑 بارگذاری کلید
# =========================
load_dotenv('local.env')

key = os.environ.get('ENCRYPTION_KEY')
if not key:
    print("❌ ENCRYPTION_KEY not found in local.env!")
    exit(1)

cipher = Fernet(key.encode())

# =========================
# 📋 لیست فایل‌های رمزنگاری شده
# =========================
files_to_decrypt = [
    "data/jobs_db_clean.db.enc",
    "cache/jobvision-data-science.json.enc",
    "cache/jobvision-developer.json.enc",
    "cache/jobvision-hr.json.enc",
    "cache/jobvision-secretary.json.enc"
]

print("=" * 50)
print("🔐 DECRYPTING FILES")
print("=" * 50)

for enc_file in files_to_decrypt:
    if not os.path.exists(enc_file):
        print(f"⚠️ File not found: {enc_file}")
        continue
    
    # خواندن فایل رمزنگاری شده
    with open(enc_file, 'rb') as f:
        encrypted = f.read()
    
    # رمزگشایی
    try:
        decrypted = cipher.decrypt(encrypted)
    except Exception as e:
        print(f"❌ Failed to decrypt {enc_file}: {e}")
        continue
    
    # ذخیره فایل معمولی
    dec_file = enc_file.replace('.enc', '')
    with open(dec_file, 'wb') as f:
        f.write(decrypted)
    
    print(f"✅ Decrypted: {enc_file} → {dec_file}")

print("=" * 50)
print("✅ All files decrypted successfully!")