from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

_embedding_cache = {}

def encode(text):
    if text in _embedding_cache:
        return _embedding_cache[text]

    vec = model.encode(text, convert_to_tensor=True)
    _embedding_cache[text] = vec
    return vec


def cosine_similarity(a, b):
    return util.cos_sim(a, b).item()
