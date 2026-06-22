# config/__init__.py
# ==========================================
# ماژول تنظیمات - دسترسی آسان به همه تنظیمات
# ==========================================

from .settings import (
    SCORE_WEIGHTS,
    EMBEDDING_MODEL,
    GENERIC_KEYWORDS,
    TECH_KEYWORDS_MAP,
    ADMIN_KEYWORDS_WEIGHTED,
    INTENT_WEIGHTS,
    HEADLESS,
    SEARCH_URLS,
    FILTERS,
    OUTPUT_DIR
)

from .resume import RESUME_TEXT

__all__ = [
    'SCORE_WEIGHTS',
    'EMBEDDING_MODEL',
    'GENERIC_KEYWORDS',
    'TECH_KEYWORDS_MAP',
    'ADMIN_KEYWORDS_WEIGHTED',
    'INTENT_WEIGHTS',
    'HEADLESS',
    'SEARCH_URLS',
    'FILTERS',
    'OUTPUT_DIR',
    'RESUME_TEXT'
]