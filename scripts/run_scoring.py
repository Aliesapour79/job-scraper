# scripts/run_scoring.py - نسخه v8 با سطح‌بندی مهارت‌ها

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tqdm import tqdm

from matcher.semantic_matcher import SemanticMatcher
from matcher.score_calculator import calculate_final_score_v8
from matcher.skill_parser import parse_resume_skills
from report.html_generator import generate_html_report
from config.resume import RESUME_TEXT
from config.settings import EMBEDDING_MODEL


DB_PATH = "data/jobs_db_clean.db"


def load_jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT id, title, company, url, description, requirements, skills,
               job_category, site, job_hash
        FROM jobvision_jobs_clean
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return rows, columns


def convert_row_to_job(row, columns):
    job = dict(zip(columns, row))
    job['sections'] = {
        'title': job.get('title', ''),
        'description': job.get('description', ''),
        'requirements': job.get('requirements', ''),
        'company': job.get('company', '')
    }
    return job


def extract_resume_info():
    return {
        'age': 25,
        'gender': 'male',
        'military': 'done',
        'education_level': 2,
        'age_required': True
    }


def score_single_job(job, semantic_matcher, resume_text, resume_skills):
    s = job.get('sections', {})
    resume_info = extract_resume_info()
    
    result = calculate_final_score_v8(
        skills=job.get('skills', ''),
        description=s.get('description', ''),
        requirements=s.get('requirements', ''),
        resume_text=resume_text,
        resume_info=resume_info,
        job_category=job.get('job_category', ''),
        semantic_matcher=semantic_matcher,
        resume_skills=resume_skills
    )
    
    result['title'] = job.get('title', 'Unknown')
    result['company'] = job.get('company', 'Unknown')
    result['url'] = job.get('url', '')
    result['job_category'] = job.get('job_category', '')
    result['description_preview'] = s.get('description', '')[:300]
    
    return result


def save_results(results, filename="scored_jobs_v8_test"):
    df = pd.DataFrame(results)
    df = df.sort_values('final', ascending=False)
    
    df.to_csv(f"{filename}.csv", index=False, encoding='utf-8-sig')
    print(f"✅ CSV saved: {filename}.csv")
    
    df.to_json(f"{filename}.json", orient='records', force_ascii=False, indent=2)
    print(f"✅ JSON saved: {filename}.json")
    
    report_data = []
    for _, row in df.iterrows():
        scores = row.get('scores', {})
        report_data.append({
            'title': row.get('title', 'Unknown'),
            'company': row.get('company', 'Unknown'),
            'url': row.get('url', ''),
            'site': 'jobvision',
            'score': row.get('final', 0),
            'technical_score': scores.get('hard', 0),
            'general_score': scores.get('soft', 0),
            'embedding_score': scores.get('semantic', 0),
            'tfidf_score': 0,
            'keyword_score': scores.get('hard', 0),
            'outlier_score': 50,
            'category': row.get('job_category', 'technical'),
            'penalty': row.get('penalty', 0),
            'boost': 0,
            'description_preview': row.get('description_preview', '')[:300],
            'matched_skills': [],
            'group_analysis': {}
        })
    
    generate_html_report(report_data, f"{filename}.html")
    print(f"✅ HTML report saved: {filename}.html")
    
    return df


def print_summary(df):
    print("\n" + "=" * 60)
    print("📊 SCORING SUMMARY (v8 - با سطح‌بندی مهارت‌ها)")
    print("=" * 60)
    
    print(f"📋 Total: {len(df)}")
    print(f"📈 Average: {df['final'].mean():.1f}%")
    print(f"🏆 Best: {df['final'].max():.1f}%")
    
    print("\n🏆 TOP 5:")
    for i, row in df.head(5).iterrows():
        scores = row.get('scores', {})
        print(f"   {i+1}. {row['final']:.1f}% - {row['title']}")
        print(f"      🎯 Hard: {scores.get('hard', 0):.1f}% | Soft: {scores.get('soft', 0):.1f}%")
        print(f"      ⚠️ Penalty: {row.get('penalty', 0)}%")
        print()


def main():
    print("=" * 60)
    print("🧪 TEST SCORING ENGINE v8 (با سطح‌بندی مهارت‌ها)")
    print("=" * 60)
    
    rows, columns = load_jobs()
    print(f"📦 Jobs loaded: {len(rows)}")
    
    print("\n🧠 Loading semantic model...")
    semantic_matcher = SemanticMatcher(EMBEDDING_MODEL)
    if not semantic_matcher.is_loaded:
        print("❌ Model not loaded!")
        return
    print("✅ Model loaded")
    
    # =========================
    # ✅ استخراج مهارت‌های رزومه
    # =========================
    print("\n📋 Extracting resume skills...")
    resume_skills = parse_resume_skills(RESUME_TEXT)
    print(f"   ✅ Found {len(resume_skills)} skills in resume")
    
    if resume_skills:
        print("   📝 Sample:")
        for skill, level in list(resume_skills.items())[:10]:
            print(f"      - {skill}: {level}")
    else:
        print("   ⚠️ No skills found! Check the resume parser.")
        return
    
    print("\n⚡ Scoring jobs with v8 (level-based)...")
    results = []
    for row in tqdm(rows, desc="Scoring (v8)", unit="job"):
        job = convert_row_to_job(row, columns)
        results.append(score_single_job(job, semantic_matcher, RESUME_TEXT, resume_skills))
    
    print("\n💾 Saving results...")
    df = save_results(results)
    print_summary(df)
    
    print("\n✅ DONE!")
    print("   📁 scored_jobs_v8_test.html")


if __name__ == "__main__":
    main()