# matcher/weights.py
"""
وزن‌های پویا برای امتیازدهی بر اساس دسته‌بندی شغلی
"""

# =========================
# 🎯 گروه‌های دسته‌بندی شغلی
# =========================

TECHNICAL_CATEGORIES = [
    "توسعه نرم افزار و برنامه نویسی",
    "علوم داده / هوش مصنوعی"
]

ADMINISTRATIVE_CATEGORIES = [
    "مسئول دفتر / کارمند اداری",
    "منابع انسانی"
]


# =========================
# ⚖️ وزن‌ها بر اساس دسته‌بندی
# =========================

WEIGHTS_CONFIG = {
    "technical": {
        "hard": 0.50,
        "functional": 0.20,
        "soft": 0.10,
        "semantic": 0.20
    },
    "administrative": {
        "hard": 0.20,
        "functional": 0.30,
        "soft": 0.20,
        "semantic": 0.30
    },
    "hybrid": {
        "hard": 0.35,
        "functional": 0.25,
        "soft": 0.25,
        "semantic": 0.15
    }
}


# =========================
# 🎯 تابع تشخیص گروه
# =========================

def get_job_group(job_category: str) -> str:
    """
    تشخیص گروه شغلی بر اساس دسته‌بندی
    
    Args:
        job_category: دسته‌بندی شغلی از دیتابیس
    
    Returns:
        str: 'technical', 'administrative', یا 'hybrid'
    """
    if not job_category:
        return "hybrid"
    
    if job_category in TECHNICAL_CATEGORIES:
        return "technical"
    
    if job_category in ADMINISTRATIVE_CATEGORIES:
        return "administrative"
    
    return "hybrid"


# =========================
# ⚖️ تابع دریافت وزن‌ها
# =========================

def get_weights(job_category: str) -> dict:
    """
    دریافت وزن‌های مناسب برای یک دسته‌بندی شغلی
    
    Args:
        job_category: دسته‌بندی شغلی
    
    Returns:
        dict: وزن‌های hard, functional, soft, semantic
    """
    group = get_job_group(job_category)
    return WEIGHTS_CONFIG.get(group, WEIGHTS_CONFIG["hybrid"])


# =========================
# 📋 تابع نمایش وزن‌ها (برای دیباگ)
# =========================

def print_weights(job_category: str):
    """نمایش وزن‌های یک دسته‌بندی"""
    weights = get_weights(job_category)
    group = get_job_group(job_category)
    
    print(f"\n📊 Weight Configuration for: {job_category}")
    print(f"   Group: {group.upper()}")
    print(f"   🎯 Hard:        {weights['hard'] * 100:.0f}%")
    print(f"   ⚙️ Functional:  {weights['functional'] * 100:.0f}%")
    print(f"   💬 Soft:        {weights['soft'] * 100:.0f}%")
    print(f"   🧠 Semantic:    {weights['semantic'] * 100:.0f}%")


# =========================
# 🧪 تست
# =========================
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TESTING WEIGHTS MODULE")
    print("=" * 50)
    
    test_categories = [
        "توسعه نرم افزار و برنامه نویسی",
        "علوم داده / هوش مصنوعی",
        "مسئول دفتر / کارمند اداری",
        "منابع انسانی",
        "نامشخص"
    ]
    
    for category in test_categories:
        print_weights(category)