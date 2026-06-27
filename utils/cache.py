"""
utils/cache.py

مدیریت کش لیست آگهی‌های استخراج‌شده از صفحات
"""

import json
import os
from datetime import datetime

CACHE_DIR = "output/cache"


def ensure_cache_dir():
    """ایجاد پوشه cache در صورت نیاز"""
    os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_path(site_name: str) -> str:
    """مسیر فایل کش مربوط به هر سایت"""
    ensure_cache_dir()
    return os.path.join(CACHE_DIR, f"{site_name}.json")


def cache_exists(site_name: str) -> bool:
    """آیا فایل کش وجود دارد؟"""
    return os.path.exists(get_cache_path(site_name))


def save_jobs_cache(site_name: str, jobs: list):
    """
    ذخیره لیست آگهی‌ها در فایل کش
    """

    data = {
        "site": site_name,
        "created_at": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "jobs": jobs
    }

    path = get_cache_path(site_name)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Cache saved ({len(jobs)} jobs)")


def load_jobs_cache(site_name: str):
    """
    بارگذاری لیست آگهی‌ها از فایل کش

    Returns:
        list | None
    """

    path = get_cache_path(site_name)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data.get("jobs", [])

    print(f"📂 Cache loaded ({len(jobs)} jobs)")

    return jobs


def clear_cache(site_name: str):
    """حذف فایل کش مربوط به سایت"""

    path = get_cache_path(site_name)

    if os.path.exists(path):
        os.remove(path)
        print("🗑 Cache removed")


def clear_all_cache():
    """حذف تمام فایل‌های کش"""

    ensure_cache_dir()

    count = 0

    for file in os.listdir(CACHE_DIR):
        if file.endswith(".json"):
            os.remove(os.path.join(CACHE_DIR, file))
            count += 1

    print(f"🗑 {count} cache file(s) removed")