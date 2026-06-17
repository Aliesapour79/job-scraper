from sentence_transformers import SentenceTransformer, util
from functools import lru_cache
import torch

# ==========================================
# MODEL (lazy + safe load)
# ==========================================
_device = "cuda" if torch.cuda.is_available() else "cpu"

model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2",
    device=_device
)

# ==========================================
# ENCODING (cached + optimized)
# ==========================================
@lru_cache(maxsize=2000)
def encode(text: str):
    if not text:
        return None

    return model.encode(
        text,
        convert_to_tensor=True,
        normalize_embeddings=True
    )


# ==========================================
# COSINE SIMILARITY
# ==========================================
def cosine_similarity(a, b):
    if a is None or b is None:
        return 0.0

    return util.cos_sim(a, b).item()
