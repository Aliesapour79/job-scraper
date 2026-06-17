import re

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    # حذف کاراکترهای اضافی
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)

    # یکسان‌سازی فاصله‌ها
    text = re.sub(r"\s+", " ", text).strip()

    return text
