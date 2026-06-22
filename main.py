import json
from datetime import datetime
import os
import time

# ==========================================
# ایمپورت‌های جدید از ساختار ماژولار
# ==========================================
from config import (
    SCORE_WEIGHTS,
    EMBEDDING_MODEL,
    FILTERS,
    RESUME_TEXT
)
from matcher import (
    calculate_final_score_v63,
    calculate_keyword_score,
    semantic_match_score,
    calculate_outlier_score,
    extract_all_jobs
)
from scrapers import JobvisionScraper
from report import generate_html_report
from matcher.semantic_matcher import SemanticMatcher, combine_scores
from utils import setup_driver

def main():
    # ایجاد پوشه خروجی
    os.makedirs("output", exist_ok=True)
    
    print("=" * 80)
    print("🚀 JOB MATCHER v6.3 - DUAL TRACK + HYBRID SCORING")
    print("   (Multi-Site Support: e-estekhdam + Jobvision - All Pages)")
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
    # تنظیمات سایت‌ها
    # ==========================================
    sites_config = [
        {
            'name': 'e-estekhdam',
            'url': "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%B4%D9%87%D8%B1-%D9%82%D8%AF%D8%B3",
            'type': 'default'
        },
        {
            'name': 'jobvision',
            'url': "https://jobvision.ir/jobs/category/developer-in-all-cities-of-tehran",
            'type': 'jobvision',
            'max_pages': 3  # None = همه صفحات, یا عدد مثل 3 برای تست
        }
    ]
    
    # ==========================================
    # Web Scraping
    # ==========================================
    driver = setup_driver()
    all_jobs = []
    
    try:
        for site in sites_config:
            print(f"\n{'='*60}")
            print(f"🔄 Scraping {site['name']}...")
            print(f"   URL: {site['url']}")
            print(f"{'='*60}")
            
            driver.get(site['url'])
            time.sleep(3)
            
            if site['type'] == 'jobvision':
                # ====== اسکرپر جاب‌ویژن (همه صفحات) ======
                scraper = JobvisionScraper(driver)
                
                # استخراج از همه صفحات
                max_pages = site.get('max_pages', None)
                jobs = scraper.extract_all_pages(max_pages=max_pages)
                
                if not jobs:
                    print(f"⚠️ No jobs found in {site['name']}")
                    continue
                
                # استخراج جزئیات برای هر آگهی
                print(f"  🔍 Extracting details for {len(jobs)} jobs...")
                print(f"  ⏱️ This may take a few minutes...")
                
                for i, job in enumerate(jobs, 1):
                    # نمایش پیشرفت هر ۱۰ تا
                    if i % 10 == 0 or i == 1:
                        print(f"     Progress: {i}/{len(jobs)}")
                    
                    detail = scraper.extract_job_detail(job['url'])
                    
                    # ترکیب اطلاعات
                    job['sections'] = {
                        'full_text': detail.get('full_text', ''),
                        'title': job.get('title', ''),
                        'description': detail.get('description', ''),
                        'requirements': detail.get('requirements', ''),
                        'company': job.get('company', '')
                    }
                    
                    # اضافه کردن مهارت‌ها برای نمایش
                    job['skills'] = detail.get('skills', [])
                    
                    # اضافه کردن به لیست
                    all_jobs.append(job)
                
                print(f"✅ Extracted {len(jobs)} jobs from {site['name']}")
                
            else:
                # ====== اسکرپر پیش‌فرض (e-estekhdam) ======
                jobs = extract_all_jobs(driver, site['url'])
                all_jobs.extend(jobs)
                print(f"✅ Extracted {len(jobs)} jobs from {site['name']}")
        
        if not all_jobs:
            print("❌ No jobs found!")
            return
        
        print(f"\n✅ Total: {len(all_jobs)} jobs extracted from all sites!")
        print("🔄 Calculating dual-track match scores...\n")
        
        results = []
        all_scores = []
        
        # جمع‌آوری متن آگهی‌ها برای Batch Embedding
        job_texts = []
        for job in all_jobs:
            sections = job.get('sections', {})
            job_text = f"""
            {sections.get('title', '')}
            {sections.get('description', '')}
            {sections.get('requirements', '')}
            {sections.get('full_text', '')}
            """
            job_texts.append(job_text)
        
        # محاسبه Batch Embedding (برای سرعت بیشتر)
        embedding_scores = []
        if semantic_matcher.is_loaded:
            print("  🧠 Calculating embeddings for all jobs...")
            embedding_scores = semantic_matcher.calculate_batch_similarity(
                job_texts, 
                RESUME_TEXT
            )
        else:
            embedding_scores = [0] * len(all_jobs)
        
        # ==========================================
        # مرحله ۱: محاسبه همه امتیازها
        # ==========================================
        print("  📊 Calculating scores for all jobs...")
        all_tfidf_scores = []
        all_embedding_scores = []
        all_job_texts = []
        all_job_titles = []
        all_keyword_scores = []
        all_matched_keywords = []
        all_group_results = []
        all_job_data = []
        
        for idx, job in enumerate(all_jobs):
            sections = job.get('sections', {})
            
            # Keyword Score (برای نمایش در گزارش)
            keyword_score, matched_keywords, group_results = calculate_keyword_score(
                sections.get('full_text', ''),
                sections.get('requirements', ''),
                sections.get('description', ''),
                sections.get('title', '') or job.get('title', '')
            )
            
            # TF-IDF Score
            combined_job_text = f"""
            {sections.get('title', '')}
            {sections.get('description', '')}
            {sections.get('requirements', '')}
            """
            tfidf_score = semantic_match_score(combined_job_text, RESUME_TEXT, matched_keywords)
            
            # Embedding Score
            embedding_score = embedding_scores[idx] if idx < len(embedding_scores) else 0
            
            # عنوان شغلی برای Context-Aware
            job_title = job.get('title', '')
            
            # ذخیره برای مرحله بعد
            all_job_texts.append(combined_job_text)
            all_job_titles.append(job_title)
            all_tfidf_scores.append(tfidf_score)
            all_embedding_scores.append(embedding_score)
            all_keyword_scores.append(keyword_score)
            all_matched_keywords.append(matched_keywords)
            all_group_results.append(group_results)
            all_job_data.append({
                "title": job_title,
                "company": job.get('company', ''),
                "url": job.get('url', ''),
                "sections": sections,
                "site": job.get('site', 'unknown'),
                "index": idx
            })
        
        # ==========================================
        # مرحله ۲: محاسبه امتیاز نهایی با v6.3 (Dual Track + Hybrid)
        # ==========================================
        print("🔄 Applying Dual Track scoring (Technical + Admin + Hybrid)...\n")
        
        for idx, job_data in enumerate(all_job_data):
            # محاسبه امتیاز نهایی با v6.3
            scores = calculate_final_score_v63(
                idx=idx,
                job_text=all_job_texts[idx],
                resume_text=RESUME_TEXT,
                embedding_score=all_embedding_scores[idx],
                tfidf_score=all_tfidf_scores[idx],
                all_embedding_scores=all_embedding_scores,
                all_tfidf_scores=all_tfidf_scores,
                semantic_matcher=semantic_matcher,
                job_title=all_job_titles[idx]
            )
            
            final_score = scores['final']
            technical_score = scores['technical']
            general_score = scores['general']
            boost = scores['boost']
            penalty = scores['penalty']
            category = scores['category']
            
            all_scores.append(final_score)
            
            # نمایش category در لاگ (فقط برای ۲۰ تا اول و آخر)
            if idx < 20 or idx >= len(all_job_data) - 5:
                category_icon = "🔧" if category == "technical" else "🧾" if category == "administrative" else "🔀"
                site_name = job_data.get('site', 'unknown')
                print(f"  📊 [{site_name}] Job {idx+1}: {category_icon} {category.upper()} | "
                      f"Technical={technical_score}% | General={general_score}% | "
                      f"Boost={boost}% | Penalty={penalty}% | Final={final_score}%")
            
            # ذخیره نتایج
            results.append({
                "title": job_data['title'],
                "company": job_data['company'],
                "url": job_data['url'],
                "site": job_data.get('site', 'unknown'),
                "keyword_score": all_keyword_scores[idx],
                "tfidf_score": int(all_tfidf_scores[idx]),
                "embedding_score": int(all_embedding_scores[idx]),
                "technical_score": technical_score,
                "general_score": general_score,
                "score": final_score,
                "penalty": penalty,
                "boost": boost,
                "category": category,
                "matched_skills": all_matched_keywords[idx],
                "group_analysis": all_group_results[idx],
                "description_preview": job_data['sections'].get('description', '')[:300],
                "index": idx
            })
        
        # ==========================================
        # محاسبه Outlier Score (با CDF اصلاح شده)
        # ==========================================
        print("  📊 Calculating outlier scores...")
        for result in results:
            result['outlier_score'] = calculate_outlier_score(all_scores, result['score'])
        
        # ==========================================
        # فیلتر بر اساس امتیاز (با حفظ آگهی‌های اداری)
        # ==========================================
        min_score = FILTERS.get('min_score', 20)
        
        # جدا کردن آگهی‌های اداری با امتیاز پایین
        admin_jobs = [r for r in results if r.get('category') == 'administrative' and r['score'] < min_score]
        other_jobs = [r for r in results if r.get('category') != 'administrative' or r['score'] >= min_score]
        
        # فیلتر کردن سایر آگهی‌ها
        filtered_results = [r for r in other_jobs if r['score'] >= min_score]
        
        # اضافه کردن آگهی‌های اداری (حتی با امتیاز پایین) با برچسب ویژه
        for admin_job in admin_jobs:
            admin_job['is_admin_safety'] = True
            filtered_results.append(admin_job)
        
        # مرتب‌سازی بر اساس امتیاز
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        # ==========================================
        # ذخیره نتایج
        # ==========================================
        json_filename = f"output/job_matches_v6.3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(filtered_results, f, ensure_ascii=False, indent=2)
        
        html_filename = f"output/job_report_v6.3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        generate_html_report(filtered_results, html_filename)
        
        # ==========================================
        # نمایش نتایج
        # ==========================================
        print("=" * 80)
        print(f"📁 Results saved to: {json_filename}")
        print(f"📄 HTML report: {html_filename}")
        
        # آمار دسته‌بندی
        tech_count = sum(1 for r in filtered_results if r.get('category') == 'technical')
        admin_count = sum(1 for r in filtered_results if r.get('category') == 'administrative')
        hybrid_count = sum(1 for r in filtered_results if r.get('category') == 'hybrid')
        
        print(f"🎯 Found {len(filtered_results)} relevant jobs out of {len(all_jobs)} total")
        print(f"   🔧 Technical: {tech_count} | 🧾 Admin: {admin_count} | 🔀 Hybrid: {hybrid_count}")
        
        # آمار بر اساس سایت
        site_stats = {}
        for r in filtered_results:
            site = r.get('site', 'unknown')
            site_stats[site] = site_stats.get(site, 0) + 1
        print(f"   📍 By site: {site_stats}")
        print("=" * 80)
        
        if filtered_results:
            print("\n🏆 TOP 10 MATCHING JOBS:\n")
            for i, job in enumerate(filtered_results[:10], 1):
                category_icon = "🔧" if job.get('category') == 'technical' else "🧾" if job.get('category') == 'administrative' else "🔀"
                site_tag = f"[{job.get('site', 'unknown')}]"
                safety_tag = " 🛡️" if job.get('is_admin_safety') else ""
                
                print(f"{i}. {category_icon} {site_tag} {job['score']}% - {job['title']}{safety_tag}")
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