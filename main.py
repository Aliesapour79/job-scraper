# main.py - نسخه نهایی با امتیازدهی به همه آگهی‌ها + ذخیره در دیتابیس

import os
import sys
import traceback
import sqlite3
from utils.decrypt import decrypt_file_to_string, decrypt_file_to_temp

# =========================
# 🔐 رمزگشایی فایل‌های تنظیمات
# =========================

# ۱. رمزگشایی config/settings.py
settings_enc = "config/settings.py.enc"
if os.path.exists(settings_enc):
    settings_content = decrypt_file_to_string(settings_enc)
    if settings_content:
        exec(settings_content, globals())

# ۲. رمزگشایی config/resume.py
resume_enc = "config/resume.py.enc"
if os.path.exists(resume_enc):
    resume_content = decrypt_file_to_string(resume_enc)
    if resume_content:
        exec(resume_content, globals())

# ۳. رمزگشایی matcher/skill_groups.py
skill_enc = "matcher/skill_groups.py.enc"
if os.path.exists(skill_enc):
    skill_content = decrypt_file_to_string(skill_enc)
    if skill_content:
        exec(skill_content, globals())

# =========================
# Imports
# =========================
from config import EMBEDDING_MODEL, FILTERS, RESUME_TEXT
from matcher.semantic_matcher import SemanticMatcher
from scrapers import JobvisionScraper
from utils import setup_driver
from utils.database import get_stats, init_db, get_all_jobs, save_score
from utils.driver_manager import safe_driver_get

from core import load_site_jobs, filter_new_jobs, extract_job_details, score_jobs, generate_output


# =========================
# ⚙️ تنظیمات
# =========================
RESTART_EVERY = 60
SLEEP_RANGE = (5, 8)
PAGE_TIMEOUT = 90
MAX_FAILURE_RATE = 0.25
PARTIAL_SAVE_EVERY = 50
MAX_EMPTY_PAGES = 2
MAX_DRIVER_RETRIES = 3

ENABLE_PROCESSING = True
ENABLE_OUTPUT = True
ENABLE_DB_SAVE = True
from tqdm import tqdm

# =========================
# 🛠️ توابع کمکی
# =========================
def save_partial(all_jobs, count):
    """ذخیره موقت"""
    import json
    from datetime import datetime
    try:
        os.makedirs("partial", exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"partial/partial_{count}_{ts}.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        print(f"💾 Partial save at {count}")
    except:
        pass


def print_status():
    """نمایش وضعیت"""
    print("=" * 80)
    print("🚀 JOB MATCHER v7 - STABLE PRODUCTION MODE")
    print("   (Multi-Site: e-estekhdam + Jobvision)")
    print("=" * 80)
    print(f"\n📋 MODE STATUS:")
    print(f"   🧠 Processing (Scoring): {'✅ ENABLED' if ENABLE_PROCESSING else '❌ DISABLED'}")
    print(f"   📤 Output (JSON/HTML):  {'✅ ENABLED' if ENABLE_OUTPUT else '❌ DISABLED'}")
    print(f"   💾 Database Save:      {'✅ ENABLED' if ENABLE_DB_SAVE else '❌ DISABLED'}")
    print("=" * 80)


def save_scores_to_db(results):
    """ذخیره امتیازها در دیتابیس"""
    print("\n💾 Saving scores to database...")
    
    conn = sqlite3.connect("data/jobs.db")
    cursor = conn.cursor()
    
    saved = 0
    failed = 0
    
    for result in tqdm(results, desc="Saving scores", unit="score"):
        try:
            # پیدا کردن job_id بر اساس URL
            cursor.execute("SELECT id FROM jobvision_jobs WHERE url = ?", (result.get('url'),))
            row = cursor.fetchone()
            
            if row:
                job_id = row[0]
                score_data = {
                    'score': result.get('score', 0),
                    'technical_score': result.get('technical_score', 0),
                    'general_score': result.get('general_score', 0),
                    'embedding_score': result.get('embedding_score', 0),
                    'tfidf_score': result.get('tfidf_score', 0),
                    'category': result.get('category', ''),
                    'outlier_score': result.get('outlier_score', 0)
                }
                save_score(job_id, score_data)
                saved += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"   ⚠️ Error saving score for {result.get('title', 'Unknown')}: {e}")
    
    conn.close()
    print(f"✅ Saved {saved} scores to database! (Failed: {failed})")


