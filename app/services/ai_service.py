import logging

from app.ai.client import call_llm

logger = logging.getLogger(__name__)


# -----------------------------
# Structure Detection
# -----------------------------
def is_structured(content: str) -> bool:

    if not content:
        return False

    lines = [l.strip() for l in content.split("\n") if l.strip()]

    if len(lines) < 4:
        return False

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

    # Headings
    heading_count = sum(
        1 for l in lines
        if len(l.split()) <= 6 and l[:1].isupper()
    )

    # Key-value
    section_count = sum(
        1 for l in lines
        if ":" in l and len(l.split()) <= 10
    )

    # Paragraphs
    paragraph_count = sum(
        1 for l in lines
        if len(l) > 60
    )

    # Tables
    table_like = any("|" in l for l in lines)

    # Diagrams
    diagram_like = any(
        "->" in l or "=>" in l or "→" in l
        for l in lines
    )

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

    return structure_score >= 4


# -----------------------------
# Improve Note
# -----------------------------
async def improve_note_content(content: str) -> str:

    if not content or len(content.strip()) < 20:
        return content

    # Preserve structured content
    if is_structured(content):
        return content

    prompt = f"""
You are a high-precision note reconstruction system.

Your job is to convert messy or OCR-extracted text into clean, readable notes.

--------------------------------------------------
CORE OBJECTIVES
--------------------------------------------------
1. Remove noise
2. Preserve original meaning
3. Improve readability
4. Reconstruct only when meaning is obvious

--------------------------------------------------
RULES
--------------------------------------------------
- NEVER hallucinate
- NEVER invent information
- Preserve tables/diagrams/code
- Keep meaning EXACT
- Remove OCR junk only

--------------------------------------------------
OUTPUT RULES
--------------------------------------------------
- Return ONLY cleaned notes
- No explanations
- No introductions

--------------------------------------------------
INPUT:
{content}
"""

    result = await call_llm(
        prompt=prompt,
        system_prompt="You are a high-precision note reconstruction system.",
        temperature=0.3
    )

    return result if result else content


# -----------------------------
# Generate Summary
# -----------------------------
async def generate_summary(content: str) -> str:

    if not content or len(content.strip()) < 20:
        return ""

    prompt = f"""
You are a high-precision summarization system.

----------------------------------
RULES
----------------------------------
- Maximum 2 lines
- No fluff
- No hallucination
- Clear and concise

----------------------------------
INPUT:
{content}
"""

    result = await call_llm(
        prompt=prompt,
        system_prompt="You are a high-precision summarization system.",
        temperature=0.3
    )

    return result if result else ""