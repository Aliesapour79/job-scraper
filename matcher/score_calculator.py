# matcher/score_calculator.py
import re
import warnings
from .weights import get_weights
from .eligibility import check_eligibility
from .skill_groups import SKILL_GROUPS
from .text_normalizer import TextNormalizer
from .skill_parser import parse_skills_with_level, calculate_skill_match_score

warnings.filterwarnings('ignore')


# =========================
# 📋 کلمات کلیدی
# =========================

FUNCTIONAL_VERBS = [
    # فارسی
    "طراحی", "پیاده‌سازی", "بهینه‌سازی", "یکپارچه‌سازی", "مدیریت", "ساخت",
    "توسعه", "برنامه‌نویسی", "تحلیل", "ارزیابی", "نگهداری", "پشتیبانی",
    # انگلیسی
    "design", "develop", "implement", "optimize", "integrate",
    "manage", "build", "create", "analyze", "maintain", "support",
    # ترکیبی
    "responsible for", "work on", "in charge of",
    "architecture", "engineering", "deployment"
]

SOFT_KEYWORDS = [
    # فارسی
    "توانایی", "مسئولیت", "دقت", "تیم", "ارتباط", "مدیریت زمان",
    "یادگیری", "خلاقیت", "تحلیل", "حل مسئله", "گزارش‌نویسی",
    "مستندسازی", "همکاری", "انعطاف‌پذیری", "خودانگیخته",
    # انگلیسی
    "ability", "responsibility", "accuracy", "team", "communication",
    "management", "learning", "creativity", "analysis", "problem solving",
    "collaboration", "ownership", "attention to detail",
    "self-motivated", "fast learner", "adaptability"
]


# =========================
# 🧠 HARD SCORE - روش کلمه‌ای (کلیدواژه‌ای)
# =========================

def calculate_keyword_score(skills_text: str) -> float:
    """
    روش قبلی برای تطابق کلمه‌ای (بدون سطح)
    """
    if not skills_text:
        return 0
    
    skills_normalized = TextNormalizer.normalize(skills_text.lower())
    
    total_score = 0
    max_possible = 0
    
    for group_name, group in SKILL_GROUPS.items():
        keywords = group["keywords"]
        base_weight = group["base_weight"]
        min_matches = group["min_matches_for_bonus"]
        bonus_per_match = group["bonus_per_match"]
        
        matches = 0
        for kw in keywords:
            kw_normalized = TextNormalizer.normalize(kw.lower())
            if kw_normalized in skills_normalized:
                matches += 1
        
        if matches > 0:
            group_score = base_weight * min(matches, 3)
            if matches >= min_matches:
                group_score += (matches - min_matches) * bonus_per_match
            total_score += group_score
        
        max_possible += base_weight * 3 + (3 - min_matches) * bonus_per_match
    
    if max_possible == 0:
        return 0
    
    raw_percent = (total_score / max_possible) * 100
    normalized = (raw_percent / 50) * 100
    normalized = min(normalized, 100)
    
    return round(normalized, 2)


# =========================
# 🧠 HARD SCORE - نسخه ترکیبی (سطح‌بندی + کلمه‌ای)
# =========================

def calculate_hard_score(skills_text: str, resume_skills_dict: dict = None) -> float:
    """
    محاسبه امتیاز مهارت‌های سخت
    - اگر resume_skills_dict موجود باشه: از روش سطح‌بندی استفاده می‌کنه
    - در غیر این صورت: از روش قبلی (کلمه‌ای) استفاده می‌کنه
    """
    if not skills_text:
        # print(f"   ⚠️ skills_text خالی است!")  # ✅ دیباگ

        return 0
    # print(f"   🔍 skills_text: {skills_text[:100]}...") 
    # print(f"   📋 resume_skills_dict: {resume_skills_dict}")
    # ========================================
    # روش جدید: سطح‌بندی شده
    # ========================================
    if resume_skills_dict:
        job_skills = parse_skills_with_level(skills_text)
        if job_skills:
            # امتیاز تطابق سطح‌بندی شده
            level_score = calculate_skill_match_score(resume_skills_dict, job_skills)
            
            # امتیاز کلمه‌ای (برای پوشش بهتر)
            keyword_score = calculate_keyword_score(skills_text)
            
            # 70% سطح‌بندی + 30% کلمه‌ای
            combined_score = (level_score * 0.70) + (keyword_score * 0.30)
            return round(min(combined_score, 100), 2)
    
    # ========================================
    # روش قبلی: کلمه‌ای
    # ========================================
    return calculate_keyword_score(skills_text)


