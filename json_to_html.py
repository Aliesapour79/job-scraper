import json
import os
from datetime import datetime


def convert_json_to_html(json_file, output_file=None):
    """Convert JSON job data to responsive HTML report (v3.1 compatible)"""

    if not output_file:
        output_file = json_file.replace('.json', '_report.html')

    # ==========================================
    # LOAD JSON
    # ==========================================
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except Exception as e:
        print(f"❌ خطا در خواندن فایل: {e}")
        return None

    if not jobs:
        print("❌ هیچ دیتایی وجود ندارد")
        return None

    # ==========================================
    # STATS
    # ==========================================
    total = len(jobs)
    scores = [j.get('score', 0) for j in jobs]

    avg_score = sum(scores) / total if total else 0
    max_score = max(scores) if scores else 0

    high = len([s for s in scores if s >= 60])
    medium = len([s for s in scores if 30 <= s < 60])
    low = len([s for s in scores if s < 30])

    # ==========================================
    # JOB CARDS
    # ==========================================
    jobs_html = ""

    for i, job in enumerate(jobs, 1):
        score = job.get("score", 0)
        title = job.get("title", "عنوان نامشخص")
        company = job.get("company", "نامشخص")
        url = job.get("url", "#")
        full_text = job.get("full_text", "")

        # score color
        if score >= 70:
            score_class = "score-high"
        elif score >= 40:
            score_class = "score-medium"
        else:
            score_class = "score-low"

        # preview
        preview = full_text[:320].replace("\n", " ").strip()
        if len(full_text) > 320:
            preview += "..."

        jobs_html += f"""
        <div class="job-card">
            <div class="job-header">
                <div class="job-title">{i}. {title}</div>
                <div class="job-score {score_class}">⭐ {score:.1f}%</div>
            </div>

            <div class="job-company">🏢 {company}</div>

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
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Job Match Report</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {{
            font-family: Tahoma;
            background: #f4f6f8;
            margin: 0;
            padding: 12px;
        }}

        .container {{
            max-width: 1000px;
            margin: auto;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 16px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 16px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }}

        .stat-box {{
            background: white;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
        }}

        .stat-box .number {{
            font-size: 20px;
            font-weight: bold;
        }}

        .job-card {{
            background: white;
            padding: 14px;
            margin-bottom: 10px;
            border-radius: 12px;
            border-right: 4px solid #667eea;
        }}

        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .job-title {{
            font-weight: bold;
            font-size: 15px;
        }}

        .job-score {{
            padding: 4px 10px;
            border-radius: 20px;
            color: white;
            font-size: 12px;
        }}

        .score-high {{ background: #2ecc71; }}
        .score-medium {{ background: #f39c12; }}
        .score-low {{ background: #e74c3c; }}

        .job-company {{
            color: gray;
            margin-top: 4px;
            font-size: 13px;
        }}

        .job-preview {{
            margin-top: 8px;
            font-size: 13px;
            color: #444;
            line-height: 1.6;
        }}

        .job-link {{
            display: inline-block;
            margin-top: 8px;
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>

<body>
<div class="container">

    <div class="header">
        <h2>📊 Job Match Report</h2>
        <p>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <div class="number">{total}</div>
            <div>Jobs</div>
        </div>

        <div class="stat-box">
            <div class="number">{avg_score:.1f}%</div>
            <div>Average</div>
        </div>

        <div class="stat-box">
            <div class="number">{max_score:.1f}%</div>
            <div>Best Match</div>
        </div>
    </div>

    {jobs_html}

</div>
</body>
</html>
"""

    # ==========================================
    # SAVE FILE
    # ==========================================
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ HTML saved: {output_file}")
    return output_file


if __name__ == "__main__":
    json_files = [f for f in os.listdir(".") if f.startswith("job_matches_") and f.endswith(".json")]

    if json_files:
        latest = sorted(json_files)[-1]
        convert_json_to_html(latest)
        print("✅ Done!")
    else:
        print("❌ No JSON found")
