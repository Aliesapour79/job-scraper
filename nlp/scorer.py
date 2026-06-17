from sentence_transformers import SentenceTransformer, util
import numpy as np
from .text_cleaner import clean_text

# ==========================================
# MODEL
# ==========================================
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ==========================================
# USER PROFILE (Balanced + Bilingual)
# ==========================================
DEFAULT_PROFILE = """
IoT, Embedded Systems, ESP32, Microcontrollers, Electronics, PCB Design, Circuit Design,
Python, C++, Machine Learning, Artificial Intelligence, Computer Vision, Image Processing,
Data Analysis, Signal Processing, Automation, Industrial Control Systems,
Linux, Networking, Git, Database (MySQL, SQLite, MongoDB),

برنامه نویسی پایتون، برنامه نویسی C++، اینترنت اشیاء، سیستم‌های نهفته، الکترونیک،
طراحی مدار، میکروکنترلر، پردازش تصویر، هوش مصنوعی، یادگیری ماشین، تحلیل داده،
اتوماسیون صنعتی، شبکه، پایگاه داده
"""

def get_user_vector(profile_text=DEFAULT_PROFILE):
    return model.encode(profile_text, convert_to_tensor=True, normalize_embeddings=True)

user_vec = get_user_vector()

# ==========================================
# CACHE
# ==========================================
_embedding_cache = {}

def cached_encode(text):
    text = clean_text(text)

    if not text:
        return None

    if text in _embedding_cache:
        return _embedding_cache[text]

    vec = model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
    _embedding_cache[text] = vec
    return vec

# ==========================================
# SEMANTIC SCORE
# ==========================================
def semantic_score(text):
    if not text:
        return 0

    job_vec = cached_encode(text)
    if job_vec is None:
        return 0

    score = util.cos_sim(user_vec, job_vec).item()
    return max(0, min(score * 100, 100))

# ==========================================
# KEYWORD SCORE (stable scaled)
# ==========================================
def keyword_score(text, core, secondary, noise):
    text = text.lower()

    score = 0

    # CORE boost
    for kw in core:
        if kw in text:
            score += 12

    # SECONDARY boost
    for kw in secondary:
        if kw in text:
            score += 5

    # NOISE penalty
    for kw in noise:
        if kw in text:
            score -= 20

    # stable scaling
    return np.tanh(score / 40) * 100

# ==========================================
# HYBRID SCORE (balanced)
# ==========================================
def hybrid_score(text, core, secondary, noise):
    sem = semantic_score(text)
    kw = keyword_score(text, core, secondary, noise)

    # balanced fusion
    return (0.65 * sem) + (0.35 * kw)

# ==========================================
# NORMALIZATION (SAFE VERSION)
# ==========================================
def minmax_normalize(scores):
    if not scores:
        return []

    min_s = min(scores)
    max_s = max(scores)

    if max_s == min_s:
        return [50 for _ in scores]

    return [
        ((s - min_s) / (max_s - min_s)) * 100
        for s in scores
    ]

# ==========================================
# MAIN SCORER
# ==========================================
def score_jobs(jobs, core_skills=None, secondary_skills=None, noise_skills=None):

    if not jobs:
        return []

    core_skills = core_skills or []
    secondary_skills = secondary_skills or []
    noise_skills = noise_skills or []

    core = [x.lower() for x in core_skills]
    secondary = [x.lower() for x in secondary_skills]
    noise = [x.lower() for x in noise_skills]

    raw_scores = []

    # STEP 1: RAW SCORES
    for job in jobs:
        text = job.get("full_text", "")

        score = hybrid_score(text, core, secondary, noise)
        raw_scores.append(score)

    # STEP 2: NORMALIZE (SAFE)
    normalized = minmax_normalize(raw_scores)

    # STEP 3: APPLY SCORES
    for i, job in enumerate(jobs):
        job["score"] = round(normalized[i], 2)
        job["debug_raw_score"] = round(raw_scores[i], 2)

    # STEP 4: SORT
    return sorted(jobs, key=lambda x: x["score"], reverse=True)
