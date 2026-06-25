# utils/driver.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import platform
import os

def setup_driver():
    """Setup Chrome driver - automatically detects OS"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # ==========================================
    # 🖥️ تشخیص سیستم عامل
    # ==========================================
    system = platform.system()
    print(f"🖥️ Operating System: {system}")

    try:
        service = None

        if system == "Windows":
            # ====== ویندوز: استفاده از کروم‌درایور محلی ======
            chrome_driver_path = r"C:\chromedriver\chromedriver.exe"

            if os.path.exists(chrome_driver_path):
                print(f"✅ Using local ChromeDriver: {chrome_driver_path}")
                service = Service(chrome_driver_path)
            else:
                print("⚠️ Local ChromeDriver not found, downloading...")
                service = Service(ChromeDriverManager().install())

        else:
            # ====== لینوکس / مک: دانلود خودکار ======
            print("🔄 Downloading ChromeDriver via webdriver-manager...")
            service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome driver started successfully!")
        return driver

    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        raise