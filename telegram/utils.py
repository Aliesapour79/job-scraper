# telegram/utils.py
import sqlite3
from datetime import datetime


def get_db_stats():
    """دریافت آمار دیتابیس"""
    conn = sqlite3.connect("data/jobs_db_clean.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs_clean")
    total_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobvision_scores WHERE score IS NOT NULL")
    scored_jobs = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_jobs': total_jobs,
        'scored_jobs': scored_jobs,
        'last_update': datetime.now().strftime('%Y/%m/%d %H:%M')
    }