from sentence_transformers import SentenceTransformer, util
import numpy as np
from scipy.stats import norm

# ==========================================
# 1. LOAD MODEL
# ==========================================
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ==========================================
# 2. USER PROFILE (می‌تونی بعداً dynamicش کنی)
# ==========================================
USER_PROFILE = """
Python, Embedded Systems, ESP32, IoT, Machine Learning, PCB Design, C++, Electronics, Control Systems
"""

user_vec = model.encode(USER_PROFILE, convert_to_tensor=True)

# ==========================================
# 3. SIMPLE CACHE (performance boost)
# ==========================================
_embedding_cache = {}

def cached_encode(text):
    """Cache embedding to avoid recomputation"""
    if text in _embedding_cache:
        return _embedding_cache[text]

    vec = model.encode(text, convert_to_tensor=True)
    _embedding_cache[text] = vec
    return vec

# ==========================================
# 4. SEMANTIC SCORE (cosine similarity)
# ==========================================
def semantic_score(text):
    """
    محاسبه شباهت معنایی بین job و پروفایل کاربر
    خروجی: 0 تا 100
    """
    if not text:
        return 0

    job_vec = cached_encode(text)
    score = util.cos_sim(user_vec, job_vec).item()

    return max(0, min(score * 100, 100))


# ==========================================
# 5. KEYWORD BACKUP SCORE (light hybrid)
# ==========================================
KEYWORDS = [
    "python", "embedded", "iot", "esp32",
    "machine learning", "pcb", "c++", "electronic"
]

def keyword_score(text):
    """Fallback keyword signal"""
    if not text:
        return 0

    text = text.lower()
    score = 0

    for kw in KEYWORDS:
        if kw in text:
            score += 5

    return min(score, 30)  # cap to avoid domination


# ==========================================
# 6. Z-SCORE → PROBABILITY NORMALIZATION
# ==========================================
def z_normalize(scores):
    """
    تبدیل distribution به probability (0-100)
    """
    mean = np.mean(scores)
    std = np.std(scores)

    if std == 0:
        return [50 for _ in scores]

    z_scores = [(x - mean) / std for x in scores]

    return [round(norm.cdf(z) * 100, 2) for z in z_scores]


# ==========================================
# 7. MAIN SCORING ENGINE (V2.5)
# ==========================================
def score_jobs(jobs):
    """
    ورودی: لیست jobها
    خروجی: jobها با score نهایی + sorted
    """

    if not jobs:
        return []

    semantic_scores = []

    # ==========================================
    # STEP 1: RAW SEMANTIC SCORES
    # ==========================================
    for job in jobs:
        text = job.get("full_text", "")

        sem = semantic_score(text)
        kw = keyword_score(text)

        # hybrid raw score
        raw_score = (0.8 * sem) + (0.2 * kw)

        semantic_scores.append(raw_score)

    # ==========================================
    # STEP 2: NORMALIZATION
    # ==========================================
    normalized_scores = z_normalize(semantic_scores)

    # ==========================================
    # STEP 3: INJECT BACK INTO JOBS
    # ==========================================
    for i, job in enumerate(jobs):
        job["score"] = normalized_scores[i]

        # optional debug info (خیلی مفید برای آینده)
        job["debug_score_raw"] = round(semantic_scores[i], 2)

    # ==========================================
    # STEP 4: SORT
    # ==========================================
    return sorted(jobs, key=lambda x: x["score"], reverse=True)
