import json
from datetime import datetime
from job_matcher_core import *
from html_generator import generate_html_report
from semantic_matcher import SemanticMatcher, combine_scores
from config import SCORE_WEIGHTS, EMBEDDING_MODEL, FILTERS

def main():
    url = "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3"
    
    print("=" * 80)
    print("🚀 JOB MATCHER v4.0 - WITH SEMANTIC EMBEDDING")
    print("   (Keyword + TF-IDF + Semantic Embedding)")
    print("=" * 80)
    
    # ==========================================
    # مقداردهی Semantic Matcher
    # ==========================================
    print("\n🔄 Loading Semantic Model...")
    semantic_matcher = SemanticMatcher(EMBEDDING_MODEL)
    
    if not semantic_matcher.is_loaded:
        print("⚠️ Semantic matching disabled (install sentence-transformers)")
        print("   Run: pip install sentence-transformers")
    
    # ==========================================
    # Web Scraping
    # ==========================================
    driver = setup_driver()
    try:
        jobs = extract_all_jobs(driver, url)
        
        if not jobs:
            print("❌ No jobs found!")
            return
        
        print(f"\n✅ Extracted {len(jobs)} jobs!")
        print("🔄 Calculating advanced match scores...\n")
        
        results = []
        all_scores = []
        
        # جمع‌آوری متن آگهی‌ها برای Batch Embedding
        job_texts = []
        for job in jobs:
            job_text = f"""
            {job['sections'].get('title', '')}
            {job['sections'].get('description', '')}
            {job['sections'].get('requirements', '')}
            """
            job_texts.append(job_text)
        
        # محاسبه Batch Embedding (برای سرعت بیشتر)
        embedding_scores = []
        if semantic_matcher.is_loaded:
            embedding_scores = semantic_matcher.calculate_batch_similarity(
                job_texts, 
                RESUME_TEXT
            )
        else:
            embedding_scores = [0] * len(jobs)
        
        # ==========================================
        # محاسبه امتیازات برای هر شغل
        # ==========================================
        for idx, job in enumerate(jobs):
            # Keyword Score (از کد قبلی)
            keyword_score, matched_keywords, group_results = calculate_keyword_score(
                job['sections'].get('full_text', ''),
                job['sections'].get('requirements', ''),
                job['sections'].get('description', ''),
                job['sections'].get('title', '') or job['title']
            )
            
            # TF-IDF Score (از کد قبلی)
            combined_job_text = f"""
            {job['sections'].get('title', '')}
            {job['sections'].get('description', '')}
            {job['sections'].get('requirements', '')}
            """
            tfidf_score = semantic_match_score(combined_job_text, RESUME_TEXT, matched_keywords)
            
            # Embedding Score (جدید)
            embedding_score = embedding_scores[idx] if idx < len(embedding_scores) else 0
            
            # ترکیب امتیازها
            final_score = combine_scores(keyword_score, tfidf_score, embedding_score)
            all_scores.append(final_score)
            
            # ذخیره موقت برای outlier
            results.append({
                "title": job['title'],
                "company": job['company'],
                "url": job['url'],
                "keyword_score": keyword_score,
                "tfidf_score": int(tfidf_score),
                "embedding_score": int(embedding_score),
                "score": final_score,
                "matched_skills": matched_keywords,
                "group_analysis": group_results,
                "description_preview": job['sections'].get('description', '')[:300],
                "index": idx
            })
        
        # ==========================================
        # محاسبه Outlier Score
        # ==========================================
        for result in results:
            result['outlier_score'] = calculate_outlier_score(all_scores, result['score'])
        
        # فیلتر بر اساس امتیاز
        min_score = FILTERS.get('min_score', 30)
        filtered_results = [r for r in results if r['score'] >= min_score]
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        # ==========================================
        # ذخیره نتایج
        # ==========================================
        json_filename = f"job_matches_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(filtered_results, f, ensure_ascii=False, indent=2)
        
        html_filename = f"job_report_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        generate_html_report(filtered_results, html_filename)
        
        # ==========================================
        # نمایش نتایج
        # ==========================================
        print("=" * 80)
        print(f"📁 Results saved to: {json_filename}")
        print(f"📄 HTML report: {html_filename}")
        print(f"🎯 Found {len(filtered_results)} relevant jobs out of {len(jobs)}")
        print("=" * 80)
        
        if filtered_results:
            print("\n🏆 TOP 5 MATCHING JOBS:\n")
            for i, job in enumerate(filtered_results[:5], 1):
                print(f"{i}. [{job['score']}%] {job['title']}")
                print(f"   🏢 {job['company']}")
                print(f"   📊 Keyword: {job['keyword_score']}% | TF-IDF: {job['tfidf_score']}% | Embedding: {job['embedding_score']}%")
                print(f"   📊 Outlier: {job['outlier_score']}%")
                print(f"   🛠️  Skills: {', '.join(job['matched_skills'][:5])}")
                print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("✅ Browser closed.")

if __name__ == "__main__":
    main()