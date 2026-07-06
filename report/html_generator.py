# report/html_generator.py
"""
تولید گزارش HTML - نسخه v8
با پشتیبانی از location, is_urgent, salary
"""

import json
from datetime import datetime
import os


def generate_html_report(results, filename="job_report.html"):
    """Generate beautiful HTML report with charts - v8"""
    
    # محاسبه‌ی آمار با مدیریت خطا
    total_jobs = len(results)
    best_score = results[0]['score'] if results and 'score' in results[0] else 0
    excellent_count = sum(1 for r in results if r.get('score', 0) > 70)
    outlier_count = sum(1 for r in results if r.get('outlier_score', 0) > 70)
    urgent_count = sum(1 for r in results if r.get('is_urgent', 0) == 1)
    
    # آمار دسته‌بندی
    tech_count = sum(1 for r in results if r.get('category') == 'technical')
    admin_count = sum(1 for r in results if r.get('category') == 'administrative')
    hybrid_count = sum(1 for r in results if r.get('category') == 'hybrid')
    
    # آمار موقعیت‌ها (Top 5)
    location_stats = {}
    for r in results:
        loc = r.get('location', 'نامشخص')
        location_stats[loc] = location_stats.get(loc, 0) + 1
    top_locations = sorted(location_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    
    html_content = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>گزارش تطبیق شغلی v8 - علی عیسی‌پور</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            padding-bottom: 30px;
            border-bottom: 3px solid #667eea;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 32px;
            color: #333;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 16px;
        }}
        .header .version-badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 16px;
            border-radius: 20px;
            font-size: 14px;
            margin-top: 8px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .stat-card .number {{
            font-size: 32px;
            font-weight: bold;
        }}
        .stat-card .label {{
            font-size: 13px;
            opacity: 0.9;
            margin-top: 3px;
        }}
        .stat-card.urgent {{
            background: linear-gradient(135deg, #f44336 0%, #c62828 100%);
        }}
        .stat-card.green {{
            background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%);
        }}
        .stat-card.orange {{
            background: linear-gradient(135deg, #ff9800 0%, #e65100 100%);
        }}
        
        .section-title {{
            font-size: 22px;
            font-weight: bold;
            padding: 12px 20px;
            border-radius: 12px;
            margin: 25px 0 15px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .section-title .count {{
            font-size: 16px;
            font-weight: normal;
            opacity: 0.7;
        }}
        .section-technical {{
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border-right: 5px solid #2e7d32;
        }}
        .section-administrative {{
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            border-right: 5px solid #e65100;
        }}
        .section-hybrid {{
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border-right: 5px solid #1565c0;
        }}
        
        .job-card {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border-right: 5px solid #667eea;
            transition: transform 0.2s;
        }}
        .job-card:hover {{
            transform: translateX(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .job-card.technical {{
            border-right-color: #2e7d32;
        }}
        .job-card.administrative {{
            border-right-color: #e65100;
        }}
        .job-card.hybrid {{
            border-right-color: #1565c0;
        }}
        
        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }}
        .job-title {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }}
        .job-company {{
            color: #666;
            font-size: 15px;
        }}
        .job-meta {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 5px;
        }}
        .job-meta-item {{
            background: #e9ecef;
            padding: 2px 12px;
            border-radius: 12px;
            font-size: 12px;
            color: #495057;
        }}
        .job-meta-item.urgent {{
            background: #ffebee;
            color: #c62828;
        }}
        .job-category-tag {{
            display: inline-block;
            padding: 2px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .job-category-tag.technical {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        .job-category-tag.administrative {{
            background: #fff3e0;
            color: #e65100;
        }}
        .job-category-tag.hybrid {{
            background: #e3f2fd;
            color: #1565c0;
        }}
        
        .score-badge {{
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 18px;
        }}
        .score-badge.high {{
            background: #28a745;
        }}
        .score-badge.medium {{
            background: #ffc107;
            color: #333;
        }}
        .score-badge.low {{
            background: #dc3545;
        }}
        
        .skill-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        .skill-tag {{
            background: #e9ecef;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            color: #495057;
        }}
        .skill-tag.matched {{
            background: #d4edda;
            color: #155724;
        }}
        .url-link {{
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
        }}
        .url-link:hover {{
            text-decoration: underline;
        }}
        
        .semantic-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 11px;
            background: #e3f2fd;
            color: #1976d2;
            margin-right: 5px;
        }}
        .technical-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 11px;
            background: #e8f5e9;
            color: #2e7d32;
            margin-right: 5px;
            font-weight: bold;
        }}
        .general-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 11px;
            background: #fff3e0;
            color: #e65100;
            margin-right: 5px;
            font-weight: bold;
        }}
        .penalty-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 11px;
            background: #ffebee;
            color: #c62828;
            margin-right: 5px;
        }}
        
        .no-jobs {{
            text-align: center;
            padding: 50px 20px;
            color: #666;
            font-size: 18px;
        }}
        @media (max-width: 600px) {{
            .job-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .score-badge {{
                margin-top: 10px;
            }}
        }}
        
        @media (prefers-color-scheme: dark) {{
            .container {{
                background: #1a1a2e;
            }}
            .header h1 {{
                color: #eee;
            }}
            .header .subtitle {{
                color: #aaa;
            }}
            .job-card {{
                background: #16213e;
            }}
            .job-title {{
                color: #eee;
            }}
            .job-company {{
                color: #aaa;
            }}
            .job-meta-item {{
                background: #2a2a4a;
                color: #ccc;
            }}
            .skill-tag {{
                background: #2a2a4a;
                color: #ccc;
            }}
            .skill-tag.matched {{
                background: #1a3a2a;
                color: #8f8;
            }}
            .semantic-badge {{
                background: #1a3a5a;
                color: #6af;
            }}
            .technical-badge {{
                background: #1a3a2a;
                color: #8f8;
            }}
            .general-badge {{
                background: #3a2a1a;
                color: #fa8;
            }}
            .penalty-badge {{
                background: #3a1a1a;
                color: #f88;
            }}
            .section-technical {{
                background: #1a3a2a;
            }}
            .section-administrative {{
                background: #3a2a1a;
            }}
            .section-hybrid {{
                background: #1a2a3a;
            }}
            .no-jobs {{
                color: #aaa;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 گزارش تطبیق شغلی v8</h1>
            <div class="subtitle">
                بر اساس رزومه‌ی علی عیسی‌پور شربیانی | 
                تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}
            </div>
            <div class="version-badge">⚡ v8 - Level-Based Matching</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="number">{total_jobs}</div>
                <div class="label">تعداد آگهی‌های مناسب</div>
            </div>
            <div class="stat-card green">
                <div class="number">{best_score}%</div>
                <div class="label">بهترین تطابق</div>
            </div>
            <div class="stat-card orange">
                <div class="number">{excellent_count}</div>
                <div class="label">تطابق عالی (&gt;۷۰%)</div>
            </div>
            <div class="stat-card urgent">
                <div class="number">{urgent_count}</div>
                <div class="label">⚡ آگهی‌های فوری</div>
            </div>
        </div>
        
        <!-- آمار دسته‌بندی -->
        <div style="display: flex; gap: 15px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap;">
            <span style="background: #e8f5e9; padding: 6px 18px; border-radius: 20px; color: #2e7d32;">
                🔧 Technical: {tech_count}
            </span>
            <span style="background: #fff3e0; padding: 6px 18px; border-radius: 20px; color: #e65100;">
                🧾 Admin: {admin_count}
            </span>
            <span style="background: #e3f2fd; padding: 6px 18px; border-radius: 20px; color: #1565c0;">
                🔀 Hybrid: {hybrid_count}
            </span>
        </div>
        
        <!-- موقعیت‌های برتر -->
        <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 25px;">
            <span style="font-size: 14px; color: #666;">📍 موقعیت‌های برتر:</span>
            {''.join(f'<span style="background: #e9ecef; padding: 4px 14px; border-radius: 12px; font-size: 13px;">{loc} ({count})</span>' for loc, count in top_locations)}
        </div>
"""

    if not results:
        html_content += """
        <div class="no-jobs">
            <p>😕 هیچ آگهی مناسبی پیدا نشد!</p>
            <p style="font-size: 14px; margin-top: 10px;">سعی کنید محدوده یا کلمات کلیدی را تغییر دهید.</p>
        </div>
        """
    else:
        # جدا کردن آگهی‌ها بر اساس دسته‌بندی
        tech_jobs = [j for j in results if j.get('category') == 'technical']
        admin_jobs = [j for j in results if j.get('category') == 'administrative']
        hybrid_jobs = [j for j in results if j.get('category') == 'hybrid']
        
        # 1. بخش Technical Jobs
        if tech_jobs:
            html_content += f"""
        <div class="section-technical" style="border-radius: 12px; padding: 5px 20px 20px 20px; margin-bottom: 20px;">
            <div class="section-title">
                🔧 شغل‌های تخصصی <span class="count">({len(tech_jobs)})</span>
            </div>
"""
            for job in tech_jobs[:15]:
                html_content += _render_job_card(job, "technical")
            html_content += """
        </div>
"""
        
        # 2. بخش Hybrid Jobs
        if hybrid_jobs:
            html_content += f"""
        <div class="section-hybrid" style="border-radius: 12px; padding: 5px 20px 20px 20px; margin-bottom: 20px;">
            <div class="section-title">
                🔀 شغل‌های ترکیبی <span class="count">({len(hybrid_jobs)})</span>
            </div>
"""
            for job in hybrid_jobs[:10]:
                html_content += _render_job_card(job, "hybrid")
            html_content += """
        </div>
"""
        
        # 3. بخش Administrative Jobs
        if admin_jobs:
            html_content += f"""
        <div class="section-administrative" style="border-radius: 12px; padding: 5px 20px 20px 20px; margin-bottom: 20px;">
            <div class="section-title">
                🧾 شغل‌های اداری <span class="count">({len(admin_jobs)})</span>
            </div>
"""
            for job in admin_jobs[:10]:
                html_content += _render_job_card(job, "administrative")
            html_content += """
        </div>
"""

    html_content += """
    </div>
</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"📄 HTML report saved to: {filename}")


def _render_job_card(job, category_type):
    """تابع کمکی برای رندر کردن یک کارت شغلی"""
    score = job.get('score', 0)
    score_class = "high" if score >= 70 else "medium" if score >= 50 else "low"
    
    # مهارت‌ها
    matched_skills = job.get('matched_skills', []) or []
    skills_html = ''.join(
        f'<span class="skill-tag matched">✓ {skill}</span>' 
        for skill in matched_skills[:10]
    )
    
    # اطلاعات شغل
    description_preview = job.get('description_preview', '') or 'توضیحاتی موجود نیست'
    penalty = job.get('penalty', 0)
    technical_score = job.get('technical_score', 0)
    general_score = job.get('general_score', 0)
    
    # فیلدهای جدید
    location = job.get('location', 'نامشخص')
    is_urgent = job.get('is_urgent', 0)
    salary = job.get('salary', 'توافقی')
    
    # بج‌ها
    penalty_html = f'<span class="penalty-badge">⚠️ Penalty: -{penalty}%</span>' if penalty > 0 else ''
    urgent_html = f'<span class="job-meta-item urgent">⚡ فوری</span>' if is_urgent else ''
    
    # برچسب دسته‌بندی
    category_labels = {
        'technical': '<span class="job-category-tag technical">🔧 Technical</span>',
        'administrative': '<span class="job-category-tag administrative">🧾 Admin</span>',
        'hybrid': '<span class="job-category-tag hybrid">🔀 Hybrid</span>'
    }
    category_label = category_labels.get(category_type, '')
    
    card_class = {
        'technical': 'technical',
        'administrative': 'administrative',
        'hybrid': 'hybrid'
    }.get(category_type, '')
    
    return f"""
            <div class="job-card {card_class}">
                <div class="job-header">
                    <div>
                        <div class="job-title">{job.get('title', 'عنوان نامشخص')} {category_label}</div>
                        <div class="job-company">🏢 {job.get('company', 'شرکت نامشخص')}</div>
                        <div class="job-meta">
                            <span class="job-meta-item">📍 {location}</span>
                            <span class="job-meta-item">💰 {salary}</span>
                            {urgent_html}
                        </div>
                    </div>
                    <div>
                        <span class="technical-badge">🎯 Tech: {technical_score}%</span>
                        <span class="general-badge">📋 Gen: {general_score}%</span>
                        <span class="semantic-badge">🧠 Emb: {job.get('embedding_score', 0) or 0:.0f}%</span>
                        <span class="semantic-badge">📊 Out: {job.get('outlier_score', 0) or 0:.0f}%</span>
                        {penalty_html}
                        <span class="score-badge {score_class}">{score}%</span>
                    </div>
                </div>
                
                <div class="job-details">
                    <a href="{job.get('url', '#')}" target="_blank" class="url-link">🔗 مشاهده آگهی</a>
                    
                    <div class="skill-tags">
                        {skills_html}
                    </div>
                    
                    <div style="margin-top: 8px; font-size: 13px; color: #666;">
                        <details>
                            <summary style="cursor: pointer;">📝 پیش‌نمایش آگهی</summary>
                            <p style="margin-top: 8px; padding: 10px; background: #f8f9fa; border-radius: 8px; white-space: pre-wrap;">
                                {description_preview}
                            </p>
                        </details>
                    </div>
                </div>
            </div>
"""


if __name__ == "__main__":
    test_results = [
        {
            "title": "برنامه‌نویس پایتون",
            "company": "شرکت فناوری نوین",
            "url": "https://example.com/job1",
            "location": "تهران",
            "salary": "50 - 70 میلیون",
            "is_urgent": True,
            "score": 85,
            "technical_score": 92,
            "general_score": 35,
            "category": "technical",
            "matched_skills": ["python", "هوش مصنوعی", "پردازش تصویر"],
            "embedding_score": 82,
            "outlier_score": 92,
            "penalty": 0,
            "description_preview": "شرکت فناوری نوین به یک برنامه‌نویس پایتون نیاز دارد."
        }
    ]
    
    generate_html_report(test_results, "test_report_v8.html")
    print("✅ گزارش تست v8 ایجاد شد: test_report_v8.html")