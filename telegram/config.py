# telegram/config.py
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# تعداد پیش‌فرض آگهی‌ها
DEFAULT_LIMIT = 50
MAX_LIMIT = 100