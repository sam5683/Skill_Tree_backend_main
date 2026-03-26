from sqlalchemy.orm import Session
from datetime import datetime
import re

from app.models.flashcard import Flashcard
from app.models.note import Note
from app.services.srs_service import update_srs


# --------------------------------------------------
# Clean text
# --------------------------------------------------
def clean_text(text: str):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


# --------------------------------------------------
# Detect Q&A pairs (numbered questions etc.)
# --------------------------------------------------
def extract_qa_pairs(text: str):
    lines = text.split("\n")
    pairs = []

    current_question = None
    current_answer = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect numbered question: 1. Question?
        if re.match(r'^\d+\.', line) or line.endswith("?"):
            if current_question and current_answer:
                pairs.append((current_question, " ".join(current_answer)))
                current_answer = []

            # Remove numbering
            line = re.sub(r'^\d+\.\s*', '', line)
            current_question = line

        else:
            if current_question:
                current_answer.append(line)

    if current_question and current_answer:
        pairs.append((current_question, " ".join(current_answer)))

    return pairs


# --------------------------------------------------
# Definition-based flashcards
# --------------------------------------------------
def extract_definition_cards(text: str):
    sentences = re.split(r'[.\n]', text)
    cards = []

    for sentence in sentences:
        sentence = clean_text(sentence)
        if len(sentence) < 20:
            continue

        lower = sentence.lower()

        if " is " in lower:
            parts = sentence.split(" is ", 1)
            q = f"What is {parts[0].strip()}?"
            a = parts[1].strip()
            cards.append((q, a))

        elif " are " in lower:
            parts = sentence.split(" are ", 1)
            q = f"What are {parts[0].strip()}?"
            a = parts[1].strip()
            cards.append((q, a))

        elif " used for " in lower:
            parts = sentence.split(" used for ", 1)
            q = f"What is {parts[0].strip()} used for?"
            a = parts[1].strip()
            cards.append((q, a))

    return cards


# --------------------------------------------------
# Bullet list flashcards
# --------------------------------------------------
def extract_bullet_cards(text: str):
    lines = text.split("\n")
    cards = []

    topic = None
    bullets = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("-") or line.startswith("•") or line.startswith("*"):
            bullets.append(line[1:].strip())

        else:
            if bullets and topic:
                cards.append(
                    (f"List items for {topic}", ", ".join(bullets))
                )
                bullets = []

            topic = line

    if bullets and topic:
        cards.append((f"List items for {topic}", ", ".join(bullets)))

    return cards


# --------------------------------------------------
# Create flashcards from note
# --------------------------------------------------
def create_flashcards_from_note(db: Session, note_id: int, user_id: int):
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == user_id
    ).first()

    if not note:
        return None

    text = note.content

    # Delete old flashcards
    db.query(Flashcard).filter(
        Flashcard.note_id == note_id
    ).delete()

    cards_data = []

    # Extract different types
    cards_data += extract_qa_pairs(text)
    cards_data += extract_definition_cards(text)
    cards_data += extract_bullet_cards(text)

    # Limit cards
    cards_data = cards_data[:20]

    flashcards = []

    for question, answer in cards_data:
        card = Flashcard(
            note_id=note_id,
            user_id=user_id,
            question=question,
            answer=answer,
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
# Delete ALL flashcards
# --------------------------------------------------
def delete_all_flashcards(db: Session, user_id: int):
    db.query(Flashcard).filter(
        Flashcard.user_id == user_id
    ).delete()
    db.commit()


# --------------------------------------------------
# Get due flashcards
# --------------------------------------------------
def get_due_flashcards(db: Session, user_id: int):
    today = datetime.utcnow()

    cards = db.query(Flashcard).filter(
        Flashcard.user_id == user_id,
        Flashcard.due_date <= today
    ).limit(50).all()

    return cards


# --------------------------------------------------
# Review flashcard
# --------------------------------------------------
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


# --------------------------------------------------
# Get flashcards for note
# --------------------------------------------------
def get_flashcards_for_note(db: Session, note_id: int, user_id: int):
    cards = db.query(Flashcard).filter(
        Flashcard.note_id == note_id,
        Flashcard.user_id == user_id
    ).all()

    return cards