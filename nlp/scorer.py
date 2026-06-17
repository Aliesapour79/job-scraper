from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

USER_PROFILE = """
Python, Embedded Systems, ESP32, IoT, Machine Learning, PCB Design, C++
"""

user_vec = model.encode(USER_PROFILE, convert_to_tensor=True)


def semantic_score(text):
    job_vec = model.encode(text, convert_to_tensor=True)
    return util.cos_sim(user_vec, job_vec).item() * 100
