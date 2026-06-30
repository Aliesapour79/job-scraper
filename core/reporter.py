# core/reporter.py
import json
from datetime import datetime

from report import generate_html_report


def generate_output(results, filters, enable_output=True):
    """تولید JSON و HTML"""
    if not enable_output:
        print("\n⏭️ Output (JSON/HTML) is DISABLED.")
        print(f"   Scores calculated for {len(results)} relevant jobs.")
        print("   Run with ENABLE_OUTPUT=True to generate files.")
        return results

    min_score = filters.get('min_score', 20)
    filtered = [r for r in results if r['score'] >= min_score]
    filtered.sort(key=lambda x: x['score'], reverse=True)

    if not filtered:
        print("⚠️ No jobs above min_score threshold")
        return filtered

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    json_file = f"output/job_matches_v7_{ts}.json"
    html_file = f"output/job_report_v7_{ts}.html"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    generate_html_report(filtered, html_file)

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

    print(f"\n🎯 Found {len(filtered)} relevant jobs out of {len(results)} total")
    print(f"   🔧 Technical: {tech_count} | 🧾 Admin: {admin_count} | 🔀 Hybrid: {hybrid_count}")
    print(f"   📍 By site: {site_stats}")
    print("=" * 80)

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

    return filtered