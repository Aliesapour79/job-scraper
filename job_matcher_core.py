from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import datetime
import platform
import re
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
from webdriver_manager.chrome import ChromeDriverManager


# ==========================================
# توابع جدید: Penalty, Boost, Normalization
# ==========================================

from config import GENERIC_KEYWORDS, TECH_KEYWORDS

def generic_penalty(job_text):
    """
    محاسبه جریمه برای آگهی‌های عمومی
    هر کلمه عمومی ۵٪ جریمه، حداکثر ۲۰٪
    """
    job_text_lower = job_text.lower()
    count = sum(1 for w in GENERIC_KEYWORDS if w.lower() in job_text_lower)
    penalty = min(0.20, count * 0.05)  # حداکثر ۲۰٪
    return penalty

def domain_boost(job_text, resume_text):
    """
    محاسبه پاداش برای آگهی‌های تخصصی
    هر کلمه تخصصی ۵٪ پاداش، حداکثر ۲۰٪
    """
    job_text_lower = job_text.lower()
    resume_text_lower = resume_text.lower()
    
    matches = 0
    for keyword in TECH_KEYWORDS:
        keyword_lower = keyword.lower()
        if keyword_lower in job_text_lower and keyword_lower in resume_text_lower:
            matches += 1
    
    boost = min(0.20, matches * 0.05)  # حداکثر ۲۰٪
    return boost

def min_max_normalize(scores):
    """
    نرمال‌سازی Min-Max روی لیست امتیازها
    خروجی: لیست امتیازهای نرمال شده در بازه ۰ تا ۱
    """
    if not scores:
        return scores
    
    min_val = min(scores)
    max_val = max(scores)
    
    if max_val == min_val:
        return [0.5] * len(scores)
    
    return [(x - min_val) / (max_val - min_val) for x in scores]

def calculate_final_score(job_text, resume_text, embedding_score, tfidf_score):
    """
    محاسبه امتیاز نهایی با فرمول جدید:
    1. نرمال‌سازی Embedding و TF-IDF
    2. ترکیب با وزن‌ها
    3. اعمال جریمه و پاداش
    """
    from config import SCORE_WEIGHTS
    
    # نرمال‌سازی امتیازها (با فرض اینکه هر دو در بازه ۰-۱۰۰ هستن)
    norm_embedding = embedding_score / 100.0
    norm_tfidf = tfidf_score / 100.0
    
    # ترکیب با وزن‌ها
    base_score = (
        norm_embedding * SCORE_WEIGHTS['embedding'] +
        norm_tfidf * SCORE_WEIGHTS['tfidf']
    )
    
    # اعمال جریمه و پاداش
    penalty = generic_penalty(job_text)
    boost = domain_boost(job_text, resume_text)
    
    final_score = base_score * (1 - penalty) * (1 + boost)
    
    # تبدیل به درصد و محدود کردن به ۰-۱۰۰
    return int(min(100, max(0, final_score * 100)))
warnings.filterwarnings('ignore')

