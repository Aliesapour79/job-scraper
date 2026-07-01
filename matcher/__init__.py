# matcher/__init__.py
# ==========================================
# ماژول تطبیق شغلی - دسترسی آسان به همه توابع
# ==========================================

from .skill_groups import SKILL_GROUPS, JOB_TITLE_WEIGHT_MAP
from .score_calculator import (
    generic_penalty,
    calculate_general_score,
    domain_boost,
    min_max_normalize,
    detect_job_category,
    calculate_final_score_v73,
    semantic_match_score,
    calculate_outlier_score,
    calculate_keyword_score,
    calculate_match_score_advanced
)

# ==========================================
# توابع اسکرپر (از scrapers وارد می‌شوند)
# ==========================================
from scrapers import extract_all_jobs

__all__ = [
    'SKILL_GROUPS',
    'JOB_TITLE_WEIGHT_MAP',
    'generic_penalty',
    'calculate_general_score',
    'domain_boost',
    'min_max_normalize',
    'detect_job_category',
    'calculate_final_score_v73',
    'semantic_match_score',
    'calculate_outlier_score',
    'calculate_keyword_score',
    'calculate_match_score_advanced',
    'extract_all_jobs',  # اضافه شد
]