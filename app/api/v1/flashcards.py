from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.flashcard import FlashcardResponse, FlashcardReview
from app.services.flashcard_service import (
    create_flashcards_from_note,
    get_due_flashcards,
    review_flashcard,
    get_flashcards_for_note,
    delete_all_flashcards
)
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


# ----------------------------------------------------
# Generate flashcards from note
# POST /flashcards/from-note/{note_id}
# ----------------------------------------------------
@router.post("/from-note/{note_id}", response_model=List[FlashcardResponse])
def generate_flashcards_from_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cards = create_flashcards_from_note(db, note_id, current_user.id)

    if not cards:
        raise HTTPException(status_code=404, detail="Note not found or no content")

    return cards


# ----------------------------------------------------
# Get due flashcards
# GET /flashcards/due
# ----------------------------------------------------
@router.get("/due", response_model=List[FlashcardResponse])
def get_due_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cards = get_due_flashcards(db, current_user.id)
    return cards


# ----------------------------------------------------
# Review flashcard (UPDATED)
# POST /flashcards/review/{card_id}
# ----------------------------------------------------
@router.post("/review/{card_id}")
def review_card(
    card_id: int,
    review: FlashcardReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = review_flashcard(db, card_id, review.rating, current_user.id)

    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    return {
        "interval": card.interval,
        "ease_factor": card.ease_factor,
        "repetitions": card.repetitions
    }
# ----------------------------------------------------
# Get flashcards for a specific note
# GET /flashcards/note/{note_id}
# ----------------------------------------------------
@router.get("/note/{note_id}", response_model=List[FlashcardResponse])
def get_cards_for_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cards = get_flashcards_for_note(db, note_id, current_user.id)
    return cards


# ----------------------------------------------------
# Delete ALL flashcards for user
# DELETE /flashcards/delete-all
# ----------------------------------------------------
@router.delete("/delete-all")
def delete_all_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_all_flashcards(db, current_user.id)
    return {"message": "All flashcards deleted"}