# =========================
# ⚙️ FUNCTIONAL SCORE (با نرمال‌سازی)
# =========================

def calculate_functional_score(description: str) -> float:
    """محاسبه امتیاز وظایف شغلی با نرمال‌سازی"""
    if not description:
        return 0
    
    text = TextNormalizer.normalize(description.lower())
    score = 0
    
    for verb in FUNCTIONAL_VERBS:
        verb_norm = TextNormalizer.normalize(verb.lower())
        if verb_norm in text:
            score += 2
    
    tech_bonus = len(re.findall(r"python|api|database|sql|system|backend|frontend|cloud", text))
    score += tech_bonus * 1.5
    
    unique_verbs = {TextNormalizer.normalize(v.lower()) for v in FUNCTIONAL_VERBS if TextNormalizer.normalize(v.lower()) in text}
    if len(unique_verbs) >= 5:
        score += 5
    elif len(unique_verbs) >= 3:
        score += 3
    
    return round(min(score * 1.5, 100), 2)


# =========================
# 💬 SOFT SCORE (با نرمال‌سازی)
# =========================

def calculate_soft_score(description: str) -> float:
    """محاسبه امتیاز مهارت‌های نرم با نرمال‌سازی"""
    if not description:
        return 0
    
    text = TextNormalizer.normalize(description.lower())
    score = 0
    
    for kw in SOFT_KEYWORDS:
        kw_norm = TextNormalizer.normalize(kw.lower())
        if kw_norm in text:
            score += 1.5
    
    unique_soft = {TextNormalizer.normalize(k.lower()) for k in SOFT_KEYWORDS if TextNormalizer.normalize(k.lower()) in text}
    if len(unique_soft) >= 4:
        score += 5
    elif len(unique_soft) >= 2:
        score += 3
    
    return round(min(score * 1.8, 100), 2)


# =========================
# 🧠 SEMANTIC SCORE
# =========================

def calculate_semantic_score(description: str, resume_text: str, semantic_matcher) -> float:
    """محاسبه شباهت معنایی بین شرح شغل و رزومه"""
    if not description or not resume_text or not semantic_matcher:
        return 0
    
    try:
        if hasattr(semantic_matcher, 'calculate_similarity'):
            return semantic_matcher.calculate_similarity(description, resume_text)
        else:
            embeddings = semantic_matcher.encode_texts([description, resume_text])
            if embeddings is not None:
                from sklearn.metrics.pairwise import cosine_similarity
                sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(sim * 100)
    except Exception as e:
        print(f"⚠️ Semantic score error: {e}")
        return 0
    
    return 0

# =========================
# 📊 OUTLIER SCORE
# =========================

def calculate_outlier_score(scores_list, current_score):
    
    import numpy as np
    
    if len(scores_list) < 5:
        return 50
    
    scores = np.array(scores_list)
    
    # Percentile robust
    percentile = (
        (np.sum(scores < current_score) + 0.5 * np.sum(scores == current_score))
        / len(scores)
    ) * 100
    
    mean_val = np.mean(scores)
    std_val = np.std(scores) + 1e-8
    
    # skewness واقعی‌تر (fallback safe)
    try:
        from scipy.stats import skew
        skewness = abs(skew(scores))
    except:
        skewness = abs((mean_val - np.median(scores)) / std_val)
    
    if skewness < 0.5:
        z = (current_score - mean_val) / std_val
        
        try:
            from scipy.stats import norm
            z_percentile = norm.cdf(z) * 100
        except:
            z_percentile = max(0, min(100, 50 + z * 34))
        
        weight_z = max(0, 1 - skewness)
        weight_p = 1 - weight_z
        
        final = z_percentile * weight_z + percentile * weight_p
    else:
        final = percentile
    
    return int(np.clip(final, 0, 100))



