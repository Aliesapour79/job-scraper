# matcher/__init__.py
# ==========================================
# ماژول تطبیق شغلی - دسترسی آسان به همه توابع
# ==========================================

# =========================
# 🔥 داده‌ها
# =========================
from .skill_groups import SKILL_GROUPS

# =========================
# 🆕 v8: توابع جدید
# =========================
from .weights import get_weights, get_job_group, WEIGHTS_CONFIG
from .eligibility import check_eligibility
from .score_calculator import (
    calculate_hard_score,
    calculate_functional_score,
    calculate_soft_score,
    calculate_semantic_score,
    calculate_final_score_v8,
    calculate_final_simple,
    calculate_outlier_score 
)
from .explainability import generate_explanation

# =========================
# 📋 لیست exportها
# =========================
__all__ = [
    # داده‌ها
    'SKILL_GROUPS',
    
    # v8 جدید
    'get_weights',
    'get_job_group',
    'WEIGHTS_CONFIG',
    'check_eligibility',
    'calculate_hard_score',
    'calculate_functional_score',
    'calculate_soft_score',
    'calculate_semantic_score',
    'calculate_final_score_v8',
    'calculate_final_simple',
    'generate_explanation',
    'calculate_outlier_score',
]