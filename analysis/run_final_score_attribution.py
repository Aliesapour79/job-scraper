# analysis/run_final_score_attribution.py
"""
تحلیل امتیازها با خواندن مستقیم از دیتابیس
"""

import sqlite3
import pandas as pd
import ast
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from matcher.weights import get_job_group

DB_PATH = "data/jobs_db_clean.db"


def get_data_from_db(limit=None):
    """دریافت داده‌های امتیاز از دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT 
            j.id,
            j.title,
            j.company,
            j.job_category,
            s.score,
            s.technical_score,
            s.general_score,
            s.embedding_score,
            s.tfidf_score,
            s.category,
            s.outlier_score,
            s.calculated_at
        FROM jobvision_scores s
        JOIN jobvision_jobs_clean j ON s.job_id = j.id
        ORDER BY s.score DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def parse_scores(row):
    """parse dict string columns safely"""
    try:
        return ast.literal_eval(row)
    except:
        return {}


def compute_weighted_contributions(df):
    contributions = {
        "hard": [],
        "functional": [],
        "soft": [],
        "semantic": []
    }

    final_scores = []

    for _, row in df.iterrows():

        # استفاده از ستون‌های دیتابیس
        hard = row.get("technical_score", 0)
        func = 0  # functional_score در دیتابیس ذخیره نمیشه
        soft = row.get("general_score", 0)
        semantic = row.get("embedding_score", 0)

        # دریافت وزن‌ها از category
        category = row.get("category", "hybrid")
        weights = get_weights_for_category(category)

        w_h = weights.get("hard", 0)
        w_f = weights.get("functional", 0)
        w_s = weights.get("soft", 0)
        w_se = weights.get("semantic", 0)

        contrib_hard = w_h * hard
        contrib_func = w_f * func
        contrib_soft = w_s * soft
        contrib_sem = w_se * semantic

        total = contrib_hard + contrib_func + contrib_soft + contrib_sem

        contributions["hard"].append(contrib_hard)
        contributions["functional"].append(contrib_func)
        contributions["soft"].append(contrib_soft)
        contributions["semantic"].append(contrib_sem)

        final_scores.append(total)

    return contributions, final_scores


def get_weights_for_category(category):
    """دریافت وزن‌های مناسب برای هر دسته‌بندی"""
    from matcher.weights import WEIGHTS_CONFIG
    
    # تعیین گروه شغلی
    if category in ["technical"]:
        group = "technical"
    elif category in ["administrative"]:
        group = "administrative"
    else:
        group = "hybrid"
    
    return WEIGHTS_CONFIG.get(group, WEIGHTS_CONFIG["hybrid"])


def sensitivity_analysis(df):
    results = {
        "no_hard": [],
        "no_functional": [],
        "no_soft": [],
        "no_semantic": []
    }

    for _, row in df.iterrows():

        hard = row.get("technical_score", 0)
        func = 0
        soft = row.get("general_score", 0)
        semantic = row.get("embedding_score", 0)

        category = row.get("category", "hybrid")
        weights = get_weights_for_category(category)

        w_h = weights.get("hard", 0)
        w_f = weights.get("functional", 0)
        w_s = weights.get("soft", 0)
        w_se = weights.get("semantic", 0)

        base = (
            w_h * hard +
            w_f * func +
            w_s * soft +
            w_se * semantic
        )

        results["no_hard"].append(base - w_h * hard)
        results["no_functional"].append(base - w_f * func)
        results["no_soft"].append(base - w_s * soft)
        results["no_semantic"].append(base - w_se * semantic)

    return results


def print_summary(contributions, final_scores, df, sensitivity):

    print("\n" + "=" * 60)
    print("🔬 FINAL SCORE ATTRIBUTION ANALYSIS (از دیتابیس)")
    print("=" * 60)

    for key in contributions:
        arr = np.array(contributions[key])
        print(f"\n📊 {key.upper()}")
        print(f"Mean contribution: {arr.mean():.3f}")
        print(f"Median: {np.median(arr):.3f}")

    print("\n📈 FINAL SCORE STATS")
    final_arr = np.array(final_scores)
    print(f"Mean: {final_arr.mean():.2f}")
    print(f"Median: {np.median(final_arr):.2f}")
    print(f"Max: {final_arr.max():.2f}")

    print("\n🧨 SENSITIVITY IMPACT")

    for k, v in sensitivity.items():
        arr = np.array(v)
        print(f"{k}: mean impact = {arr.mean():.3f}")


def correlation_analysis(df):

    scores = {
        "hard": df["technical_score"].values,
        "functional": np.zeros(len(df)),
        "soft": df["general_score"].values,
        "semantic": df["embedding_score"].values,
        "final": df["score"].values
    }

    print("\n🔗 CORRELATION WITH FINAL SCORE")

    for k in ["hard", "functional", "soft", "semantic"]:
        corr = np.correlate(scores[k], scores["final"])[0] / (len(scores["final"]) - 1) if len(scores["final"]) > 1 else 0
        # یا استفاده از np.corrcoef
        if len(scores[k]) > 1 and len(scores["final"]) > 1:
            corr = np.corrcoef(scores[k], scores["final"])[0, 1]
        else:
            corr = 0
        print(f"{k}: {corr:.3f}")


def get_stats(df):
    """آمار کلی از دیتابیس"""
    print("\n" + "=" * 60)
    print("📊 آمار کلی از دیتابیس")
    print("=" * 60)
    
    total = len(df)
    print(f"📋 تعداد کل امتیازها: {total}")
    
    # آمار بر اساس دسته‌بندی
    cat_stats = df.groupby('category').agg({
        'score': ['count', 'mean', 'max', 'min']
    }).round(2)
    
    print("\n📊 آمار بر اساس دسته‌بندی:")
    print(cat_stats)
    
    # بهترین آگهی‌ها
    print("\n🏆 TOP 5 آگهی‌های با بیشترین امتیاز:")
    top5 = df.nlargest(5, 'score')[['title', 'company', 'score', 'category']]
    for i, row in top5.iterrows():
        print(f"   {row['title']} ({row['company']}) → {row['score']}% [{row['category']}]")


def main():

    print("\n🚀 Loading data from database...")
    
    # دریافت همه داده‌ها
    df = get_data_from_db(limit=None)
    
    if df.empty:
        print("❌ هیچ داده‌ای در دیتابیس پیدا نشد!")
        print("   لطفاً ابتدا main.py را اجرا کنید.")
        return
    
    print(f"📦 Rows loaded: {len(df)}")
    
    # نمایش آمار کلی
    get_stats(df)
    
    print("\n🔬 Computing contributions...")
    contributions, final_scores = compute_weighted_contributions(df)
    
    sensitivity = sensitivity_analysis(df)
    
    print_summary(contributions, final_scores, df, sensitivity)
    
    correlation_analysis(df)
    
    print("\n✅ DONE")


if __name__ == "__main__":
    main()