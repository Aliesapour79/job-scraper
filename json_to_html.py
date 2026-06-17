import json
import os
from datetime import datetime


def convert_json_to_html(json_file, output_file=None):
    """Convert JSON job data to beautiful responsive HTML report"""

    if not output_file:
        output_file = json_file.replace('.json', '_report.html')

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except Exception as e:
        print(f"❌ خطا در خواندن فایل: {e}")
        return None

    # ==========================================
    # STATISTICS
    # ==========================================
    total = len(jobs)
    scores = [j.get('score', 0) for j in jobs]

    avg_score = sum(scores) / total if total else 0
    max_score = max(scores) if scores else 0

    high = len([s for s in scores if s >= 50])
    medium = len([s for s in scores if 20 <= s < 50])
    low = len([s for s in scores if 0 < s < 20])

    # ==========================================
    # JOB CARDS
    # ==========================================
    jobs_html = ""

    for i, job in enumerate(jobs, 1):

        score = job.get('score', 0)
        title = job.get('title', 'عنوان نامشخص')
        company = job.get('company', 'نامشخص')
        url = job.get('url', '#')

        # ⚠️ در scorer جدید ممکنه وجود نداشته باشه
        skills = job.get('matched_skills', [])
        if not isinstance(skills, list):
            skills = []

        full_text = job.get('full_text', '')

        # score color
        if score >= 50:
            score_class = "score-high"
        elif score >= 20:
            score_class = "score-medium"
        else:
            score_class = "score-low"

        # skills HTML
        skills_html = ""
        for skill in skills[:10]:
            skills_html += f'<span class="skill-tag">{skill}</span>'

        # preview
        preview = full_text[:300].replace('\n', ' ').strip()
        if len(full_text) > 300:
            preview += "..."

        jobs_html += f"""
        <div class="job-card">
            <div class="job-header">
                <div class="job-title">{i}. {title}</div>
                <div class="job-score {score_class}">⭐ {score}%</div>
            </div>

            <div class="job-company">🏢 {company}</div>

            <div class="job-skills">{skills_html}</div>

            <div class="job-preview">{preview}</div>

            <a href="{url}" target="_blank" class="job-link">
                🔗 مشاهده آگهی در سایت
            </a>
        </div>
        """

    # ==========================================
    # HTML TEMPLATE
    # ==========================================
    html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>گزارش تطابق آگهی‌ها</title>

    <style>
        body {{
            font-family: Tahoma, sans-serif;
            background: #f5f7fb;
            margin: 0;
            padding: 10px;
        }}

        .container {{
            max-width: 1100px;
            margin: auto;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 15px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}

        .stat-box {{
            background: white;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
        }}

        .job-card {{
            background: white;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
            border-right: 4px solid #667eea;
        }}

        .job-header {{
            display: flex;
            justify-content: space-between;
        }}

        .job-title {{
            font-weight: bold;
        }}

        .job-score {{
            padding: 4px 10px;
            border-radius: 20px;
            color: white;
            font-size: 12px;
        }}

        .score-high {{ background: #22c55e; }}
        .score-medium {{ background: #f59e0b; }}
        .score-low {{ background: #ef4444; }}

        .job-company {{
            color: #666;
            margin: 5px 0;
        }}

        .job-skills {{
            margin: 8px 0;
        }}

        .skill-tag {{
            display: inline-block;
            background: #eef2ff;
            color: #4338ca;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px;
        }}

        .job-preview {{
            font-size: 12px;
            color: #444;
            background: #f9fafb;
            padding: 8px;
            border-radius: 8px;
        }}

        .job-link {{
            display: inline-block;
            margin-top: 8px;
            color: #4f46e5;
            text-decoration: none;
        }}
    </style>
</head>

<body>
<div class="container">

    <div class="header">
        <h2>📊 گزارش آگهی‌های استخدام</h2>
        <p>{datetime.now().strftime('%Y/%m/%d %H:%M')}</p>
    </div>

    <div class="stats">
        <div class="stat-box">📌 {total}<br>کل آگهی‌ها</div>
        <div class="stat-box">⭐ {avg_score:.0f}%<br>میانگین</div>
        <div class="stat-box">🔺 {max_score}%<br>بالاترین</div>
    </div>

    {jobs_html if jobs else "<p>هیچ آگهی پیدا نشد</p>"}

</div>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ HTML ساخته شد: {output_file}")
    return output_file


if __name__ == "__main__":
    json_files = [f for f in os.listdir('.') if f.startswith('job_matches_') and f.endswith('.json')]

    if json_files:
        latest = sorted(json_files)[-1]
        convert_json_to_html(latest)
    else:
        print("❌ فایل JSON پیدا نشد")