# =========================
# 🔥 FINAL SCORE
# =========================

def calculate_final_score_v8(
    skills: str,
    description: str,
    requirements: str,
    resume_text: str,
    resume_info: dict,
    job_category: str,
    semantic_matcher=None,
    resume_skills: dict = None
) -> dict:
    """محاسبه امتیاز نهایی با معماری جدید"""
    
    eligibility_result = check_eligibility(requirements, resume_info)
    penalty = eligibility_result['penalty']
    
    # ارسال resume_skills به calculate_hard_score
    hard_score = calculate_hard_score(skills, resume_skills)
    func_score = calculate_functional_score(description)
    soft_score = calculate_soft_score(description)
    semantic_score = calculate_semantic_score(description, resume_text, semantic_matcher)
    
    weights = get_weights(job_category)
    
    raw_score = (
        weights['hard'] * hard_score +
        weights['functional'] * func_score +
        weights['soft'] * soft_score +
        weights['semantic'] * semantic_score
    )
    
    final_score = raw_score * (1 - penalty / 100)
    final_score = round(min(max(final_score, 0), 100), 2)
    
    return {
        'final': final_score,
        'raw': round(raw_score, 2),
        'penalty': penalty,
        'penalty_reasons': eligibility_result['reasons'],
        'scores': {
            'hard': hard_score,
            'functional': func_score,
            'soft': soft_score,
            'semantic': semantic_score
        },
        'weights': weights,
        'eligibility_details': eligibility_result['details']
    }


# =========================
# 📋 نسخه ساده برای تست
# =========================

def calculate_final_simple(skills: str, description: str, job_category: str = "technical") -> dict:
    """نسخه ساده برای تست سریع (بدون embedding و resume)"""
    hard = calculate_hard_score(skills)
    func = calculate_functional_score(description)
    soft = calculate_soft_score(description)
    weights = get_weights(job_category)
    
    final = (
        weights['hard'] * hard +
        weights['functional'] * func +
        weights['soft'] * soft
    )
    
    return {
        'final': round(final, 2),
        'hard': hard,
        'functional': func,
        'soft': soft,
        'weights': weights
    }


# =========================
# 🧪 تست
# =========================
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TESTING SCORE CALCULATOR v8 (با نرمال‌سازی + سطح‌بندی)")
    print("=" * 50)
    
    # رزومه نمونه با سطح
    resume_skills = {
        "python": "پیشرفته",
        "c++": "متوسط",
        "opencv": "پیشرفته",
        "linux": "مقدماتی",
        "git": "متوسط"
    }
    
    skills = "نرم افزارها Python | پیشرفته Django | پیشرفته React | مقدماتی GIT | پیشرفته"
    description = """
    شرح شغل و وظایف: توسعه و نگهداری سرویس‌های Backend با Python و Django. 
    طراحی REST API و پیاده‌سازی میکروسرویس‌ها. 
    همکاری با تیم محصول و مستندسازی.
    """
    requirements = "شرایط احراز: سن 22 - 35 سال، جنسیت تفاوتی ندارد، تحصیلات کارشناسی"
    
    # تست با resume_skills
    result = calculate_final_simple(skills, description, "توسعه نرم افزار و برنامه نویسی")
    print(f"\n📊 Simple Test (بدون سطح‌بندی):")
    print(f"   Final: {result['final']}")
    print(f"   Hard: {result['hard']}")
    print(f"   Functional: {result['functional']}")
    print(f"   Soft: {result['soft']}")
    
    # تست با سطح‌بندی
    hard_score = calculate_hard_score(skills, resume_skills)
    print(f"\n📊 Hard Score با سطح‌بندی: {hard_score}%")