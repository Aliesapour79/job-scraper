from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import time
import json
from datetime import datetime

from nlp.scorer import score_jobs


# ==========================================
# DRIVER SETUP
# ==========================================
def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ==========================================
# EXTRACT SINGLE JOB PAGE
# ==========================================
def extract_job_details(driver, url):
    try:
        driver.get(url)
        time.sleep(3)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1").text
        except:
            title = "Unknown"

        try:
            company = driver.find_element(By.CSS_SELECTOR, ".company, .employer").text
        except:
            company = "Unknown"

        combined_text = f"""
Title: {title}
Company: {company}
Content:
{body_text}
"""

        return combined_text, body_text

    except Exception as e:
        print(f"❌ Error extracting job page: {e}")
        return "", ""


# ==========================================
# EXTRACT ALL JOBS FROM LIST PAGE
# ==========================================
def extract_all_jobs(driver, url, limit=80):
    print("🌐 Loading job list page...")
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list")))

    job_links = driver.find_elements(By.CSS_SELECTOR, ".search-list .item a.item-content")

    print(f"🔎 Found {len(job_links)} jobs")

    jobs = []
    main_window = driver.current_window_handle

    for i, link in enumerate(job_links[:limit], 1):
        try:
            print(f"➡️ Processing {i}/{len(job_links)}")

            title = link.text.split("\n")[0]
            url = link.get_attribute("href")

            if not url:
                continue

            # open new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])

            full_text, raw = extract_job_details(driver, url)

            # close tab
            driver.close()
            driver.switch_to.window(main_window)

            jobs.append({
                "title": title,
                "company": "Unknown",
                "url": url,
                "full_text": full_text,
                "description": raw[:500]
            })

            print(f"   ✅ OK: {title}")

        except Exception as e:
            print(f"   ⚠️ Skip job {i}: {e}")

            # safety fallback
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)

    return jobs


# ==========================================
# MAIN
# ==========================================
def main():
    url = "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3"

    print("=" * 60)
    print("🚀 JOB SCRAPER v4.0 CLEAN ARCHITECTURE")
    print("=" * 60)

    driver = setup_driver()

    try:
        # ==========================================
        # 1. SCRAPE DATA ONLY
        # ==========================================
        jobs = extract_all_jobs(driver, url)

        if not jobs:
            print("❌ No jobs found")
            return

        print(f"\n📦 Extracted {len(jobs)} jobs")

        # ==========================================
        # 2. SCORING (ONLY HERE)
        # ==========================================
        jobs = score_jobs(jobs)

        print("\n🎯 Scoring completed\n")

        for j in jobs:
            print(f"{j['score']}% → {j['title']}")

        # ==========================================
        # 3. SAVE OUTPUT
        # ==========================================
        filename = f"job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print(f"💾 Saved: {filename}")
        print(f"📊 Total jobs: {len(jobs)}")
        print("=" * 60)

    finally:
        driver.quit()
        print("🧹 Browser closed")


if __name__ == "__main__":
    main()
