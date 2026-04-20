from sqlalchemy.orm import Session
from datetime import datetime
import re
import requests

from app.models.flashcard import Flashcard
from app.models.note import Note
from app.services.srs_service import update_srs
from app.core.config import settings


# -----------------------------
# CONFIG
# -----------------------------
MAX_CARDS = 12
MIN_LEN = 20
USE_AI_ENHANCER = True  # toggle


# -----------------------------
# GROQ CONFIG
# -----------------------------
GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# -----------------------------
# LLM CALL
# -----------------------------
def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You improve flashcards."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    res = requests.post(GROQ_URL, headers=headers, json=data)

    if res.status_code != 200:
        return None

    return res.json()["choices"][0]["message"]["content"]


# -----------------------------
# NORMALIZE
# -----------------------------
def normalize_line(line: str):
    line = line.strip()

    # remove numbering like "1. "
    line = re.sub(r"^\d+\.\s*", "", line)

    # normalize spaces
    line = re.sub(r"\s+", " ", line)

    return line


# -----------------------------
# VALIDATION (FIXED)
# -----------------------------
def is_valid(line: str):
    if len(line) < MIN_LEN:
        return False

    if not line[0].isupper():
        return False

    # allow technical content now ✅
    if line.count("=") > 3:
        return False

    return True


# -----------------------------
# MULTI-LINE ANSWER EXTRACTION 🔥
# -----------------------------
def extract_answer_block(lines, start_index):
    answer_lines = []

    for j in range(start_index + 1, len(lines)):
        line = normalize_line(lines[j])

        if not line:
            break

        if line.endswith("?"):
            break

        answer_lines.append(line)

        if len(" ".join(answer_lines)) > 200:
            break

    return " ".join(answer_lines)


# -----------------------------
# QUESTION EXTRACTION
# -----------------------------
def extract_questions(lines):
    cards = []

    for i, raw in enumerate(lines):
        line = normalize_line(raw)

        if not line.endswith("?"):
            continue

        if not is_valid(line):
            continue

        answer = extract_answer_block(lines, i)

        if len(answer) > 10:
            cards.append((line, answer))

    return cards


# -----------------------------
# DEFINITIONS
# -----------------------------
def extract_definitions(lines):
    cards = []

    for raw in lines:
        line = normalize_line(raw)

        if not is_valid(line):
            continue

        match = re.match(r"(.+?)\s+(is|are)\s+(.+)", line, re.IGNORECASE)
        if not match:
            continue

        subject = match.group(1).strip()
        value = match.group(3).strip()

        if len(subject.split()) > 6:
            continue

        if len(value) < 10:
            continue

        q = f"What is {subject}?"
        a = value

        cards.append((q, a))

    return cards


# -----------------------------
# LABELED
# -----------------------------
def extract_labeled(lines):
    cards = []

    for raw in lines:
        if ":" not in raw:
            continue

        title, desc = raw.split(":", 1)

        title = title.strip()
        desc = normalize_line(desc)

        if len(title) < 3 or len(desc) < 10:
            continue

        q = f"What is {title}?"
        a = desc

        cards.append((q, a))

    return cards


# -----------------------------
# BULLETS + NUMBERED 🔥
# -----------------------------
def extract_bullets(lines):
    cards = []

    for raw in lines:
        line = raw.strip()

        if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
            clean = normalize_line(line)

            if len(clean) > 20:
                q = f"What does this mean: {clean[:40]}?"
                a = clean
                cards.append((q, a))

    return cards


# -----------------------------
# REFINE QUESTION
# -----------------------------
def refine_question(q):
    q = q.strip()
    q = re.sub(r"\s+", " ", q)
    q = q.replace("What does", "How does")
    return q


# -----------------------------
# DEDUP
# -----------------------------
def deduplicate(cards):
    seen = set()
    result = []

    for q, a in cards:
        key = re.sub(r'\W+', '', q.lower())

        if key not in seen:
            seen.add(key)
            result.append((q, a))

    return result


# -----------------------------
# SCORING
# -----------------------------
def score_card(q, a):
    score = 0

    if len(q.split()) <= 12:
        score += 2

    if 8 <= len(a.split()) <= 40:
        score += 3

    if not a.lower().startswith(("it ", "this ", "there ")):
        score += 2

    if any(v in a.lower() for v in ["ensures", "allows", "manages", "improves"]):
        score += 2

    return score


# -----------------------------
# AI ENHANCER (SAFE)
# -----------------------------
def enhance_flashcard(q, a):
    if not GROQ_API_KEY:
        return q, a

    prompt = f"""
Improve this flashcard WITHOUT changing meaning.

Rules:
- Keep meaning EXACT
- Make question clearer
- Make answer concise (1-2 lines max)
- Do NOT add new info

Q: {q}
A: {a}

Return:
Q: ...
A: ...
"""

    result = call_llm(prompt)

    if not result:
        return q, a

    try:
        lines = result.split("\n")
        new_q = lines[0].replace("Q:", "").strip()
        new_a = lines[1].replace("A:", "").strip()
        return new_q, new_a
    except:
        return q, a


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def create_flashcards_from_note(db: Session, note_id: int, user_id: int):
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == user_id
    ).first()

    if not note:
        return None

    raw_lines = [l for l in note.content.split("\n") if l.strip()]

    # delete old
    db.query(Flashcard).filter(
        Flashcard.note_id == note_id
    ).delete()

    # extraction
    candidates = []
    candidates += extract_questions(raw_lines)
    candidates += extract_definitions(raw_lines)
    candidates += extract_labeled(raw_lines)
    candidates += extract_bullets(raw_lines)

    # refine
    refined = [(refine_question(q), a) for q, a in candidates]

    # dedup
    refined = deduplicate(refined)

    # score
    scored = [(q, a, score_card(q, a)) for q, a in refined]
    scored.sort(key=lambda x: x[2], reverse=True)

    best_cards = [(q, a) for q, a, _ in scored[:MAX_CARDS]]

    # 🔥 AI enhancer (optional)
    if USE_AI_ENHANCER:
        best_cards = [enhance_flashcard(q, a) for q, a in best_cards]

    flashcards = []

    for q, a in best_cards:
        card = Flashcard(
            note_id=note_id,
            user_id=user_id,
            question=q,
            answer=a,
            ease_factor=2.5,
            interval=1,
            repetitions=0,
            due_date=datetime.utcnow(),
            created_at=datetime.utcnow()
        )

        db.add(card)
        flashcards.append(card)

    db.commit()
    return flashcards


# -----------------------------
# OTHER (unchanged)
# -----------------------------
def get_due_flashcards(db: Session, user_id: int):
    return db.query(Flashcard).filter(
        Flashcard.user_id == user_id,
        Flashcard.due_date <= datetime.utcnow()
    ).limit(20).all()


def review_flashcard(db: Session, card_id: int, rating: str, user_id: int):
    card = db.query(Flashcard).filter(
        Flashcard.id == card_id,
        Flashcard.user_id == user_id
    ).first()

    if not card:
        return None

    update_srs(card, rating)

    db.commit()
    db.refresh(card)

    return card


def get_flashcards_for_note(db: Session, note_id: int, user_id: int):
    return db.query(Flashcard).filter(
        Flashcard.note_id == note_id,
        Flashcard.user_id == user_id
    ).all()


def delete_all_flashcards(db: Session, user_id: int):
    db.query(Flashcard).filter(
        Flashcard.user_id == user_id
    ).delete()
    db.commit()