# utils/database.py
# ==========================================
# مدیریت دیتابیس SQLite برای ذخیره آگهی‌های شغلی
# ==========================================

import sqlite3
import json
import hashlib
from datetime import datetime
import os

# =========================
# تنظیمات دیتابیس
# =========================
DB_PATH = "data/jobs.db"


def get_connection():
    """دریافت اتصال به دیتابیس"""
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """ایجاد جدول‌های دیتابیس"""
    conn = get_connection()
    cursor = conn.cursor()

    # =========================
    # جدول آگهی‌ها با فیلد job_category
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobvision_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            url TEXT UNIQUE,
            location TEXT,
            salary TEXT,
            is_urgent BOOLEAN,
            description TEXT,
            requirements TEXT,
            full_text TEXT,
            skills TEXT,
            age_range TEXT,
            gender TEXT,
            job_category TEXT,
            site TEXT DEFAULT 'jobvision',
            job_hash TEXT UNIQUE,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # جدول امتیازها
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobvision_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            score INTEGER,
            technical_score INTEGER,
            general_score INTEGER,
            embedding_score INTEGER,
            tfidf_score INTEGER,
            category TEXT,
            outlier_score INTEGER,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobvision_jobs(id)
        )
    """)

    # =========================
    # جدول تاریخچه اسکرپ
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobvision_scraping_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_pages INTEGER,
            total_jobs INTEGER,
            new_jobs INTEGER,
            failed INTEGER,
            duration_seconds INTEGER,
            started_at TIMESTAMP,
            finished_at TIMESTAMP
        )
    """)

    # =========================
    # ایندکس‌ها
    # =========================
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobvision_jobs_url ON jobvision_jobs(url)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobvision_jobs_company ON jobvision_jobs(company)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobvision_jobs_category ON jobvision_jobs(job_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobvision_jobs_scraped_at ON jobvision_jobs(scraped_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobvision_scores_job_id ON jobvision_scores(job_id)")

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")


def get_job_hash(title, company, url):
    """تولید هش یکتا برای هر آگهی"""
    text = f"{title}{company}{url}"
    return hashlib.md5(text.encode()).hexdigest()


def save_job(job_data):
    """
    ذخیره یک آگهی در دیتابیس
    
    Args:
        job_data: دیکشنری شامل اطلاعات آگهی
    
    Returns:
        bool: True اگر آگهی جدید بود، False اگر تکراری بود
    """
    conn = get_connection()
    cursor = conn.cursor()

    job_hash = get_job_hash(
        job_data.get('title', ''),
        job_data.get('company', ''),
        job_data.get('url', '')
    )

    sections = job_data.get('sections', {})
    skills = job_data.get('skills', [])

    cursor.execute("""
        INSERT OR IGNORE INTO jobvision_jobs (
            job_hash, title, company, url, location, salary,
            is_urgent, description, requirements, full_text,
            skills, age_range, gender, job_category, site
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_hash,
        job_data.get('title', ''),
        job_data.get('company', ''),
        job_data.get('url', ''),
        job_data.get('location', ''),
        job_data.get('salary', ''),
        1 if job_data.get('is_urgent', False) else 0,
        sections.get('description', ''),
        sections.get('requirements', ''),
        sections.get('full_text', ''),
        json.dumps(skills, ensure_ascii=False),
        job_data.get('age_range', ''),
        job_data.get('gender', ''),
        job_data.get('job_category', ''),
        job_data.get('site', 'jobvision')
    ))

    conn.commit()
    conn.close()

    return cursor.rowcount > 0


def save_jobs_batch(jobs_data):
    """
    ذخیره لیست آگهی‌ها در دیتابیس
    
    Args:
        jobs_data: لیست دیکشنری‌های آگهی
    
    Returns:
        tuple: (تعداد جدید, تعداد تکراری, تعداد خطا)
    """
    new_count = 0
    duplicate_count = 0
    error_count = 0

    for job in jobs_data:
        try:
            if save_job(job):
                new_count += 1
            else:
                duplicate_count += 1
        except Exception as e:
            error_count += 1
            print(f"     ❌ DB error: {e}")

    return new_count, duplicate_count, error_count


def save_score(job_id, score_data):
    """ذخیره امتیاز یک آگهی"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobvision_scores (
            job_id, score, technical_score, general_score,
            embedding_score, tfidf_score, category, outlier_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        score_data.get('score', 0),
        score_data.get('technical_score', 0),
        score_data.get('general_score', 0),
        score_data.get('embedding_score', 0),
        score_data.get('tfidf_score', 0),
        score_data.get('category', ''),
        score_data.get('outlier_score', 0)
    ))

    conn.commit()
    conn.close()


def save_scraping_log(total_pages, total_jobs, new_jobs, failed, duration_seconds, started_at, finished_at):
    """ذخیره تاریخچه یک اجرای اسکرپ"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobvision_scraping_log (
            total_pages, total_jobs, new_jobs, failed,
            duration_seconds, started_at, finished_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        total_pages,
        total_jobs,
        new_jobs,
        failed,
        duration_seconds,
        started_at,
        finished_at
    ))

    conn.commit()
    conn.close()


def get_job_by_url(url):
    """دریافت یک آگهی با URL"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobvision_jobs WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result


def get_jobs_by_company(company, limit=100):
    """دریافت آگهی‌های یک شرکت"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobvision_jobs 
        WHERE company LIKE ? 
        ORDER BY scraped_at DESC LIMIT ?
    """, (f"%{company}%", limit))
    results = cursor.fetchall()
    conn.close()
    return results


