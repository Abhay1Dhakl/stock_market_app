import re


def normalize_text(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = re.sub(r"[^\w\s]", " ", lowered)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned
