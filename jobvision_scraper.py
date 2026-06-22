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
        
    def extract_job_cards(self):
        """استخراج لیست آگهی‌ها از صفحه جاب‌ویژن"""
        cards = []
        
        # صبر برای بارگذاری کارت‌ها
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.desktop-job-card'))
            )
        except:
            print("  ⚠️ No job cards found on this page")
            return cards
        
        job_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a.desktop-job-card')
        
        for elem in job_elements:
            try:
                # عنوان شغلی
                title_elem = elem.find_element(By.CSS_SELECTOR, 'div.job-card-title')
                title = title_elem.text.strip()
                
                # شرکت (دومین لینک)
                company_links = elem.find_elements(By.CSS_SELECTOR, 'a.text-black.jvt-leading-6')
                company = company_links[0].text.strip() if company_links else 'Unknown'
                
                # لینک آگهی
                url = elem.get_attribute('href')
                
                # شهر
                location_spans = elem.find_elements(By.CSS_SELECTOR, 'span.jvt-pointer-events-none')
                location = location_spans[0].text.strip() if location_spans else ''
                
                # حقوق
                salary = ''
                try:
                    salary_elem = elem.find_element(By.XPATH, './/span[contains(text(), "میلیون")]')
                    salary = salary_elem.text.strip()
                except:
                    pass
                
                # فوری
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
                        'full_text': title + ' ' + company + ' ' + location + ' ' + salary,
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
    
    def extract_all_pages(self, max_pages=None):
        """
        استخراج آگهی‌ها از تمام صفحات
        
        Args:
            max_pages: حداکثر تعداد صفحات (اگر None باشه، تا آخرین صفحه میرود)
        
        Returns:
            list: لیست تمام آگهی‌ها
        """
        all_cards = []
        page_num = 1
        
        print(f"  🔄 Starting multi-page scraping...")
        
        while True:
            print(f"  📄 Scraping page {page_num}...")
            
            # استخراج کارت‌های صفحه فعلی
            cards = self.extract_job_cards()
            
            if not cards:
                print(f"     ⚠️ No jobs found on page {page_num}")
                break
                
            all_cards.extend(cards)
            print(f"     ✅ Found {len(cards)} jobs on page {page_num}")
            
            # اگر به حداکثر صفحات رسیدیم، بایست
            if max_pages and page_num >= max_pages:
                print(f"     ⏹️ Reached max pages ({max_pages})")
                break
            
            # پیدا کردن لینک صفحه بعدی
            next_url = self.get_next_page_url()
            if not next_url:
                print(f"     ⏹️ No more pages")
                break
            
            # رفتن به صفحه بعدی
            print(f"     ➡️ Going to page {page_num + 1}...")
            self.driver.get(next_url)
            time.sleep(2)
            page_num += 1
        
        print(f"  ✅ Total: {len(all_cards)} jobs from {page_num} pages")
        return all_cards
    
    def extract_job_detail(self, url):
        """استخراج جزئیات یک آگهی از جاب‌ویژن"""
        self.driver.get(url)
        time.sleep(2)
        
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
            'url': url
        }
        
        try:
            # ====== دریافت کل متن ======
            body = self.driver.find_element(By.TAG_NAME, 'body')
            detail['full_text'] = body.text
            
            # ====== شرح شغل ======
            desc_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'div[dir="rtl"]'
            )
            for elem in desc_elements:
                text = elem.text.strip()
                if text and len(text) > 50:  # شرح شغل معمولاً طولانی‌تره
                    detail['description'] = text
                    break
            
            # ====== مهارت‌ها ======
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
            
            # ====== شرایط احراز ======
            requirement_titles = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'div.requirement-title'
            )
            requirement_values = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'div.requirement-value'
            )
            
            for i, title_elem in enumerate(requirement_titles):
                title_text = title_elem.text.strip()
                if i < len(requirement_values):
                    value_text = requirement_values[i].text.strip()
                    if 'سن' in title_text:
                        detail['age_range'] = value_text
                    elif 'جنسیت' in title_text:
                        detail['gender'] = value_text
            
            return detail
            
        except Exception as e:
            print(f"  ⚠️ Error extracting detail: {e}")
            return detail
    
    def get_next_page_url(self):
        """
        دریافت URL صفحه بعدی از جاب‌ویژن
        با پشتیبانی از دو حالت:
        1. لینک "بعدی" در صفحه‌بندی
        2. ساخت دستی URL با افزایش شماره صفحه
        """
        try:
            # ====== روش اول: پیدا کردن لینک "بعدی" ======
            next_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'li.page-item a'
            )
            for link in next_links:
                if 'بعدی' in link.text:
                    href = link.get_attribute('href')
                    if href and href != '#':
                        return href
            
            # ====== روش دوم: ساخت دستی URL ======
            current_url = self.driver.current_url
            
            # اگر page= در URL وجود داره
            if 'page=' in current_url:
                match = re.search(r'page=(\d+)', current_url)
                if match:
                    current_page = int(match.group(1))
                    next_page = current_page + 1
                    # جایگزینی شماره صفحه
                    next_url = re.sub(r'page=\d+', f'page={next_page}', current_url)
                    return next_url
                else:
                    # اگر page= وجود داشت ولی عدد پیدا نشد
                    return current_url + '&page=2'
            else:
                # اگر page= وجود نداشت
                if '?' in current_url:
                    return current_url + '&page=2'
                else:
                    return current_url + '?page=2'
                    
        except Exception as e:
            print(f"  ⚠️ Error getting next page URL: {e}")
            return None