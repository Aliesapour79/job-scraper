import json
from datetime import datetime
import os
import time
import random
import traceback

from config import (
    EMBEDDING_MODEL,
    FILTERS,
    RESUME_TEXT
)

from matcher import (
    calculate_final_score_v63,
    calculate_keyword_score,
    semantic_match_score,
    calculate_outlier_score
)

from scrapers import JobvisionScraper, EEstekhdamScraper
from report import generate_html_report
from matcher.semantic_matcher import SemanticMatcher
from utils import setup_driver

# =========================
# 📌 اضافه کردن import دیتابیس
# =========================
from utils.database import save_job, get_stats, init_db


# =========================
# CONFIG (Stable Production)
# =========================
RESTART_EVERY = 30
SLEEP_RANGE = (2, 4)
PAGE_TIMEOUT = 90
MAX_FAILURE_RATE = 0.25
PARTIAL_SAVE_EVERY = 50
MAX_EMPTY_PAGES = 2

# =========================
# 🎯 FLAGS: کنترل بخش‌های مختلف
# =========================
ENABLE_PROCESSING = False   # پردازش و امتیازدهی (Embedding, TF-IDF, Scoring)
ENABLE_OUTPUT = False       # تولید خروجی (JSON + HTML + Statistics)
ENABLE_DB_SAVE = True       # 📌 جدید: ذخیره در دیتابیس


# =========================
# DRIVER RESTART
# =========================
def restart_driver(driver):
    """Restart Chrome driver to free memory"""
    print("🔄 Restarting Chrome driver...")
    try:
        driver.quit()
    except:
        pass

    time.sleep(2)
    return setup_driver()


