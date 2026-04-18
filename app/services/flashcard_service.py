from sqlalchemy.orm import Session
from datetime import datetime
import re

from app.models.flashcard import Flashcard
from app.models.note import Note
from app.services.srs_service import update_srs


MAX_CARDS = 12
MIN_LEN = 20


# --------------------------------------------------
# CLEAN / NORMALIZE
# --------------------------------------------------
def normalize_line(line: str):
    line = line.strip()

    # remove numbering: "1. ", "2. "
    line = re.sub(r"^\d+\.\s*", "", line)

    # remove labels like "High Performance:"
    line = re.sub(r"^[A-Za-z\s]+:\s*", "", line)

    # fix spacing
    line = re.sub(r"\s+", " ", line)

    return line


def is_valid(line: str):
    if len(line) < MIN_LEN:
        return False

    # reject weak sentence starts
    if line.lower().startswith(("this", "that", "it", "there")):
        return False

    # reject code-like lines
    if any(x in line for x in ["(", ")", "=", "import", "print", "def ", "class "]):
        return False

    # reject fragments (not proper sentence)
    if not line[0].isupper():
        return False

    return True


# --------------------------------------------------
# 1. QUESTIONS
# --------------------------------------------------
def extract_questions(lines):
    cards = []

    for i, raw in enumerate(lines):
        line = normalize_line(raw)

        if not line.endswith("?"):
            continue

        if not is_valid(line):
            continue

        answer = ""
        for j in range(i + 1, len(lines)):
            next_line = normalize_line(lines[j])
            if next_line:
                answer = next_line
                break

        if answer and len(answer) > 10:
            cards.append((line, answer))

    return cards


# --------------------------------------------------
# 2. DEFINITIONS (X is Y)
# --------------------------------------------------
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

        # reject weak subjects
        if len(subject.split()) > 6:
            continue

        if subject.lower().startswith(("what", "how", "why")):
            continue

        if subject.lower().startswith(("ensures", "provides", "handles")):
            continue

        if subject.lower().startswith(("in short", "overall", "basically")):
            continue

        if len(value) < 10:
            continue

        q = f"What is {subject}?"
        a = value

        cards.append((q, a))

    return cards


# --------------------------------------------------
# 3. LABEL: DESCRIPTION
# --------------------------------------------------
def extract_labeled(lines):
    cards = []

    for raw in lines:
        if ":" not in raw:
            continue

        parts = raw.split(":", 1)

        title = parts[0].strip()
        desc = normalize_line(parts[1])

        if len(title) < 3 or len(desc) < 10:
            continue

        if title.lower().startswith(("this", "it", "there")):
            continue

        if any(x in desc for x in ["(", ")", "=", "import", "print"]):
            continue

        q = f"What is {title}?"
        a = desc

        cards.append((q, a))

    return cards


# --------------------------------------------------
# 4. SENTENCE EXTRACTION (controlled)
# --------------------------------------------------
def extract_sentences(lines):
    cards = []

    verbs = (
        "ensures", "provides", "allows",
        "handles", "manages", "improves",
        "supports", "reduces", "increases"
    )

    for raw in lines:
        line = normalize_line(raw)

        if not is_valid(line):
            continue

        if " is " in line.lower():
            continue

        words = line.split()
        if len(words) < 6:
            continue

        for v in verbs:
            if v in line.lower():
                subject = " ".join(words[:3])
                rest = line.split(v, 1)[-1].strip()

                if len(rest) < 8:
                    continue

                q = f"What does {subject} {v}?"
                a = rest

                cards.append((q, a))
                break

    return cards


# --------------------------------------------------
# DEDUP
# --------------------------------------------------
def deduplicate(cards):
    seen_q = set()
    result = []

    for q, a in cards:
        key = re.sub(r'\W+', '', q.lower())

        if key not in seen_q:
            seen_q.add(key)
            result.append((q, a))

    return result


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def create_flashcards_from_note(db: Session, note_id: int, user_id: int):
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == user_id
    ).first()

    if not note:
        return None

    raw_lines = [l for l in note.content.split("\n") if l.strip()]

    db.query(Flashcard).filter(
        Flashcard.note_id == note_id
    ).delete()

    cards = []

    cards += extract_questions(raw_lines)
    cards += extract_definitions(raw_lines)
    cards += extract_labeled(raw_lines)
    cards += extract_sentences(raw_lines)

    cards = deduplicate(cards)
    cards = cards[:MAX_CARDS]

    flashcards = []

    for q, a in cards:
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


# --------------------------------------------------
# OTHER
# --------------------------------------------------
def delete_all_flashcards(db: Session, user_id: int):
    db.query(Flashcard).filter(
        Flashcard.user_id == user_id
    ).delete()
    db.commit()


def get_due_flashcards(db: Session, user_id: int):
    return db.query(Flashcard).filter(
        Flashcard.user_id == user_id,
        Flashcard.due_date <= datetime.utcnow()
    ).limit(50).all()


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