# dashboard.py
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import tempfile
import requests
from utils.decrypt import decrypt_data, decrypt_file_to_string

# =========================
# تنظیمات صفحه
# =========================
st.set_page_config(
    page_title="JobVision Dashboard",
    page_icon="📊",
    layout="wide"
)

# =========================
# CSS سفارشی
# =========================
st.markdown("""
<style>
.stApp{
    background: #0f172a;
    color: white;
}

[data-testid="metric-container"]{
    background: linear-gradient(135deg,#1e293b,#334155);
    border:1px solid #334155;
    border-radius:18px;
    padding:20px;
    box-shadow:0 5px 20px rgba(0,0,0,.3);
    transition: all 0.3s ease;
}

[data-testid="metric-container"]:hover{
    transform: translateY(-4px);
    box-shadow:0 8px 30px rgba(0,0,0,.5);
}

[data-testid="metric-container"] label{
    color:#cbd5e1;
}

[data-testid="metric-container"] [data-testid="stMetricValue"]{
    color:white;
    font-size:34px;
    font-weight:700;
}

[data-testid="stDataFrame"]{
    border-radius:15px;
    overflow:hidden;
}

.stButton>button{
    border-radius:12px;
    border:none;
    background:#2563eb;
    color:white;
    font-weight:600;
    transition: all 0.3s ease;
}

.stButton>button:hover{
    background:#1d4ed8;
    transform: scale(1.02);
}

section[data-testid="stSidebar"]{
    background:#111827;
}

/* کارت‌های نمایش آگهی */
.job-card{
    background: linear-gradient(135deg,#1e293b,#0f172a);
    border:1px solid #334155;
    border-radius:16px;
    padding:16px 20px;
    margin-bottom:12px;
    transition: all 0.3s ease;
}

.job-card:hover{
    border-color:#2563eb;
    box-shadow:0 0 20px rgba(37,99,235,0.15);
    transform: translateX(6px);
}

/* اسکرول بار */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #1e293b;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb {
    background: #2563eb;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: #1d4ed8;
}
</style>
""", unsafe_allow_html=True)
def get_last_update_time():
    """دریافت آخرین زمان بروزرسانی دیتابیس"""
    try:
        conn = sqlite3.connect("data/jobs.db")
        cursor = conn.cursor()
        
        # دریافت آخرین زمان scraped_at از جدول jobs
        cursor.execute("""
            SELECT MAX(scraped_at) 
            FROM jobvision_jobs
        """)
        result = cursor.fetchone()[0]
        conn.close()
        
        if result:
            return datetime.strptime(result, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.now()
    except:
        return datetime.now()
# =========================
# 🔐 لاگین ادمین (کشویی)
# =========================
if "admin" not in st.session_state:
    st.session_state.admin = False

# =========================
# رمزگشایی
# =========================
skill_enc = "matcher/skill_groups.py.enc"
if os.path.exists(skill_enc):
    skill_content = decrypt_file_to_string(skill_enc)
    if skill_content:
        exec(skill_content, globals())

# =========================
# بارگذاری دیتابیس
# =========================
def load_db():
    try:
        enc_path = "data/jobs.db.enc"
        if not os.path.exists(enc_path):
            if os.path.exists("data/jobs.db"):
                return sqlite3.connect("data/jobs.db")
            else:
                st.error("❌ دیتابیس پیدا نشد!")
                return None

        with open(enc_path, 'rb') as f:
            encrypted = f.read()

        decrypted = decrypt_data(encrypted)
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.write(decrypted)
        temp_db.close()
        return sqlite3.connect(temp_db.name)

    except Exception as e:
        st.error(f"❌ خطا در رمزگشایی: {e}")
        return None

conn = load_db()
if conn is None:
    st.stop()

# =========================
# سایدبار - ادمین کشویی + دکمه اجرا
# =========================
with st.sidebar:
    st.markdown("### 🔐 پنل ادمین")
    
    if not st.session_state.admin:
        # 🔥 کشویی (Expandable)
        with st.expander("🔑 ورود به پنل ادمین", expanded=False):
            password = st.text_input("رمز ورود", type="password", key="admin_password")
            if st.button("ورود", key="admin_login"):
                try:
                    # حذف فاصله‌های اضافی و کاراکترهای مخفی
                    clean_password = ''.join(c for c in password.strip() if c.isprintable())
                    clean_secret = ''.join(c for c in st.secrets["admin"]["password"].strip() if c.isprintable())
                    
                    if clean_password == clean_secret:
                        st.session_state.admin = True
                        st.rerun()
                    else:
                        st.error("❌ رمز اشتباه است")
                except:
                    st.error("❌ رمز در Secrets تنظیم نشده!")
    else:
        st.success("✅ ادمین عزیز خوش آمدی")
        
        # دکمه اجرا
        if st.button("🚀 اجرای اسکرپ جدید", use_container_width=True):
            with st.spinner("⏳ در حال ارسال درخواست به گیت‌هاب..."):
                try:
                    response = requests.post(
                        "https://api.github.com/repos/Aliesapour79/job-scraper/actions/workflows/job-matcher.yml/dispatches",
                        headers={
                            "Authorization": f"token {st.secrets['github']['token']}",
                            "Accept": "application/vnd.github.v3+json"
                        },
                        json={"ref": "main"}
                    )
                    if response.status_code == 204:
                        st.success("✅ اسکرپ با موفقیت اجرا شد!")
                        st.info("⏱️ چند دقیقه دیگه نتیجه رو در داشبورد ببین.")
                    else:
                        st.error(f"❌ خطا: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"❌ خطا در ارتباط با گیت‌هاب: {e}")
        
        if st.button("🚪 خروج", use_container_width=True):
            st.session_state.admin = False
            st.rerun()
    
    st.markdown("---")

# =========================
# هدر
# =========================
st.markdown("""
# 🚀 JobVision Dashboard
### تحلیل هوشمند بازار کار ایران
""")

col1, col2 = st.columns([3,1])

with col1:
    last_update = get_last_update_time()
    st.caption(f"📅 آخرین بروزرسانی : {last_update:%Y/%m/%d %H:%M}")
with col2:
    st.success("🟢 System Online")

st.markdown("---")

# =========================
# آمار کلی
# =========================
df_stats = pd.read_sql_query("""
    SELECT 
        (SELECT COUNT(*) FROM jobvision_jobs) as total_jobs,
        (SELECT COUNT(DISTINCT company) FROM jobvision_jobs) as total_companies,
        (SELECT COUNT(DISTINCT location) FROM jobvision_jobs) as total_cities,
        (SELECT COUNT(*) FROM jobvision_jobs WHERE is_urgent = 1) as urgent
""", conn)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("📋 کل آگهی‌ها", f"{df_stats['total_jobs'].iloc[0]:,}")

with c2:
    st.metric("🏢 شرکت‌ها", f"{df_stats['total_companies'].iloc[0]:,}")

with c3:
    st.metric("📍 شهرها", f"{df_stats['total_cities'].iloc[0]:,}")

with c4:
    st.metric("⚡ فوری", f"{df_stats['urgent'].iloc[0]:,}")

st.markdown("---")

# =========================
# نمودارها
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 توزیع دسته‌بندی شغلی")

    df_cat = pd.read_sql_query("""
        SELECT job_category, COUNT(*) as count 
        FROM jobvision_jobs 
        WHERE job_category != '' 
        GROUP BY job_category 
        ORDER BY count DESC 
        LIMIT 10
    """, conn)

    if not df_cat.empty:
        fig = px.pie(
            df_cat,
            values='count',
            names='job_category',
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font_color="white",
            showlegend=False,
            height=380
        )

        fig.update_traces(textinfo='percent+label', textposition='inside')

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("هنوز داده‌ای برای نمایش وجود ندارد")

with col2:
    st.subheader("🏢 برترین شرکت‌ها")

    df_company = pd.read_sql_query("""
        SELECT company, COUNT(*) as count 
        FROM jobvision_jobs 
        WHERE company != '' 
        GROUP BY company 
        ORDER BY count DESC 
        LIMIT 10
    """, conn)

    if not df_company.empty:
        fig = px.bar(
            df_company,
            x='count',
            y='company',
            orientation='h',
            text='count',
            color='count',
            color_continuous_scale='Viridis'
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font_color="white",
            xaxis_title="تعداد آگهی",
            yaxis_title="",
            height=380
        )

        fig.update_traces(textposition='outside')

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("هنوز داده‌ای برای نمایش وجود ندارد")

st.markdown("---")

# =========================
# بهترین تطابق‌ها
# =========================
st.subheader("🏆 بهترین تطابق‌ها")

df_top = pd.read_sql_query("""
    SELECT 
        j.title,
        j.company,
        j.location,
        s.score,
        s.category,
        s.technical_score,
        s.general_score,
        j.url
    FROM jobvision_jobs j
    LEFT JOIN jobvision_scores s ON j.id = s.job_id
    WHERE s.score IS NOT NULL
    ORDER BY s.score DESC
    LIMIT 20
""", conn)

if not df_top.empty:
    for _, row in df_top.iterrows():
        # تعیین رنگ نوار پیشرفت بر اساس امتیاز
        score = int(row['score'])
        if score >= 70:
            color = "#22c55e"
        elif score >= 50:
            color = "#eab308"
        else:
            color = "#ef4444"

        st.markdown(f"""
        <div class="job-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                <div>
                    <h4 style="color:white; margin:0; font-weight:600;">{row['title']}</h4>
                    <div style="color:#94a3b8; font-size:14px; margin-top:4px;">
                        🏢 {row['company']}  •  📍 {row['location']}
                    </div>
                </div>
                <div style="background:#2563eb; border-radius:12px; padding:6px 16px;">
                    <span style="color:white; font-weight:700; font-size:18px;">{score}%</span>
                </div>
            </div>
            <div style="margin-top:10px;">
                <div style="background:#1e293b; border-radius:99px; height:8px; overflow:hidden;">
                    <div style="background:{color}; width:{score}%; height:100%; border-radius:99px;"></div>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; flex-wrap:wrap; margin-top:8px;">
                <span style="color:#94a3b8; font-size:13px;">
                    🎯 فنی: {row['technical_score']}%  •  📋 عمومی: {row['general_score']}%
                </span>
                <a href="{row['url']}" target="_blank" style="color:#60a5fa; text-decoration:none; font-size:13px;">
                    🔗 مشاهده آگهی →
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("هنوز امتیازی ثبت نشده است. ابتدا `main.py` را با `ENABLE_PROCESSING=True` اجرا کنید.")

st.markdown("---")

# =========================
# جستجو
# =========================
st.subheader("🔎 جستجوی آگهی")

with st.container(border=True):
    col1, col2, col3 = st.columns([4, 3, 1])

    with col1:
        search_term = st.text_input(
            "جستجو در عنوان یا شرکت",
            placeholder="مثلاً: Python یا شرکت...",
            label_visibility="collapsed"
        )

    with col2:
        df_cat_filter = pd.read_sql_query("""
            SELECT DISTINCT job_category 
            FROM jobvision_jobs 
            WHERE job_category != '' 
            ORDER BY job_category
        """, conn)

        categories = ['همه'] + list(df_cat_filter['job_category'].dropna())
        selected_category = st.selectbox("دسته‌بندی", categories, label_visibility="collapsed")

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍 جستجو", use_container_width=True)

# =========================
# نتایج جستجو با امتیاز
# =========================
if search_btn or search_term or selected_category != 'همه':
    query = """
        SELECT 
            j.title, 
            j.company, 
            j.location, 
            j.url,
            s.score
        FROM jobvision_jobs j
        LEFT JOIN jobvision_scores s ON j.id = s.job_id
        WHERE 1=1
    """
    params = []

    if search_term:
        query += " AND (j.title LIKE ? OR j.company LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    if selected_category != 'همه':
        query += " AND j.job_category = ?"
        params.append(selected_category)

    query += " LIMIT 50"

    df_search = pd.read_sql_query(query, conn, params=params)

    if not df_search.empty:
        df_search.columns = ['عنوان', 'شرکت', 'موقعیت', 'لینک', 'امتیاز']
        
        # نمایش امتیاز با رنگ
        def style_score(val):
            if val and val >= 70:
                return 'background-color: #d4edda; color: #155724; font-weight: bold;'
            elif val and val >= 50:
                return 'background-color: #fff3cd; color: #856404;'
            elif val:
                return 'background-color: #f8d7da; color: #721c24;'
            return ''

        st.success(f"✅ {len(df_search)} آگهی پیدا شد")

        st.dataframe(
            df_search.style.map(style_score, subset=['امتیاز']),
            use_container_width=True,
            hide_index=True,
            column_config={
                'لینک': st.column_config.LinkColumn(
                    'لینک',
                    display_text='🔗 مشاهده'
                ),
                'امتیاز': st.column_config.NumberColumn(
                    'امتیاز',
                    format='%d%%'
                )
            }
        )
    else:
        st.warning("هیچ آگهی‌ای پیدا نشد")
# =========================
# بستن اتصال
# =========================
conn.close()

# =========================
# فوتر
# =========================
st.markdown("---")

st.markdown("""
<div style='text-align:center;color:#94a3b8;padding:20px 0;'>

**JobVision Analytics** — تحلیل هوشمند بازار کار ایران

Built with ❤️ using Streamlit & Plotly

© 2026 علی عیسی‌پور

</div>
""", unsafe_allow_html=True)