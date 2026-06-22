# jobvision_scraper.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class JobvisionScraper:
    def __init__(self, driver):
        self.driver = driver
        self.site_name = 'jobvision'
        
    def extract_job_cards(self):
        """استخراج لیست آگهی‌ها از صفحه جاب‌ویژن"""
        cards = []
        
        # صبر برای بارگذاری کارت‌ها
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.desktop-job-card'))
        )
        
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
        """دریافت URL صفحه بعدی"""
        try:
            # پیدا کردن لینک صفحه بعدی
            next_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'li.page-item a'
            )
            for link in next_links:
                if 'بعدی' in link.text or 'Next' in link.text:
                    href = link.get_attribute('href')
                    if href and href != '#':
                        return href
        except:
            pass
        return None