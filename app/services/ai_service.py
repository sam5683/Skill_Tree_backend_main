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

    if not content or len(content.strip()) < 20:
        return content

    # 🔥 Keep your guard
    if is_structured(content):
        return content

    prompt = f"""
You are a high-precision note reconstruction system.

Your goal is NOT just editing.
Your goal is to:
1. CLEAN noise
2. PRESERVE meaning
3. STRUCTURE content
4. RECONSTRUCT only when safe

----------------------------------
STEP 1: CLASSIFY EACH LINE
----------------------------------
For every line, classify:

- SIGNAL → meaningful content
- NOISE → OCR junk, UI text, broken fragments

NOISE examples:
- website headers/footers
- random symbols or broken words
- navigation text (BLOG | ABOUT | etc.)
- repeated garbage fragments
- incomplete unreadable tokens

REMOVE noise aggressively.

----------------------------------
STEP 2: PRESERVE USER INTENT
----------------------------------
- If content is already clear → KEEP it
- If user wrote personal notes → DO NOT rewrite tone
- Do NOT over-formalize human writing

----------------------------------
STEP 3: SMART RECONSTRUCTION (CRITICAL)
----------------------------------
You MAY reconstruct missing or broken parts ONLY IF:

✔ Context is clear
✔ Meaning is obvious
✔ Confidence is HIGH

Examples:
- "Avoidant Atta" → "Avoidant Attachment Style" ✅
- Broken sentence → fix grammar ✅

If uncertain:
→ KEEP original text

NEVER invent facts.

----------------------------------
STEP 4: STRUCTURE OUTPUT
----------------------------------
Convert into clean readable format:

- Add headings when obvious
- Use bullet points for lists
- Break long paragraphs
- Group related ideas

DO NOT over-structure.

----------------------------------
STEP 5: STRICT RULES
----------------------------------
- NEVER change meaning
- NEVER add new concepts
- NEVER hallucinate missing info
- REMOVE only clear noise
- KEEP valuable imperfect content

----------------------------------
STEP 6: OUTPUT STYLE
----------------------------------
- Clean
- Human-like
- Readable
- Structured
- Not robotic

----------------------------------
STEP 7: IDEMPOTENT
----------------------------------
Running this again should NOT change output.

----------------------------------
INPUT:
{content}

----------------------------------
OUTPUT:
Return ONLY the cleaned and structured note.
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

    if not content or len(content.strip()) < 20:
        return ""
    
    prompt = f"""
You are a high-precision summarization system.

Your goal is to extract the CORE meaning of the note.

----------------------------------
OUTPUT REQUIREMENTS
----------------------------------
- Maximum 2 lines (prefer 1 line if possible)
- No fluff, no filler words
- No meta phrases ("This note explains...")
- No labels or formatting
- Must be clear and meaningful on its own

----------------------------------
HOW TO THINK
----------------------------------
1. Identify the main topic
2. Identify the key idea or takeaway
3. Ignore examples, noise, and repetition

----------------------------------
STRICT RULES
----------------------------------
- DO NOT repeat sentences from input
- DO NOT list points
- DO NOT generalize vaguely
- DO NOT hallucinate missing info

----------------------------------
QUALITY CHECK (IMPORTANT)
----------------------------------
The summary must answer:
"What would someone learn from this note in one glance?"

----------------------------------
INPUT:
{content}

----------------------------------
OUTPUT:
Return ONLY the summary.

"""
    result = call_llm(prompt)
    return result if result else ""