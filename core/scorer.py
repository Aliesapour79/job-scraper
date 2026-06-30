# core/scorer.py
from tqdm import tqdm

from matcher import calculate_final_score_v63, calculate_keyword_score, semantic_match_score, calculate_outlier_score


def convert_db_row_to_job(row):
    """
    تبدیل یک ردیف از دیتابیس (tuple) به دیکشنری job
    
    ساختار tuple از get_all_jobs():
    (id, title, company, url, location, salary, is_urgent, 
     description, requirements, full_text, skills, age_range, 
     gender, job_category, site, job_hash, scraped_at)
    """
    return {
        'sections': {
            'title': row[1] or '',           # title
            'company': row[2] or '',         # company
            'description': row[7] or '',     # description
            'requirements': row[8] or '',    # requirements
            'full_text': row[9] or '',       # full_text
        },
        'skills': row[10] or [],             # skills (JSON string)
        'site': row[14] or 'unknown',        # site
        'url': row[3] or '',                 # url
        'title': row[1] or '',               # title
        'company': row[2] or '',             # company
        'job_category': row[13] or '',       # job_category
    }


def score_jobs(all_jobs, semantic_matcher, resume_text):
    """امتیازدهی به آگهی‌ها (پشتیبانی از tuple و dict)"""
    print("\n🔄 Calculating match scores...")
    print("   This may take a few minutes...")

    # =========================
    # تبدیل tuple به dict (اگر لازم باشد)
    # =========================
    converted_jobs = []
    for job in all_jobs:
        if isinstance(job, tuple):
            # تبدیل tuple به dict
            converted_jobs.append(convert_db_row_to_job(job))
        else:
            # قبلاً dict هست
            converted_jobs.append(job)
    
    all_jobs = converted_jobs

    # =========================
    # ساخت متن‌ها برای embedding
    # =========================
    job_texts = []
    for job in all_jobs:
        s = job.get('sections', {})
        job_texts.append(
            f"{s.get('title','')} {s.get('description','')} {s.get('requirements','')}"
        )

    print("  🧠 Running embeddings...")
    embedding_scores = (
        semantic_matcher.calculate_batch_similarity(job_texts, resume_text)
        if semantic_matcher.is_loaded
        else [0] * len(all_jobs)
    )

    print("  📊 Scoring jobs...")
    results = []
    all_scores = []
    all_tfidf_scores = []

    for idx, job in enumerate(tqdm(all_jobs, desc="Scoring jobs", unit="job")):
        s = job.get('sections', {})

        keyword_score, matched_keywords, _ = calculate_keyword_score(
            s.get('full_text', ''),
            s.get('requirements', ''),
            s.get('description', ''),
            s.get('title', '')
        )

        tfidf_score = semantic_match_score(
            f"{s.get('title','')} {s.get('description','')}",
            resume_text,
            matched_keywords
        )

        all_tfidf_scores.append(tfidf_score)

        scores = calculate_final_score_v63(
            idx=idx,
            job_text=job_texts[idx],
            resume_text=resume_text,
            embedding_score=embedding_scores[idx],
            tfidf_score=tfidf_score,
            all_embedding_scores=embedding_scores,
            all_tfidf_scores=all_tfidf_scores,
            semantic_matcher=semantic_matcher,
            job_title=job.get('title', '')
        )

        final = scores['final']
        all_scores.append(final)

        results.append({
            "title": job.get('title', 'Unknown'),
            "company": job.get('company', 'Unknown'),
            "url": job.get('url', ''),
            "site": job.get('site', 'unknown'),
            "score": final,
            "technical_score": scores.get('technical', 0),
            "general_score": scores.get('general', 0),
            "embedding_score": int(embedding_scores[idx]),
            "tfidf_score": int(tfidf_score),
            "keyword_score": keyword_score,
            "matched_skills": matched_keywords,
            "category": scores.get('category', 'technical'),
            "penalty": scores.get('penalty', 0),
            "boost": scores.get('boost', 0),
            "description_preview": s.get('description', '')[:300],
            "error": job.get('error', None)
        })

    print("  📊 Calculating outlier scores...")
    for r in results:
        r['outlier_score'] = calculate_outlier_score(all_scores, r['score'])

    return results