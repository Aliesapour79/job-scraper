# telegram/sender.py
import sqlite3
import requests
from datetime import datetime
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEFAULT_LIMIT, MAX_LIMIT


def get_top_jobs(limit=DEFAULT_LIMIT):
    """دریافت آگهی‌های برتر از دیتابیس"""
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    
    conn = sqlite3.connect("data/jobs_db_clean.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            j.title,
            j.company,
            j.location,
            j.salary,
            j.url,
            s.score,
            s.technical_score,
            s.general_score,
            s.category
        FROM jobvision_jobs_clean j
        LEFT JOIN jobvision_scores s ON j.id = s.job_id
        WHERE s.score IS NOT NULL
        ORDER BY s.score DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def format_jobs_message(jobs):
    """فرمت‌سازی پیام برای ارسال"""
    if not jobs:
        return "❌ هیچ آگهی با امتیاز پیدا نشد!"
    
    header = f"🚀 *MatchFlow Pipeline - {len(jobs)} آگهی برتر*\n📅 {datetime.now().strftime('%Y/%m/%d')}\n━━━━━━━━━━━━━━━━━━━━\n\n"
    messages = [header]

    for i, job in enumerate(jobs, 1):
        title, company, location, salary, url, score, tech, gen, cat = job
        
        # ایموجی بر اساس امتیاز
        if score >= 70:
            emoji = "🔥"
        elif score >= 50:
            emoji = "⭐"
        else:
            emoji = "📌"
        
        msg = f"""{emoji} {i}. *{title}*
🏢 {company}
📍 {location}
💰 {salary or 'توافقی'}
📊 امتیاز: *{score}%*
🔗 [مشاهده آگهی]({url})

"""
        messages.append(msg)

    return "".join(messages)


def send_top_jobs(limit=DEFAULT_LIMIT):
    """ارسال آگهی‌های برتر به تلگرام"""
    jobs = get_top_jobs(limit)
    if not jobs:
        print("❌ هیچ آگهی با امتیاز پیدا نشد!")
        return False
    
    full_text = format_jobs_message(jobs)
    
    # تقسیم پیام به دلیل محدودیت ۴۰۹۶ کاراکتری تلگرام
    chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده!")
        return False
    
    for chunk in chunks:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            response = requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }, timeout=30)
            
            if response.status_code == 200:
                print("✅ بخشی از پیام ارسال شد!")
            else:
                print(f"❌ خطا: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ خطا در ارسال: {e}")
            return False
    
    print("✅ همه آگهی‌ها ارسال شدند!")
    return True


if __name__ == "__main__":
    send_top_jobs()