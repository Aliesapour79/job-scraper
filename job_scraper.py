from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import json
from datetime import datetime

from webdriver_manager.chrome import ChromeDriverManager
from nlp.scorer import score_jobs


# ==========================================
# SETUP DRIVER
# ==========================================
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


# ==========================================
# EXTRACT JOB DETAILS
# ==========================================
def extract_job_details(driver, url):
    try:
        driver.get(url)
        time.sleep(4)

        full_text = driver.find_element(By.TAG_NAME, "body").text

        title = "Unknown"
        try:
            title = driver.find_element(
                By.CSS_SELECTOR,
                ".entry-title h1, h1.entry-title span"
            ).text.strip()
        except:
            pass

        return title, full_text

    except Exception as e:
        print(f"Error: {e}")
        return "Unknown", ""


# ==========================================
# SCRAPE ALL JOBS
# ==========================================
def extract_all_jobs(driver, url):
    print("Loading page...")
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list")))

    job_links = driver.find_elements(By.CSS_SELECTOR, ".search-list .item a.item-content")

    print(f"Found {len(job_links)} jobs")

    jobs = []
    main = driver.current_window_handle

    for i, link in enumerate(job_links[:80], 1):
        try:
            href = link.get_attribute("href")
            if not href:
                continue

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])

            title, full_text = extract_job_details(driver, href)

            driver.close()
            driver.switch_to.window(main)

            jobs.append({
                "title": title,
                "url": href,
                "full_text": full_text
            })

            print(f"{i}. extracted")

        except Exception as e:
            print(f"Error on job {i}: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main)

    return jobs


# ==========================================
# MAIN
# ==========================================
def main():
    url = "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3"

    print("START")

    driver = setup_driver()

    try:
        jobs = extract_all_jobs(driver, url)

        print(f"Scraped: {len(jobs)} jobs")

        # 🔥 AI SCORING (ONLY ONE SYSTEM)
        jobs = score_jobs(jobs)

        results = []
        for job in jobs:
            results.append({
                "title": job["title"],
                "url": job["url"],
                "score": job["score"],
                "full_text": job["full_text"][:1000]
            })

            print(f"[{job['score']}] {job['title']}")

        filename = f"job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print("Saved:", filename)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
