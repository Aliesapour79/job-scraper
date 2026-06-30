# monitor.py - نسخه پیشرفته با نمایش زیبا
import sqlite3
import time
from datetime import datetime
import os

DB_PATH = "data/jobs.db"

def get_stats():
    """دریافت آمار کامل از دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # تعداد کل
    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs")
    total = cursor.fetchone()[0]
    
    # ۵ دقیقه اخیر
    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs WHERE scraped_at > datetime('now', '-5 minute')")
    last_5min = cursor.fetchone()[0]
    
    # ۱ ساعت اخیر
    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs WHERE scraped_at > datetime('now', '-1 hour')")
    last_hour = cursor.fetchone()[0]
    
    # امروز
    cursor.execute("SELECT COUNT(*) FROM jobvision_jobs WHERE date(scraped_at) = date('now')")
    today = cursor.fetchone()[0]
    
    # تعداد شرکت‌ها
    cursor.execute("SELECT COUNT(DISTINCT company) FROM jobvision_jobs WHERE company != ''")
    companies = cursor.fetchone()[0]
    
    # آخرین آگهی اضافه شده
    cursor.execute("SELECT title, company, scraped_at FROM jobvision_jobs ORDER BY id DESC LIMIT 1")
    last_job = cursor.fetchone()
    
    conn.close()
    return total, last_5min, last_hour, today, companies, last_job

def clear_screen():
    """پاک کردن صفحه (اختیاری)"""
    os.system('cls' if os.name == 'nt' else 'clear')

# =========================
# حالت نمایش: Static (به‌روز در جای خود)
# =========================
def display_static():
    """نمایش ثابت با به‌روزرسانی در جای خود"""
    print("\n" + "=" * 80)
    print("📊 JOBVISION DATABASE MONITOR")
    print("=" * 80)
    
    # متغیرهای قبلی برای محاسبه نرخ
    prev_total = None
    prev_time = None
    
    while True:
        try:
            total, last_5min, last_hour, today, companies, last_job = get_stats()
            
            now = datetime.now().strftime("%H:%M:%S")
            
            # محاسبه نرخ
            rate_text = ""
            if prev_total is not None and prev_time is not None:
                time_diff = (datetime.now() - prev_time).total_seconds()
                if time_diff > 0:
                    rate = (total - prev_total) / time_diff * 60
                    rate_text = f" | 📈 Rate: {rate:.2f}/min"
            
            # نمایش
            print(f"\n🕐 {now} {rate_text}")
            print("─" * 80)
            print(f"📋 Total Jobs:     {total:,}")
            print(f"📊 Last 5 min:     +{last_5min}")
            print(f"📊 Last 1 hour:    +{last_hour}")
            print(f"📅 Today:          +{today}")
            print(f"🏢 Companies:      {companies:,}")
            
            if last_job:
                title = last_job[0][:40] + "..." if len(last_job[0]) > 40 else last_job[0]
                print(f"🔖 Last Job:       {title} - {last_job[1]}")
                print(f"⏰ Added at:       {last_job[2]}")
            
            print("=" * 80)
            print("Press Ctrl+C to exit")
            
            # ذخیره برای محاسبه نرخ بعدی
            prev_total = total
            prev_time = datetime.now()
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

# =========================
# حالت نمایش: Scroll (همیشه جدید)
# =========================
def display_scroll():
    """نمایش اسکرول شونده (هر بار خط جدید)"""
    print("\n" + "=" * 80)
    print("📊 JOBVISION DATABASE MONITOR (SCROLL MODE)")
    print("=" * 80)
    
    prev_total = None
    prev_time = None
    
    while True:
        try:
            total, last_5min, last_hour, today, companies, last_job = get_stats()
            
            now = datetime.now().strftime("%H:%M:%S")
            
            # محاسبه نرخ
            rate_text = ""
            if prev_total is not None and prev_time is not None:
                time_diff = (datetime.now() - prev_time).total_seconds()
                if time_diff > 0:
                    rate = (total - prev_total) / time_diff * 60
                    rate_text = f" | {rate:.2f}/min"
            
            # نمایش در یک خط
            print(f"[{now}] 📊 Total: {total:,} | +5m: {last_5min} | +1h: {last_hour} | Today: {today} | Rate: {rate_text}")
            
            prev_total = total
            prev_time = datetime.now()
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

# =========================
# حالت نمایش: Progress Bar
# =========================
def display_progress(target=1594):
    """نمایش با نوار پیشرفت (برای کل پروژه)"""
    print("\n" + "=" * 80)
    print("📊 JOBVISION PROGRESS MONITOR")
    print("=" * 80)
    
    start_total = None
    start_time = datetime.now()
    
    while True:
        try:
            total, last_5min, last_hour, today, companies, last_job = get_stats()
            
            now = datetime.now().strftime("%H:%M:%S")
            
            # محاسبه پیشرفت
            if start_total is None:
                start_total = total - last_hour  # تخمین شروع
            
            progress = total - start_total
            percent = (progress / target) * 100 if target > 0 else 0
            
            # نوار پیشرفت
            bar_length = 50
            filled = int(bar_length * percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            elapsed_str = f"{int(elapsed//3600)}h {int((elapsed%3600)//60)}m {int(elapsed%60)}s"
            
            if progress > 0:
                rate = progress / elapsed * 60
                remaining = (target - progress) / rate if rate > 0 else 0
                remaining_str = f"{int(remaining//3600)}h {int((remaining%3600)//60)}m"
            else:
                remaining_str = "Calculating..."
            
            # پاک کردن صفحه و نمایش
            clear_screen()
            print("=" * 80)
            print("📊 JOBVISION PROGRESS MONITOR")
            print("=" * 80)
            print(f"🕐 {now} | ⏱️ Elapsed: {elapsed_str}")
            print("─" * 80)
            print(f"🎯 Progress: {bar} {percent:.1f}%")
            print(f"📋 Jobs:     {progress:,} / {target:,}")
            print(f"⏳ Remaining: {remaining_str} (Rate: {rate:.2f}/min)")
            print("─" * 80)
            print(f"📊 Total DB:  {total:,}")
            print(f"🏢 Companies: {companies:,}")
            print(f"📅 Today:     +{today}")
            
            if last_job:
                title = last_job[0][:35] + "..." if len(last_job[0]) > 35 else last_job[0]
                print(f"🔖 Last:      {title}")
            
            print("=" * 80)
            print("Press Ctrl+C to exit")
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

# =========================
# انتخاب حالت
# =========================
if __name__ == "__main__":
    print("=" * 80)
    print("📊 JOBVISION DATABASE MONITOR")
    print("=" * 80)
    print("Select display mode:")
    print("  1. Static (به‌روز در جای خود) - پیشنهادی")
    print("  2. Scroll (اسکرول شونده)")
    print("  3. Progress (نوار پیشرفت برای کل پروژه)")
    print("  4. Simple (نمایش ساده در یک خط)")
    print("=" * 80)
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == "1":
        display_static()
    elif choice == "2":
        display_scroll()
    elif choice == "3":
        display_progress(target=508)  # تعداد کل آگهی‌های جدید
    elif choice == "4":
        # حالت ساده (همون قبلی)
        print("\n📊 Simple mode...")
        while True:
            try:
                total, last_5min, last_hour, today, companies, last_job = get_stats()
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] 📊 Total: {total} | Last 5min: +{last_5min} | Last hour: +{last_hour}")
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except:
                time.sleep(5)
    else:
        print("❌ Invalid choice. Running default (Static)...")
        display_static()