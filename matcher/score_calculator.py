
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import datetime
import platform
import re
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
from webdriver_manager.chrome import ChromeDriverManager
from utils import setup_driver
# ==========================================
# ایمپورت‌های جدید از ساختار ماژولار
# ==========================================
from config import RESUME_TEXT
from config.settings import GENERIC_KEYWORDS, TECH_KEYWORDS_MAP, ADMIN_KEYWORDS_WEIGHTED
from .skill_groups import SKILL_GROUPS, JOB_TITLE_WEIGHT_MAP

def generic_penalty(job_text):
    """
    محاسبه جریمه برای آگهی‌های عمومی
    هر کلمه عمومی ۵٪ جریمه، حداکثر ۲۰٪
    """
    job_text_lower = job_text.lower()
    count = sum(1 for w in GENERIC_KEYWORDS if w.lower() in job_text_lower)
    penalty = min(0.20, count * 0.05)
    return penalty

def calculate_general_score(job_text, job_title=""):
    """
    محاسبه امتیاز عمومی با وزن‌دهی به کلمات
    Context-aware: اگر عنوان شامل کلمات اداری باشه، ضریب میخوره
    """
    from config import ADMIN_KEYWORDS_WEIGHTED
    
    job_text_lower = job_text.lower()
    total_score = 0
    
    for keyword, weight in ADMIN_KEYWORDS_WEIGHTED.items():
        keyword_lower = keyword.lower()
        if keyword_lower in job_text_lower:
            total_score += weight
        # partial match برای کلمات ترکیبی
        elif len(keyword_lower) > 3:
            parts = keyword_lower.split()
            if any(part in job_text_lower for part in parts):
                total_score += weight * 0.5
    
    # نرمال‌سازی: حداکثر ۱۰۰
    general_score = min(100, total_score * 5)
    
    # ====== Context-Aware: تقویت General برای آگهی‌های اداری ======
    job_title_lower = job_title.lower()
    if "منشی" in job_title_lower or "اداری" in job_title_lower:
        general_score = min(100, general_score * 1.2)
    
    return int(general_score)

def domain_boost(job_text, resume_text, semantic_matcher=None):
    """
    محاسبه پاداش با استفاده از semantic similarity
    اگر semantic_matcher در دسترس باشه، از embedding استفاده میکنه
    در غیر این صورت از rule-based استفاده میکنه
    """
    from config import TECH_KEYWORDS_MAP
    
    # ====== روش Semantic (با embedding) ======
    if semantic_matcher:
        try:
            job_emb = semantic_matcher.encode_texts([job_text])[0]
            resume_emb = semantic_matcher.encode_texts([resume_text])[0]
            
            from sklearn.metrics.pairwise import cosine_similarity
            sim = cosine_similarity([job_emb], [resume_emb])[0][0]
            
            if sim > 0.5:
                return 15
            elif sim > 0.4:
                return 10
            elif sim > 0.3:
                return 8
            elif sim > 0.25:
                return 5
            else:
                return 0
        except:
            pass
    
    # ====== روش Rule-Based (fallback) ======
    job_text_lower = job_text.lower()
    resume_text_lower = resume_text.lower()
    
    matches = 0
    for category, keywords in TECH_KEYWORDS_MAP.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in job_text_lower and keyword_lower in resume_text_lower:
                matches += 1
                break
            elif len(keyword_lower) > 3:
                parts = keyword_lower.split()
                if any(part in job_text_lower for part in parts) and \
                   any(part in resume_text_lower for part in parts):
                    matches += 0.5
                    break
    
    boost = min(15, int(matches * 4))
    return boost

def min_max_normalize(scores):
    if not scores:
        return scores
    
    min_val = min(scores)
    max_val = max(scores)
    
    if max_val == min_val:
        return [0.5] * len(scores)
    
    return [(x - min_val) / (max_val - min_val) for x in scores]

# ==========================================
# 🔥 v6.3: Dual Track + Hybrid Scoring
# ==========================================

def detect_job_category(job_title, job_text, technical_score, general_score):
    """
    تشخیص دسته‌بندی شغل:
    - technical: مشاغل فنی و تخصصی
    - administrative: مشاغل اداری (Core)
    - hybrid: مشاغل ترکیبی (مثل پشتیبانی فنی)
    """
    job_title_lower = job_title.lower()
    job_text_lower = job_text.lower()
    
    # ====== تشخیص Core Admin Jobs ======
    admin_keywords = ["منشی", "پذیرش", "کارمند اداری", "امور اداری", "دبیرخانه"]
    for kw in admin_keywords:
        if kw in job_title_lower:
            return "administrative"
    
    # ====== تشخیص Hybrid Jobs (پشتیبانی فنی) ======
    hybrid_keywords = ["پشتیبانی فنی", "پشتیبانی", "support", "helpdesk"]
    for kw in hybrid_keywords:
        if kw in job_title_lower or kw in job_text_lower:
            return "hybrid"
    
    # ====== تشخیص Technical Jobs ======
    # اگر technical_score > general_score + 10 → فنی
    if technical_score > general_score + 10:
        return "technical"
    
    # ====== تشخیص Administrative ======
    if general_score > technical_score + 10:
        return "administrative"
    
    # ====== بقیه موارد: Hybrid (تعادل بین دو) ======
    if abs(technical_score - general_score) <= 10:
        return "hybrid"
    
    return "technical"  # پیش‌فرض

