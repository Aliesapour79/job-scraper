from collections import deque
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
    print("🚀 JOB MATCHER v7 - RESILIENT MODE (Signal-Based)")
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
            # JOBVISION SCRAPER (نسخه Signal-Based)
            # ==========================================
            if site['type'] == 'jobvision':
                scraper = JobvisionScraper(driver)
                max_pages = site.get('max_pages', None)
                jobs = scraper.extract_all_pages(max_pages=max_pages)

                if not jobs:
                    print(f"⚠️ No jobs found in {site['name']}")
                    continue

                print(f"  🔍 Extracting details for {len(jobs)} jobs...")
                print(f"  ⏱️ This may take a while (~45-60 min for 886 jobs)...")

                # =========================
                # SIGNAL SYSTEM
                # =========================
                consecutive_timeouts = 0
                consecutive_failures = 0
                slow_requests = 0

                failure_window = deque(maxlen=20)
                last_restart_at = 0
                min_gap = 50

                successful = 0
                failed = 0

                for i, job in enumerate(jobs, 1):
                    # نمایش پیشرفت هر ۵۰ تا
                    if i % 50 == 0 or i == 1:
                        print(f"     Progress: {i}/{len(jobs)} (Success: {successful}, Failed: {failed})")

                    # =========================
                    # SIGNAL DECISION
                    # =========================
                    should_restart = False
                    reason = ""

                    failure_rate = failed / i if i > 0 else 0

                    # Priority 1: failure rate
                    if i > 20 and failure_rate > 0.20:
                        should_restart = True
                        reason = f"high failure rate {failure_rate:.1%}"

                    # Priority 2: consecutive failures
                    elif consecutive_failures >= 5:
                        should_restart = True
                        reason = f"{consecutive_failures} consecutive failures"

                    # Priority 3: timeout
                    elif consecutive_timeouts >= 3:
                        should_restart = True
                        reason = f"{consecutive_timeouts} timeouts"

                    # Priority 4: failure window
                    elif sum(failure_window) >= 6:
                        should_restart = True
                        reason = "failure spike (window)"

                    # Priority 5: slow requests
                    elif slow_requests >= 5:
                        should_restart = True
                        reason = "too many slow requests"

                    # Fallback
                    elif i - last_restart_at >= 150:
                        should_restart = True
                        reason = "fallback (150 requests)"

                    # =========================
                    # RESTART
                    # =========================
                    if should_restart and i - last_restart_at >= min_gap:
                        print(f"     🔄 Restart at {i} | {reason}")
                        driver.quit()
                        driver = setup_driver()
                        driver.get(site['url'])
                        time.sleep(3)
                        scraper = JobvisionScraper(driver)

                        consecutive_timeouts = 0
                        consecutive_failures = 0
                        slow_requests = 0
                        failure_window.clear()
                        last_restart_at = i

                    # =========================
                    # REQUEST
                    # =========================
                    try:
                        driver.set_page_load_timeout(30)

                        start = time.time()
                        detail = scraper.extract_job_detail(job['url'])
                        load_time = time.time() - start

                        is_slow = load_time > 10
                        is_error = detail.get('error') is not None

                        # update signals
                        if is_slow:
                            slow_requests += 1
                        else:
                            slow_requests = max(0, slow_requests - 1)

                        if is_error:
                            failed += 1
                            consecutive_failures += 1
                            failure_window.append(1)
                            job['error'] = detail['error']
                            continue
                        else:
                            successful += 1
                            consecutive_failures = 0
                            failure_window.append(0)

                        # timeout detection
                        if load_time > 30:
                            consecutive_timeouts += 1
                        else:
                            consecutive_timeouts = 0

                        # =========================
                        # SAVE JOB
                        # =========================
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

                    except Exception as e:
                        failed += 1
                        consecutive_failures += 1
                        failure_window.append(1)

                        if "timeout" in str(e).lower():
                            consecutive_timeouts += 1

                        print(f"     ❌ Error: {str(e)[:80]}")

                    finally:
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
            s = job.get('sections', {})
            job_texts.append(f"{s.get('title','')} {s.get('description','')} {s.get('requirements','')} {s.get('full_text','')}")

        # =========================
        # محاسبه Embedding (Batch)
        # =========================
        print("  🧠 Calculating embeddings...")
        if semantic_matcher.is_loaded:
            embedding_scores = semantic_matcher.calculate_batch_similarity(job_texts, RESUME_TEXT)
        else:
            embedding_scores = [0] * len(all_jobs)

        # =========================
        # محاسبه امتیازها
        # =========================
        print("  📊 Calculating scores...")
        results = []
        all_scores = []
        all_tfidf = []

        for i, job in enumerate(all_jobs):
            s = job.get('sections', {})

            keyword_score, matched, group_results = calculate_keyword_score(
                s.get('full_text', ''),
                s.get('requirements', ''),
                s.get('description', ''),
                s.get('title', '') or job.get('title', '')
            )

            tfidf = semantic_match_score(
                s.get('description', ''),
                RESUME_TEXT,
                matched
            )
            all_tfidf.append(tfidf)

            embed = embedding_scores[i]

            scores = calculate_final_score_v63(
                idx=i,
                job_text=job_texts[i],
                resume_text=RESUME_TEXT,
                embedding_score=embed,
                tfidf_score=tfidf,
                all_embedding_scores=embedding_scores,
                all_tfidf_scores=all_tfidf,
                semantic_matcher=semantic_matcher,
                job_title=job.get('title', '')
            )

            final = scores['final']
            all_scores.append(final)

            # محاسبه outlier
            outlier_score = calculate_outlier_score(all_scores, final)

            results.append({
                "title": job.get('title', 'Unknown'),
                "company": job.get('company', 'Unknown'),
                "url": job.get('url', ''),
                "site": job.get('site', 'unknown'),
                "score": final,
                "technical_score": scores.get('technical', 0),
                "general_score": scores.get('general', 0),
                "embedding_score": int(embed),
                "tfidf_score": int(tfidf),
                "keyword_score": keyword_score,
                "matched_skills": matched,
                "category": scores.get('category', 'technical'),
                "penalty": scores.get('penalty', 0),
                "boost": scores.get('boost', 0),
                "outlier_score": outlier_score,
                "description_preview": s.get('description', '')[:300],
                "error": job.get('error', None)
            })

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
        json_path = f"output/job_matches_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(filtered_results, f, ensure_ascii=False, indent=2)

        html_path = f"output/job_report_{timestamp}.html"
        generate_html_report(filtered_results, html_path)

        # =========================
        # نمایش نتایج
        # =========================
        print("=" * 80)
        print(f"📁 JSON saved: {json_path}")
        print(f"📄 HTML saved: {html_path}")

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

                print(f"{i}. {category_icon} {site_tag} {job['score']}% - {job['title']}")
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