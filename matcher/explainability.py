# matcher/explainability.py
"""
سیستم توضیح‌دهی امتیازها (Explainability Layer)
"""


def generate_explanation(result: dict, job_title: str, company: str) -> dict:
    """
    تولید توضیح برای امتیاز یک آگهی
    
    Args:
        result: خروجی از `calculate_final_score_v8`
        job_title: عنوان شغل
        company: نام شرکت
    
    Returns:
        dict: توضیح کامل شامل بخش‌های مختلف
    """
    scores = result['scores']
    weights = result['weights']
    penalty = result['penalty']
    reasons = result['penalty_reasons']
    
    # =========================
    # ۱. خلاصه کلی
    # =========================
    summary = generate_summary(scores, penalty, job_title)
    
    # =========================
    # ۲. توضیح هر بخش
    # =========================
    hard_explanation = explain_hard_score(scores['hard'], weights['hard'])
    functional_explanation = explain_functional_score(scores['functional'], weights['functional'])
    soft_explanation = explain_soft_score(scores['soft'], weights['soft'])
    semantic_explanation = explain_semantic_score(scores['semantic'], weights['semantic'])
    
    # =========================
    # ۳. توضیح پنالتی
    # =========================
    penalty_explanation = explain_penalty(penalty, reasons)
    
    # =========================
    # ۴. توصیه نهایی
    # =========================
    recommendation = generate_recommendation(result['final'])
    
    return {
        'summary': summary,
        'breakdown': {
            'hard': hard_explanation,
            'functional': functional_explanation,
            'soft': soft_explanation,
            'semantic': semantic_explanation,
            'penalty': penalty_explanation
        },
        'recommendation': recommendation,
        'raw_data': {
            'scores': scores,
            'weights': weights,
            'penalty': penalty,
            'penalty_reasons': reasons
        }
    }


# =========================
# 🔍 توابع کمکی
# =========================

def generate_summary(scores: dict, penalty: int, job_title: str) -> str:
    """خلاصه کلی امتیاز"""
    final_score = 100 - penalty
    
    if final_score >= 80:
        level = "عالی"
        desc = "این آگهی بسیار مناسب شماست"
    elif final_score >= 60:
        level = "خوب"
        desc = "این آگهی تا حد زیادی مناسب شماست"
    elif final_score >= 40:
        level = "متوسط"
        desc = "این آگهی تا حدی مناسب شماست"
    else:
        level = "ضعیف"
        desc = "این آگهی چندان مناسب شما نیست"
    
    return f"{desc} ({level}). امتیاز نهایی: {final_score}%"


def explain_hard_score(score: float, weight: float) -> dict:
    """توضیح امتیاز مهارت‌های سخت"""
    status = "عالی" if score >= 70 else "خوب" if score >= 50 else "متوسط" if score >= 30 else "ضعیف"
    
    return {
        'score': score,
        'weight': weight,
        'contribution': round(score * weight, 2),
        'status': status,
        'description': f"امتیاز مهارت‌های سخت: {score}% ({status})"
    }


def explain_functional_score(score: float, weight: float) -> dict:
    """توضیح امتیاز وظایف شغلی"""
    status = "عالی" if score >= 70 else "خوب" if score >= 50 else "متوسط" if score >= 30 else "ضعیف"
    
    return {
        'score': score,
        'weight': weight,
        'contribution': round(score * weight, 2),
        'status': status,
        'description': f"امتیاز وظایف شغلی: {score}% ({status})"
    }


def explain_soft_score(score: float, weight: float) -> dict:
    """توضیح امتیاز مهارت‌های نرم"""
    status = "عالی" if score >= 70 else "خوب" if score >= 50 else "متوسط" if score >= 30 else "ضعیف"
    
    return {
        'score': score,
        'weight': weight,
        'contribution': round(score * weight, 2),
        'status': status,
        'description': f"امتیاز مهارت‌های نرم: {score}% ({status})"
    }


def explain_semantic_score(score: float, weight: float) -> dict:
    """توضیح امتیاز شباهت معنایی"""
    status = "عالی" if score >= 70 else "خوب" if score >= 50 else "متوسط" if score >= 30 else "ضعیف"
    
    return {
        'score': score,
        'weight': weight,
        'contribution': round(score * weight, 2),
        'status': status,
        'description': f"شباهت معنایی با رزومه: {score}% ({status})"
    }


def explain_penalty(penalty: int, reasons: list) -> dict:
    """توضیح پنالتی شرایط احراز"""
    if penalty == 0:
        return {
            'penalty': 0,
            'description': "✅ همه شرایط احراز برقرار است.",
            'reasons': []
        }
    
    return {
        'penalty': penalty,
        'description': f"⚠️ {penalty}% پنالتی به دلیل شرایط احراز",
        'reasons': reasons
    }


def generate_recommendation(final_score: float) -> str:
    """توصیه نهایی"""
    if final_score >= 80:
        return "🔹 این آگهی برای شما بسیار مناسب است. حتماً اقدام کنید."
    elif final_score >= 60:
        return "🔸 این آگهی برای شما مناسب است. اقدام کنید."
    elif final_score >= 40:
        return "🔹 این آگهی تا حدی مناسب است. با بررسی بیشتر اقدام کنید."
    else:
        return "🔸 این آگهی چندان مناسب شما نیست. بهتر است آن را رد کنید."
