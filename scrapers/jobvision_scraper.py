# jobvision_scraper.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re


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
    # استخراج همه صفحات (نسخه مقاوم با Retry صفحات ناموفق)
    # =========================
    def extract_all_pages(self, max_pages=None):
        all_cards = []
        page_num = 1
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        # =========================
        # 📌 لیست صفحات ناموفق برای Retry
        # =========================
        failed_pages = []  # صفحاتی که خطا خوردند

        print(f"  🔄 Starting resilient multi-page scraping...")

        while True:
            print(f"  📄 Scraping page {page_num}...")

            try:
                cards = None

                # retry برای استخراج کارت‌ها
                for attempt in range(3):
                    try:
                        cards = self.extract_job_cards()
                        break
                    except Exception as e:
                        print(f"     ⚠️ Attempt {attempt + 1} failed: {e}")
                        time.sleep(5)

                # اگر هیچ نتیجه‌ای نگرفتیم
                if not cards:
                    consecutive_failures += 1

                    if consecutive_failures >= max_consecutive_failures:
                        print(f"     ❌ Too many failures, stopping...")
                        break

                    print(f"     ⚠️ No cards found, trying next page...")
                    page_num += 1
                    continue

                all_cards.extend(cards)
                print(f"     ✅ Found {len(cards)} jobs on page {page_num}")

                consecutive_failures = 0

                if max_pages and page_num >= max_pages:
                    print(f"     ⏹️ Reached max pages ({max_pages})")
                    break

                next_url = self.get_next_page_url()

                if not next_url:
                    print(f"     ⏹️ No more pages")
                    break

                print(f"     ➡️ Going to page {page_num + 1}...")
                self.driver.get(next_url)
                time.sleep(3)

                page_num += 1

            except Exception as e:
                print(f"     ❌ Error on page {page_num}: {e}")
                
                # =========================
                # 📌 ذخیره صفحه خطا برای Retry
                # =========================
                failed_pages.append(page_num)
                print(f"     📌 Page {page_num} added to retry list")

                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print(f"     ❌ Too many failures, stopping...")
                    break

                time.sleep(5)
                page_num += 1

        # =========================
        # 📌 Retry صفحات ناموفق
        # =========================
        if failed_pages:
            print(f"\n  🔄 Retrying {len(failed_pages)} failed pages: {failed_pages}")
            
            for page_num in failed_pages:
                print(f"  📄 Retrying page {page_num}...")
                
                # ساخت URL صفحه
                current_url = self.driver.current_url
                if 'page=' in current_url:
                    page_url = re.sub(r'page=\d+', f'page={page_num}', current_url)
                else:
                    page_url = current_url + f'?page={page_num}'
                
                try:
                    self.driver.get(page_url)
                    time.sleep(5)
                    
                    # تلاش برای استخراج کارت‌ها با Retry
                    cards = None
                    for attempt in range(3):
                        try:
                            cards = self.extract_job_cards()
                            break
                        except Exception as e:
                            print(f"     ⚠️ Retry attempt {attempt + 1} failed: {e}")
                            time.sleep(3)
                    
                    if cards:
                        print(f"     ✅ Found {len(cards)} jobs on page {page_num} (retry successful)")
                        all_cards.extend(cards)
                    else:
                        print(f"     ⚠️ No jobs found on page {page_num} (retry)")
                        
                except Exception as e:
                    print(f"     ❌ Retry failed for page {page_num}: {e}")

        print(f"  ✅ Total: {len(all_cards)} jobs from {page_num} pages")
        return all_cards

    # =========================
    # استخراج جزئیات آگهی (نسخه مقاوم با Retry)
    # =========================
    def extract_job_detail(self, url, retry=3):
        """
        استخراج جزئیات یک آگهی با Retry برای Timeout
        
        Args:
            url: لینک آگهی
            retry: تعداد تلاش مجدد در صورت Timeout (پیش‌فرض ۲)
        """
        detail = {
            'title': '',
            'company': '',
            'description': '',
            'requirements': '',
            'skills': [],
            'age_range': '',
            'gender': '',
            'full_text': '',
            'site': self.site_name,
            'url': url,
            'error': None
        }

        for attempt in range(retry + 1):
            try:
                self.driver.set_page_load_timeout(30)

                try:
                    self.driver.get(url)
                except Exception as e:
                    # اگر Timeout بود و تلاش باقی مانده، دوباره تلاش کن
                    if "timeout" in str(e).lower() and attempt < retry:
                        print(f"     ⏳ Retry {attempt+1}/{retry} for {url[:50]}...")
                        time.sleep(3)
                        continue
                    else:
                        print(f"     ⚠️ Page load failed: {e}")
                        detail['error'] = str(e)
                        return detail

                time.sleep(1.5)

                # کل متن
                body = self.driver.find_element(By.TAG_NAME, 'body')
                detail['full_text'] = body.text

                # شرح شغل
                desc_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[dir="rtl"]')
                for elem in desc_elements:
                    text = elem.text.strip()
                    if text and len(text) > 50:
                        detail['description'] = text
                        break

                # مهارت‌ها
                skill_tags = self.driver.find_elements(By.CSS_SELECTOR, 'app-tag')
                skills_text = []

                for tag in skill_tags:
                    try:
                        title = tag.find_element(By.CSS_SELECTOR, '.tag-title').text.strip()
                        value = tag.find_element(By.CSS_SELECTOR, '.tag-value').text.strip()

                        detail['skills'].append({
                            'name': title,
                            'level': value
                        })

                        skills_text.append(f"{title} ({value})")

                    except:
                        pass

                detail['requirements'] = ' | '.join(skills_text)

                # شرایط احراز
                titles = self.driver.find_elements(By.CSS_SELECTOR, 'div.requirement-title')
                values = self.driver.find_elements(By.CSS_SELECTOR, 'div.requirement-value')

                for i, title_elem in enumerate(titles):
                    if i < len(values):
                        title_text = title_elem.text.strip()
                        value_text = values[i].text.strip()

                        if 'سن' in title_text:
                            detail['age_range'] = value_text
                        elif 'جنسیت' in title_text:
                            detail['gender'] = value_text

                # اگر به اینجا رسیدیم، موفق بوده
                return detail

            except Exception as e:
                # اگر خطای Timeout بود و تلاش باقی مانده، ادامه بده
                if "timeout" in str(e).lower() and attempt < retry:
                    print(f"     ⏳ Retry {attempt+1}/{retry} for {url[:50]}...")
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