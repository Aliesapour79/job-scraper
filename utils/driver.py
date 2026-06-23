# utils/driver.py
# ==========================================
# مدیریت مرورگر برای اسکرپینگ
# ==========================================

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import platform

def setup_driver():
    """Setup Chrome driver with automatic driver management"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome driver started successfully!")
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        print("   Trying fallback method...")
        
        try:
            if platform.system() == 'Windows':
                chrome_driver_path = r"C:\chromedriver\chromedriver.exe"
            else:
                chrome_driver_path = "/usr/local/bin/chromedriver"
            
            service = Service(chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome driver started with fallback!")
            return driver
        except:
            print("❌ Could not start Chrome driver. Please check installation.")
            raise