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
    
    # محاسبه آمار
    total = len(jobs)
    scores = [j.get('score', 0) for j in jobs]
    avg_score = sum(scores) / total if total > 0 else 0
    max_score = max(scores) if scores else 0
    high = len([s for s in scores if s >= 50])
    medium = len([s for s in scores if 20 <= s < 50])
    low = len([s for s in scores if 0 < s < 20])
    
    # ساخت کارت‌های آگهی
    jobs_html = ""
    for i, job in enumerate(jobs, 1):
        score = job.get('score', 0)
        title = job.get('title', 'عنوان نامشخص')
        company = job.get('company', 'نامشخص')
        url = job.get('url', '#')
        skills = job.get('matched_skills', [])
        full_text = job.get('full_text', '')
        
        if score >= 50:
            score_class = "score-high"
        elif score >= 20:
            score_class = "score-medium"
        else:
            score_class = "score-low"
        
        skills_html = ""
        for skill in skills[:10]:
            skills_html += f'<span class="skill-tag">{skill}</span>'
        
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
            <a href="{url}" target="_blank" class="job-link">🔗 مشاهده آگهی در سایت</a>
        </div>
        """
    
    html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
    <title>گزارش تطابق آگهی‌های استخدام</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', 'Vazir', Tahoma, 'Helvetica Neue', sans-serif;
            background: #f0f4f8;
            padding: 12px;
            color: #2d3748;
            min-height: 100vh;
            -webkit-text-size-adjust: 100%;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }}
        
        /* ========== HEADER ========== */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 24px;
            border-radius: 16px;
            margin-bottom: 24px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 22px;
            margin-bottom: 6px;
            word-break: break-word;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 14px;
            margin: 4px 0;
        }}
        
        .header .file-name {{
            font-size: 12px;
            opacity: 0.7;
            margin-top: 6px;
            word-break: break-all;
        }}
        
        /* ========== STATS ========== */
        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 24px;
        }}
        
        .stat-box {{
            background: white;
            padding: 14px 8px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        
        .stat-box .number {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            display: block;
        }}
        
        .stat-box .label {{
            font-size: 11px;
            color: #718096;
            margin-top: 4px;
            display: block;
        }}
        
        .stat-box.high .number {{ color: #48bb78; }}
        .stat-box.medium .number {{ color: #ed8936; }}
        .stat-box.low .number {{ color: #fc8181; }}
        
        /* ========== JOB CARDS ========== */
        .job-card {{
            background: white;
            border-radius: 12px;
            padding: 16px 18px;
            margin-bottom: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-right: 4px solid #667eea;
            transition: all 0.2s;
        }}
        
        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 4px;
            flex-wrap: wrap;
        }}
        
        .job-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2d3748;
            flex: 1;
            word-break: break-word;
        }}
        
        .job-score {{
            padding: 2px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 13px;
            color: white;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        
        .score-high {{ background: #48bb78; }}
        .score-medium {{ background: #ed8936; }}
        .score-low {{ background: #fc8181; }}
        
        .job-company {{
            color: #718096;
            font-size: 14px;
            margin: 4px 0 10px 0;
        }}
        
        .job-skills {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 8px 0 10px 0;
        }}
        
        .skill-tag {{
            background: #ebf8ff;
            color: #2b6cb0;
            padding: 4px 12px;
            border-radius: 14px;
            font-size: 12px;
            border: 1px solid #bee3f8;
            white-space: nowrap;
        }}
        
        .job-preview {{
            color: #4a5568;
            font-size: 13px;
            line-height: 1.7;
            padding: 10px 12px;
            background: #f7fafc;
            border-radius: 8px;
            margin: 8px 0 10px 0;
            max-height: 90px;
            overflow: hidden;
            position: relative;
            word-break: break-word;
        }}
        
        .job-preview::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 35px;
            background: linear-gradient(transparent, #f7fafc);
        }}
        
        .job-link {{
            display: inline-block;
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
            padding: 8px 0;
            font-weight: 500;
            -webkit-tap-highlight-color: transparent;
        }}
        
        .job-link:active {{
            opacity: 0.6;
        }}
        
        .no-match {{
            text-align: center;
            padding: 40px 20px;
            background: white;
            border-radius: 12px;
            color: #718096;
        }}
        
        .no-match .icon {{ font-size: 48px; margin-bottom: 12px; }}
        
        .footer {{
            text-align: center;
            color: #a0aec0;
            font-size: 11px;
            margin-top: 24px;
            padding: 16px 0;
            border-top: 1px solid #e2e8f0;
        }}
        
        /* ========== RESPONSIVE ========== */
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .header {{ padding: 16px 18px; }}
            .header h1 {{ font-size: 19px; }}
            .header p {{ font-size: 13px; }}
            
            .stats {{
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
            }}
            
            .stat-box {{ padding: 12px 6px; }}
            .stat-box .number {{ font-size: 20px; }}
            .stat-box .label {{ font-size: 10px; }}
            
            .job-card {{ padding: 14px; }}
            .job-title {{ font-size: 15px; }}
            .job-score {{ font-size: 12px; padding: 2px 12px; }}
            .job-preview {{ font-size: 12px; max-height: 80px; }}
            .skill-tag {{ font-size: 11px; padding: 3px 10px; }}
        }}
        
        @media (max-width: 480px) {{
            body {{ padding: 8px; }}
            .header h1 {{ font-size: 17px; }}
            .stats {{
                grid-template-columns: repeat(2, 1fr);
                gap: 6px;
            }}
            .stat-box .number {{ font-size: 18px; }}
            .job-title {{ font-size: 14px; }}
            .job-header {{
                flex-direction: column;
                align-items: stretch;
                gap: 6px;
            }}
            .job-score {{ align-self: flex-start; }}
            .job-preview {{ font-size: 12px; max-height: 70px; }}
        }}
        
        @media (max-width: 360px) {{
            .stats {{
                grid-template-columns: repeat(2, 1fr);
                gap: 4px;
            }}
            .stat-box {{ padding: 8px 4px; }}
            .stat-box .number {{ font-size: 16px; }}
            .stat-box .label {{ font-size: 9px; }}
            .job-card {{ padding: 10px; }}
            .job-title {{ font-size: 13px; }}
            .skill-tag {{ font-size: 10px; padding: 2px 8px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 گزارش تطابق آگهی‌های استخدام</h1>
            <p>بر اساس مهارت‌های شما • {datetime.now().strftime('%Y/%m/%d %H:%M')}</p>
            <p class="file-name">📄 {os.path.basename(json_file)}</p>
        </div>
        
        <div class="stats">
            <div class="stat-box"><span class="number">{total}</span><span class="label">📌 کل آگهی‌ها</span></div>
            <div class="stat-box"><span class="number">{avg_score:.0f}%</span><span class="label">⭐ میانگین تطابق</span></div>
            <div class="stat-box"><span class="number">{max_score}%</span><span class="label">🔺 بالاترین امتیاز</span></div>
            <div class="stat-box high"><span class="number">{high}</span><span class="label">🟢 تطابق بالا (۵۰%+)</span></div>
            <div class="stat-box medium"><span class="number">{medium}</span><span class="label">🟡 تطابق متوسط (۲۰-۴۹%)</span></div>
            <div class="stat-box low"><span class="number">{low}</span><span class="label">🔴 تطابق پایین (۱-۱۹%)</span></div>
        </div>
        
        {jobs_html if jobs else '<div class="no-match"><div class="icon">😕</div><h2>هیچ آگهی مرتبطی پیدا نشد!</h2></div>'}
        
        <div class="footer">
            تهیه شده توسط برنامه اسکرپ ای استخدام • {datetime.now().strftime('%Y/%m/%d')}
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ گزارش HTML در '{output_file}' ذخیره شد.")
    return output_file

if __name__ == "__main__":
    # پیدا کردن جدیدترین فایل JSON
    json_files = [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('job_matches_')]
    if json_files:
        latest = sorted(json_files, reverse=True)[0]
        convert_json_to_html(latest)
        print("✅ گزارش HTML با موفقیت ساخته شد!")
    else:
        print("❌ هیچ فایل JSON پیدا نشد!")
