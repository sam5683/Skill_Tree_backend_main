import re

def generate_summary(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    return " ".join(sentences[:3])