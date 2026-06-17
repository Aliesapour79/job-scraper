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
# BALANCED SKILL SYSTEM v3.2
# ==========================================

CORE_SKILLS = [
    "iot", "embedded", "esp32", "pcb",
    "الکترونیک", "میکروکنترلر",
    "machine learning", "ai", "opencv",
    "arduino", "سخت افزار", "سخت‌افزار"
]

SECONDARY_SKILLS = [
    "it", "network", "linux", "excel",
    "sql", "office", "admin", "data"
]

NOISE_SKILLS = [
    "آبدارچی", "نظافت", "خدماتی",
    "cleaner", "janitor"
]


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
# EXTRACT JOB PAGE
# ==========================================
def extract_job_details(driver, url):
    try:
        driver.get(url)
        time.sleep(4)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        try:
            title = driver.find_element(By.CSS_SELECTOR, "h1").text
        except:
            title = "Unknown"

        try:
            company = driver.find_element(By.CSS_SELECTOR, ".company, .employer").text
        except:
            company = "Unknown"

        combined_text = f"{title}\n{company}\n{body_text}"

        return combined_text, body_text

    except Exception as e:
        print(f"Error extracting: {e}")
        return "", ""


# ==========================================
# EXTRACT JOB LIST
# ==========================================
def extract_all_jobs(driver, url):
    print("Loading page...")
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list")))

    job_links = driver.find_elements(By.CSS_SELECTOR, ".search-list .item a.item-content")
    print(f"Found {len(job_links)} jobs")

    jobs = []
    main_window = driver.current_window_handle

    for i, link in enumerate(job_links[:80], 1):
        try:
            print(f"Job {i}/{len(job_links)}")

            title = link.text.split("\n")[0]
            url = link.get_attribute("href")

            if not url:
                continue

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])

            text, raw = extract_job_details(driver, url)

            driver.close()
            driver.switch_to.window(main_window)

            jobs.append({
                "title": title,
                "company": "Unknown",
                "url": url,
                "full_text": text,
                "description": raw[:400]
            })

            print(f"OK: {title}")

        except Exception as e:
            print(f"Skip job {i}: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)

    return jobs


# ==========================================
# MAIN
# ==========================================
def main():
    url = "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3"

    print("=" * 50)
    print("JOB SCRAPER v3.2")
    print("=" * 50)

    driver = setup_driver()

    try:
        jobs = extract_all_jobs(driver, url)

        if not jobs:
            print("No jobs found")
            return

        print(f"Extracted {len(jobs)} jobs")

        # 🔥 IMPORTANT: scoring system (balanced version)
        jobs = score_jobs(jobs, CORE_SKILLS, SECONDARY_SKILLS, NOISE_SKILLS)

        print("\nScoring results:")
        for job in jobs:
            print(f"{job['score']}% -> {job['title']}")

        filename = f"job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print("\nSaved:", filename)

    finally:
        driver.quit()
        print("Browser closed")


if __name__ == "__main__":
    main()
