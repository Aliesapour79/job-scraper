from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
from datetime import datetime
import os
import platform
from webdriver_manager.chrome import ChromeDriverManager
from nlp.scorer import score_jobs
# ==========================================
# SKILLS WEIGHT (Based on your resume)
# ==========================================
SKILLS_WEIGHT = {
    # ==========================================
    # CORE TECHNICAL SKILLS (Weight 10)
    # ==========================================
    "iot": 10,
    "اینترنت اشیاء": 10,
    "الکترونیک": 10,
    "میکروکنترلر": 10,
    "esp32": 10,
    "can bus": 10,
    "mqtt": 10,
    "طراحی مدار": 10,
    "pcb": 10,
    "altium": 10,
    "arduino": 10,
    "embedded": 10,
    "سیستم‌های نهفته": 10,
    "سنسور": 9,
    "پروتکل": 9,

    # ==========================================
    # PROGRAMMING SKILLS (Weight 8)
    # ==========================================
    "python": 8,
    "c++": 8,
    "برنامه نویسی": 8,

    # ==========================================
    # AI & DATA SKILLS (Weight 6-7)
    # ==========================================
    "هوش مصنوعی": 7,
    "machine learning": 7,
    "یادگیری ماشین": 7,
    "پردازش تصویر": 7,
    "opencv": 7,
    "تحلیل داده": 6,
    "sql": 6,

    # ==========================================
    # CONTEXTUAL / INDUSTRY SKILLS (Weight 5)
    # کلماتی که نشان می‌دهند آگهی به حوزه‌ی صنعتی شما مربوط است
    # ==========================================
    "صنعتی": 5,
    "تولیدی": 5,
    "کارخانه": 5,
    "سیستم هوشمند": 5,
    "اتوماسیون": 5,
    "رباتیک": 5,
    "کنترل": 5,
    "پایش": 5,
    "مانیتورینگ": 5,
    "ابزار دقیق": 5,
    "تجهیزات": 5,
    "سخت افزار": 5,
    "سخت‌افزار": 5,
    "تعمیرات": 5,
    "نگهداری": 5,

    # ==========================================
    # GENERAL SKILLS (Weight 4)
    # مهارت‌های پایه‌ای که همه بلدند
    # ==========================================
    "word": 4,
    "excel": 4,
    "مدیریت زمان": 4,
    "الگوریتم": 4,
    "network": 4,
    "شبکه": 4,
    "linux": 4,
    "لینوکس": 4,
    "git": 4,
}

# ==========================================
# SETUP DRIVER
# ==========================================

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # وب‌درایور منیجر به‌طور خودکار کروم‌درایور را دانلود و مدیریت می‌کند
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver
# ==========================================
# EXTRACT JOB DETAILS FROM PAGE
# ==========================================
def extract_job_details(driver, url):
    """Extract full job details from a single job page"""
    try:
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get all text from the page
        full_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Try to find specific sections
        sections = {}
        
        # Find job title
        try:
            title_elem = driver.find_element(By.CSS_SELECTOR, ".entry-title h1, h1.entry-title span")
            sections["title"] = title_elem.text.strip()
        except:
            sections["title"] = "Unknown"
        
        # Find company/description
        try:
            desc = driver.find_element(By.CSS_SELECTOR, ".job-content p:first-child")
            sections["description"] = desc.text.strip()
        except:
            sections["description"] = ""
        
        # Find requirements section
        try:
            # Look for "شرایط احراز" section
            requirements = driver.find_element(By.XPATH, "//h2[contains(text(), 'شرایط احراز')]/following-sibling::ul")
            sections["requirements"] = requirements.text.strip()
        except:
            sections["requirements"] = ""
        
        # Find all job details
        try:
            # Get all detail items
            detail_items = driver.find_elements(By.CSS_SELECTOR, ".job-content .fs-xs.d-inline-block")
            details = []
            for item in detail_items:
                details.append(item.text.strip())
            sections["details"] = "\n".join(details)
        except:
            sections["details"] = ""
        
        # Find location
        try:
            location = driver.find_element(By.CSS_SELECTOR, ".job-content .text-center h5")
            sections["location"] = location.text.strip()
        except:
            sections["location"] = ""
        
        # Combine all text
        combined_text = f"""
Title: {sections.get('title', '')}
Description: {sections.get('description', '')}
Requirements: {sections.get('requirements', '')}
Details: {sections.get('details', '')}
Location: {sections.get('location', '')}
Full Text: {full_text}
"""
        
        return combined_text, full_text
        
    except Exception as e:
        print(f"  Error extracting job details: {e}")
        return "", ""

