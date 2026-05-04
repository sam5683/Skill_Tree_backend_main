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
    if not content:
        return False

    lines = [l.strip() for l in content.split("\n") if l.strip()]

    if len(lines) < 4:
        return False

    # --- SIGNALS OF STRUCTURE ---

    # Bullet points
    bullet_count = sum(
        1 for l in lines
        if l.startswith(("-", "*", "•"))
    )

    # Numbered lists
    numbered_count = sum(
        1 for l in lines
        if l[:2].isdigit() or l[:3].replace(".", "").isdigit()
    )

    # Headings (short + capitalized)
    heading_count = sum(
        1 for l in lines
        if len(l.split()) <= 6 and l[:1].isupper()
    )

    # Key-value / section style (e.g. "Client Request:")
    section_count = sum(
        1 for l in lines
        if ":" in l and len(l.split()) <= 10
    )

    # Long readable lines (paragraphs)
    paragraph_count = sum(
        1 for l in lines
        if len(l) > 60
    )

    # Table detection
    table_like = any("|" in l for l in lines)

    # Diagram detection (flow arrows etc.)
    diagram_like = any("->" in l or "=>" in l or "→" in l for l in lines)

    # --- DECISION LOGIC (deterministic) ---

    structure_score = 0

    if bullet_count >= 3:
        structure_score += 2

    if numbered_count >= 2:
        structure_score += 2

    if heading_count >= 2:
        structure_score += 1

    if section_count >= 2:
        structure_score += 2

    if paragraph_count >= 2:
        structure_score += 1

    if table_like:
        structure_score += 3

    if diagram_like:
        structure_score += 2

    # --- FINAL DECISION ---

    return structure_score >= 4

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

Your job is to convert messy or OCR-extracted text into clean, readable notes.

--------------------------------------------------
CORE OBJECTIVES
--------------------------------------------------
1. Remove noise (OCR junk, UI text, broken fragments)
2. Preserve original meaning and intent
3. Improve readability and structure
4. Reconstruct only when meaning is clear

--------------------------------------------------
STEP 1 — FILTER NOISE
--------------------------------------------------
Remove lines that are clearly not useful:

- Website navigation (BLOG | ABOUT | etc.)
- Random symbols or broken words
- Repeated fragments
- Headers/footers from websites
- Unreadable OCR artifacts

Keep anything that might carry meaning.
----------------------------------
IMPORTANT: STRUCTURED DATA PRESERVATION
----------------------------------
DO NOT remove or alter:

- Tables (rows, columns, | separators)
- Diagrams (arrows →, =>, flow-like text)
- Code-like structures
- Numbered steps or sequences

If content looks structured (table/diagram/code):
→ PRESERVE it as is
→ Only clean surrounding noise

--------------------------------------------------
STEP 2 — PRESERVE INTENT
--------------------------------------------------
- Keep original meaning EXACT
- Do not rewrite personal tone unnecessarily
- Do not over-formalize simple notes
- Do not remove useful but imperfect content

--------------------------------------------------
STEP 3 — SAFE RECONSTRUCTION
--------------------------------------------------
You may fix or complete text ONLY if:

✔ Meaning is obvious  
✔ Context is clear  
✔ Confidence is high  

Otherwise → leave it as is

NEVER guess or invent information.

--------------------------------------------------
STEP 4 — STRUCTURE FOR READABILITY
--------------------------------------------------
Improve structure where needed:

- Use headings if clearly implied
- Use bullet points for lists
- Break long paragraphs
- Group related ideas

Avoid over-formatting.

--------------------------------------------------
STEP 5 — STRICT RULES
--------------------------------------------------
- NEVER change meaning
- NEVER add new information
- NEVER hallucinate
- ONLY remove clear noise
- KEEP meaningful content even if imperfect

--------------------------------------------------
OUTPUT RULES (CRITICAL)
--------------------------------------------------
- Return ONLY the final cleaned note
- DO NOT explain anything
- DO NOT describe steps
- DO NOT add introductions or conclusions
- DO NOT include phrases like:
  "Here is", "Based on", "I have", etc.

The output must look like clean, well-structured notes.

--------------------------------------------------
INPUT:
{content}
----------------------------------
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