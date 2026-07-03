# scrapers/jobvision_scraper.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

from utils.text_processor import (
    normalize,
    extract_section,
    extract_skills_from_requirements,
    clean_requirements,
    extract_salary,
    extract_age,
    extract_gender
)

class JobvisionScraper:
    def __init__(self, driver):
        self.driver = driver
        self.site_name = 'jobvision'

    # =========================
    # استخراج لیست آگهی‌ها
    # =========================
    def extract_job_cards(self):
        cards = []

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.desktop-job-card'))
            )
        except:
            print("  ⚠️ No job cards found on this page")
            return []

        job_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a.desktop-job-card')

        for elem in job_elements:
            try:
                title = elem.find_element(By.CSS_SELECTOR, 'div.job-card-title').text.strip()

                company_links = elem.find_elements(By.CSS_SELECTOR, 'a.text-black.jvt-leading-6')
                company = company_links[0].text.strip() if company_links else 'Unknown'

                url = elem.get_attribute('href')

                location_spans = elem.find_elements(By.CSS_SELECTOR, 'span.jvt-pointer-events-none')
                location = location_spans[0].text.strip() if location_spans else ''

                salary = ''
                try:
                    salary = elem.find_element(
                        By.XPATH, './/span[contains(text(), "میلیون")]'
                    ).text.strip()
                except:
                    pass

                is_urgent = False
                try:
                    elem.find_element(By.CSS_SELECTOR, 'div.urgent-tag')
                    is_urgent = True
                except:
                    pass

                cards.append({
                    'title': title,
                    'company': company,
                    'url': url,
                    'location': location,
                    'salary': salary,
                    'is_urgent': is_urgent,
                    'site': self.site_name,
                    'sections': {
                        'full_text': f"{title} {company} {location} {salary}",
                        'title': title,
                        'company': company,
                        'description': '',
                        'requirements': ''
                    }
                })

            except Exception as e:
                print(f"  ⚠️ Error extracting card: {e}")
                continue

        return cards

    # =========================
    # ساخت URL صفحه (کمکی)
    # =========================
    def _build_page_url(self, page_num):
        """
        ساخت امن URL برای صفحه Retry
        """
        try:
            current_url = self.driver.current_url

            if "page=" in current_url:
                return re.sub(r"page=\d+", f"page={page_num}", current_url)

            if "?" in current_url:
                return f"{current_url}&page={page_num}"

            return f"{current_url}?page={page_num}"

        except:
            return current_url + f"?page={page_num}"

    # =========================
    # استخراج همه صفحات (نسخه مقاوم با تشخیص صفحات خالی)
    # =========================
    def extract_all_pages(self, max_pages=None):
        all_cards = []
        page_num = 1

        consecutive_failures = 0
        max_consecutive_failures = 5
        MAX_PAGE_RETRY = 3
        EMPTY_PAGE_LIMIT = 3

        failed_pages = {}
        seen_urls = set()
        empty_page_count = 0

        print("  🔄 Starting resilient multi-page scraping...")

        while True:
            print(f"\n  📄 Scraping page {page_num}...")

            page_success = False

            for attempt in range(1, MAX_PAGE_RETRY + 1):
                try:
                    cards = self.extract_job_cards()

                    if cards and len(cards) > 0:
                        empty_page_count = 0
                        new_cards = 0

                        for card in cards:
                            url = card.get("url")

                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                all_cards.append(card)
                                new_cards += 1

                        print(f"     ✅ Found {len(cards)} jobs ({new_cards} new)")

                        page_success = True
                        consecutive_failures = 0
                        break

                    else:
                        print(f"     ⚠️ Empty page detected (attempt {attempt})")
                        empty_page_count += 1
                        time.sleep(2)

                        if empty_page_count >= EMPTY_PAGE_LIMIT:
                            print(f"     🛑 {empty_page_count} consecutive empty pages → STOP pagination")
                            print(f"  ✅ Total collected jobs: {len(all_cards)}")
                            return all_cards

                except Exception as e:
                    print(f"     ❌ Attempt {attempt} failed: {str(e)[:80]}")
                    time.sleep(3)

            if not page_success:
                consecutive_failures += 1

                failed_pages[page_num] = {
                    "retry": failed_pages.get(page_num, {}).get("retry", 0) + 1,
                    "reason": "no_cards_or_error"
                }

                print(f"     📌 Page {page_num} added to retry queue")

                if consecutive_failures >= max_consecutive_failures:
                    print("     ❌ Too many consecutive failures, stopping scraping")
                    break

            if max_pages and page_num >= max_pages:
                print(f"     ⏹️ Reached max pages ({max_pages})")
                break

            try:
                next_url = self.get_next_page_url()

                if not next_url:
                    print("     ⏹️ No next page found")
                    break

                print(f"     ➡️ Going to page {page_num + 1}...")

                self.driver.get(next_url)
                time.sleep(3)

                page_num += 1

            except Exception as e:
                print(f"     ❌ Navigation error to page {page_num + 1}: {e}")

                failed_pages[page_num + 1] = {
                    "retry": failed_pages.get(page_num + 1, {}).get("retry", 0) + 1,
                    "reason": "navigation_error"
                }

                time.sleep(5)
                page_num += 1

        if failed_pages:
            print(f"\n  🔄 Retrying {len(failed_pages)} failed pages...")

            for page, info in failed_pages.items():
                if info["retry"] >= MAX_PAGE_RETRY:
                    print(f"     ⛔ Skipping page {page} (max retries reached)")
                    continue

                try:
                    retry_url = self._build_page_url(page)

                    print(f"  📄 Retrying page {page}...")

                    self.driver.get(retry_url)
                    time.sleep(4)

                    cards = self.extract_job_cards()

                    if cards:
                        new_cards = 0

                        for card in cards:
                            url = card.get("url")

                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                all_cards.append(card)
                                new_cards += 1

                        print(f"     ✅ Retry success: {len(cards)} jobs ({new_cards} new)")
                    else:
                        print(f"     ⚠️ No jobs found on retry page {page}")

                except Exception as e:
                    print(f"     ❌ Retry failed for page {page}: {e}")

        print(f"\n  ✅ Total collected jobs: {len(all_cards)}")
        return all_cards

    # =========================
    # استخراج جزئیات آگهی (نسخه نهایی با ETL داخلی)
    # =========================
    def extract_job_detail(self, url, retry=5, base_timeout=20):
        """
        استخراج جزئیات با Timeout افزایشی (Exponential Backoff)
        + استخراج فیلدها از full_text با استفاده از text_processor
        """
        detail = {
            'title': '',
            'company': '',
            'description': '',
            'requirements': '',
            'skills': [],
            'age_range': '',
            'gender': '',
            'salary': '',
            'full_text': '',
            'site': self.site_name,
            'url': url,
            'error': None
        }

        for attempt in range(retry + 1):
            try:
                timeout = base_timeout + (attempt * 25)
                self.driver.set_page_load_timeout(timeout)
                print(f"     ⏳ Loading with {timeout}s timeout (attempt {attempt+1})")
                
                try:
                    self.driver.get(url)
                except Exception as e:
                    if "timeout" in str(e).lower() and attempt < retry:
                        print(f"     ⏳ Timeout with {timeout}s, retrying with more time...")
                        time.sleep(5)
                        continue
                    else:
                        print(f"     ⚠️ Page load failed: {e}")
                        detail['error'] = str(e)
                        return detail

                time.sleep(2)

                # =========================
                # 📄 full_text
                # =========================
                body = self.driver.find_element(By.TAG_NAME, 'body')
                full_text = body.text
                detail['full_text'] = full_text

                # =========================
                # 🔥 ETL: استخراج از full_text
                # =========================
                text = normalize(full_text)

                # ۱. شرح شغل (description)
                description_text = extract_section(text, 
                    ["شرح شغل و وظایف", "Job Description"], 
                    ["شرایط احراز شغل", "Job Requirements"]
                )
                detail['description'] = description_text

                # ۲. شرایط احراز (requirements)
                requirements_text = extract_section(text, 
                    ["شرایط احراز شغل", "Job Requirements"], 
                    ["ثبت مشکل و تخلف آگهی", "موقعیت های شغلی مشابه", "ارسال رزومه"]
                )
                requirements_text = clean_requirements(requirements_text)
                detail['requirements'] = requirements_text

                # ۳. مهارت‌ها (skills) - استخراج از بخش نرم افزارها
                skills_text = extract_skills_from_requirements(text)
                detail['skills'] = skills_text

                # ۴. حقوق (salary)
                salary = extract_salary(text)
                detail['salary'] = salary

                # ۵. محدوده سنی (age_range) - از requirements استخراج میشه
                age_range = extract_age(requirements_text)
                detail['age_range'] = age_range

                # ۶. جنسیت (gender) - از requirements استخراج میشه
                gender = extract_gender(requirements_text)
                detail['gender'] = gender

                return detail

            except Exception as e:
                if "timeout" in str(e).lower() and attempt < retry:
                    print(f"     ⏳ Timeout, retrying with more time...")
                    time.sleep(3)
                    continue
                else:
                    print(f"     ⚠️ Error extracting detail: {e}")
                    detail['error'] = str(e)
                    return detail

        return detail

    # =========================
    # صفحه بعدی
    # =========================
    def get_next_page_url(self):
        try:
            # روش 1: لینک "بعدی"
            next_links = self.driver.find_elements(By.CSS_SELECTOR, 'li.page-item a')

            for link in next_links:
                if 'بعدی' in link.text:
                    href = link.get_attribute('href')
                    if href and href != '#':
                        return href

            # روش 2: ساخت URL
            current_url = self.driver.current_url

            if 'page=' in current_url:
                match = re.search(r'page=(\d+)', current_url)

                if match:
                    next_page = int(match.group(1)) + 1
                    return re.sub(r'page=\d+', f'page={next_page}', current_url)
                else:
                    return current_url + '&page=2'

            else:
                if '?' in current_url:
                    return current_url + '&page=2'
                else:
                    return current_url + '?page=2'

        except Exception as e:
            print(f"  ⚠️ Error getting next page URL: {e}")
            return None