# scripts/run_scoring.py

import sqlite3
import json
import sys
import os

# اضافه کردن مسیر پروژه به PATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tqdm import tqdm

from matcher.semantic_matcher import SemanticMatcher
from matcher.score_calculator import (
    calculate_keyword_score,
    calculate_general_score,
    domain_boost,
    generic_penalty,
    detect_job_category,
    calculate_final_score_v73,
    semantic_match_score
)
from report.html_generator import generate_html_report
from config.resume import RESUME_TEXT
from config.settings import EMBEDDING_MODEL, FILTERS


DB_PATH = "data/jobss.db"


def load_jobs(limit=None):
    """بارگذاری آگهی‌ها از دیتابیس (بدون تغییر در دیتابیس)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT id, title, company, url, location, salary, is_urgent,
               description, requirements, full_text, skills,
               age_range, gender, job_category, site,
               job_hash, scraped_at
        FROM jobvision_jobs
    """
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    
    columns = [description[0] for description in cursor.description]
    conn.close()
    
    return rows, columns


def convert_row_to_job(row, columns):
    """تبدیل ردیف دیتابیس به دیکشنری job"""
    job = dict(zip(columns, row))
    
    # ساخت sections
    job['sections'] = {
        'full_text': job.get('full_text', ''),
        'title': job.get('title', ''),
        'description': job.get('description', ''),
        'requirements': job.get('requirements', ''),
        'company': job.get('company', '')
    }
    
    return job


def score_single_job(job, semantic_matcher, resume_text, all_scores, all_tfidf):
    """امتیازدهی به یک آگهی با استفاده از تابع جدید"""
    
    s = job.get('sections', {})
    
    # محاسبه امتیازها
    keyword_score, matched_keywords, group_results = calculate_keyword_score(
        s.get('full_text', ''),
        s.get('requirements', ''),
        s.get('description', ''),
        s.get('title', '')
    )
    
    job_text = f"{s.get('title','')} {s.get('description','')} {s.get('requirements','')}"
    
    # =========================
    # 🔥 محاسبه Embedding و TF-IDF
    # =========================
    try:
        embedding_scores = semantic_matcher.calculate_batch_similarity([job_text], resume_text)
        embedding_score = embedding_scores[0] if embedding_scores else 0
    except Exception as e:
        print(f"⚠️ Embedding error: {e}")
        embedding_score = 0
    
    tfidf_score = semantic_match_score(job_text, resume_text, matched_keywords)
    
    all_tfidf.append(tfidf_score)
    all_scores.append(embedding_score)
    
    # 🎯 استفاده از تابع جدید v7.2
    result = calculate_final_score_v73(
        idx=len(all_scores) - 1,
        job_text=job_text,
        resume_text=resume_text,
        embedding_score=embedding_score,
        tfidf_score=tfidf_score,
        all_embedding_scores=all_scores,
        all_tfidf_scores=all_tfidf,
        semantic_matcher=semantic_matcher,
        job_title=job.get('title', '')
    )
    
    # =========================
    # 🔥 اضافه کردن embedding_score و tfidf_score به result
    # =========================
    result['embedding_score'] = embedding_score
    result['tfidf_score'] = tfidf_score
    result['keyword_score'] = keyword_score
    
    # اضافه کردن اطلاعات پایه
    result['title'] = job.get('title', 'Unknown')
    result['company'] = job.get('company', 'Unknown')
    result['url'] = job.get('url', '')
    result['site'] = job.get('site', 'unknown')
    result['job_category'] = job.get('job_category', '')
    result['location'] = job.get('location', '')
    result['description_preview'] = s.get('description', '')[:300]
    result['matched_keywords'] = matched_keywords
    result['group_results'] = group_results
    
    return result


