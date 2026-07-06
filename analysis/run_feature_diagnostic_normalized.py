import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # job-scraper
sys.path.insert(0, str(ROOT))


import pandas as pd
import ast
import numpy as np
import os
from matcher.normalization import normalize_series

def load_data(path):
    df = pd.read_csv(path)
    df["scores"] = df["scores"].apply(ast.literal_eval)
    df["weights"] = df["weights"].apply(ast.literal_eval)
    return df


def extract_features(df):
    hard, func, soft, sem = [], [], [], []

    for _, row in df.iterrows():
        s = row["scores"]

        hard.append(s.get("hard", 0))
        func.append(s.get("functional", 0))
        soft.append(s.get("soft", 0))
        sem.append(s.get("semantic", 0))

    return hard, func, soft, sem


def compute_normalized_contribution(df):
    hard, func, soft, sem = extract_features(df)

    hard_n = normalize_series(hard)
    func_n = normalize_series(func)
    soft_n = normalize_series(soft)
    sem_n = normalize_series(sem)

    results = []

    for i in range(len(df)):
        weights = df.iloc[i]["weights"]

        contrib = {
            "hard": hard_n[i] * weights["hard"],
            "functional": func_n[i] * weights["functional"],
            "soft": soft_n[i] * weights["soft"],
            "semantic": sem_n[i] * weights["semantic"],
        }

        total = sum(contrib.values())

        if total == 0:
            continue

        results.append({
            "hard": contrib["hard"] / total,
            "functional": contrib["functional"] / total,
            "soft": contrib["soft"] / total,
            "semantic": contrib["semantic"] / total,
        })

    return pd.DataFrame(results)


def analyze(df):
    print("\n" + "=" * 60)
    print("🔬 NORMALIZED FEATURE CONTRIBUTION")
    print("=" * 60)

    for col in ["hard", "functional", "soft", "semantic"]:
        print(f"\n📊 {col}")
        print(f"Mean  : {df[col].mean():.3f}")
        print(f"Median: {df[col].median():.3f}")


def main():
    df = load_data("scored_jobs_v8_test.csv")

    contrib = compute_normalized_contribution(df)

    print(f"Rows analyzed: {len(contrib)}")

    analyze(contrib)


if __name__ == "__main__":
    main()