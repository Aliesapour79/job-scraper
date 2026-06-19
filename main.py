import json
from datetime import datetime
import os
from job_matcher_core import *
from html_generator import generate_html_report
from semantic_matcher import SemanticMatcher, combine_scores
from config import SCORE_WEIGHTS, EMBEDDING_MODEL, FILTERS

def main():
    # ایجاد پوشه خروجی
    os.makedirs("output", exist_ok=True)
    
    url = "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3"
    
    print("=" * 80)
    print("🚀 JOB MATCHER v6.1 - MULTI-INTENT SCORING")
    print("   (Technical + Weighted General + Semantic Boost)")
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
        print("🔄 Calculating multi-intent match scores...\n")
        
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
        # مرحله ۱: محاسبه همه امتیازها
        # ==========================================
        all_tfidf_scores = []
        all_embedding_scores = []
        all_job_texts = []
        all_keyword_scores = []
        all_matched_keywords = []
        all_group_results = []
        all_job_data = []
        
        for idx, job in enumerate(jobs):
            # Keyword Score (برای نمایش در گزارش)
            keyword_score, matched_keywords, group_results = calculate_keyword_score(
                job['sections'].get('full_text', ''),
                job['sections'].get('requirements', ''),
                job['sections'].get('description', ''),
                job['sections'].get('title', '') or job['title']
            )
            
            # TF-IDF Score
            combined_job_text = f"""
            {job['sections'].get('title', '')}
            {job['sections'].get('description', '')}
            {job['sections'].get('requirements', '')}
            """
            tfidf_score = semantic_match_score(combined_job_text, RESUME_TEXT, matched_keywords)
            
            # Embedding Score
            embedding_score = embedding_scores[idx] if idx < len(embedding_scores) else 0
            
            # ذخیره برای مرحله بعد
            all_job_texts.append(combined_job_text)
            all_tfidf_scores.append(tfidf_score)
            all_embedding_scores.append(embedding_score)
            all_keyword_scores.append(keyword_score)
            all_matched_keywords.append(matched_keywords)
            all_group_results.append(group_results)
            all_job_data.append({
                "title": job['title'],
                "company": job['company'],
                "url": job['url'],
                "sections": job['sections'],
                "index": idx
            })
        
        # ==========================================
        # مرحله ۲: محاسبه امتیاز نهایی با Multi-Intent Scoring (v6.1)
        # ==========================================
        print("🔄 Applying Multi-Intent scoring (Weighted General + Semantic Boost)...\n")
        
        for idx, job_data in enumerate(all_job_data):
            # محاسبه امتیاز نهایی با Multi-Intent و semantic_matcher
            scores = calculate_final_score(
                idx=idx,
                job_text=all_job_texts[idx],
                resume_text=RESUME_TEXT,
                embedding_score=all_embedding_scores[idx],
                tfidf_score=all_tfidf_scores[idx],
                all_embedding_scores=all_embedding_scores,
                all_tfidf_scores=all_tfidf_scores,
                semantic_matcher=semantic_matcher  # ← اضافه شد برای Boost semantic
            )
            
            final_score = scores['final']
            technical_score = scores['technical']
            general_score = scores['general']
            boost = scores['boost']
            penalty = scores['penalty']
            
            all_scores.append(final_score)
            
            # لاگ دیباگ با نمایش امتیازهای جداگانه
            print(f"  📊 Job {idx+1}: Technical={technical_score}% | General={general_score}% | "
                  f"Boost={boost}% | Penalty={penalty}% | Final={final_score}%")
            
            # ذخیره نتایج
            results.append({
                "title": job_data['title'],
                "company": job_data['company'],
                "url": job_data['url'],
                "keyword_score": all_keyword_scores[idx],
                "tfidf_score": int(all_tfidf_scores[idx]),
                "embedding_score": int(all_embedding_scores[idx]),
                "technical_score": technical_score,
                "general_score": general_score,
                "score": final_score,
                "penalty": penalty,
                "boost": boost,
                "matched_skills": all_matched_keywords[idx],
                "group_analysis": all_group_results[idx],
                "description_preview": job_data['sections'].get('description', '')[:300],
                "index": idx
            })
        
        # ==========================================
        # محاسبه Outlier Score (با CDF اصلاح شده)
        # ==========================================
        for result in results:
            result['outlier_score'] = calculate_outlier_score(all_scores, result['score'])
        
        # فیلتر بر اساس امتیاز
        min_score = FILTERS.get('min_score', 20)
        filtered_results = [r for r in results if r['score'] >= min_score]
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        # ==========================================
        # ذخیره نتایج
        # ==========================================
        json_filename = f"output/job_matches_v6.1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(filtered_results, f, ensure_ascii=False, indent=2)
        
        html_filename = f"output/job_report_v6.1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
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
                print(f"   🎯 Technical: {job.get('technical_score', 0)}% | 📋 General: {job.get('general_score', 0)}%")
                print(f"   📊 Embedding: {job['embedding_score']}% | TF-IDF: {job['tfidf_score']}%")
                if job.get('penalty', 0) > 0:
                    print(f"   ⚠️  Penalty: -{job['penalty']}% | Boost: +{job.get('boost', 0)}%")
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
