# scrapers/e_estekhdam_scraper.py
# ==========================================
# اسکرپر مخصوص سایت e-estekhdam (نسخه کلاسی)
# ==========================================

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class EEstekhdamScraper:
    def __init__(self, driver):
        self.driver = driver
        self.site_name = 'e-estekhdam'

    # =========================
    # استخراج جزئیات یک آگهی
    # =========================
    def extract_job_details(self, url):
        """Extract full job details with multiple fallback selectors"""
        try:
            self.driver.get(url)
            time.sleep(5)

            full_text = self.driver.find_element(By.TAG_NAME, "body").text

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
                            elem = self.driver.find_element(By.XPATH, selector)
                        else:
                            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        sections[key] = elem.text.strip()
                        break
                    except:
                        continue
                if key not in sections:
                    sections[key] = ""

            try:
                location = self.driver.find_element(By.CSS_SELECTOR, ".job-content .text-center h5")
                sections["location"] = location.text.strip()
            except:
                sections["location"] = ""

            sections["full_text"] = full_text

            return sections

        except Exception as e:
            print(f"  Error extracting job details: {e}")
            return {}

    # =========================
    # استخراج همه آگهی‌ها
    # =========================
    def extract_all_jobs(self):
        """استخراج تمام آگهی‌ها از سایت e-estekhdam با اسکرول هوشمند"""
        print("Loading page...")
        self.driver.get(self.url)

        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list")))

        # =========================
        # 🔄 اسکرول هوشمند تا انتهای صفحه
        # =========================
        print("🔄 Scrolling to load all jobs...")

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 30
        new_jobs_loaded = True

        while new_jobs_loaded and scroll_attempts < max_scroll_attempts:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                new_jobs_loaded = False
            else:
                scroll_attempts += 1
                if scroll_attempts % 5 == 0:
                    print(f"     📜 Scrolled {scroll_attempts} times...")
                last_height = new_height

        print(f"     ✅ Finished scrolling after {scroll_attempts} attempts")

        # =========================
        # استخراج آگهی‌ها
        # =========================
        job_links = self.driver.find_elements(By.CSS_SELECTOR, ".search-list .item a.item-content")
        print(f"✅ Found {len(job_links)} job links")

        jobs_data = []
        main_window = self.driver.current_window_handle

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

                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])

                sections = self.extract_job_details(href)

                self.driver.close()
                self.driver.switch_to.window(main_window)
                time.sleep(0.5)

                if sections:
                    jobs_data.append({
                        "title": title,
                        "company": company,
                        "url": href,
                        "sections": sections,
                        "site": self.site_name,
                        "index": idx
                    })
                    print(f"  ✅ Extracted: {title[:30]}...")

            except Exception as e:
                print(f"  ❌ Error: {str(e)[:100]}")
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(main_window)
                continue

        return jobs_data