from sentence_transformers import SentenceTransformer, util
import numpy as np

# ==========================================
# 1. LOAD MODEL
# ==========================================
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ==========================================
# 2. USER PROFILE (مهارت‌های شما)
# ==========================================
USER_PROFILE = """
Python, Embedded Systems, ESP32, IoT, Machine Learning, PCB Design, C++
"""

user_vec = model.encode(USER_PROFILE, convert_to_tensor=True)


# ==========================================
# 3. SEMANTIC SCORING (Embedding)
# ==========================================
def semantic_score(text):
    """
    محاسبه شباهت معنایی بین job و پروفایل کاربر
    """
    if not text:
        return 0

    job_vec = model.encode(text, convert_to_tensor=True)
    score = util.cos_sim(user_vec, job_vec).item()

    return score * 100  # تبدیل به 0-100


# ==========================================
# 4. Z-SCORE NORMALIZATION
# ==========================================
def z_normalize(scores):
    """
    نرمال‌سازی آماری برای قابل مقایسه شدن امتیازها
    """
    mean = np.mean(scores)
    std = np.std(scores)

    if std == 0:
        return [50 for _ in scores]

    return [
        50 + (x - mean) / std * 15
        for x in scores
    ]


# ==========================================
# 5. MAIN SCORING ENGINE (v2 core)
# ==========================================
def score_jobs(jobs):
    """
    ورودی: لیست job ها
    خروجی: job ها با score هوشمند + مرتب‌شده
    """

    if not jobs:
        return []

    semantic_scores = []

    # 1. محاسبه امتیاز معنایی برای همه jobها
    for job in jobs:
        text = job.get("full_text", "")
        semantic_scores.append(semantic_score(text))

    # 2. نرمال‌سازی آماری
    normalized_scores = z_normalize(semantic_scores)

    # 3. تزریق score داخل jobها
    for i, job in enumerate(jobs):
        job["score"] = round(normalized_scores[i], 2)

    # 4. مرتب‌سازی بر اساس بهترین تطابق
    return sorted(jobs, key=lambda x: x["score"], reverse=True)
