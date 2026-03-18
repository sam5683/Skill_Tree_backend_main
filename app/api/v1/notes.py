from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.summary import generate_summary
from app.db.session import SessionLocal
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.core.security import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter(
    prefix="/notes",
    tags=["notes"]
)

# -------------------- DB DEPENDENCY --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- CREATE --------------------

@router.post("", response_model=NoteOut)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = note.summary or generate_summary(note.content)

    new_note = Note(
        title=note.title,
        content=note.content,
        summary=summary,
        tags=[t.strip().lower() for t in note.tags] if note.tags else None,
        user_id=current_user.id,
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

# -------------------- LIST --------------------

@router.get("", response_model=list[NoteOut])
def get_notes(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Note).filter(Note.user_id == current_user.id)

    if search:
        query = query.filter(Note.title.ilike(f"%{search}%"))

    if tag:
        tags = [t.strip().lower() for t in tag.split(",")]

        query = query.filter(
        Note.tags.overlap(tags)
        )

    notes = (
        query
        .order_by(Note.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return notes
# -------------------- DETAIL --------------------
@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(
            Note.id == note_id,
            Note.user_id == current_user.id
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note

# -------------------- UPDATE --------------------
@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note_update.title is not None:
        note.title = note_update.title

    if note_update.content is not None:
        note.content = note_update.content
        # regenerate ONLY if user didn't supply summary
        if note_update.summary is None:
            note.summary = generate_summary(note_update.content)

    if note_update.summary is not None:
        note.summary = note_update.summary

    if note_update.tags is not None:
        note.tags = [t.strip().lower() for t in note_update.tags]

    db.commit()
    db.refresh(note)
    return note

# -------------------- DELETE --------------------
@router.delete("/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(
            Note.id == note_id,
            Note.user_id == current_user.id
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()

    return {"detail": "Note deleted"}

# -------------------- REGENERATE SUMMARY --------------------

@router.post("/{note_id}/regenerate-summary", response_model=NoteOut)
def regenerate_summary(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.summary = generate_summary(note.content)

    db.commit()
    db.refresh(note)
    return note