# =========================
# PARTIAL SAVE
# =========================
def save_partial(all_jobs, count):
    """Save partial results to prevent data loss"""
    try:
        os.makedirs("output", exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        with open(f"output/partial_{count}_{ts}.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)

        print(f"💾 Partial save at {count}")
    except:
        pass


# =========================
# 📌 ذخیره خط به خط در دیتابیس
# =========================
def save_job_to_db(job, site_name):
    """ذخیره یک آگهی در دیتابیس (خط به خط)"""
    if not ENABLE_DB_SAVE:
        return False
    
    try:
        # تنظیم اطلاعات برای ذخیره
        job['site'] = site_name
        
        # ذخیره در دیتابیس
        result = save_job(job)
        
        if result:
            print(f"     💾 Saved to DB")
        else:
            print(f"     🔄 Duplicate (already in DB)")
        
        return result
    except Exception as e:
        print(f"     ❌ DB error: {e}")
        return False


# =========================
# MAIN
# =========================
def main():
    os.makedirs("output", exist_ok=True)

    print("=" * 80)
    print("🚀 JOB MATCHER v7 - STABLE PRODUCTION MODE")
    print("   (Multi-Site: e-estekhdam + Jobvision)")
    print("=" * 80)

    # نمایش وضعیت Flagها
    print(f"\n📋 MODE STATUS:")
    print(f"   🧠 Processing (Scoring): {'✅ ENABLED' if ENABLE_PROCESSING else '❌ DISABLED'}")
    print(f"   📤 Output (JSON/HTML):  {'✅ ENABLED' if ENABLE_OUTPUT else '❌ DISABLED'}")
    print(f"   💾 Database Save:      {'✅ ENABLED' if ENABLE_DB_SAVE else '❌ DISABLED'}")
    print("=" * 80)

    # =========================
    # LOAD MODEL
    # =========================
    if ENABLE_PROCESSING:
        print("\n🔄 Loading Semantic Model...")
        semantic_matcher = SemanticMatcher(EMBEDDING_MODEL)

        if not semantic_matcher.is_loaded:
            print("⚠️ Semantic matching disabled (install sentence-transformers)")
    else:
        print("\n⏭️ Skipping Semantic Model (Processing disabled)")
        semantic_matcher = None

    # =========================
    # INIT DATABASE (اگر فعال باشد)
    # =========================
    if ENABLE_DB_SAVE:
        print("\n📁 Initializing database...")
        init_db()
        print("✅ Database ready")

    # =========================
    # SITE CONFIGURATION
    # =========================
    sites_config = [
    {
        'name': 'jobvision-developer',
        'url': "https://jobvision.ir/jobs/category/developer-in-all-cities-of-tehran",
        'type': 'jobvision',
        'max_pages': 100,
        'job_category': 'توسعه نرم افزار و برنامه نویسی'
    },
    {
        'name': 'jobvision-data-science',
        'url': "https://jobvision.ir/jobs/category/data-science-in-all-cities-of-tehran",
        'type': 'jobvision',
        'max_pages': 100,
        'job_category': 'علوم داده / هوش مصنوعی'
    },
    {
        'name': 'jobvision-secretary',
        'url': "https://jobvision.ir/jobs/category/secretary-in-all-cities-of-tehran",
        'type': 'jobvision',
        'max_pages': 100,
        'job_category': 'مسئول دفتر / کارمند اداری'
    },
    {
        'name': 'jobvision-hr',
        'url': "https://jobvision.ir/jobs/category/human-resources-in-all-cities-of-tehran",
        'type': 'jobvision',
        'max_pages': 100,
        'job_category': 'منابع انسانی'
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

            # =========================
            # JOBVISION SCRAPER
            # =========================
            if site['type'] == 'jobvision':
                scraper = JobvisionScraper(driver)

                jobs = scraper.extract_all_pages(
                    max_pages=site.get('max_pages', 100)
                )

                if not jobs:
                    print("⚠️ No jobs found")
                    continue

                print(f"🔍 {len(jobs)} jobs found")
                print("⏱️ Extracting details... (this will take ~45-60 min)")

                successful = 0
                failed = 0
                db_saved = 0
                db_duplicate = 0

                for i, job in enumerate(jobs, 1):

                    if i % 50 == 0 or i == 1:
                        print(f"     Progress: {i}/{len(jobs)} | OK: {successful} | Fail: {failed} | DB: {db_saved}")

                    if i > 20 and failed / i > MAX_FAILURE_RATE:
                        print(f"⚠️ Failure rate too high ({failed}/{i}), stopping batch")
                        break

                    if i % RESTART_EVERY == 0:
                        print(f"     🔄 Restart at {i}...")
                        driver = restart_driver(driver)
                        scraper = JobvisionScraper(driver)
                        driver.get(site['url'])
                        time.sleep(3)

                    try:
                        driver.set_page_load_timeout(PAGE_TIMEOUT)
                        driver.set_script_timeout(PAGE_TIMEOUT)

                        detail = scraper.extract_job_detail(job['url'])

                        driver.get('about:blank')

                        if not detail or detail.get("error"):
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
                        job['site'] = site['name']
                        
                        all_jobs.append(job)
                        successful += 1

                        # =========================
                        # 💾 ذخیره در دیتابیس (خط به خط)
                        # =========================
                        if ENABLE_DB_SAVE:
                            result = save_job(job)
                            if result:
                                db_saved += 1
                            else:
                                db_duplicate += 1

                    except Exception as e:
                        failed += 1
                        msg = str(e).lower()
                        print(f"     ❌ Error {i}: {msg[:80]}")

                        if "timeout" in msg or "crash" in msg:
                            driver = restart_driver(driver)
                            scraper = JobvisionScraper(driver)
                            driver.get(site['url'])
                            time.sleep(3)

                    finally:
                        time.sleep(random.uniform(*SLEEP_RANGE))

                    if i % PARTIAL_SAVE_EVERY == 0:
                        save_partial(all_jobs, i)

                print(f"✅ Done: {successful} success | {failed} failed | DB Saved: {db_saved} | DB Duplicate: {db_duplicate}")
                print(f"✅ Extracted {successful} jobs from {site['name']}")

            # =========================
            # E-ESTEKHDAM SCRAPER
            # =========================
            elif site['type'] == 'e_estekhdam':
                scraper = EEstekhdamScraper(driver)
                
                scraper.url = site['url']
                
                jobs = scraper.extract_all_jobs()

                if not jobs:
                    print("⚠️ No jobs found")
                    continue

                print(f"✅ Extracted {len(jobs)} jobs from {site['name']}")
                
                # ذخیره آگهی‌های e-estekhdam در دیتابیس
                db_saved = 0
                db_duplicate = 0
                for job in jobs:
                    job['site'] = site['name']
                    all_jobs.append(job)
                    
                    if ENABLE_DB_SAVE:
                        result = save_job(job)
                        if result:
                            db_saved += 1
                        else:
                            db_duplicate += 1
                
                print(f"   💾 DB Saved: {db_saved} | DB Duplicate: {db_duplicate}")

        # =========================
        # FINAL CHECK
        # =========================
        if not all_jobs:
            print("❌ No jobs found")
            return

        print(f"\n✅ TOTAL JOBS EXTRACTED: {len(all_jobs)}")

        # نمایش آمار دیتابیس
        if ENABLE_DB_SAVE:
            stats = get_stats()
            print(f"\n📈 Database Statistics:")
            print(f"   📋 Total Jobs: {stats['total_jobs']}")
            print(f"   🏢 Total Companies: {stats['total_companies']}")
            print(f"   📍 Total Cities: {stats['total_cities']}")
            print(f"   📅 Last Week: {stats['last_week']}")
            print(f"   ⚡ Urgent: {stats['urgent']}")

        # =========================
        # 🎯 SKIP PROCESSING IF DISABLED
        # =========================
        if not ENABLE_PROCESSING:
            print("\n⏭️ Processing (Scoring) is DISABLED.")
            print("   Data extracted successfully. Run with ENABLE_PROCESSING=True to score.")
            print(f"   Extracted {len(all_jobs)} jobs ready for processing.")
            return

        # =========================
        # PREPARE FOR SCORING
        # =========================
        print("\n🔄 Calculating match scores...")
        print("   This may take a few minutes...")

        job_texts = []
        for job in all_jobs:
            s = job.get('sections', {})
            job_texts.append(
                f"{s.get('title','')} {s.get('description','')} {s.get('requirements','')}"
            )

        # =========================
        # EMBEDDINGS
        # =========================
        print("  🧠 Running embeddings...")
        embedding_scores = (
            semantic_matcher.calculate_batch_similarity(job_texts, RESUME_TEXT)
            if semantic_matcher.is_loaded
            else [0] * len(all_jobs)
        )

        # =========================
        # SCORING
        # =========================
        print("  📊 Scoring jobs...")
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

            scores = calculate_final_score_v63(
                idx=idx,
                job_text=job_texts[idx],
                resume_text=RESUME_TEXT,
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

        # =========================
        # OUTLIER DETECTION
        # =========================
        print("  📊 Calculating outlier scores...")
        for r in results:
            r['outlier_score'] = calculate_outlier_score(all_scores, r['score'])

        # =========================
        # FILTER
        # =========================
        min_score = FILTERS.get('min_score', 20)
        filtered = [r for r in results if r['score'] >= min_score]
        filtered.sort(key=lambda x: x['score'], reverse=True)

        # =========================
        # 🎯 SKIP OUTPUT IF DISABLED
        # =========================
        if not ENABLE_OUTPUT:
            print("\n⏭️ Output (JSON/HTML) is DISABLED.")
            print(f"   Scores calculated for {len(filtered)} relevant jobs.")
            print("   Run with ENABLE_OUTPUT=True to generate files.")
            return

        # =========================
        # SAVE OUTPUT
        # =========================
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        json_file = f"output/job_matches_v7_{ts}.json"
        html_file = f"output/job_report_v7_{ts}.html"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)

        generate_html_report(filtered, html_file)

        # =========================
        # STATISTICS
        # =========================
        tech_count = sum(1 for r in filtered if r.get('category') == 'technical')
        admin_count = sum(1 for r in filtered if r.get('category') == 'administrative')
        hybrid_count = sum(1 for r in filtered if r.get('category') == 'hybrid')

        site_stats = {}
        for r in filtered:
            site = r.get('site', 'unknown')
            site_stats[site] = site_stats.get(site, 0) + 1

        print("\n" + "=" * 80)
        print(f"📁 JSON saved: {json_file}")
        print(f"📄 HTML saved: {html_file}")
        print("=" * 80)

        print(f"\n🎯 Found {len(filtered)} relevant jobs out of {len(all_jobs)} total")
        print(f"   🔧 Technical: {tech_count} | 🧾 Admin: {admin_count} | 🔀 Hybrid: {hybrid_count}")
        print(f"   📍 By site: {site_stats}")
        print("=" * 80)

        # =========================
        # TOP 10
        # =========================
        if filtered:
            print("\n🏆 TOP 10 MATCHING JOBS:\n")
            for i, job in enumerate(filtered[:10], 1):
                category_icon = "🔧" if job.get('category') == 'technical' else "🧾" if job.get('category') == 'administrative' else "🔀"
                site_tag = f"[{job.get('site', 'unknown')}]"

                print(f"{i}. {category_icon} {site_tag} {job['score']}% - {job['title']}")
                print(f"   🏢 {job['company']}")
                print(f"   🎯 Technical: {job.get('technical_score', 0)}% | 📋 General: {job.get('general_score', 0)}%")
                print(f"   📊 Outlier: {job.get('outlier_score', 0)}%")
                print(f"   🛠️  Skills: {', '.join(job.get('matched_skills', [])[:5])}")
                print()

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()

    finally:
        try:
            driver.quit()
        except:
            pass
        print("\n✅ Browser closed")


if __name__ == "__main__":
    main()