def save_results(results, filename="scored_jobs_v72"):
    """ذخیره نتایج در فایل‌های CSV و JSON و HTML"""
    
    # ۱. تبدیل به DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values('final', ascending=False)
    
    # ۲. ذخیره CSV
    csv_file = f"{filename}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"✅ CSV saved: {csv_file}")
    
    # ۳. ذخیره JSON
    json_file = f"{filename}.json"
    df.to_json(json_file, orient='records', force_ascii=False, indent=2)
    print(f"✅ JSON saved: {json_file}")
    
    # ۴. 🔥 تولید HTML Report با استفاده از html_generator
    html_file = f"{filename}.html"
    
    # تبدیل به فرمت مورد نیاز html_generator
    report_data = []
    for _, row in df.iterrows():
        report_data.append({
            'title': row.get('title', 'Unknown'),
            'company': row.get('company', 'Unknown'),
            'url': row.get('url', ''),
            'site': row.get('site', 'unknown'),
            'score': row.get('final', 0),
            'technical_score': row.get('technical', 0),
            'general_score': row.get('general', 0),
            'embedding_score': row.get('embedding_score', 0),   # 🔥 اصلاح
            'tfidf_score': row.get('tfidf_score', 0),           # 🔥 اصلاح
            'keyword_score': row.get('keyword_score', 0),       # 🔥 اصلاح
            'outlier_score': row.get('outlier', 50),
            'category': row.get('category', 'technical'),
            'penalty': row.get('penalty', 0),
            'boost': row.get('boost', 0),
            'description_preview': row.get('description_preview', '')[:300],
            'matched_skills': row.get('matched_keywords', [])[:10],
            'group_analysis': row.get('group_results', {})
        })
    
    generate_html_report(report_data, html_file)
    print(f"✅ HTML report saved: {html_file}")
    
    return df


def print_summary(df):
    """نمایش خلاصه نتایج"""
    print("\n" + "=" * 60)
    print("📊 SCORING SUMMARY (v7.2)")
    print("=" * 60)
    
    print(f"📋 Total jobs scored: {len(df)}")
    print(f"📈 Average score: {df['final'].mean():.1f}%")
    print(f"🏆 Best score: {df['final'].max():.1f}%")
    print(f"📉 Worst score: {df['final'].min():.1f}%")
    
    print("\n📊 Category breakdown:")
    cat_counts = df['category'].value_counts()
    for cat, count in cat_counts.items():
        avg = df[df['category'] == cat]['final'].mean()
        print(f"   {cat}: {count} jobs (avg: {avg:.1f}%)")
    
    print("\n🏆 TOP 5 MATCHING JOBS:")
    for i, row in df.head(5).iterrows():
        print(f"   {i+1}. {row['final']}% - {row['title']}")
        print(f"      🏢 {row['company']}")
        print(f"      🎯 Technical: {row['technical']}% | 📋 General: {row['general']}%")
        print(f"      📊 Category: {row['category']}")
        if 'weights' in row and isinstance(row['weights'], dict):
            w = row['weights']
            print(f"      ⚖️  Weights: S:{w.get('semantic',0):.2f} T:{w.get('technical',0):.2f} G:{w.get('general',0):.2f}")
        print()


def main():
    print("=" * 60)
    print("🧪 TEST SCORING ENGINE v7.2")
    print("   (Read-only mode - no database changes)")
    print("=" * 60)
    
    # بارگذاری آگهی‌ها
    print("\n🔄 Loading jobs from database...")
    rows, columns = load_jobs(limit=100)  # همه آگهی‌ها
    
    print(f"📦 Jobs loaded: {len(rows)}")
    
    # بارگذاری مدل
    print("\n🧠 Loading semantic model...")
    semantic_matcher = SemanticMatcher(EMBEDDING_MODEL)
    
    if not semantic_matcher.is_loaded:
        print("❌ Model not loaded! Exiting...")
        return
    
    print("✅ Model loaded successfully")
    
    # امتیازدهی
    print("\n⚡ Scoring jobs...")
    results = []
    all_scores = []
    all_tfidf = []
    
    for row in tqdm(rows, desc="Scoring", unit="job"):
        job = convert_row_to_job(row, columns)
        result = score_single_job(job, semantic_matcher, RESUME_TEXT, all_scores, all_tfidf)
        results.append(result)
    
    # ذخیره نتایج
    print("\n💾 Saving results...")
    df = save_results(results, "scored_jobs_v72")
    
    # نمایش خلاصه
    print_summary(df)
    
    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("   📁 scored_jobs_v72.csv - Full results in CSV")
    print("   📁 scored_jobs_v72.json - Full results in JSON")
    print("   📁 scored_jobs_v72.html - Visual report (open in browser)")
    print("=" * 60)
    print("\n💡 Open scored_jobs_v72.html in your browser to see the report.")
    print("   Compare with previous reports to evaluate the new scoring engine.")


if __name__ == "__main__":
    main()