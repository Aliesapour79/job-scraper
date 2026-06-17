import re

# basic Persian + English stop noise removal
STOP_CHARS = r"[^\w\s\u0600-\u06FF]"

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    # remove punctuation
    text = re.sub(STOP_CHARS, " ", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text
