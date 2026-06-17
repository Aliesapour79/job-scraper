import numpy as np
from scipy.stats import norm

from nlp.embeddings import encode, cosine_similarity
from nlp.text_cleaner import clean_text


# ==========================================
# USER PROFILE (FA + EN MIXED)
# ==========================================
USER_PROFILE = """
Python, Embedded Systems, ESP32, IoT, Machine Learning, AI,
پردازش تصویر, هوش مصنوعی, الکترونیک, طراحی مدار, میکروکنترلر,
برنامه نویسی, تحلیل داده, C++, Linux, شبکه
"""

user_vec = encode(USER_PROFILE)


# ==========================================
# KEYWORDS (BOOST not FILTER)
# ==========================================
KEYWORDS = [
    "python", "iot", "esp32", "embedded",
    "machine learning", "ai", "pcb",
    "الکترونیک", "میکروکنترلر", "هوش مصنوعی",
    "برنامه نویسی", "پردازش تصویر"
]


def keyword_score(text):
    if not text:
        return 0

    text = clean_text(text)
    score = 0

    for kw in KEYWORDS:
        if kw in text:
            score += 1

    return min(score * 3, 25)  # فقط boost


# ==========================================
# SEMANTIC SCORE
# ==========================================
def semantic_score(text):
    if not text:
        return 0

    text = clean_text(text)

    job_vec = encode(text)
    score = cosine_similarity(user_vec, job_vec)

    return max(0, min(score * 100, 100))


# ==========================================
# HYBRID SCORE
# ==========================================
def hybrid_score(text):
    sem = semantic_score(text)
    kw = keyword_score(text)

    # semantic dominant
    return (0.85 * sem) + (0.15 * kw)


# ==========================================
# Z-SCORE NORMALIZATION → PROBABILITY
# ==========================================
def z_normalize(scores):
    mean = np.mean(scores)
    std = np.std(scores)

    if std == 0:
        return [50 for _ in scores]

    z_scores = [(x - mean) / std for x in scores]
    return [round(norm.cdf(z) * 100, 2) for z in z_scores]


# ==========================================
# MAIN ENGINE V3.1
# ==========================================
def score_jobs(jobs):
    if not jobs:
        return []

    raw_scores = []

    # STEP 1: RAW SCORES
    for job in jobs:
        text = job.get("full_text", "")
        raw_scores.append(hybrid_score(text))

    # STEP 2: NORMALIZATION
    final_scores = z_normalize(raw_scores)

    # STEP 3: INJECT
    for i, job in enumerate(jobs):
        job["score"] = final_scores[i]
        job["score_raw"] = round(raw_scores[i], 2)

    # STEP 4: SORT
    return sorted(jobs, key=lambda x: x["score"], reverse=True)