def calculate_final_score_v63(idx, job_text, resume_text, embedding_score, tfidf_score, 
                              all_embedding_scores, all_tfidf_scores, semantic_matcher=None, job_title=""):
    """
    محاسبه امتیاز نهایی با سیستم Dual Track + Hybrid
    نسخه v6.3:
    1. Technical Track: برای مشاغل فنی
    2. Admin Track: برای مشاغل اداری با حداقل ۳۰% نمایش
    3. Hybrid: برای مشاغل ترکیبی (پشتیبانی فنی)
    """
    from config import SCORE_WEIGHTS, INTENT_WEIGHTS
    
    # ====== Scale-Aware Normalization ======
    norm_embedding = embedding_score / 100.0
    norm_tfidf = min(tfidf_score / 20.0, 1.0)
    
    # ====== Technical Score ======
    technical_score = (norm_embedding * 0.7 + norm_tfidf * 0.3) * 100
    
    # ====== General Score ======
    general_score = calculate_general_score(job_text, job_title)
    
    # ====== Boost ======
    boost = domain_boost(job_text, resume_text, semantic_matcher)
    
    # ====== Penalty ======
    penalty = generic_penalty(job_text)
    penalty_percent = int(penalty * 100)
    
    # ====== تشخیص دسته‌بندی شغل ======
    category = detect_job_category(job_title, job_text, technical_score, general_score)
    
    # ====== محاسبه امتیاز بر اساس دسته‌بندی ======
    
    # Technical Track: امتیاز فنی با تأثیر کم General
    technical_final = (0.7 * technical_score) + (0.3 * general_score)
    technical_final = technical_final + (boost * 0.5)
    technical_final = technical_final * (1 - penalty)
    
    # Admin Track: امتیاز اداری با تأثیر بیشتر General
    admin_final = (0.3 * technical_score) + (0.7 * general_score)
    admin_final = admin_final + (boost * 0.3)
    admin_final = admin_final * (1 - penalty * 0.7)  # Penalty کمتر برای اداری‌ها
    
    # Hybrid Track: ترکیب متعادل
    hybrid_final = (0.5 * technical_score) + (0.5 * general_score)
    hybrid_final = hybrid_final + (boost * 0.5)
    hybrid_final = hybrid_final * (1 - penalty * 0.8)
    
    # ====== انتخاب امتیاز نهایی بر اساس دسته‌بندی ======
    if category == "technical":
        final_score = technical_final
    elif category == "administrative":
        final_score = admin_final
        # Admin Safety Layer: حداقل ۳۰% برای نمایش
        final_score = max(final_score, 30)
        # Admin Cap: حداکثر ۵۵% (برای جلوگیری از dominance)
        final_score = min(final_score, 55)
    else:  # hybrid
        final_score = hybrid_final
    
    # ====== اطمینان از محدوده ۰-۱۰۰ ======
    final_score = int(min(100, max(0, final_score)))
    
    # ====== امتیازهای جداگانه برای نمایش ======
    return {
        'final': final_score,
        'technical': int(technical_score),
        'general': int(general_score),
        'boost': boost,
        'penalty': penalty_percent,
        'category': category,
        'technical_score_raw': int(technical_final),
        'admin_score_raw': int(admin_final),
        'hybrid_score_raw': int(hybrid_final)
    }


warnings.filterwarnings('ignore')


# ==========================================
# LEVEL 3: SEMANTIC MATCHING WITH TF-IDF
# ==========================================



def semantic_match_score(job_text, resume_text, skill_keywords):
    """محاسبه‌ی شباهت معنایی با TF-IDF و Cosine Similarity"""
    if not job_text or not resume_text:
        return 0
    
    enhanced_resume = resume_text + " " + " ".join(skill_keywords * 2)
    job_text_clean = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', job_text).lower()
    resume_clean = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', enhanced_resume).lower()
    
    try:
        corpus = [job_text_clean, resume_clean]
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words=None,
            ngram_range=(1, 2),
            min_df=1
        )
        
        tfidf_matrix = vectorizer.fit_transform(corpus)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        return similarity[0][0] * 100
        
    except Exception as e:
        print(f"  ⚠️ TF-IDF Error: {e}")
        return 0



