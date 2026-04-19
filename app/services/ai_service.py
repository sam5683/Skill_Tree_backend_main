import requests
from app.core.config import settings

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# -----------------------------
# Structure Detection 
# -----------------------------
def is_structured(content: str) -> bool:
    lines = content.split("\n")

    heading_count = sum(
        1 for l in lines
        if len(l.strip()) > 0
        and not l.strip().endswith(":")
        and l.strip().istitle()
    )

    paragraph_count = sum(
        1 for l in lines
        if len(l.strip()) > 40
    )

    return heading_count >= 3 and paragraph_count >= 3


# -----------------------------
# Core LLM Call
# -----------------------------
def call_llm(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise Exception("GROQ_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(GROQ_URL, headers=headers, json=data)

    print("GROQ STATUS:", response.status_code)
    print("GROQ RESPONSE:", response.text)

    if response.status_code != 200:
        raise Exception(response.text)

    result = response.json()

    return result["choices"][0]["message"]["content"]


# -----------------------------
# Improve Note (🔥 FIXED)
# -----------------------------
def improve_note_content(content: str) -> str:

    # 🔥 IMPORTANT: prevent repeated degradation
    if is_structured(content):
        return content

    prompt = f"""
You are a strict note cleaner.

Your task is NOT to rewrite or restructure the note.

You must PRESERVE the exact structure.

STRICT RULES:
- Do NOT add headings or subheadings
- Do NOT remove headings
- Do NOT change paragraph order
- Do NOT convert text into markdown
- Do NOT summarize or shorten
- Do NOT reformat lists or sections

ONLY DO:
- Fix grammar mistakes
- Fix spacing and line breaks
- Remove duplicate or broken lines

STRUCTURE LOCK:
If the note already looks structured and readable, return it unchanged.

Return ONLY the cleaned note.

Note:
{content}
"""

    return call_llm(prompt)


# -----------------------------
# Generate Summary
# -----------------------------
def generate_summary(content: str) -> str:
    prompt = f"""
You are a precise study assistant.

Task:
Summarize the note in 2–3 clean sentences.

Rules:
- DO NOT say "Here is a summary"
- DO NOT use labels like "Topic" or "Key Idea"
- Write naturally like a human explanation
- Keep it short and clear
- No bullet points
- No formatting symbols

Note:
{content}
"""
    return call_llm(prompt)