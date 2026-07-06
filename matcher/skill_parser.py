# matcher/skill_parser.py
"""
پارسر مهارت‌ها - نسخه نهایی
فرمت ورودی: "Python (پیشرفته), C (متوسط), OpenCV (مقدماتی)"
"""

import re
from .text_normalizer import TextNormalizer

# =========================
# 📊 وزن‌های سطوح
# =========================

LEVEL_WEIGHTS = {
    "مقدماتی": 1.0,
    "متوسط": 2.0,
    "پیشرفته": 3.0,
}

LEVEL_NAMES = {"مقدماتی", "متوسط", "پیشرفته"}


# =========================
# 📋 مهارت‌های رزومه با سطح دقیق
# =========================

RESUME_SKILLS_DICT = {
    # زبان‌های برنامه‌نویسی
    "python": "پیشرفته",
    "c++": "متوسط",
    "c#": "متوسط",
    "java": "متوسط",
    "embedded c": "متوسط",
    
    # هوش مصنوعی و بینایی ماشین
    "machine learning": "پیشرفته",
    "computer vision": "پیشرفته",
    "opencv": "پیشرفته",
    "keras": "متوسط",
    "image processing": "پیشرفته",
    
    # اینترنت اشیاء و الکترونیک
    "esp32": "پیشرفته",
    "arduino": "پیشرفته",
    "can bus": "متوسط",
    "iot": "پیشرفته",
    "embedded": "پیشرفته",
    "microcontroller": "پیشرفته",
    "sensor": "متوسط",
    "proteus": "متوسط",
    "altium designer": "متوسط",
    
    # پایگاه داده
    "mysql": "متوسط",
    "mongodb": "متوسط",
    "sql": "متوسط",
    "sql server": "متوسط",
    "t-sql": "متوسط",
    
    # ابزارها
    "linux": "مقدماتی",
    "git": "متوسط",
    "microsoft excel": "متوسط",
    
    # تحلیل داده
    "pandas": "متوسط",
    "numpy": "متوسط",
    "data analysis": "پیشرفته",
    
    # مهارت‌های نرم
    "teamwork": "پیشرفته",
    "communication": "پیشرفته",
    "problem solving": "پیشرفته",
    "time management": "پیشرفته",
    "documentation": "پیشرفته",
    "project management": "پیشرفته",
}


# =========================
# 🧠 پارسر آگهی شغلی (فرمت: Python (پیشرفته), C (متوسط))
# =========================

def parse_job_skills(skills_text: str) -> dict:
    """
    پارس کردن مهارت‌های آگهی شغلی
    ورودی: "Python (پیشرفته), C (متوسط), OpenCV (مقدماتی)"
    خروجی: {"python": "پیشرفته", "c": "متوسط", "opencv": "مقدماتی"}
    """
    if not skills_text:
        return {}
    
    skills = {}
    
    # جداسازی با ,
    parts = [p.strip() for p in skills_text.split(",") if p.strip()]
    
    for part in parts:
        # استخراج نام و سطح با regex: "Python (پیشرفته)"
        match = re.match(r"(.+?)\s*\((.+?)\)", part)
        if match:
            skill_name = match.group(1).strip().lower()
            level = match.group(2).strip()
            
            # نرمال‌سازی نام مهارت
            skill_name = TextNormalizer.normalize(skill_name)
            
            # اگر سطح معتبر بود، اضافه کن
            if level in LEVEL_NAMES:
                skills[skill_name] = level
    
    return skills


# =========================
# 🧠 پارسر رزومه
# =========================

def parse_resume_skills(resume_text: str) -> dict:
    """
    استخراج مهارت‌ها از رزومه با استفاده از دیکشنری ثابت
    """
    if not resume_text:
        return {}
    
    resume_lower = resume_text.lower()
    found_skills = {}
    
    for skill_name, level in RESUME_SKILLS_DICT.items():
        if skill_name in resume_lower:
            found_skills[skill_name] = level
    
    return found_skills


# =========================
# 📊 محاسبه امتیاز تطابق مهارت‌ها
# =========================

def calculate_skill_match_score(resume_skills: dict, job_skills: dict) -> float:
    """
    محاسبه امتیاز تطابق مهارت‌ها با سطح
    """
    if not resume_skills or not job_skills:
        return 0
    
    total_score = 0
    total_weight = 0
    
    for job_skill, job_level in job_skills.items():
        job_weight = LEVEL_WEIGHTS.get(job_level, 1)
        
        if job_skill in resume_skills:
            resume_level = resume_skills[job_skill]
            resume_weight = LEVEL_WEIGHTS.get(resume_level, 1)
            
            ratio = resume_weight / job_weight
            match_score = min(ratio, 1.0)
            total_score += match_score * job_weight
        else:
            total_score += 0
        
        total_weight += job_weight
    
    if total_weight == 0:
        return 0
    
    raw_score = (total_score / total_weight) * 100
    return round(min(raw_score, 100), 2)


# =========================
# 🔄 تابع ترکیبی (سازگاری با کد قبلی)
# =========================

def parse_skills_with_level(skills_text: str) -> dict:
    """
    تابع سازگار با کد قبلی - برای آگهی‌های شغلی
    """
    return parse_job_skills(skills_text)