def calculate_outlier_score(scores_list, current_score):
    """
    محاسبه‌ی امتیاز outlier با استفاده از ترکیب Z-Score و Percentile
    - اگر داده‌ها نرمال باشند: ترکیب Z-Score + Percentile
    - اگر داده‌ها چوله (Skewed) باشند: فقط Percentile
    """
    import numpy as np
    
    # اگر تعداد داده‌ها کم باشد، مقدار پیش‌فرض برگردان
    if len(scores_list) < 5:
        return 50
    
    scores = np.array(scores_list)
    
    # ====== Percentile واقعی (مقاوم) ======
    percentile = (np.sum(scores <= current_score) / len(scores)) * 100
    
    # ====== بررسی چولگی (Skewness) داده‌ها ======
    mean_val = np.mean(scores)
    median_val = np.median(scores)
    std_val = np.std(scores) + 1e-8  # جلوگیری از تقسیم بر صفر
    skewness = abs((mean_val - median_val) / std_val)
    
    # ====== اگر داده‌ها نرمال هستند (Skewness کم) ======
    if skewness < 0.5:
        # محاسبه Z-Score
        z = (current_score - mean_val) / std_val
        
        try:
            from scipy.stats import norm
            z_percentile = norm.cdf(z) * 100
        except ImportError:
            # اگر scipy نصب نبود، از روش تقریبی استفاده کن
            if z >= 0:
                z_percentile = 50 + (z * 34)
            else:
                z_percentile = 50 + (z * 34)
        
        # ترکیب Z-Score و Percentile (۵۰-۵۰)
        final = (z_percentile * 0.5) + (percentile * 0.5)
    
    # ====== اگر داده‌ها چوله هستند ======
    else:
        # فقط از Percentile استفاده کن (مقاوم‌تر)
        final = percentile
    
    # محدود کردن به بازه ۰-۱۰۰
    return int(np.clip(final, 0, 100))
# ==========================================
# CALCULATE KEYWORD SCORE
# ==========================================
def calculate_keyword_score(full_text, requirements_text, description_text, title_text):
    """محاسبه‌ی امتیاز بر اساس کلمات کلیدی (سطح ۲)"""
    
    full_text_lower = full_text.lower()
    requirements_lower = requirements_text.lower()
    description_lower = description_text.lower()
    title_lower = title_text.lower()
    
    group_weight_multipliers = defaultdict(float)
    for keyword, group_names in JOB_TITLE_WEIGHT_MAP.items():
        if keyword.lower() in title_lower:
            for group_name in group_names:
                group_weight_multipliers[group_name] = max(
                    group_weight_multipliers[group_name], 1.5
                )
    
    group_results = {}
    total_score = 0
    all_matched_keywords = []
    
    for group_name, group_config in SKILL_GROUPS.items():
        keywords = group_config["keywords"]
        base_weight = group_config["base_weight"]
        bonus_per_match = group_config["bonus_per_match"]
        min_matches_for_bonus = group_config["min_matches_for_bonus"]
        
        multiplier = group_weight_multipliers.get(group_name, 1.0)
        effective_weight = base_weight * multiplier
        
        matched = []
        match_count = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            importance_score = 0
            if keyword_lower in requirements_lower:
                importance_score += 2
            if keyword_lower in description_lower:
                importance_score += 1.2
            if keyword_lower in full_text_lower:
                importance_score += 0.8
            
            if importance_score > 0:
                count_in_text = full_text_lower.count(keyword_lower)
                count_in_req = requirements_lower.count(keyword_lower)
                
                total_occurrences = min(count_in_text + count_in_req * 2, 5)
                match_count += total_occurrences
                matched.append(keyword)
                all_matched_keywords.append(keyword)
        
        bonus = 0
        if match_count >= min_matches_for_bonus:
            bonus = min(match_count * bonus_per_match, effective_weight * 0.5)
        
        group_score = (match_count * effective_weight * 0.3) + bonus
        group_results[group_name] = {
            "score": int(group_score),
            "match_count": match_count,
            "matched_keywords": matched[:10],
            "effective_weight": effective_weight,
            "bonus": int(bonus),
            "multiplier": multiplier
        }
        total_score += group_score
    
    max_possible_score = sum([
        config["base_weight"] * 5 * 0.3 + (config["base_weight"] * 0.5) 
        for config in SKILL_GROUPS.values()
    ])
    
    if max_possible_score == 0:
        return 0, [], {}
    
    percentage = int((total_score / max_possible_score) * 100)
    matched_keywords = list(set(all_matched_keywords))[:20]
    
    return min(100, percentage), matched_keywords, group_results

# ==========================================
# CALCULATE MATCH SCORE (سطح ۲ + ۳)
# ==========================================
def calculate_match_score_advanced(sections, job_title="", all_scores=None):
    """ترکیب سطح ۲ (گروه‌بندی) و سطح ۳ (TF-IDF + Outlier)"""
    
    if not sections:
        return 0, [], {}, 0, 0
    
    full_text = sections.get("full_text", "")
    requirements_text = sections.get("requirements", "")
    description_text = sections.get("description", "")
    title_text = sections.get("title", "") or job_title
    
    keyword_score, matched_keywords, group_results = calculate_keyword_score(
        full_text, requirements_text, description_text, title_text
    )
    
    combined_job_text = f"{title_text} {description_text} {requirements_text}"
    semantic_score = semantic_match_score(combined_job_text, RESUME_TEXT, matched_keywords)
    
    final_score = int((keyword_score * 0.7) + (semantic_score * 0.3))
    
    outlier_score = 0
    if all_scores and len(all_scores) > 2:
        outlier_score = calculate_outlier_score(all_scores, final_score)
    
    return final_score, matched_keywords, group_results, semantic_score, outlier_score
