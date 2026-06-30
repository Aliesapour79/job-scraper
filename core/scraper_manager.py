# core/scraper_manager.py
import time
import random
import re
from tqdm import tqdm
from utils.url_normalizer import normalize_url
from utils.database import save_job, get_all_existing_urls
from utils.cache import cache_exists, load_jobs_cache, save_jobs_cache, clear_cache
from utils.driver_manager import safe_driver_get, restart_driver
from scrapers import JobvisionScraper


def get_jobs_from_site_range(driver, scraper, site, start_index=0, count=10):
    """
    دریافت تعداد مشخصی آگهی از سایت (با sort=0)
    
    Args:
        driver: WebDriver
        scraper: JobvisionScraper
        site: اطلاعات سایت
        start_index: از چندمین آگهی شروع کن
        count: تعداد آگهی مورد نیاز
    """
    try:
        url = site['url']
        if 'sort=' not in url:
            url = f"{url}?sort=0"
        elif 'sort=0' not in url:
            url = url.replace('sort=', 'sort=0')
        
        # اگه start_index > 0 باشه، باید صفحه مناسب رو پیدا کنه
        # هر صفحه ۳۰ تا آگهی داره
        if start_index > 0:
            page_num = (start_index // 30) + 1
            if '?' in url:
                url = f"{url}&page={page_num}"
            else:
                url = f"{url}?page={page_num}"
        
        driver.get(url)
        time.sleep(3)
        
        cards = scraper.extract_job_cards()
        if not cards:
            return []
        
        # محاسبه offset در صفحه
        offset = start_index % 30
        end_index = min(offset + count, len(cards))
        selected_cards = cards[offset:end_index]
        
        result = []
        for card in selected_cards:
            job_url = card.get('href') or card.get('url')
            if not job_url:
                job_url = card.get('data-url') or card.get('link')
            
            if job_url and not job_url.startswith('http'):
                job_url = f"https://jobvision.ir{job_url}"
            
            result.append({
                'url': job_url,
                'normalized_url': normalize_url(job_url),
                'title': card.get('title'),
                'company': card.get('company'),
                'location': card.get('location', ''),
                'salary': card.get('salary', ''),
                'is_urgent': card.get('is_urgent', False),
                'site': site['name']
            })
        
        return result
        
    except Exception as e:
        print(f"⚠️ Could not get jobs from site: {e}")
        return []


def get_jobs_from_cache_range(cached_jobs, start_index=0, count=10):
    """دریافت تعداد مشخصی آگهی از کش"""
    if not cached_jobs:
        return []
    
    end_index = min(start_index + count, len(cached_jobs))
    return cached_jobs[start_index:end_index]


def find_new_jobs_adaptive(cached_jobs, driver, scraper, site, batch_size=10):
    """
    پیدا کردن آگهی‌های جدید با روش تطبیقی
    
    Returns:
        list: آگهی‌های جدید
    """
    all_new_jobs = []
    start_index = 0
    total_cached = len(cached_jobs)
    
    print(f"🔍 Adaptive search for new jobs (batch size: {batch_size})...")
    
    while True:
        # گرفتن از کش
        cache_batch = get_jobs_from_cache_range(cached_jobs, start_index, batch_size)
        
        # گرفتن از سایت
        site_batch = get_jobs_from_site_range(driver, scraper, site, start_index, batch_size)
        
        # اگه سایتی نبود یا به آخر رسیدیم
        if not site_batch:
            print(f"   ⏹️ No more jobs on site at index {start_index}")
            break
        
        # اگه کش تموم شد، همه آگهی‌های باقی‌مانده جدید هستن
        if not cache_batch:
            print(f"   ✅ Cache ended at index {start_index}, remaining {len(site_batch)} jobs are new")
            all_new_jobs.extend(site_batch)
            break
        
        # مقایسه
        cache_urls = {job.get('normalized_url') for job in cache_batch}
        new_in_batch = []
        duplicate_found = False
        
        for job in site_batch:
            if job.get('normalized_url') not in cache_urls:
                new_in_batch.append(job)
            else:
                duplicate_found = True
                # اگه تکراری پیدا شد، بقیه رو هم چک کن (چون ممکنه بعد از تکراری، دوباره جدید باشه)
                # ولی فعلاً اولویت با پیدا کردن تکراریه
        
        if new_in_batch:
            print(f"   ✅ Batch at index {start_index}: {len(new_in_batch)} new job(s)")
            all_new_jobs.extend(new_in_batch)
        
        # 🎯 شرط توقف: اگه حداقل ۱ تکراری پیدا شد، بایست
        if duplicate_found:
            print(f"   🛑 Duplicate found at index {start_index}, stopping")
            break
        
        # اگه همه ۱۰ تا جدید بودن، برو ۱۰ تای بعدی
        if len(new_in_batch) == batch_size:
            print(f"   ➡️ All {batch_size} jobs are new, moving to next batch...")
            start_index += batch_size
        else:
            # اگه بعضی جدید و بعضی نه (ولی تکراری پیدا نشد)
            # یعنی آگهی‌های جدید کمتر از batch_size هستن
            break
    
    return all_new_jobs


def load_site_jobs(scraper, site):
    """
    بارگذاری هوشمند آگهی‌ها با روش تطبیقی
    
    منطق:
    ۱. کش رو چک کن
    ۲. ۱۰ تا ۱۰ تا آگهی رو مقایسه کن
    ۳. اگه همه ۱۰ تا جدید بودن → برو ۱۰ تای بعدی
    ۴. اگه حداقل ۱ تکراری پیدا شد → بایست
    ۵. آگهی‌های جدید رو به کش اضافه کن
    """
    
    # =========================
    # مرحله ۱: چک کردن کش
    # =========================
    if cache_exists(site['name']):
        print(f"\n📂 Cache found for {site['name']}")
        cached_jobs = load_jobs_cache(site['name'])
        
        if not cached_jobs:
            print("⚠️ Cache is empty, scraping from scratch...")
            clear_cache(site['name'])
            # fall through to scrape
        
        else:
            # =========================
            # مرحله ۲: پیدا کردن آگهی‌های جدید با روش تطبیقی
            # =========================
            print(f"🔍 Checking for new jobs on {site['name']}...")
            
            new_jobs = find_new_jobs_adaptive(
                cached_jobs, 
                scraper.driver, 
                scraper, 
                site, 
                batch_size=10
            )
            
            if not new_jobs:
                print(f"✅ No new jobs found!")
                print(f"   Using cache ({len(cached_jobs)} jobs)")
                return cached_jobs
            
            print(f"\n✅ Found {len(new_jobs)} new job(s) total!")
            for job in new_jobs[:10]:
                print(f"   🆕 {job.get('title')} - {job.get('company')}")
            if len(new_jobs) > 10:
                print(f"   ... and {len(new_jobs) - 10} more")
            
            # اضافه کردن آگهی‌های جدید به اول کش
            updated_jobs = new_jobs + cached_jobs
            
            # ذخیره کش جدید
            save_jobs_cache(site['name'], updated_jobs)
            print(f"💾 Cache updated: {len(updated_jobs)} jobs total")
            print(f"   +{len(new_jobs)} new jobs added to top")
            
            return updated_jobs
    
    # =========================
    # مرحله ۳: اسکرپ کامل (بدون کش)
    # =========================
    print(f"\n🌐 Scraping all pages for {site['name']}...")
    jobs = scraper.extract_all_pages(max_pages=site.get('max_pages', 100))
    
    if jobs:
        simplified_jobs = []
        for job in jobs:
            job_url = job.get('href') or job.get('url')
            if not job_url:
                job_url = job.get('data-url') or job.get('link')
            
            if job_url and not job_url.startswith('http'):
                job_url = f"https://jobvision.ir{job_url}"
            
            simplified_jobs.append({
                'url': job_url,
                'normalized_url': normalize_url(job_url),
                'title': job.get('title'),
                'company': job.get('company'),
                'location': job.get('location', ''),
                'salary': job.get('salary', ''),
                'is_urgent': job.get('is_urgent', False),
                'site': job.get('site', site['name'])
            })
        
        save_jobs_cache(site['name'], simplified_jobs)
        print(f"💾 Cache saved ({len(simplified_jobs)} jobs)")
        return simplified_jobs
    else:
        print("⚠️ No jobs found during scraping")
        return []


# =========================
# بقیه توابع بدون تغییر
# =========================
def filter_new_jobs(jobs, enable_db_save=True):
    """فیلتر آگهی‌های جدید با استفاده از normalized_url"""
    if not enable_db_save:
        return jobs
    
    print("\n🔍 Loading existing URLs from database...")
    existing_urls = get_all_existing_urls()
    print(f"   📋 {len(existing_urls)} existing jobs in DB")
    
    original_count = len(jobs)
    jobs = [job for job in jobs if job.get('normalized_url') not in existing_urls]
    skipped = original_count - len(jobs)
    
    print(f"   ✅ {len(jobs)} new jobs | ⏭️ {skipped} duplicates skipped")
    
    if not jobs:
        print("⚠️ No new jobs, skipping...")
        return []
    
    print(f"\n📥 Extracting details for {len(jobs)} new jobs...")
    return jobs


def extract_job_details(jobs, site, driver, all_jobs, config, save_partial_func):
    """استخراج جزئیات آگهی‌ها"""
    RESTART_EVERY = config.get('RESTART_EVERY', 60)
    SLEEP_RANGE = config.get('SLEEP_RANGE', (5, 8))
    MAX_FAILURE_RATE = config.get('MAX_FAILURE_RATE', 0.25)
    PARTIAL_SAVE_EVERY = config.get('PARTIAL_SAVE_EVERY', 50)
    ENABLE_DB_SAVE = config.get('ENABLE_DB_SAVE', True)
    
    scraper = JobvisionScraper(driver)
    successful = 0
    failed = 0
    db_saved = 0
    db_duplicate = 0
    
    for i, job in enumerate(tqdm(jobs, desc=f"Extracting {site['name']}", unit="job")):
        idx = i + 1
        
        if idx > 20 and failed / idx > MAX_FAILURE_RATE:
            print(f"⚠️ Failure rate too high ({failed}/{idx}), stopping")
            break
        
        if idx % RESTART_EVERY == 0:
            driver = restart_driver(driver)
            scraper = JobvisionScraper(driver)
            driver.get(site['url'])
            time.sleep(3)
        
        try:
            if not safe_driver_get(driver, job['url']):
                failed += 1
                print(f"     ❌ Skipping job {idx}")
                continue
            
            detail = scraper.extract_job_detail(job['url'])
            driver.get('about:blank')
            
            if not detail or detail.get("error"):
                failed += 1
                continue
            
            job['sections'] = {
                'full_text': detail.get('full_text', ''),
                'title': job.get('title', ''),
                'description': detail.get('description', ''),
                'requirements': detail.get('requirements', ''),
                'company': job.get('company', '')
            }
            job['skills'] = detail.get('skills', [])
            job['site'] = site['name']
            job['job_category'] = site.get('job_category', '')
            
            all_jobs.append(job)
            successful += 1
            
            if ENABLE_DB_SAVE:
                result = save_job(job)
                if result:
                    db_saved += 1
                else:
                    db_duplicate += 1
                    
        except Exception as e:
            failed += 1
            print(f"     ❌ Error on job {idx}: {str(e)[:80]}")
            if "crash" in str(e).lower():
                driver = restart_driver(driver)
                scraper = JobvisionScraper(driver)
                driver.get(site['url'])
                time.sleep(3)
        
        finally:
            time.sleep(random.uniform(*SLEEP_RANGE))
        
        if idx % PARTIAL_SAVE_EVERY == 0:
            save_partial_func(all_jobs, idx)
    
    print(f"✅ Done: {successful} success | {failed} failed | DB Saved: {db_saved} | DB Duplicate: {db_duplicate}")
    return all_jobs, driver