import json
from datetime import datetime
import os
import time
import random

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
from matcher.semantic_matcher import SemanticMatcher
from utils import setup_driver


def main():
    os.makedirs("output", exist_ok=True)

    print("=" * 80)
    print("🚀 JOB MATCHER v7 - RESILIENT MODE")
    print("   (Weekly Full-Run: e-estekhdam + Jobvision All Pages)")
    print("=" * 80)

    # =========================
    # بارگذاری مدل Semantic
    # =========================
    print("\n🔄 Loading Semantic Model...")
    semantic_matcher = SemanticMatcher(EMBEDDING_MODEL)

    if not semantic_matcher.is_loaded:
        print("⚠️ Semantic matching disabled (install sentence-transformers)")

    # =========================
    # تنظیمات سایت‌ها
    # =========================
    sites_config = [
    {
        'name': 'e-estekhdam',
        'url': "https://www.e-estekhdam.com/search/%D8%A7%D8%B3%D8%AA%D8%AE%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1-%D8%AA%D9%87%D8%B1%D8%A7%D9%86",
        'type': 'default'
    },
    {
        'name': 'jobvision',
        'url': "https://jobvision.ir/jobs/category/developer-in-all-cities-of-tehran",
        'type': 'jobvision',
        'max_pages': None  # None = همه صفحات (برای اجرای هفتگی)
    }
]

    driver = setup_driver()
    all_jobs = []

    try:
        for site in sites_config:
            print(f"\n{'='*60}")
            print(f"🔄 Scraping {site['name']}")
            print(f"   URL: {site['url']}")
            print(f"{'='*60}")

            driver.get(site['url'])
            time.sleep(3)

            # ==========================================
            # JOBVISION SCRAPER (نسخه مقاوم)
            # ==========================================
            if site['type'] == 'jobvision':
                scraper = JobvisionScraper(driver)
                max_pages = site.get('max_pages', None)

                # استخراج همه صفحات با مدیریت خطا
                jobs = scraper.extract_all_pages(max_pages=max_pages)

                if not jobs:
                    print(f"⚠️ No jobs found in {site['name']}")
                    continue

                print(f"  🔍 Extracting details for {len(jobs)} jobs...")
                print(f"  ⏱️ This may take a while (~45-60 min for 886 jobs)...")

                successful = 0
                failed = 0

                for i, job in enumerate(jobs, 1):
                    # نمایش پیشرفت هر ۵۰ تا
                    if i % 50 == 0 or i == 1:
                        print(f"     Progress: {i}/{len(jobs)} (Success: {successful}, Failed: {failed})")

                    try:
                        # تنظیم timeout برای هر صفحه
                        driver.set_page_load_timeout(30)
                        detail = scraper.extract_job_detail(job['url'])

                        # اگر خطایی در detail وجود دارد، skip کن
                        if detail.get('error'):
                            failed += 1
                            job['error'] = detail['error']
                            continue

                        # ترکیب اطلاعات
                        job['sections'] = {
                            'full_text': detail.get('full_text', ''),
                            'title': job.get('title', ''),
                            'description': detail.get('description', ''),
                            'requirements': detail.get('requirements', ''),
                            'company': job.get('company', '')
                        }

                        job['skills'] = detail.get('skills', [])
                        job['error'] = None

                        all_jobs.append(job)
                        successful += 1

                    except Exception as e:
                        failed += 1
                        job['error'] = str(e)
                        print(f"     ❌ Error on job {i}: {str(e)[:80]}")

                    finally:
                        # تأخیر تصادفی بین ۲-۴ ثانیه
                        time.sleep(random.uniform(2, 4))

                    # اگر بیش از ۳۰٪ خطا داشتیم، متوقف شو
                    if failed > 100 or (i > 0 and failed / i > 0.3):
                        print(f"     ⚠️ Too many failures ({failed}/{i}), stopping...")
                        break

                print(f"  ✅ Completed: {successful} successful, {failed} failed")
                print(f"  ✅ Extracted {successful} jobs from {site['name']}")

            # ==========================================
            # DEFAULT SCRAPER (e-estekhdam)
            # ==========================================
            else:
                jobs = extract_all_jobs(driver, site['url'])
                all_jobs.extend(jobs)
                print(f"✅ Extracted {len(jobs)} jobs from {site['name']}")

        # =========================
        # اگر هیچ آگهی پیدا نشد
        # =========================
        if not all_jobs:
            print("❌ No jobs found!")
            return

        print(f"\n✅ Total jobs extracted: {len(all_jobs)}")
        print("🔄 Calculating match scores...\n")

        # =========================
        # آماده‌سازی متن‌ها برای Embedding
        # =========================
        job_texts = []
        for job in all_jobs:
            sections = job.get('sections', {})
            text = f"""
            {sections.get('title', '')}
            {sections.get('description', '')}
            {sections.get('requirements', '')}
            {sections.get('full_text', '')}
            """
            job_texts.append(text)

        # =========================
        # محاسبه Embedding (Batch)
        # =========================
        print("  🧠 Calculating embeddings...")
        if semantic_matcher.is_loaded:
            embedding_scores = semantic_matcher.calculate_batch_similarity(
                job_texts,
                RESUME_TEXT
            )
        else:
            embedding_scores = [0] * len(all_jobs)

        # =========================
        # محاسبه امتیازها
        # =========================
        print("  📊 Calculating scores...")
        results = []
        all_scores = []
        all_tfidf_scores = []

        for idx, job in enumerate(all_jobs):
            sections = job.get('sections', {})

            # Keyword Score
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
            tfidf_score = semantic_match_score(
                combined_job_text,
                RESUME_TEXT,
                matched_keywords
            )
            all_tfidf_scores.append(tfidf_score)

            # Embedding Score
            embedding_score = embedding_scores[idx] if idx < len(embedding_scores) else 0

            # امتیاز نهایی
            scores = calculate_final_score_v63(
                idx=idx,
                job_text=job_texts[idx],
                resume_text=RESUME_TEXT,
                embedding_score=embedding_score,
                tfidf_score=tfidf_score,
                all_embedding_scores=embedding_scores,
                all_tfidf_scores=all_tfidf_scores,
                semantic_matcher=semantic_matcher,
                job_title=job.get('title', '')
            )

            final_score = scores['final']
            all_scores.append(final_score)

            results.append({
                "title": job.get('title', 'Unknown'),
                "company": job.get('company', 'Unknown'),
                "url": job.get('url', ''),
                "site": job.get('site', 'unknown'),
                "score": final_score,
                "technical_score": scores.get('technical', 0),
                "general_score": scores.get('general', 0),
                "embedding_score": int(embedding_score),
                "tfidf_score": int(tfidf_score),
                "keyword_score": keyword_score,
                "matched_skills": matched_keywords,
                "category": scores.get('category', 'technical'),
                "penalty": scores.get('penalty', 0),
                "boost": scores.get('boost', 0),
                "description_preview": sections.get('description', '')[:300],
                "error": job.get('error', None)
            })

        # =========================
        # محاسبه Outlier Score
        # =========================
        print("  📊 Calculating outlier scores...")
        for r in results:
            r['outlier_score'] = calculate_outlier_score(all_scores, r['score'])

        # =========================
        # فیلتر بر اساس امتیاز
        # =========================
        min_score = FILTERS.get('min_score', 20)
        filtered_results = [r for r in results if r['score'] >= min_score]
        filtered_results.sort(key=lambda x: x['score'], reverse=True)

        # =========================
        # ذخیره نتایج
        # =========================
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"output/job_matches_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(filtered_results, f, ensure_ascii=False, indent=2)

        html_file = f"output/job_report_{timestamp}.html"
        generate_html_report(filtered_results, html_file)

        # =========================
        # نمایش نتایج
        # =========================
        print("=" * 80)
        print(f"📁 JSON saved: {json_file}")
        print(f"📄 HTML saved: {html_file}")

        # آمار
        tech_count = sum(1 for r in filtered_results if r.get('category') == 'technical')
        admin_count = sum(1 for r in filtered_results if r.get('category') == 'administrative')
        hybrid_count = sum(1 for r in filtered_results if r.get('category') == 'hybrid')

        print(f"\n🎯 Found {len(filtered_results)} relevant jobs out of {len(all_jobs)} total")
        print(f"   🔧 Technical: {tech_count} | 🧾 Admin: {admin_count} | 🔀 Hybrid: {hybrid_count}")

        # آمار بر اساس سایت
        site_stats = {}
        for r in filtered_results:
            site = r.get('site', 'unknown')
            site_stats[site] = site_stats.get(site, 0) + 1
        print(f"   📍 By site: {site_stats}")
        print("=" * 80)

        # نمایش ۱۰ آگهی برتر
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
