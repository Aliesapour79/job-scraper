from sentence_transformers import SentenceTransformer, util
import numpy as np
from scipy.stats import norm
from .text_cleaner import clean_text

# ==========================================
# MODEL
# ==========================================
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ==========================================
# USER PROFILE (can be dynamic now)
# ==========================================
DEFAULT_PROFILE = """
Python Embedded Systems ESP32 IoT
Machine Learning PCB Electronics
C++ Microcontroller AI Image Processing
"""

def get_user_vector(profile_text=DEFAULT_PROFILE):
    return model.encode(profile_text, convert_to_tensor=True, normalize_embeddings=True)

user_vec = get_user_vector()

# ==========================================
# ENCODING CACHE
# ==========================================
_embedding_cache = {}

def cached_encode(text):
    text = clean_text(text)

    if text in _embedding_cache:
        return _embedding_cache[text]

    vec = model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
    _embedding_cache[text] = vec
    return vec

# ==========================================
# SCORE: SEMANTIC
# ==========================================
def semantic_score(text, user_vec):
    if not text:
        return 0

    job_vec = cached_encode(text)
    return max(0, min(util.cos_sim(user_vec, job_vec).item() * 100, 100))

# ==========================================
# KEYWORD SCORE (FIXED SCALE)
# ==========================================
def keyword_score(text, core, secondary, noise):
    text = text.lower()

    score = 0

    for kw in core:
        if kw in text:
            score += 10

    for kw in secondary:
        if kw in text:
            score += 4

    for kw in noise:
        if kw in text:
            score -= 15

    # normalize (IMPORTANT FIX)
    return np.tanh(score / 50) * 100

# ==========================================
# HYBRID SCORE (BALANCED)
# ==========================================
def hybrid_score(text, user_vec, core, secondary, noise):
    sem = semantic_score(text, user_vec)
    kw = keyword_score(text, core, secondary, noise)

    return (0.75 * sem) + (0.25 * kw)

# ==========================================
# NORMALIZATION
# ==========================================
def z_normalize(scores):
    mean = np.mean(scores)
    std = np.std(scores)

    if std == 0:
        return [50 for _ in scores]

    z = [(x - mean) / std for x in scores]
    return [round(norm.cdf(v) * 100, 2) for v in z]

# ==========================================
# MAIN
# ==========================================
def score_jobs(jobs, core_skills=None, secondary_skills=None, noise_skills=None):

    core_skills = core_skills or []
    secondary_skills = secondary_skills or []
    noise_skills = noise_skills or []

    core = [x.lower() for x in core_skills]
    secondary = [x.lower() for x in secondary_skills]
    noise = [x.lower() for x in noise_skills]

    raw_scores = []

    for job in jobs:
        text = job.get("full_text", "")
        score = hybrid_score(text, user_vec, core, secondary, noise)
        raw_scores.append(score)

    normalized = z_normalize(raw_scores)

    for i, job in enumerate(jobs):
        job["score"] = normalized[i]
        job["debug_raw_score"] = round(raw_scores[i], 2)

    return sorted(jobs, key=lambda x: x["score"], reverse=True)
