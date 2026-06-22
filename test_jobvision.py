# test_jobvision.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from jobvision_scraper import JobvisionScraper
import time

def test_jobvision():
    # تنظیم مرورگر
    options = Options()
    options.add_argument("--headless")  # بدون نمایش مرورگر
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        # آدرس صفحه جاب‌ویژن
        url = "https://jobvision.ir/jobs/category/developer-in-all-cities-of-tehran"
        
        print("🚀 Loading page...")
        driver.get(url)
        time.sleep(3)
        
        # ایجاد اسکرپر
        scraper = JobvisionScraper(driver)
        
        # استخراج کارت‌ها
        print("📋 Extracting job cards...")
        cards = scraper.extract_job_cards()
        
        print(f"✅ Found {len(cards)} jobs!\n")
        
        # نمایش چند آگهی اول
        for i, card in enumerate(cards[:5], 1):
            print(f"{i}. {card['title']}")
            print(f"   🏢 {card['company']}")
            print(f"   📍 {card['location']}")
            print(f"   💰 {card['salary']}")
            print(f"   🔗 {card['url']}")
            if card['is_urgent']:
                print("   ⚡ فوری!")
            print()
        
        # تست جزئیات یک آگهی
        if cards:
            print("🔍 Testing detail extraction...")
            detail = scraper.extract_job_detail(cards[0]['url'])
            print(f"   📝 Description: {detail['description'][:100]}...")
            print(f"   🛠️ Skills: {detail['skills']}")
            print(f"   📊 Age: {detail['age_range']}")
            print(f"   🚻 Gender: {detail['gender']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("\n✅ Done!")

if __name__ == "__main__":
    test_jobvision()