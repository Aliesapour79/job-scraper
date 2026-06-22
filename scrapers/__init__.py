# scrapers/__init__.py
# ==========================================
# ماژول اسکرپرها - دسترسی آسان به همه اسکرپرها
# ==========================================

from .jobvision_scraper import JobvisionScraper
from .e_estekhdam_scraper import extract_all_jobs, extract_job_details

__all__ = [
    'JobvisionScraper',
    'extract_all_jobs',
    'extract_job_details',
]