# utils/driver_manager.py
import time
from .driver import setup_driver

PAGE_TIMEOUT = 90
MAX_DRIVER_RETRIES = 3


def safe_driver_get(driver, url, max_retries=MAX_DRIVER_RETRIES):
    """بارگذاری URL با Retry (بدون ریستارت اضطراری)"""
    for attempt in range(max_retries):
        try:
            driver.set_page_load_timeout(PAGE_TIMEOUT)
            driver.get(url)
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"     ⚠️ Attempt {attempt+1}/{max_retries} failed: {str(e)[:60]}")
            
            if any(k in error_msg for k in ["crash", "connection", "timeout"]):
                print(f"     ⏳ Retrying...")
                time.sleep(3)
                continue
            else:
                print(f"     ❌ Non-retryable error")
                return False
    
    print(f"     ❌ Failed after {max_retries} attempts")
    return False


def restart_driver(driver):
    """Restart Chrome driver to free memory"""
    print("🔄 Restarting Chrome driver...")
    try:
        driver.quit()
    except:
        pass

    time.sleep(2)
    return setup_driver()