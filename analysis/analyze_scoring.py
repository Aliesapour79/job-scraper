# scripts/analyze_scoring.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


INPUT_FILE = "scored_jobs_v8_test.csv"


def load_data():
    df = pd.read_csv(INPUT_FILE)
    return df


def basic_stats(df):
    print("\n" + "=" * 60)
    print("📊 BASIC STATISTICS")
    print("=" * 60)

    print(f"Total jobs: {len(df)}")
    print(f"Mean score: {df['final'].mean():.2f}")
    print(f"Median score: {df['final'].median():.2f}")
    print(f"Std deviation: {df['final'].std():.2f}")
    print(f"Min score: {df['final'].min():.2f}")
    print(f"Max score: {df['final'].max():.2f}")


def score_distribution(df):
    print("\n" + "=" * 60)
    print("📈 SCORE DISTRIBUTION")
    print("=" * 60)

    bins = [0, 20, 40, 60, 80, 100]

    df['bucket'] = pd.cut(df['final'], bins=bins)

    dist = df['bucket'].value_counts().sort_index()

    for k, v in dist.items():
        print(f"{k}: {v} jobs ({v/len(df)*100:.1f}%)")

    # plot
    plt.figure()
    dist.plot(kind='bar')
    plt.title("Score Distribution")
    plt.xlabel("Score Range")
    plt.ylabel("Number of Jobs")
    plt.tight_layout()
    plt.show()


def top_k_analysis(df, k=20):
    print("\n" + "=" * 60)
    print(f"🏆 TOP {k} JOBS")
    print("=" * 60)

    top = df.sort_values("final", ascending=False).head(k)

    for i, row in top.iterrows():
        print(f"{row['final']:.1f}% | {row['title']} | {row['company']}")


def category_bias_check(df):
    print("\n" + "=" * 60)
    print("📊 CATEGORY BIAS CHECK")
    print("=" * 60)

    if 'job_category' not in df.columns:
        print("No category data")
        return

    group = df.groupby("job_category")["final"].mean().sort_values(ascending=False)

    print(group)

    group.plot(kind='bar')
    plt.title("Average Score by Category")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.show()


def score_spread(df):
    print("\n" + "=" * 60)
    print("📉 SCORE SPREAD ANALYSIS")
    print("=" * 60)

    p10 = np.percentile(df["final"], 10)
    p50 = np.percentile(df["final"], 50)
    p90 = np.percentile(df["final"], 90)

    print(f"P10: {p10:.2f}")
    print(f"P50: {p50:.2f}")
    print(f"P90: {p90:.2f}")

    print(f"Spread (P90 - P10): {p90 - p10:.2f}")


def correlation_analysis(df):
    print("\n" + "=" * 60)
    print("🔗 CORRELATION ANALYSIS")
    print("=" * 60)

    if "scores" in df.columns:
        print("Skipping (nested column not usable in CSV)")
        return

    cols = ["final", "penalty"]
    corr = df[cols].corr()

    print(corr)


def main():
    print("=" * 60)
    print("📊 SCORING ANALYSIS v8")
    print("=" * 60)

    df = load_data()

    basic_stats(df)
    score_distribution(df)
    top_k_analysis(df, k=20)
    category_bias_check(df)
    score_spread(df)
    correlation_analysis(df)

    print("\n✅ ANALYSIS DONE")


if __name__ == "__main__":
    main()