# ==========================================
# YOUR RESUME TEXT (UPDATED)
# ==========================================
RESUME_TEXT = """
علی عیسی پور شربیانی
برنامه‌نویس با تمرکز بر پیاده‌سازی پروژه‌های مبتنی بر هوش مصنوعی و IoT

مهارت‌های فنی:
- برنامه‌نویسی: Python, C++, JavaScript
- هوش مصنوعی: Machine Learning, Deep Learning, Computer Vision
- پردازش تصویر: OpenCV, YOLO, CNN
- اینترنت اشیاء: ESP32, MQTT, Arduino, Raspberry Pi
- الکترونیک: طراحی مدار, PCB, Altium, میکروکنترلر
- تحلیل داده: Pandas, NumPy, MySQL, SQLite, MongoDB
- شبکه: TCP/IP, DNS, Linux, Git

مهارت‌های اداری:
- تسلط کامل بر Word, Excel, PowerPoint, Outlook
- مدیریت دفتر و مکاتبات اداری
- گزارش‌نویسی و مستندسازی
- مدیریت زمان و اولویت‌بندی وظایف
- هماهنگی و پیگیری امور اداری
- مدیریت پروژه‌های گروهی
- ارتباط موثر با تیم‌های مختلف

سوابق کاری:
- برنامه‌نویس در آیسان (پروژه‌های AI و IoT) - ۱۲/۱۴۰۲ تا ۰۴/۱۴۰۴
- مدیر IT در دفتر خدمات الکترونیک قضایی - ۰۳/۱۳۹۹ تا ۰۶/۱۴۰۰

تحصیلات:
- کارشناسی مهندسی تکنولوژی نرم‌افزار (معدل ۱۷.۴) - دانشگاه گنبد کاووس
- کاردانی فناوری اطلاعات (معدل ۱۶.۹۹) - دانشکده شهید شمسی‌پور

پروژه‌ها:
1. مدیریت ورود و خروج خودرو به پارکینگ با QR (ESP32 + Database)
2. سیستم حضور غیاب با اثر انگشت
3. تشخیص اجزای ماشین با هوش مصنوعی
4. طبقه‌بندی اعداد فارسی با بینایی کامپیوتر
5. تشخیص نوع زیتون با Web Application
6. تشخیص بیماری گیاهان با یادگیری عمیق

دستاوردها:
- معدل عالی در مقطع کاردانی و کارشناسی
- دبیر انجمن علمی کامپیوتر دانشگاه گنبد کاووس
- دستیار آموزشی (TA) در دانشگاه
- شخصیت تحلیلی و هدف‌گرا (ENTJ-A)
"""

# ==========================================
# SKILL GROUPS (UPDATED)
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
        "base_weight": 5,
        "bonus_per_match": 0.8,
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
# JOB TITLE KEYWORDS FOR DYNAMIC WEIGHT (UPDATED)
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

# ==========================================
# SETUP DRIVER
# ==========================================
def setup_driver():
    """Setup Chrome driver with automatic driver management"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # استفاده از webdriver-manager برای مدیریت خودکار ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome driver started successfully!")
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        print("   Trying fallback method...")
        
        # Fallback: استفاده از مسیر مستقیم
        try:
            if platform.system() == 'Windows':
                chrome_driver_path = r"C:\chromedriver\chromedriver.exe"
            else:
                chrome_driver_path = "/usr/local/bin/chromedriver"
            
            service = Service(chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome driver started with fallback!")
            return driver
        except:
            print("❌ Could not start Chrome driver. Please check installation.")
            raise

# ==========================================
# EXTRACT JOB DETAILS
# ==========================================
def extract_job_details(driver, url):
    """Extract full job details with multiple fallback selectors"""
    try:
        driver.get(url)
        time.sleep(5)
        
        full_text = driver.find_element(By.TAG_NAME, "body").text
        
        selectors = {
            "title": [
                ".entry-title h1", "h1.entry-title span", 
                ".job-title h1", "h1[itemprop='title']",
                ".page-header h1"
            ],
            "description": [
                ".job-content p:first-child", 
                ".job-description p",
                "[itemprop='description']",
                ".content p"
            ],
            "requirements": [
                "//h2[contains(text(), 'شرایط احراز')]/following-sibling::ul",
                "//h3[contains(text(), 'مهارت‌ها')]/following-sibling::ul",
                "//h2[contains(text(), 'نیازمندی‌ها')]/following-sibling::ul",
                "//div[contains(@class, 'requirements')]//ul"
            ]
        }
        
        sections = {}
        for key, selector_list in selectors.items():
            for selector in selector_list:
                try:
                    if selector.startswith("//"):
                        elem = driver.find_element(By.XPATH, selector)
                    else:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                    sections[key] = elem.text.strip()
                    break
                except:
                    continue
            if key not in sections:
                sections[key] = ""
        
        try:
            location = driver.find_element(By.CSS_SELECTOR, ".job-content .text-center h5")
            sections["location"] = location.text.strip()
        except:
            sections["location"] = ""
        
        sections["full_text"] = full_text
        sections["combined"] = f"""
