# matcher/skill_groups.py
# ==========================================
# گروه‌های مهارتی برای تطبیق شغلی
# ==========================================

SKILL_GROUPS = {
    "iot_embedded": {
        "keywords": ["esp32", "mqtt", "arduino", "can bus", "raspberry pi", "modbus", 
                     "اینترنت اشیاء", "سیستم‌های نهفته", "embedded", "iot", "اینترنت اشیا"],
        "base_weight": 10,
        "bonus_per_match": 2,
        "min_matches_for_bonus": 2
    },
    "hardware_electronics": {
        "keywords": ["الکترونیک", "طراحی مدار", "pcb", "altium", "میکروکنترلر", 
                     "سنسور", "شبیه‌سازی", "کنترل", "power", "analog", "digital"],
        "base_weight": 10,
        "bonus_per_match": 2.0,
        "min_matches_for_bonus": 2
    },
    "ai_computer_vision": {
        "keywords": ["هوش مصنوعی", "machine learning", "یادگیری ماشین", "پردازش تصویر", 
                     "opencv", "deep learning", "yolo", "cnn", "tensorflow", "pytorch",
                     "بینایی ماشین", "طبقه‌بندی", "تشخیص", "computer vision"],
        "base_weight": 9,
        "bonus_per_match": 2.0,
        "min_matches_for_bonus": 2
    },
    "programming": {
        "keywords": ["python", "c++", "جاوا", "javascript", "برنامه‌نویسی", "کدنویسی",
                     "api", "rest", "flask", "django", "fastapi", "backend"],
        "base_weight": 7,
        "bonus_per_match": 1,
        "min_matches_for_bonus": 3
    },
    "data_analytics": {
        "keywords": ["تحلیل داده", "داده‌کاوی", "sql", "mongodb", "mysql", "postgresql",
                     "pandas", "numpy", "power bi", "tableau", "etl", "data analysis"],
        "base_weight": 6,
        "bonus_per_match": 1.5,
        "min_matches_for_bonus": 2
    },
    "networking_sysadmin": {
        "keywords": ["network", "شبکه", "tcp/ip", "dns", "linux", "لینوکس", "سرور",
                     "nginx", "apache", "docker", "kubernetes", "cloud", "azure", "aws"],
        "base_weight": 5,
        "bonus_per_match": 1,
        "min_matches_for_bonus": 3
    },
    "industrial_automation": {
        "keywords": ["صنعتی", "تولیدی", "کارخانه", "اتوماسیون", "رباتیک", "ابزار دقیق",
                     "پایش", "مانیتورینگ", "plc", "scada", "hmi", "turbine", "موتور"],
        "base_weight": 5,
        "bonus_per_match": 1,
        "min_matches_for_bonus": 2
    },
    "office_administration": {
        "keywords": [
            "اداری", "منشی", "دفتر", "پشتیبانی", "حضور و غیاب", "مدیریت زمان",
            "word", "excel", "powerpoint", "outlook", "آفیس", "مکاتبات",
            "بایگانی", "نامه‌نگاری", "مدارک", "هماهنگی", "گزارش‌نویسی",
            "دبیرخانه", "مدیریت اسناد", "تنظیم قرارداد", "پیگیری",
            "کارمند", "کارمندی", "پذیرش", "دفترداری", "امور اداری"
        ],
        "base_weight": 4,
        "bonus_per_match": 0.5,
        "min_matches_for_bonus": 3
    },
    "general": {
        "keywords": ["word", "excel", "مدیریت زمان", "الگوریتم", "git", 
                     "مستندسازی", "تیم‌ورزی", "ارتباط موثر", "مدیریت پروژه",
                     "تحلیل", "گزارش", "مکاتبه", "پشتیبانی"],
        "base_weight": 4,
        "bonus_per_match": 0.8,
        "min_matches_for_bonus": 4
    }
}

# ==========================================
# وزن‌های پویا بر اساس عنوان شغل
# ==========================================
JOB_TITLE_WEIGHT_MAP = {
    "iot": ["iot_embedded", "hardware_electronics", "industrial_automation"],
    "اینترنت اشیاء": ["iot_embedded", "hardware_electronics", "industrial_automation"],
    "embedded": ["iot_embedded", "hardware_electronics", "programming"],
    "سیستم‌های نهفته": ["iot_embedded", "hardware_electronics", "programming"],
    "هوش مصنوعی": ["ai_computer_vision", "data_analytics", "programming"],
    "machine learning": ["ai_computer_vision", "data_analytics", "programming"],
    "پردازش تصویر": ["ai_computer_vision", "programming", "data_analytics"],
    "بینایی ماشین": ["ai_computer_vision", "programming", "data_analytics"],
    "data analyst": ["data_analytics", "programming", "ai_computer_vision"],
    "تحلیل داده": ["data_analytics", "programming", "ai_computer_vision"],
    "برنامه‌نویس": ["programming", "ai_computer_vision", "data_analytics"],
    "developer": ["programming", "ai_computer_vision", "data_analytics"],
    "full stack": ["programming", "data_analytics", "networking_sysadmin"],
    "backend": ["programming", "data_analytics", "networking_sysadmin"],
    "devops": ["networking_sysadmin", "programming", "data_analytics"],
    "network": ["networking_sysadmin", "iot_embedded", "general"],
    "الکترونیک": ["hardware_electronics", "iot_embedded", "industrial_automation"],
    "رباتیک": ["industrial_automation", "hardware_electronics", "ai_computer_vision"],
    "اتوماسیون": ["industrial_automation", "iot_embedded", "hardware_electronics"],
    # ========== گروه‌های اداری ==========
    "اداری": ["office_administration", "general"],
    "منشی": ["office_administration", "general"],
    "کارمند": ["office_administration", "general"],
    "پشتیبانی": ["office_administration", "general"],
    "مکاتبات": ["office_administration", "general"],
    "گزارش‌نویسی": ["office_administration", "general", "data_analytics"],
    "دفتر": ["office_administration", "general"],
    "پذیرش": ["office_administration", "general"],
    "امور اداری": ["office_administration", "general"],
    "کارمندی": ["office_administration", "general"]
}