import json
from datetime import datetime
import os
def generate_html_report(results, filename="job_report.html"):
    """Generate beautiful HTML report with charts - v6.3 Dual Track"""
    
    # محاسبه‌ی آمار با مدیریت خطا
    total_jobs = len(results)
    best_score = results[0]['score'] if results and 'score' in results[0] else 0
    excellent_count = sum(1 for r in results if r.get('score', 0) > 70)
    outlier_count = sum(1 for r in results if r.get('outlier_score', 0) > 70)
    
    # آمار دسته‌بندی
    tech_count = sum(1 for r in results if r.get('category') == 'technical')
    admin_count = sum(1 for r in results if r.get('category') == 'administrative')
    hybrid_count = sum(1 for r in results if r.get('category') == 'hybrid')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>گزارش تطبیق شغلی v6.3 - علی عیسی‌پور</title>
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
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .stat-card .number {{
            font-size: 36px;
            font-weight: bold;
        }}
        .stat-card .label {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        /* ====== بخش‌های جداگانه ====== */
        .section-title {{
            font-size: 24px;
            font-weight: bold;
            padding: 15px 20px;
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
        .section-admin-safety {{
            background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%);
            border-right: 5px solid #c62828;
        }}
        .section-admin-safety .section-title {{
            background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%);
            border-right: 5px solid #c62828;
        }}
        
        /* ====== کارت شغلی ====== */
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
        .job-card.admin-safety {{
            border-right-color: #c62828;
            border-style: dashed;
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
            font-size: 16px;
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
        .job-category-tag.admin-safety {{
            background: #fce4ec;
            color: #c62828;
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
        .job-details {{
            margin-top: 10px;
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
        .group-analysis {{
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 10px;
        }}
        .group-bar {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        .group-name {{
            width: 150px;
            font-size: 13px;
            color: #555;
        }}
        .group-bar-fill {{
            height: 20px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 10px;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-size: 11px;
            font-weight: bold;
            min-width: 30px;
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
            font-size: 12px;
            background: #e3f2fd;
            color: #1976d2;
            margin-right: 10px;
        }}
        .technical-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            background: #e8f5e9;
            color: #2e7d32;
            margin-right: 10px;
            font-weight: bold;
        }}
        .general-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            background: #fff3e0;
            color: #e65100;
            margin-right: 10px;
            font-weight: bold;
        }}
        .penalty-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            background: #ffebee;
            color: #c62828;
            margin-right: 10px;
        }}
        .boost-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            background: #e8f5e9;
            color: #2e7d32;
            margin-right: 10px;
        }}
        .safety-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            background: #fce4ec;
            color: #c62828;
            margin-right: 10px;
            font-weight: bold;
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
            .group-name {{
                width: 100px;
                font-size: 11px;
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
            .skill-tag {{
                background: #2a2a4a;
                color: #ccc;
            }}
            .skill-tag.matched {{
                background: #1a3a2a;
                color: #8f8;
            }}
            .group-analysis {{
                background: #1a1a3e;
            }}
            .group-name {{
                color: #aaa;
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
            .boost-badge {{
                background: #1a3a2a;
                color: #8f8;
            }}
            .safety-badge {{
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
            .section-admin-safety {{
                background: #3a1a1a;
            }}
            .section-admin-safety .section-title {{
                background: #3a1a1a;
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
            <h1>🎯 گزارش تطبیق شغلی v6.3</h1>
            <div class="subtitle">
                بر اساس رزومه‌ی علی عیسی‌پور شربیانی | 
                تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}
            </div>
            <div class="version-badge">⚡ Dual Track + Hybrid Scoring</div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="number">{total_jobs}</div>
                <div class="label">تعداد آگهی‌های مناسب</div>
            </div>
            <div class="stat-card">
                <div class="number">{best_score}%</div>
                <div class="label">بهترین تطابق</div>
            </div>
            <div class="stat-card">
                <div class="number">{excellent_count}</div>
                <div class="label">تطابق عالی (&gt;۷۰%)</div>
            </div>
            <div class="stat-card">
                <div class="number">{outlier_count}</div>
                <div class="label">Outlier &gt; ۷۰%</div>
            </div>
        </div>
        
        <!-- آمار دسته‌بندی -->
        <div style="display: flex; gap: 20px; justify-content: center; margin-bottom: 25px; flex-wrap: wrap;">
            <span style="background: #e8f5e9; padding: 8px 20px; border-radius: 20px; color: #2e7d32;">
                🔧 Technical: {tech_count}
            </span>
            <span style="background: #fff3e0; padding: 8px 20px; border-radius: 20px; color: #e65100;">
                🧾 Admin: {admin_count}
            </span>
            <span style="background: #e3f2fd; padding: 8px 20px; border-radius: 20px; color: #1565c0;">
                🔀 Hybrid: {hybrid_count}
            </span>
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
        # ====== جدا کردن آگهی‌ها بر اساس دسته‌بندی ======
        tech_jobs = [j for j in results if j.get('category') == 'technical']
        admin_jobs = [j for j in results if j.get('category') == 'administrative']
        hybrid_jobs = [j for j in results if j.get('category') == 'hybrid']
        
        # آگهی‌های اداری با safety tag
        admin_safety_jobs = [j for j in results if j.get('is_admin_safety')]
        
        # ====== رندر کردن هر بخش ======
        
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
        
        # 3. بخش Recommended Admin Jobs
        if admin_jobs:
            html_content += f"""
        <div class="section-administrative" style="border-radius: 12px; padding: 5px 20px 20px 20px; margin-bottom: 20px;">
            <div class="section-title">
                🧾 شغل‌های اداری (پیشنهادهای تکمیلی) <span class="count">({len(admin_jobs)})</span>
            </div>
"""
            for job in admin_jobs[:10]:
                html_content += _render_job_card(job, "administrative")
            html_content += """
        </div>
"""
        
        # 4. بخش Admin Safety (آگهی‌های اداری با امتیاز پایین)
        if admin_safety_jobs:
            html_content += f"""
        <div class="section-admin-safety" style="border-radius: 12px; padding: 5px 20px 20px 20px; margin-bottom: 20px; border: 2px dashed #c62828;">
            <div class="section-title" style="background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%); border-right: 5px solid #c62828; border-radius: 12px;">
                🛡️ آگهی‌های اداری (حفظ شده) <span class="count">({len(admin_safety_jobs)})</span>
            </div>
            <p style="color: #666; font-size: 14px; margin-bottom: 15px;">
                ⚠️ این آگهی‌ها با وجود امتیاز پایین‌تر، به دلیل اهمیت حوزه اداری در رزومه شما حفظ شده‌اند.
            </p>
"""
            for job in admin_safety_jobs[:10]:
                html_content += _render_job_card(job, "admin-safety")
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
    
    # دریافت مهارت‌ها
    matched_skills = job.get('matched_skills', []) or []
    skills_html = ''.join(
        f'<span class="skill-tag matched">✓ {skill}</span>' 
        for skill in matched_skills[:10]
    )
    
    # دریافت تحلیل گروه‌ها
    group_analysis = job.get('group_analysis', {}) or {}
    groups_html = ""
    for group_name, data in group_analysis.items():
        if data and data.get('score', 0) > 0:
            group_score = data.get('score', 0)
            multiplier = data.get('multiplier', 1.0)
            groups_html += f'''
                    <div class="group-bar">
                        <span class="group-name">{group_name.replace('_', ' ').title()}</span>
                        <div style="flex:1; background:#e9ecef; border-radius:10px; height:20px; margin:0 10px;">
                            <div class="group-bar-fill" style="width:{min(group_score / 2, 100)}%;">
                                {group_score} pts
                            </div>
                        </div>
                        <span style="font-size:12px; color:#666;">×{multiplier:.1f}</span>
                    </div>
                    '''
    
    description_preview = job.get('description_preview', '') or 'توضیحاتی موجود نیست'
    
    penalty = job.get('penalty', 0)
    boost = job.get('boost', 0)
    technical_score = job.get('technical_score', 0)
    general_score = job.get('general_score', 0)
    
    penalty_html = f'<span class="penalty-badge">⚠️ Penalty: -{penalty}%</span>' if penalty > 0 else ''
    boost_html = f'<span class="boost-badge">🚀 Boost: +{boost}%</span>' if boost > 0 else ''
    safety_html = '<span class="safety-badge">🛡️ Admin Safety</span>' if job.get('is_admin_safety') else ''
    
    # برچسب دسته‌بندی
    category_labels = {
        'technical': '<span class="job-category-tag technical">🔧 Technical</span>',
        'administrative': '<span class="job-category-tag administrative">🧾 Admin</span>',
        'hybrid': '<span class="job-category-tag hybrid">🔀 Hybrid</span>',
        'admin-safety': '<span class="job-category-tag admin-safety">🛡️ Admin Safety</span>'
    }
    category_label = category_labels.get(category_type, '')
    
    card_class = {
        'technical': 'technical',
        'administrative': 'administrative',
        'hybrid': 'hybrid',
        'admin-safety': 'admin-safety'
    }.get(category_type, '')
    
    return f"""
            <div class="job-card {card_class}">
                <div class="job-header">
                    <div>
                        <div class="job-title">{job.get('title', 'عنوان نامشخص')} {category_label}</div>
                        <div class="job-company">🏢 {job.get('company', 'شرکت نامشخص')}</div>
                    </div>
                    <div>
                        <span class="technical-badge">🎯 Technical: {technical_score}%</span>
                        <span class="general-badge">📋 General: {general_score}%</span>
                        <span class="semantic-badge">🧠 Embedding: {job.get('embedding_score', 0) or 0:.0f}%</span>
                        <span class="semantic-badge">📊 TF-IDF: {job.get('tfidf_score', 0) or 0:.0f}%</span>
                        <span class="semantic-badge">📊 Outlier: {job.get('outlier_score', 0) or 0:.0f}%</span>
                        {penalty_html}
                        {boost_html}
                        {safety_html}
                        <span class="score-badge {score_class}">{score}%</span>
                    </div>
                </div>
                
                <div class="job-details">
                    <a href="{job.get('url', '#')}" target="_blank" class="url-link">🔗 مشاهده آگهی</a>
                    
                    <div class="skill-tags">
                        {skills_html}
                    </div>
                    
                    <div class="group-analysis">
                        {groups_html}
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


# تست با داده‌های نمونه
if __name__ == "__main__":
    test_results = [
        {
            "title": "برنامه‌نویس پایتون",
            "company": "شرکت فناوری نوین",
            "url": "https://example.com/job1",
            "score": 85,
            "technical_score": 92,
            "general_score": 35,
            "category": "technical",
            "matched_skills": ["python", "هوش مصنوعی", "پردازش تصویر"],
            "embedding_score": 82,
            "tfidf_score": 78,
            "outlier_score": 92,
            "penalty": 0,
            "boost": 10,
            "is_admin_safety": False,
            "group_analysis": {
                "programming": {"score": 25, "multiplier": 1.5},
                "ai_computer_vision": {"score": 20, "multiplier": 1.2}
            },
            "description_preview": "شرکت فناوری نوین به یک برنامه‌نویس پایتون نیاز دارد."
        },
        {
            "title": "کارمند اداری",
            "company": "شرکت خدمات اداری",
            "url": "https://example.com/job2",
            "score": 45,
            "technical_score": 20,
            "general_score": 78,
            "category": "administrative",
            "matched_skills": ["word", "excel", "اداری"],
            "embedding_score": 30,
            "tfidf_score": 25,
            "outlier_score": 70,
            "penalty": 15,
            "boost": 0,
            "is_admin_safety": False,
            "group_analysis": {
                "office_administration": {"score": 35, "multiplier": 1.0}
            },
            "description_preview": "شرکت خدمات اداری به یک کارمند مسلط به Word و Excel نیاز دارد."
        },
        {
            "title": "کارمند اداری (پایین)",
            "company": "شرکت کوچک",
            "url": "https://example.com/job3",
            "score": 25,
            "technical_score": 10,
            "general_score": 45,
            "category": "administrative",
            "matched_skills": ["word", "اداری"],
            "embedding_score": 15,
            "tfidf_score": 10,
            "outlier_score": 50,
            "penalty": 20,
            "boost": 0,
            "is_admin_safety": True,
            "group_analysis": {
                "office_administration": {"score": 20, "multiplier": 1.0}
            },
            "description_preview": "یک شرکت کوچک به کارمند اداری نیاز دارد."
        }
    ]
    
    generate_html_report(test_results, "test_report_v63.html")
    print("✅ گزارش تست v6.3 ایجاد شد: test_report_v63.html")
