from sentence_transformers import SentenceTransformer, util
import numpy as np
from scipy.stats import norm

# ==========================================
# 1. MODEL LOAD
# ==========================================
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


# ==========================================
# 2. USER PROFILE (CORE INTENT)
# ==========================================
USER_PROFILE = """
Python, Embedded Systems, ESP32, IoT,
Machine Learning, PCB Design, Electronics,
C++, Microcontroller, AI, Image Processing
"""

user_vec = model.encode(USER_PROFILE, convert_to_tensor=True)


# ==========================================
# 3. SIMPLE EMBEDDING CACHE
# ==========================================
_embedding_cache = {}

def cached_encode(text):
    if text in _embedding_cache:
        return _embedding_cache[text]

    vec = model.encode(text, convert_to_tensor=True)
    _embedding_cache[text] = vec
    return vec


# ==========================================
# 4. CORE / SECONDARY / NOISE SYSTEM
# ==========================================

def build_skill_maps(core, secondary, noise):
    return (
        [x.lower() for x in core],
        [x.lower() for x in secondary],
        [x.lower() for x in noise]
    )


# ==========================================
# 5. SEMANTIC SCORE
# ==========================================
def semantic_score(text, user_vec):
    if not text:
        return 0

    job_vec = cached_encode(text)
    score = util.cos_sim(user_vec, job_vec).item()

    return max(0, min(score * 100, 100))


# ==========================================
# 6. KEYWORD BOOST SYSTEM (BALANCED)
# ==========================================
def keyword_boost(text, core, secondary, noise):
    if not text:
        return 0

    text = text.lower()

    boost = 0
    penalty = 0

    # CORE (high impact)
    for kw in core:
        if kw in text:
            boost += 12

    # SECONDARY (soft support)
    for kw in secondary:
        if kw in text:
            boost += 4

    # NOISE (hard penalty)
    for kw in noise:
        if kw in text:
            penalty += 25

    return boost - penalty


# ==========================================
# 7. HYBRID RAW SCORE
# ==========================================
def hybrid_score(text, user_vec, core, secondary, noise):
    sem = semantic_score(text, user_vec)
    kw = keyword_boost(text, core, secondary, noise)

    return (0.70 * sem) + (0.30 * kw)


# ==========================================
# 8. Z-NORMALIZATION (PROBABILITY STYLE)
# ==========================================
def z_normalize(scores):
    mean = np.mean(scores)
    std = np.std(scores)

    if std == 0:
        return [50 for _ in scores]

    z_scores = [(x - mean) / std for x in scores]

    return [round(norm.cdf(z) * 100, 2) for z in z_scores]


# ==========================================
# 9. MAIN SCORER (v3.2)
# ==========================================
def score_jobs(jobs, core_skills=None, secondary_skills=None, noise_skills=None):
    if not jobs:
        return []

    if core_skills is None:
        core_skills = []
    if secondary_skills is None:
        secondary_skills = []
    if noise_skills is None:
        noise_skills = []

    core, secondary, noise = build_skill_maps(
        core_skills, secondary_skills, noise_skills
    )

    raw_scores = []

    # STEP 1: RAW SCORES
    for job in jobs:
        text = job.get("full_text", "")

        score = hybrid_score(
            text,
            user_vec,
            core,
            secondary,
            noise
        )

        raw_scores.append(score)

    # STEP 2: NORMALIZE
    normalized = z_normalize(raw_scores)

    # STEP 3: INJECT RESULTS
    for i, job in enumerate(jobs):
        job["score"] = normalized[i]
        job["debug_raw_score"] = round(raw_scores[i], 2)

    # STEP 4: SORT
    return sorted(jobs, key=lambda x: x["score"], reverse=True)
