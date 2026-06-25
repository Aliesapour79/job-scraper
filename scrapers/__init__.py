# scrapers/__init__.py

from .jobvision_scraper import JobvisionScraper
from .e_estekhdam_scraper import EEstekhdamScraper

# =========================
# توابع قدیمی e-estekhdam (برای سازگاری)
# =========================
# اگر از extract_all_jobs در جای دیگری استفاده می‌شود
try:
    from .e_estekhdam_scraper import extract_all_jobs, extract_job_details
except ImportError:
    # اگر فایل قدیمی وجود ندارد، تابع ساختگی
    def extract_all_jobs(*args, **kwargs):
        print("⚠️ extract_all_jobs is deprecated. Use EEstekhdamScraper class instead.")
        return []
    def extract_job_details(*args, **kwargs):
        return {}

__all__ = [
    'JobvisionScraper',
    'EEstekhdamScraper',
    'extract_all_jobs',
    'extract_job_details',
]