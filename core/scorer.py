# core/scorer.py
from tqdm import tqdm
from matcher.skill_parser import parse_resume_skills, parse_job_skills
from matcher.weights import get_job_group  # ✅ اضافه شد

from matcher import (
    calculate_final_score_v8,
    calculate_outlier_score,
    generate_explanation
)


def convert_db_row_to_job(row):
    """
    تبدیل یک ردیف از دیتابیس (tuple) به دیکشنری job
    
    ترتیب SELECT از get_all_jobs():
    (id, title, company, url, location, salary, is_urgent,
     description, requirements, full_text, skills, age_range,
     gender, job_category, site, job_hash, scraped_at)
    """
    return {
        'sections': {
            'title': row[1] or '',
            'company': row[2] or '',
            'description': row[7] or '',
            'requirements': row[8] or '',
            'full_text': row[9] or '',
        },
        'skills': row[10] or '',
        'site': row[14] or 'unknown',
        'url': row[3] or '',
        'title': row[1] or '',
        'company': row[2] or '',
        'job_category': row[13] or '',
        'age_range': row[11] or '',
        'gender': row[12] or '',
        'location': row[4] or '',
        'is_urgent': row[6] or 0,
        'salary': row[5] or '',
    }


def extract_resume_info(row):
    """
    استخراج اطلاعات رزومه
    
    Returns:
        dict: {
            'age': int,
            'gender': str,
            'military': str,
            'education_level': int,
            'age_required': bool
        }
    """
    return {
        'age': 28,
        'gender': 'male',
        'military': 'done',
        'education_level': 2,
        'age_required': True
    }


def score_jobs(all_jobs, semantic_matcher, resume_text):
    """
    امتیازدهی به آگهی‌ها با معماری v8
    
    Args:
        all_jobs: لیست آگهی‌ها (tuple یا dict)
        semantic_matcher: شیء SemanticMatcher
        resume_text: متن رزومه
    
    Returns:
        list: نتایج امتیازدهی با توضیحات
    """
    print("\n🔄 Calculating match scores (v8)...")
    print("   This may take a few minutes...")

    # =========================
    # ۱. تبدیل tuple به dict
    # =========================
    converted_jobs = []
    for job in all_jobs:
        if isinstance(job, tuple):
            converted_jobs.append(convert_db_row_to_job(job))
        else:
            converted_jobs.append(job)
    
    all_jobs = converted_jobs

    # =========================
    # ۲. اطلاعات رزومه و مهارت‌های رزومه
    # =========================
    resume_info = extract_resume_info(None)
    
    # استخراج مهارت‌های رزومه
    resume_skills = parse_resume_skills(resume_text)
    print(f"   📋 Found {len(resume_skills)} skills in resume")

    # =========================
    # ۳. امتیازدهی
    # =========================
    print("  📊 Scoring jobs...")
    results = []
    all_scores = []

    for job in tqdm(all_jobs, desc="Scoring jobs (v8)", unit="job"):
        s = job.get('sections', {})
        
        # =========================
        # 🏷️ تشخیص گروه شغلی از job_category
        # =========================
        job_category = job.get('job_category', '')
        group = get_job_group(job_category)  # ✅ technical / administrative / hybrid
        
        # # =========================
        # # 🔍 دیباگ: نمایش job_category و group (فقط ۵ نمونه اول)
        # # =========================
        # if not hasattr(score_jobs, '_debug_count'):
        #     score_jobs._debug_count = 0
        # if score_jobs._debug_count < 5:
        #     # print(f"   🔍 Sample {score_jobs._debug_count+1}: Category='{job_category}' → Group='{group}'")
        #     score_jobs._debug_count += 1
    
        # محاسبه امتیاز با v8
        result = calculate_final_score_v8(
            skills=job.get('skills', ''),
            description=s.get('description', ''),
            requirements=s.get('requirements', ''),
            resume_text=resume_text,
            resume_info=resume_info,
            job_category=job_category,  # ← ارسال به weights.py
            semantic_matcher=semantic_matcher,
            resume_skills=resume_skills
        )
        
        # =========================
        # 🔍 استخراج مهارت‌های تطابق‌یافته
        # =========================
        job_skills = parse_job_skills(job.get('skills', ''))
        matched = set(resume_skills.keys()) & set(job_skills.keys())
        
        # =========================
        # ۴. تولید توضیح
        # =========================
        explanation = generate_explanation(
            result,
            job_title=job.get('title', 'Unknown'),
            company=job.get('company', 'Unknown')
        )
        
        # =========================
        # ۵. ساخت خروجی با matched_skills و category درست
        # =========================
        results.append({
            "title": job.get('title', 'Unknown'),
            "company": job.get('company', 'Unknown'),
            "url": job.get('url', ''),
            "site": job.get('site', 'unknown'),
            "location": job.get('location', ''),
            "is_urgent": job.get('is_urgent', 0),
            "salary": job.get('salary', ''),
            "score": result['final'],
            "technical_score": result['scores']['hard'],
            "general_score": result['scores']['soft'],
            "embedding_score": result['scores']['semantic'],
            "tfidf_score": 0,
            "keyword_score": result['scores']['hard'],
            "matched_skills": list(matched)[:10],
            "category": group,  # ✅ اینجا group ذخیره میشه (technical/administrative/hybrid)
            "category_raw": job_category,  # ✅ برای دیباگ (اختیاری)
            "penalty": result['penalty'],
            "penalty_reasons": result['penalty_reasons'],
            "boost": 0,
            "description_preview": s.get('description', '')[:300],
            "error": job.get('error', None),
            "raw_score": result['raw'],
            "scores": result['scores'],
            "weights": result['weights'],
            "explanation": explanation
        })
        
        all_scores.append(result['final'])

    # =========================
    # ۶. Outlier Score
    # =========================
    print("  📊 Calculating outlier scores...")
    for r in results:
        r['outlier_score'] = calculate_outlier_score(all_scores, r['score'])

    return results