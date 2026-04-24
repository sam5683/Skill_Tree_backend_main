import requests
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        logger.error("GROQ_API_KEY not set")
        return None

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

    try:
        response = requests.post(GROQ_URL, headers=headers, json=data, timeout=5)

        if response.status_code != 200:
            logger.error(f"GROQ failed: {response.status_code} - {response.text}")
            return None

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except requests.RequestException as e:
        logger.error(f"GROQ request error: {str(e)}")
        return None


# -----------------------------
# Improve Note (SMART STRUCTURE)
# -----------------------------
def improve_note_content(content: str) -> str:

    # 🔥 Keep your guard
    if is_structured(content):
        return content

    prompt = f"""
You are a precise note optimizer.

Your goal is to CLEAN notes ONLY IF they are messy or unclear.
DO NOT restructure content that is already readable.
DO NOT change meaning or harm good content.

Think in 2 layers:
1. PRESERVE what is already good
2. FIX only what is messy or unclear

-----------------------
CRITICAL DECISION STEP
-----------------------
Before making ANY change:

Ask:
Is this note already readable and meaningful?

If YES:
→ Return it unchanged (except minor grammar fixes)

If NO:
→ Apply improvements carefully, but do NOT change meaning.

-----------------------
STRICT RULES (CRITICAL)
-----------------------
- NEVER change meaning
- NEVER rewrite correct definitions
- NEVER remove useful information
- NEVER reorder logical sections
- NEVER modify already structured parts

-----------------------
DO NOT TOUCH IF ALREADY GOOD:
-----------------------
- Proper definitions
- Existing bullet points
- Already formatted sections (**bold**, *, -)
- Clean paragraphs

-----------------------
YOU MAY IMPROVE ONLY IF NEEDED:
-----------------------
- Fix grammar and broken sentences
- Remove duplicate lines
- Remove incomplete or meaningless fragments
- Fix spacing and line breaks

-----------------------
SMART STRUCTURING (ONLY FOR RAW TEXT):
-----------------------
If a section is messy or unstructured:
- Convert into clean bullet points when appropriate
- Group related ideas together
- Add light emphasis using **bold** ONLY for key terms
- Break long paragraphs into readable chunks

-----------------------
IMPORTANT BEHAVIOR:
-----------------------
- Work LOCALLY (line by line), not globally
- If content is already clean → leave it EXACTLY as is
- If partially messy → fix ONLY those parts
- Output must look natural, not AI-generated

-----------------------
IDEMPOTENT RULE:
-----------------------
If this prompt is applied again, the output should NOT change.

-----------------------
OUTPUT:
-----------------------
Return ONLY the improved note. No explanation.

-----------------------
NOTE:
{content}
"""

    result = call_llm(prompt)
    return result if result else content

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
    result = call_llm(prompt)
    return result if result else ""