def get_all_jobs(limit=1000):
    """دریافت همه آگهی‌ها"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobvision_jobs 
        ORDER BY scraped_at DESC LIMIT ?
    """, (limit,))
    results = cursor.fetchall()
    conn.close()
    return results


def get_jobs_by_category(category, limit=1000):
    """دریافت آگهی‌ها بر اساس گروه شغلی"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobvision_jobs 
        WHERE job_category = ? 
        ORDER BY scraped_at DESC LIMIT ?
    """, (category, limit))
    results = cursor.fetchall()
    conn.close()
    return results


def get_jobs_count():
    """دریافت تعداد کل آگهی‌ها"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_stats():
    """دریافت آمار کلی دیتابیس"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs")
    total_jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT company) FROM jobvision_jobs")
    total_companies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT location) FROM jobvision_jobs WHERE location != ''")
    total_cities = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM jobvision_jobs 
        WHERE scraped_at > datetime('now', '-7 day')
    """)
    last_week = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs WHERE is_urgent = 1")
    urgent = cursor.fetchone()[0]

    # آمار بر اساس گروه شغلی
    cursor.execute("""
        SELECT job_category, COUNT(*) 
        FROM jobvision_jobs 
        WHERE job_category != '' 
        GROUP BY job_category
    """)
    category_stats = cursor.fetchall()

    conn.close()

    return {
        'total_jobs': total_jobs,
        'total_companies': total_companies,
        'total_cities': total_cities,
        'last_week': last_week,
        'urgent': urgent,
        'category_stats': category_stats
    }


# =========================
# تست دیتابیس
# =========================
if __name__ == "__main__":
    print("🧪 Testing database...")
    init_db()
    
    # تست با داده‌های نمونه
    test_job = {
        'title': 'تست برنامه نویس',
        'company': 'شرکت تست',
        'url': 'https://test.com/job/1',
        'location': 'تهران',
        'salary': '50 - 70 میلیون تومان',
        'is_urgent': True,
        'sections': {
            'description': 'توضیحات تست',
            'requirements': 'Python, Django',
            'full_text': 'متن کامل تست'
        },
        'skills': [{'name': 'Python', 'level': 'پیشرفته'}],
        'age_range': '20-35',
        'gender': 'تفاوتی ندارد',
        'job_category': 'توسعه نرم افزار و برنامه نویسی',
        'site': 'jobvision'
    }
    
    result = save_job(test_job)
    print(f"✅ Test save: {result}")
    
    stats = get_stats()
    print(f"📊 Stats: {stats}")
    print("✅ Database test complete")