# =========================
# 🚀 MAIN
# =========================
def main():
    os.makedirs("output", exist_ok=True)
    os.makedirs("partial", exist_ok=True)
    print_status()

    # بارگذاری مدل
    semantic_matcher = None
    if ENABLE_PROCESSING:
        print("\n🔄 Loading Semantic Model...")
        semantic_matcher = SemanticMatcher(EMBEDDING_MODEL)
        if not semantic_matcher.is_loaded:
            print("⚠️ Semantic matching disabled (install sentence-transformers)")
    else:
        print("\n⏭️ Skipping Semantic Model (Processing disabled)")

    # آماده‌سازی دیتابیس
    if ENABLE_DB_SAVE:
        print("\n📁 Initializing database...")
        init_db()
        print("✅ Database ready")

    # تنظیمات سایت‌ها
    sites_config = [
        {
            'name': 'jobvision-developer',
            'url': "https://jobvision.ir/jobs/category/developer-in-all-cities-of-tehran",
            'type': 'jobvision',
            'max_pages': 100,
            'job_category': 'توسعه نرم افزار و برنامه نویسی'
        },
        {
            'name': 'jobvision-data-science',
            'url': "https://jobvision.ir/jobs/category/data-science-in-all-cities-of-tehran",
            'type': 'jobvision',
            'max_pages': 100,
            'job_category': 'علوم داده / هوش مصنوعی'
        },
        {
            'name': 'jobvision-secretary',
            'url': "https://jobvision.ir/jobs/category/secretary-in-all-cities-of-tehran",
            'type': 'jobvision',
            'max_pages': 100,
            'job_category': 'مسئول دفتر / کارمند اداری'
        },
        {
            'name': 'jobvision-hr',
            'url': "https://jobvision.ir/jobs/category/human-resources-in-all-cities-of-tehran",
            'type': 'jobvision',
            'max_pages': 100,
            'job_category': 'منابع انسانی'
        }
    ]

    driver = setup_driver()
    all_jobs = []  # فقط برای آگهی‌های جدید (برای استخراج)
    
    config = {
        'RESTART_EVERY': RESTART_EVERY,
        'SLEEP_RANGE': SLEEP_RANGE,
        'MAX_FAILURE_RATE': MAX_FAILURE_RATE,
        'PARTIAL_SAVE_EVERY': PARTIAL_SAVE_EVERY,
        'ENABLE_DB_SAVE': ENABLE_DB_SAVE
    }

    try:
        # =========================
        # مرحله ۱: استخراج آگهی‌های جدید
        # =========================
        for site in sites_config:
            print(f"\n{'='*60}")
            print(f"🔄 Scraping {site['name']}")
            print(f"   URL: {site['url']}")
            print(f"{'='*60}")

            if not safe_driver_get(driver, site['url']):
                print(f"⚠️ Could not load {site['name']}, skipping...")
                continue

            scraper = JobvisionScraper(driver)
            jobs = load_site_jobs(scraper, site)

            if not jobs:
                print("⚠️ No jobs found")
                continue

            print(f"🔍 {len(jobs)} jobs found")

            jobs = filter_new_jobs(jobs, ENABLE_DB_SAVE)
            if not jobs:
                continue

            all_jobs, driver = extract_job_details(jobs, site, driver, all_jobs, config, save_partial)

        # =========================
        # مرحله ۲: چک کردن وجود آگهی
        # =========================
        if not all_jobs:
            print("⚠️ No new jobs extracted.")
            print("📊 But we can still score all jobs in database!")
        
        print(f"\n✅ NEW JOBS EXTRACTED: {len(all_jobs)}")

        if ENABLE_DB_SAVE:
            stats = get_stats()
            print(f"\n📈 Database Statistics:")
            print(f"   📋 Total Jobs: {stats['total_jobs']}")
            print(f"   🏢 Total Companies: {stats['total_companies']}")
            print(f"   📍 Total Cities: {stats['total_cities']}")
            print(f"   📅 Last Week: {stats['last_week']}")
            print(f"   ⚡ Urgent: {stats['urgent']}")

        if not ENABLE_PROCESSING:
            print("\n⏭️ Processing (Scoring) is DISABLED.")
            print("   Data extracted successfully. Run with ENABLE_PROCESSING=True to score.")
            return

        # =========================
        # مرحله ۳: امتیازدهی به همه آگهی‌های دیتابیس
        # =========================
        print("\n" + "=" * 80)
        print("📊 SCORING ALL JOBS IN DATABASE")
        print("=" * 80)
        
        # گرفتن همه آگهی‌ها از دیتابیس
        all_db_jobs = get_all_jobs(limit=10000)
        print(f"📋 Total jobs in database: {len(all_db_jobs)}")
        
        if not all_db_jobs:
            print("❌ No jobs in database to score!")
            return
        
        # امتیازدهی به همه
        results = score_jobs(all_db_jobs, semantic_matcher, RESUME_TEXT)
        generate_output(results, FILTERS, ENABLE_OUTPUT)
        
        # =========================
        # 🔥 مرحله ۴: ذخیره امتیازها در دیتابیس
        # =========================
        save_scores_to_db(results)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()

    finally:
        try:
            driver.quit()
        except:
            pass

        print("\n" + "=" * 80)
        print("✅ ALL SITES COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        if ENABLE_DB_SAVE:
            try:
                stats = get_stats()
                print(f"\n📊 Final Statistics:")
                print(f"   📋 Total Jobs: {stats['total_jobs']}")
                print(f"   🏢 Total Companies: {stats['total_companies']}")
                print(f"   📍 Total Cities: {stats['total_cities']}")
                print(f"   📅 Last Week: {stats['last_week']}")
                print(f"   ⚡ Urgent: {stats['urgent']}")
            except:
                pass

        print(f"\n💾 Database: data/jobs.db")
        print(f"📁 Output: output/")
        print(f"📁 Partial: partial/")
        print("\n" + "=" * 80)
        print("✅ Browser closed")


if __name__ == "__main__":
    main()