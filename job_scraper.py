from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import json
import time
from datetime import datetime

from nlp.scorer import score_jobs


# ==========================================
# DRIVER SETUP (stable version)
# ==========================================
def setup_driver():
    options = Options()

    # headless stable mode
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(service=service, options=options)


# ==========================================
# WAIT SAFE CLICK
# ==========================================
def safe_get(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception as e:
        print(f"⚠️ Load issue: {e}")


# ==========================================
# EXTRACT JOB DETAILS (NO NEW TABS)
# ==========================================
def extract_job_details(driver):
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text

        def safe_css(selector):
            try:
                return driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            except:
                return ""

        title = safe_css(".entry-title h1, h1.entry-title span")
        description = safe_css(".job-content p:first-child")
        location = safe_css(".job-content .text-center h5")

        return {
            "title": title or "Unknown",
            "description": description,
            "location": location,
            "full_text": body_text
        }

    except Exception as e:
        print(f"❌ extract error: {e}")
        return {
            "title": "Unknown",
            "description": "",
            "location": "",
            "full_text": ""
        }


# ==========================================
# SCRAPE JOB LIST (FIXED - NO TABS)
# ==========================================
def extract_all_jobs(driver, url, limit=50):
    print("🌐 Loading page...")

    safe_get(driver, url)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list")))

    job_cards = driver.find_elements(By.CSS_SELECTOR, ".search-list .item a.item-content")

    print(f"✅ Found {len(job_cards)} jobs")

    jobs = []

    for i, card in enumerate(job_cards[:limit], 1):
        try:
            title_line = card.text.split("\n")

            title = title_line[0] if len(title_line) > 0 else "Unknown"
            company = title_line[1] if len(title_line) > 1 else "Unknown"
            url = card.get_attribute("href")

            if not url:
                continue

            print(f"➡️ {i}/{limit}: {title}")

            safe_get(driver, url)

            data = extract_job_details(driver)

            jobs.append({
                "title": title,
                "company": company,
                "url": url,
                "full_text": data["full_text"],
                "description": data["description"],
                "location": data["location"]
            })

        except Exception as e:
            print(f"❌ job error {i}: {e}")
            continue

    return jobs


# ==========================================
# MAIN
# ==========================================
def main():
    url = "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3"

    print("=" * 50)
    print("🔍 JOB SCRAPER v2 (FIXED)")
    print("=" * 50)

    driver = setup_driver()

    try:
        jobs = extract_all_jobs(driver, url)

        if not jobs:
            print("❌ No jobs found")
            return

        print(f"\n🧠 Scoring {len(jobs)} jobs...")

        jobs = score_jobs(jobs)

        results = []

        for job in jobs:
            results.append({
                "title": job["title"],
                "company": job["company"],
                "url": job["url"],
                "score": job["score"],
                "description": job.get("description", ""),
                "full_text": job["full_text"][:800]
            })

            print(f"⭐ {job['score']}% - {job['title']}")

        results.sort(key=lambda x: x["score"], reverse=True)

        filename = f"job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 50)
        print(f"💾 Saved: {filename}")
        print(f"📊 Total: {len(results)}")
        print("=" * 50)

    finally:
        driver.quit()
        print("🧹 Browser closed")


if __name__ == "__main__":
    main()
