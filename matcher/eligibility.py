# matcher/eligibility.py
"""
سیستم پنالتی برای بررسی شرایط احراز شغل
"""

import re


# =========================
# 🎯 توابع کمکی
# =========================

def extract_age_range(text: str) -> tuple:
    """
    استخراج محدوده سنی از متن
    
    Args:
        text: متن شرایط احراز
    
    Returns:
        tuple: (min_age, max_age) یا (None, None)
    """
    if not text:
        return None, None
    
    # الگوهای مختلف
    patterns = [
        r'سن\s*از\s*(\d+)\s*تا\s*(\d+)',           # "سن از 22 تا 35"
        r'سن\s*(\d+)\s*-\s*(\d+)',                  # "سن 22 - 35"
        r'سن\s*(\d+)\s*تا\s*(\d+)',                 # "سن 22 تا 35"
        r'سن\s*از\s*(\d+)',                         # "سن از 22"
        r'سن\s*(\d+)\s*سال',                        # "سن 22 سال"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return int(groups[0]), int(groups[1])
            elif len(groups) == 1:
                return int(groups[0]), None
    
    return None, None


def extract_gender_requirement(text: str) -> dict:
    """
    استخراج جنسیت مورد نیاز از متن
    
    Returns:
        dict: {'type': 'required'/'preferred', 'gender': 'male'/'female'}
    """
    if not text:
        return {}
    
    text_lower = text.lower()
    
    # تشخیص نوع
    if "فقط" in text and ("خانم" in text or "زن" in text):
        return {"type": "required", "gender": "female"}
    
    if "فقط" in text and ("آقا" in text or "مرد" in text):
        return {"type": "required", "gender": "male"}
    
    if "ترجیحاً" in text and ("خانم" in text or "زن" in text):
        return {"type": "preferred", "gender": "female"}
    
    if "ترجیحاً" in text and ("آقا" in text or "مرد" in text):
        return {"type": "preferred", "gender": "male"}
    
    if "خانم" in text or "زن" in text:
        return {"type": "preferred", "gender": "female"}
    
    if "آقا" in text or "مرد" in text:
        return {"type": "preferred", "gender": "male"}
    
    return {}


def extract_military_requirement(text: str) -> str:
    """استخراج وضعیت سربازی مورد نیاز"""
    if not text:
        return "none"
    
    if "الزامی" in text or "اتمام" in text:
        return "required"
    
    return "none"


def extract_education_level(text: str) -> int:
    """
    استخراج سطح تحصیلات مورد نیاز
    
    Returns:
        int: 0=دیپلم, 1=کاردانی, 2=کارشناسی, 3=کارشناسی ارشد, 4=دکتری
    """
    if not text:
        return 0
    
    text_lower = text.lower()
    
    if "دکتری" in text_lower or "phd" in text_lower:
        return 4
    if "کارشناسی ارشد" in text_lower or "فوق لیسانس" in text_lower:
        return 3
    if "کارشناسی" in text_lower or "لیسانس" in text_lower:
        return 2
    if "کاردانی" in text_lower:
        return 1
    if "دیپلم" in text_lower:
        return 0
    
    return 0


# =========================
# 🔍 تابع اصلی بررسی شرایط
# =========================

def check_eligibility(requirements: str, resume_info: dict) -> dict:
    """
    بررسی شرایط احراز با سیستم پنالتی
    
    Args:
        requirements: متن شرایط احراز
        resume_info: اطلاعات رزومه شامل age, gender, military, education
    
    Returns:
        dict: {
            'penalty': int (0-100),
            'reasons': list,
            'details': dict
        }
    """
    penalty = 0
    reasons = []
    details = {}
    
    if not requirements or not resume_info:
        return {
            'penalty': 0,
            'reasons': ["هیچ شرطی بررسی نشد"],
            'details': {}
        }
    if not isinstance(requirements,str):
        requirements = str(requirements) if requirements is not None else ""

    # =========================
    # ۱. سن
    # =========================
    age_required = resume_info.get('age_required')
    age_resume = resume_info.get('age')
    
    if age_required and age_resume:
        min_age, max_age = extract_age_range(requirements)
        if min_age and max_age:
            if age_resume < min_age or age_resume > max_age:
                diff = min(abs(age_resume - min_age), abs(age_resume - max_age))
                if diff <= 2:
                    penalty += 5
                    reasons.append(f"سن ({diff} سال اختلاف) → -5%")
                elif diff <= 5:
                    penalty += 15
                    reasons.append(f"سن ({diff} سال اختلاف) → -15%")
                else:
                    penalty += 30
                    reasons.append(f"سن ({diff} سال اختلاف) → -30%")
    
    # =========================
    # ۲. جنسیت
    # =========================
    gender_req = extract_gender_requirement(requirements)
    gender_resume = resume_info.get('gender')
    
    if gender_req and gender_resume:
        if gender_req['type'] == 'required' and gender_req['gender'] != gender_resume:
            penalty += 20
            reasons.append(f"جنسیت (فقط {gender_req['gender']}) → -20%")
        elif gender_req['type'] == 'preferred' and gender_req['gender'] != gender_resume:
            penalty += 10
            reasons.append(f"جنسیت (ترجیحاً {gender_req['gender']}) → -10%")
    
    # =========================
    # ۳. خدمت سربازی
    # =========================
    military_req = extract_military_requirement(requirements)
    military_resume = resume_info.get('military', 'done')
    
    if military_req == 'required' and military_resume != 'done':
        penalty += 25
        reasons.append("خدمت سربازی (انجام نشده) → -25%")
    
    # =========================
    # ۴. تحصیلات
    # =========================
    edu_required = extract_education_level(requirements)
    edu_resume = resume_info.get('education_level', 0)
    
    if edu_required > 0 and edu_resume > 0:
        diff = edu_required - edu_resume
        if diff == 1:
            penalty += 10
            reasons.append(f"تحصیلات (یک مقطع پایین‌تر) → -10%")
        elif diff >= 2:
            penalty += 25
            reasons.append(f"تحصیلات ({diff} مقطع پایین‌تر) → -25%")
    
    # =========================
    # محدود کردن پنالتی
    # =========================
    penalty = min(penalty, 100)
    
    return {
        'penalty': penalty,
        'reasons': reasons if reasons else ["همه شرایط برقرار است"],
        'details': {
            'age_required': age_required,
            'gender_required': gender_req,
            'military_required': military_req,
            'education_required': edu_required
        }
    }