# ==========================================
# EXTRACT ALL JOB POSTINGS
# ==========================================
def extract_all_jobs(driver, url):
    """Extract all job postings by visiting each job link"""
    print("Loading page...")
    driver.get(url)
    
    # Wait for page to load
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list")))
    
    # Scroll to load all content
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    
    # Find all job links
    job_links = driver.find_elements(By.CSS_SELECTOR, ".search-list .item a.item-content")
    print(f"✅ Found {len(job_links)} job links")
    
    jobs_data = []
    main_window = driver.current_window_handle
    
    for idx, link in enumerate(job_links[:80], 1):
        try:
            print(f"Processing job {idx}/{len(job_links)}...")
            
            # Get job title and company from the link text
            link_text = link.text.strip()
            lines = link_text.split('\n')
            title = lines[0] if lines else f"Job {idx}"
            company = lines[1] if len(lines) > 1 else "Unknown"
            
            # Get the href attribute
            href = link.get_attribute('href')
            if not href:
                print(f"  ⚠️ No href found for job {idx}")
                continue
            
            # Open in new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            
            # Extract job details
            combined_text, full_text = extract_job_details(driver, href)
            
            # Close the tab and go back to main
            driver.close()
            driver.switch_to.window(main_window)
            time.sleep(0.5)
            
            jobs_data.append({
                "title": title,
                "company": company,
                "url": href,
                "full_text": combined_text,
                "description": full_text[:500] + "..." if len(full_text) > 500 else full_text,
                "index": idx
            })
            
            print(f"  ✅ Extracted: {title[:30]}... ({len(combined_text)} chars)")
            
        except Exception as e:
            print(f"  ❌ Error on job {idx}: {str(e)[:100]}")
            # Make sure we're back on the main page
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            continue
    
    return jobs_data

# ==========================================
# CALCULATE MATCH SCORE
# ==========================================
def calculate_match_score(text):
    """Calculate match percentage based on skills"""
    if not text:
        return 0, []
    
    text_lower = text.lower()
    total_score = 0
    matched_skills = []
    
    for skill, weight in SKILLS_WEIGHT.items():
        skill_lower = skill.lower()
        if skill_lower in text_lower:
            count = text_lower.count(skill_lower)
            score = weight * min(count, 3)
            total_score += score
            if skill not in matched_skills:
                matched_skills.append(skill)
    
    # Calculate percentage
    max_possible = sum(weight * 3 for weight in SKILLS_WEIGHT.values())
    if max_possible == 0:
        return 0, []
    
    percentage = int((total_score / max_possible) * 100)
    return min(100, percentage), matched_skills

# ==========================================
# MAIN FUNCTION
# ==========================================
def main():
    url = "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3"

    print("=" * 60)
    print("🔍 Scraping Job Postings - Ghods City")
    print("=" * 60)

    driver = setup_driver()

    try:
        print("🌐 Connecting to website...")

        # ==========================================
        # 1. SCRAPE JOBS
        # ==========================================
        jobs = extract_all_jobs(driver, url)

        if not jobs:
            print("❌ No jobs found!")
            return

        print(f"✅ Extracted {len(jobs)} jobs")

        # ==========================================
        # 2. AI SCORING (NEW VERSION)
        # ==========================================
        jobs = score_jobs(jobs)

        print("🔄 Jobs scored successfully...\n")

        # ==========================================
        # 3. SAVE RESULTS (NOW SAFE)
        # ==========================================
        results = []

        for job in jobs:
            results.append({
                "title": job["title"],
                "company": job["company"],
                "url": job["url"],
                "score": job["score"],
                "description": job["description"],
                "full_text": job["full_text"][:1000]
            })

            print(f"  ✅ [{job['score']}%] {job['title']}")

        # sort (optional, already sorted)
        results.sort(key=lambda x: x["score"], reverse=True)

        # save json
        filename = f"job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print(f"📁 Saved: {filename}")
        print(f"🎯 Total: {len(results)} jobs")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n✅ Browser closed.")
if __name__ == "__main__":
    main()
