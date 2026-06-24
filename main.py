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


# =========================
# CONFIG
# =========================
RESTART_EVERY = 120
SLEEP_RANGE = (2, 4)
PAGE_TIMEOUT = 25
PARTIAL_SAVE_EVERY = 100
MAX_FAILURE_RATE = 0.3


def restart_driver(driver):
    try:
        driver.quit()
    except:
        pass

    print("🔄 Restarting browser...")
    driver = setup_driver()
    return driver


def save_partial(all_jobs, count):
    """ذخیره موقت داده‌ها"""
    try:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"output/partial_{count}_{ts}.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        print(f"💾 Partial save at {count}")
    except:
        pass


def main():
    os.makedirs("output", exist_ok=True)

    print("=" * 80)
    print("🚀 JOB MATCHER v7 - STABLE MODE (Production Ready)")
    print("=" * 80)

    # =========================
    # Semantic Model
    # =========================
    print("\n🔄 Loading Semantic Model...")
    semantic_matcher = SemanticMatcher(EMBEDDING_MODEL)

    if not semantic_matcher.is_loaded:
        print("⚠️ Semantic matching disabled")

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
            'max_pages': None
        }
    ]

    driver = setup_driver()
    all_jobs = []

    try:
        for site in sites_config:
            print(f"\n🔄 Scraping {site['name']}")

            driver.get(site['url'])
            time.sleep(3)

            # =========================
            # JOBVISION
            # =========================
            if site['type'] == 'jobvision':
                scraper = JobvisionScraper(driver)
                jobs = scraper.extract_all_pages(max_pages=site.get('max_pages'))

                if not jobs:
                    print("⚠️ No jobs found")
                    continue

                print(f"🔍 {len(jobs)} jobs found")

                successful = 0
                failed = 0
                total_processed = 0

                for i, job in enumerate(jobs, 1):
                    total_processed += 1

                    # progress
                    if i % 50 == 0 or i == 1:
                        print(f"Progress: {i}/{len(jobs)} | OK: {successful} | Fail: {failed}")

                    # =========================
                    # RESTART (ساده و پایدار)
                    # =========================
                    if i % RESTART_EVERY == 0:
                        driver = restart_driver(driver)
                        # فقط scraper جدید کافی است (بدون driver.get(site['url']))
                        scraper = JobvisionScraper(driver)

                    # =========================
                    # FAILURE TRACKING
                    # =========================
                    if total_processed > 20 and failed / total_processed > MAX_FAILURE_RATE:
                        print(f"⚠️ Too many failures ({failed}/{total_processed}), stopping...")
                        break

                    try:
                        driver.set_page_load_timeout(PAGE_TIMEOUT)

                        detail = scraper.extract_job_detail(job['url'])

                        # ====== 📌 آزادسازی حافظه ======
                        driver.get('about:blank')

                        if detail.get('error'):
                            failed += 1
                            continue

                        job['sections'] = {
                            'full_text': detail.get('full_text', ''),
                            'title': job.get('title', ''),
                            'description': detail.get('description', ''),
                            'requirements': detail.get('requirements', ''),
                            'company': job.get('company', '')
                        }

                        job['skills'] = detail.get('skills', [])
                        all_jobs.append(job)
                        successful += 1

                    except Exception as e:
                        failed += 1
                        print(f"❌ Error {i}: {str(e)[:60]}")

                        if "timeout" in str(e).lower():
                            driver = restart_driver(driver)
                            scraper = JobvisionScraper(driver)  # ← اصلاح شد

                    finally:
                        time.sleep(random.uniform(*SLEEP_RANGE))

                    # =========================
                    # PARTIAL SAVE
                    # =========================
                    if i % PARTIAL_SAVE_EVERY == 0:
                        save_partial(all_jobs, i)

                print(f"✅ Done: {successful} success | {failed} failed")

            # =========================
            # DEFAULT
            # =========================
            else:
                jobs = extract_all_jobs(driver, site['url'])
                all_jobs.extend(jobs)
                print(f"✅ {len(jobs)} jobs extracted")

        if not all_jobs:
            print("❌ No jobs found")
            return

        print(f"\n✅ Total jobs: {len(all_jobs)}")

        # =========================
        # SCORING
        # =========================
        job_texts = []
        for job in all_jobs:
            s = job.get('sections', {})
            job_texts.append(f"{s.get('title','')} {s.get('description','')} {s.get('requirements','')}")

        print("🧠 Embeddings...")
        if semantic_matcher.is_loaded:
            embedding_scores = semantic_matcher.calculate_batch_similarity(
                job_texts, RESUME_TEXT
            )
        else:
            embedding_scores = [0] * len(all_jobs)

        print("📊 Scoring...")
        results = []
        all_scores = []
        all_tfidf_scores = []

        for idx, job in enumerate(all_jobs):
            s = job.get('sections', {})

            keyword_score, matched_keywords, _ = calculate_keyword_score(
                s.get('full_text', ''),
                s.get('requirements', ''),
                s.get('description', ''),
                s.get('title', '')
            )

            tfidf_score = semantic_match_score(
                f"{s.get('title','')} {s.get('description','')}",
                RESUME_TEXT,
                matched_keywords
            )

            all_tfidf_scores.append(tfidf_score)

            embedding_score = embedding_scores[idx]

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

            final = scores['final']
            all_scores.append(final)

            results.append({
                "title": job.get('title'),
                "company": job.get('company'),
                "url": job.get('url'),
                "score": final,
                "matched_skills": matched_keywords
            })

        # outlier
        for r in results:
            r['outlier_score'] = calculate_outlier_score(all_scores, r['score'])

        # filter
        filtered = [r for r in results if r['score'] >= FILTERS.get('min_score', 20)]
        filtered.sort(key=lambda x: x['score'], reverse=True)

        # =========================
        # SAVE
        # =========================
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        json_file = f"output/job_matches_v7_{ts}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)

        html_file = f"output/job_report_v7_{ts}.html"
        generate_html_report(filtered, html_file)

        print(f"\n📁 {json_file}")
        print(f"📄 {html_file}")

        print(f"\n🏆 TOP 10:")
        for i, j in enumerate(filtered[:10], 1):
            print(f"{i}. {j['score']}% - {j['title']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")


if __name__ == "__main__":
    main()
