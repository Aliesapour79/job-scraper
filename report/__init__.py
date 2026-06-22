# report/__init__.py
# ==========================================
# ماژول گزارش‌دهی - دسترسی آسان به تولید گزارش
# ==========================================

from .html_generator import generate_html_report

__all__ = [
    'generate_html_report',
]