TITLE_SECTION: {sections.get('title', '')}
DESCRIPTION_SECTION: {sections.get('description', '')}
REQUIREMENTS_SECTION: {sections.get('requirements', '')}
LOCATION_SECTION: {sections.get('location', '')}
FULL_TEXT: {full_text}
"""
        
        return sections
        
    except Exception as e:
        print(f"  Error extracting job details: {e}")
        return {}

# ==========================================
# LEVEL 3: SEMANTIC MATCHING WITH TF-IDF
# ==========================================
def semantic_match_score(job_text, resume_text, skill_keywords):
    """محاسبه‌ی شباهت معنایی با TF-IDF و Cosine Similarity"""
    if not job_text or not resume_text:
        return 0
    
    enhanced_resume = resume_text + " " + " ".join(skill_keywords * 2)
    job_text_clean = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', job_text).lower()
    resume_clean = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', enhanced_resume).lower()
    
    try:
        corpus = [job_text_clean, resume_clean]
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words=None,
            ngram_range=(1, 2),
            min_df=1
        )
        
        tfidf_matrix = vectorizer.fit_transform(corpus)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return similarity[0][0] * 100
        
    except Exception as e:
        print(f"  ⚠️ TF-IDF Error: {e}")
        return 0

def calculate_outlier_score(scores_list, current_score):
    """
    محاسبه‌ی امتیاز outlier با استفاده از CDF نرمال
    تبدیل Z-score به percentile با استفاده از توزیع نرمال
    """
    if len(scores_list) < 5:
        return 50
    
    mean = np.mean(scores_list)
    std = np.std(scores_list)
    
    if std == 0:
        return 50
    
    z_score = (current_score - mean) / std
    
    # استفاده از CDF برای تبدیل Z-score به percentile
    try:
        from scipy.stats import norm
        percentile = norm.cdf(z_score) * 100
        return int(min(100, max(0, percentile)))
    except ImportError:
        # Fallback: اگر scipy نصب نبود، از روش تقریبی استفاده کن
        # تقریب خوب برای CDF نرمال
        if z_score >= 0:
            percentile = 50 + (z_score * 34)  # تقریب خطی برای z-score مثبت
        else:
            percentile = 50 + (z_score * 34)
        return int(min(100, max(0, percentile)))

# ==========================================
# CALCULATE KEYWORD SCORE
# ==========================================
def calculate_keyword_score(full_text, requirements_text, description_text, title_text):
    """محاسبه‌ی امتیاز بر اساس کلمات کلیدی (سطح ۲)"""
    
    full_text_lower = full_text.lower()
    requirements_lower = requirements_text.lower()
    description_lower = description_text.lower()
    title_lower = title_text.lower()
    
    # Dynamic weight adjustment
    group_weight_multipliers = defaultdict(float)
    for keyword, group_names in JOB_TITLE_WEIGHT_MAP.items():
        if keyword.lower() in title_lower:
            for group_name in group_names:
                group_weight_multipliers[group_name] = max(
                    group_weight_multipliers[group_name], 1.5
                )
    
    group_results = {}
    total_score = 0
    all_matched_keywords = []
    
    for group_name, group_config in SKILL_GROUPS.items():
        keywords = group_config["keywords"]
        base_weight = group_config["base_weight"]
        bonus_per_match = group_config["bonus_per_match"]
        min_matches_for_bonus = group_config["min_matches_for_bonus"]
        
        multiplier = group_weight_multipliers.get(group_name, 1.0)
        effective_weight = base_weight * multiplier
        
        matched = []
        match_count = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            importance_score = 0
            if keyword_lower in requirements_lower:
                importance_score += 2
            if keyword_lower in description_lower:
                importance_score += 1.2
            if keyword_lower in full_text_lower:
                importance_score += 0.8
            
            if importance_score > 0:
                count_in_text = full_text_lower.count(keyword_lower)
                count_in_req = requirements_lower.count(keyword_lower)
                
                total_occurrences = min(count_in_text + count_in_req * 2, 5)
                match_count += total_occurrences
                matched.append(keyword)
                all_matched_keywords.append(keyword)
        
        bonus = 0
        if match_count >= min_matches_for_bonus:
            bonus = min(match_count * bonus_per_match, effective_weight * 0.5)
        
        group_score = (match_count * effective_weight * 0.3) + bonus
        group_results[group_name] = {
            "score": int(group_score),
            "match_count": match_count,
            "matched_keywords": matched[:10],
            "effective_weight": effective_weight,
            "bonus": int(bonus),
            "multiplier": multiplier
        }
        total_score += group_score
    
    # Normalize
    max_possible_score = sum([
        config["base_weight"] * 5 * 0.3 + (config["base_weight"] * 0.5) 
        for config in SKILL_GROUPS.values()
    ])
    
    if max_possible_score == 0:
        return 0, [], {}
    
    percentage = int((total_score / max_possible_score) * 100)
    matched_keywords = list(set(all_matched_keywords))[:20]
    
    return min(100, percentage), matched_keywords, group_results

# ==========================================
# CALCULATE MATCH SCORE (سطح ۲ + ۳)
# ==========================================
def calculate_match_score_advanced(sections, job_title="", all_scores=None):
    """ترکیب سطح ۲ (گروه‌بندی) و سطح ۳ (TF-IDF + Outlier)"""
    
    if not sections:
        return 0, [], {}, 0, 0
    
    full_text = sections.get("full_text", "")
    requirements_text = sections.get("requirements", "")
    description_text = sections.get("description", "")
    title_text = sections.get("title", "") or job_title
    
    # 📊 STEP 1: Keyword-based scoring (Level 2)
    keyword_score, matched_keywords, group_results = calculate_keyword_score(
        full_text, requirements_text, description_text, title_text
    )
    
    # 📊 STEP 2: Semantic scoring (Level 3 - TF-IDF)
    combined_job_text = f"{title_text} {description_text} {requirements_text}"
    semantic_score = semantic_match_score(combined_job_text, RESUME_TEXT, matched_keywords)
    
    # 📊 STEP 3: Combined score
    final_score = int((keyword_score * 0.7) + (semantic_score * 0.3))
    
    # 📊 STEP 4: Outlier score (Level 3 - Z-Score)
    outlier_score = 0
    if all_scores and len(all_scores) > 2:
        outlier_score = calculate_outlier_score(all_scores, final_score)
    
    return final_score, matched_keywords, group_results, semantic_score, outlier_score

# ==========================================
# EXTRACT ALL JOBS
# ==========================================
def extract_all_jobs(driver, url):
    print("Loading page...")
    driver.get(url)
    
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list")))
    
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    
    job_links = driver.find_elements(By.CSS_SELECTOR, ".search-list .item a.item-content")
    print(f"✅ Found {len(job_links)} job links")
    
    jobs_data = []
    main_window = driver.current_window_handle
    
    for idx, link in enumerate(job_links, 1):
        try:
            print(f"Processing job {idx}/{len(job_links)}...")
            
            link_text = link.text.strip()
            lines = link_text.split('\n')
            title = lines[0] if lines else f"Job {idx}"
            company = lines[1] if len(lines) > 1 else "Unknown"
            href = link.get_attribute('href')
            
            if not href:
                continue
            
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            
            sections = extract_job_details(driver, href)
            
            driver.close()
            driver.switch_to.window(main_window)
            time.sleep(0.5)
            
            if sections:
                jobs_data.append({
                    "title": title,
                    "company": company,
                    "url": href,
                    "sections": sections,
                    "index": idx
                })
                print(f"  ✅ Extracted: {title[:30]}...")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            continue
    
    return jobs_data
