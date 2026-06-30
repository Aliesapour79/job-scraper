# utils/decrypt.py
from cryptography.fernet import Fernet
import os
import streamlit as st
import tempfile
from dotenv import load_dotenv

def get_key():
    """دریافت کلید از Secrets یا محیط"""
    # اول Streamlit Secrets رو چک کن
    try:
        key = st.secrets["encryption"]["key"]
        return key.encode()
    except:
        pass
    
    # بارگذاری از local.env
    load_dotenv('local.env')
    
    # بعد محیط رو چک کن
    key = os.environ.get('ENCRYPTION_KEY')
    if key:
        return key.encode()
    
    raise Exception("❌ ENCRYPTION_KEY not found! Add it to .streamlit/secrets.toml or local.env")


def decrypt_data(encrypted_data):
    """رمزگشایی داده"""
    cipher = Fernet(get_key())
    return cipher.decrypt(encrypted_data)


def decrypt_file_to_string(encrypted_file_path):
    """
    رمزگشایی یک فایل و برگرداندن محتوای آن به صورت رشته
    
    Args:
        encrypted_file_path: مسیر فایل رمزنگاری شده (مثلاً config/settings.py.enc)
    
    Returns:
        str: محتوای رمزگشایی شده
    """
    if not os.path.exists(encrypted_file_path):
        # اگه فایل رمزنگاری شده نبود، فایل معمولی رو چک کن
        original_file = encrypted_file_path.replace('.enc', '')
        if os.path.exists(original_file):
            with open(original_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    with open(encrypted_file_path, 'rb') as f:
        encrypted = f.read()
    
    decrypted = decrypt_data(encrypted)
    return decrypted.decode('utf-8')


def decrypt_file_to_temp(encrypted_file_path, suffix='.py'):
    """
    رمزگشایی یک فایل و ذخیره در فایل موقت
    
    Args:
        encrypted_file_path: مسیر فایل رمزنگاری شده
        suffix: پسوند فایل موقت
    
    Returns:
        str: مسیر فایل موقت رمزگشایی شده
    """
    content = decrypt_file_to_string(encrypted_file_path)
    if content is None:
        return None
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(content.encode('utf-8'))
    temp_file.close()
    
    return temp_file.name