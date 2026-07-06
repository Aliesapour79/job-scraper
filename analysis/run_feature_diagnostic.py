# scripts/run_feature_diagnostic.py

import pandas as pd
import ast
import numpy as np


# ==============================
# 📌 LOAD DATA
# ==============================

def load_scored_jobs(path: str):
    df = pd.read_csv(path)

    # تبدیل ستون‌های dict-like
    df["scores"] = df["scores"].apply(ast.literal_eval)
    df["weights"] = df["weights"].apply(ast.literal_eval)

    return df


# ==============================
# 📌 FEATURE DECOMPOSITION
# ==============================

def compute_contributions(df: pd.DataFrame):
    rows = []

    for _, row in df.iterrows():
        scores = row["scores"]
        weights = row["weights"]

        hard = scores.get("hard", 0)
        func = scores.get("functional", 0)
        soft = scores.get("soft", 0)
        sem = scores.get("semantic", 0)

        w_hard = weights.get("hard", 0)
        w_func = weights.get("functional", 0)
        w_soft = weights.get("soft", 0)
        w_sem = weights.get("semantic", 0)

        contributions = {
            "hard": hard * w_hard,
            "functional": func * w_func,
            "soft": soft * w_soft,
            "semantic": sem * w_sem
        }

        total = sum(contributions.values())

        if total == 0:
            continue

        rows.append({
            "hard": contributions["hard"] / total,
            "functional": contributions["functional"] / total,
            "soft": contributions["soft"] / total,
            "semantic": contributions["semantic"] / total,
            "final": row["final"]
        })

    return pd.DataFrame(rows)


# ==============================
# 📊 ANALYSIS
# ==============================

def analyze(df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("🔬 FEATURE CONTRIBUTION DIAGNOSTIC")
    print("=" * 60)

    features = ["hard", "functional", "soft", "semantic"]

    summary = {}

    for f in features:
        summary[f] = {
            "mean": df[f].mean(),
            "median": df[f].median(),
            "std": df[f].std(),
            "min": df[f].min(),
            "max": df[f].max()
        }

    for f, stats in summary.items():
        print(f"\n📊 {f.upper()} CONTRIBUTION")
        print(f"   Mean   : {stats['mean']:.3f}")
        print(f"   Median : {stats['median']:.3f}")
        print(f"   Std    : {stats['std']:.3f}")
        print(f"   Min    : {stats['min']:.3f}")
        print(f"   Max    : {stats['max']:.3f}")

    print("\n" + "=" * 60)

    print("📌 INTERPRETATION:")
    print("- >0.50 → dominant feature")
    print("- 0.20–0.50 → balanced contribution")
    print("- <0.20 → weak signal")

    print("\n🏁 DONE")


# ==============================
# 🚀 MAIN
# ==============================

def main():
    path = "scored_jobs_v8_test.csv"

    print("\n🚀 Loading data...")
    df = load_scored_jobs(path)

    print(f"📦 Rows loaded: {len(df)}")

    print("\n🔬 Computing contributions...")
    contrib_df = compute_contributions(df)

    print(f"📊 Analyzed rows: {len(contrib_df)}")

    analyze(contrib_df)


if __name__ == "__main__":
    main()