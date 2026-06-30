# utils/url_normalizer.py
"""
ماژول مرکزی برای نرمال‌سازی URLها
همه جای برنامه از این ماژول استفاده میکنن
"""

import re


def normalize_url(url):
    """
    نرمال‌سازی URL با حذف پارامترهای متغیر
    مثل: searchId, score, row, pageSize, ReferrerJobPosition
    
    Args:
        url (str): URL ورودی
        
    Returns:
        str: URL نرمال شده
    """
    if not url:
        return url
    
    # حذف پارامترهای متغیر
    patterns = [
        r'searchId=[^&]*',           # searchId
        r'score=[^&]*',              # score
        r'row=[^&]*',                # row
        r'pageSize=[^&]*',           # pageSize
        r'ReferrerJobPosition=[^&]*', # ReferrerJobPosition
        r'&?\w+=\d+\.\d+',           # هر پارامتر عددی با اعشار
    ]
    
    normalized = url
    for pattern in patterns:
        normalized = re.sub(pattern, '', normalized)
    
    # پاک کردن کاراکترهای اضافی
    normalized = re.sub(r'[?&]{2,}', '?', normalized)
    normalized = re.sub(r'[?&]$', '', normalized)
    
    return normalized


def is_normalized(url):
    """
    بررسی اینکه آیا URL نرمال شده است یا نه
    
    Args:
        url (str): URL ورودی
        
    Returns:
        bool: True اگر نرمال شده باشد
    """
    if not url:
        return True
    
    # اگر پارامترهای متغیر وجود داشته باشد، نرمال نشده است
    patterns = [
        r'searchId=',
        r'score=',
        r'row=',
        r'pageSize=',
        r'ReferrerJobPosition=',
        r'=\d+\.\d+',
    ]
    
    for pattern in patterns:
        if re.search(pattern, url):
            return False
    
    return True


def batch_normalize_urls(urls):
    """
    نرمال‌سازی لیستی از URLها
    
    Args:
        urls (list): لیست URLها
        
    Returns:
        list: لیست URLهای نرمال شده
    """
    return [normalize_url(url) for url in urls]


def normalize_job_urls(job):
    """
    نرمال‌سازی URL یک آگهی (دیکشنری)
    
    Args:
        job (dict): دیکشنری آگهی
        
    Returns:
        dict: دیکشنری آگهی با URL نرمال شده
    """
    if not job:
        return job
    
    url = job.get('url')
    if url:
        job['url'] = normalize_url(url)
    
    return job


def normalize_jobs_urls(jobs):
    """
    نرمال‌سازی URLهای لیستی از آگهی‌ها
    
    Args:
        jobs (list): لیست دیکشنری‌های آگهی
        
    Returns:
        list: لیست آگهی‌ها با URLهای نرمال شده
    """
    return [normalize_job_urls(job) for job in jobs]


# =========================
# تست
# =========================
if __name__ == "__main__":
    test_urls = [
        "https://jobvision.ir/jobs/123?searchId=xxx&score=26.52&row=1",
        "https://jobvision.ir/jobs/456?pageSize=30&ReferrerJobPosition=8",
        "https://jobvision.ir/jobs/789?searchId=yyy&score=15.5",
        "https://jobvision.ir/jobs/123/normal-url",
    ]
    
    print("🔧 Testing URL Normalizer")
    print("=" * 60)
    
    for url in test_urls:
        normalized = normalize_url(url)
        is_norm = is_normalized(url)
        print(f"\n📌 Original:  {url}")
        print(f"   Normalized: {normalized}")
        print(f"   Is normalized: {is_norm}")