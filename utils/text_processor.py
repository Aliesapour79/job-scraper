# utils/text_processor.py
"""
ماژول پردازش متن - استخراج فیلدها از full_text
"""

import re

# =========================
# SOFTWARE SECTION
# =========================

SOFTWARE_END_MARKERS = [
    "ثبت مشکل و تخلف",
    "موقعیت های شغلی مشابه",
    "ارسال رزومه",
    "ارسال رزومه برای",
    "حقوق",
    "مزایا",
    "درباره شرکت"
]

LEVELS = {
    "مقدماتی",
    "متوسط",
    "پیشرفته",
    "حرفه ای",
    "حرفه‌ای",
    "بالاتر از متوسط",
    "ضعیف",
    "خوب",
    "عالی",
    # انگلیسی
    "Basic",
    "Intermediate",
    "Advanced",
    "Expert"
}


# =========================
# CLEAN TEXT HELPERS
# =========================

def normalize(text):
    if not text:
        return ""
    return text.replace("\n", " ").replace("\r", " ").strip()


def find_first(text, keywords):
    text_lower = text.lower()
    for k in keywords:
        idx = text_lower.find(k.lower())
        if idx != -1:
            return idx
    return -1


def extract_section(text, start_keys, end_keys):
    """
    استخراج بخش از متن با پشتیبانی از چند کلیدواژه (فارسی و انگلیسی)
    """
    start = find_first(text, start_keys)
    if start == -1:
        return ""

    end = len(text)
    for k in end_keys:
        idx = text.lower().find(k.lower(), start)
        if idx != -1:
            end = min(end, idx)

    return text[start:end].strip()


# =========================
# FIELD EXTRACTION
# =========================

def extract_gender(text):
    if not text:
        return "تفاوتی ندارد"

    text_lower = text.lower()
    
    # فارسی
    if "خانم" in text or "زن" in text:
        return "خانم"
    if "آقا" in text or "مرد" in text:
        return "آقا"
    
    # انگلیسی
    if "female" in text_lower or "woman" in text_lower:
        return "خانم"
    if "male" in text_lower or "man" in text_lower:
        return "آقا"
    if "men" in text_lower or "both" in text_lower:
        return "تفاوتی ندارد"

    return "تفاوتی ندارد"


def extract_age(text):
    if not text:
        return ""

    # فارسی: سن 22 - 35 سال
    m = re.search(r"سن\s*[:\-]?\s*(\d+\s*[-–]\s*\d+|\d+)", text)
    if m:
        return m.group(1)
    
    # انگلیسی: Age 22 - 35
    m = re.search(r"[Aa]ge\s*[:\-]?\s*(\d+\s*[-–]\s*\d+|\d+)", text)
    if m:
        return m.group(1)
    
    return ""


def extract_salary(text):
    """
    استخراج حقوق با الگوهای فارسی و انگلیسی
    """
    if not text:
        return "توافقی"

    # الگوی فارسی: عدد - عدد میلیون تومان
    pattern_persian = r"(\d+\s*[-–]\s*\d+)\s*میلیون"
    match = re.search(pattern_persian, text)
    if match:
        return match.group(1).strip()
    
    # الگوی انگلیسی: عدد - عدد Million Tomans
    pattern_english = r"(\d+\s*[-–]\s*\d+)\s*[Mm]illion"
    match = re.search(pattern_english, text)
    if match:
        return match.group(1).strip()
    
    # الگوی عدد - عدد تومان (بدون میلیون)
    pattern_toman = r"(\d+\s*[-–]\s*\d+)\s*تومان"
    match = re.search(pattern_toman, text)
    if match:
        return match.group(1).strip()
    
    return "توافقی"


# =========================
# SKILLS (ONLY SOFTWARES)
# =========================

def extract_skills_from_requirements(text):
    """
    استخراج فقط لیست نرم افزارها (فارسی و انگلیسی)
    """
    if not text:
        return ""

    start = find_first(text, ["نرم افزارها", "Software"])

    if start == -1:
        return ""

    end = len(text)

    for marker in SOFTWARE_END_MARKERS:
        idx = text.find(marker, start)
        if idx != -1:
            end = min(end, idx)

    block = text[start:end]

    skills = []

    for line in block.splitlines():
        line = line.strip()

        if not line:
            continue

        # حذف خطوط اضافی
        if line in ["|", "نرم افزارها", "Software"]:
            continue

        # حذف سطوح مهارت (فارسی و انگلیسی)
        if line in LEVELS:
            continue

        # درصد مهارت
        if re.fullmatch(r"\d+٪?", line):
            continue

        skills.append(line)

    skills = list(dict.fromkeys(skills))
    return ", ".join(skills)


def clean_requirements(text):
    """
    حذف کامل بخش نرم افزارها از requirements (فارسی و انگلیسی)
    """
    if not text:
        return ""

    start = find_first(text, ["نرم افزارها", "Software"])

    if start == -1:
        return text.strip()

    end = len(text)

    for marker in SOFTWARE_END_MARKERS:
        idx = text.find(marker, start)
        if idx != -1:
            end = min(end, idx)

    return (text[:start] + text[end:]).strip()