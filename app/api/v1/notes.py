from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_   
from app.services.ai_service import generate_summary
from app.db.session import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.core.security import get_current_user
from app.models.user import User
from typing import Optional
from datetime import datetime
from fastapi import UploadFile, File
from app.services.ocr_service import extract_text_from_image
from app.services.ai_service import improve_note_content
from fastapi import BackgroundTasks
from app.services.retrieval_service import (process_note_embeddings)

router = APIRouter(
    prefix="/notes",
    tags=["notes"]
)

# -------------------- CREATE --------------------

@router.post("", response_model=NoteOut)
def create_note(
    note: NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = note.summary or ""

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

    background_tasks.add_task(process_note_embeddings,db,new_note.id,current_user.id)

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

    # ✅ FIXED SEARCH (title + content + summary)
    if search:
       search = search.strip().lower()

       query = query.filter(
            or_(
                Note.title.ilike(f"%{search}%"),
                Note.content.ilike(f"%{search}%"),
                Note.summary.ilike(f"%{search}%"),
            )
       )

    # TAG FILTER (unchanged but correct)
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
    background_tasks: BackgroundTasks,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == current_user.id)
        .first()
    )
    
    content_updated = False
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        

    if note_update.title is not None:
        note.title = note_update.title

    if note_update.content is not None:
        note.content = note_update.content
        content_updated = True

        if note_update.summary is None:
            note.summary = generate_summary(note_update.content)
            

    if note_update.summary is not None:
        note.summary = note_update.summary

    if note_update.tags is not None:
        note.tags = [t.strip().lower() for t in note_update.tags]

    db.commit()
    db.refresh(note)

# -----------------------------# Re-embed updated content # -----------------------------
    if content_updated:

        background_tasks.add_task(

            process_note_embeddings,

            db,

            note.id,

            current_user.id
        )
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
async def regenerate_summary(
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

    note.summary = await generate_summary(note.content)

    db.commit()
    db.refresh(note)
    return note


#-------------------------------------- OCR UPLOAD --------------------------------------
@router.post("/ocr")
async def ocr_note(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    text = await extract_text_from_image(file)

    return {
        "extracted_text": text
    }
#--------------------------------- improve notes using ai ---------------------------------------
@router.post("/improve")
async def improve_note(
    data: dict,
    current_user: User = Depends(get_current_user)   # ✅ MUST be in params
):
    content = data.get("content")

    if not content:
        return {"improved_content": ""}

    improved = await improve_note_content(content)

    return {"improved_content": improved}



#--------------------------------------- emdedding notes -----------------------------------

@router.post("/{note_id}/embed")
async def embed_note(

    note_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)

):

    chunks = await process_note_embeddings(

        db=db,

        note_id=note_id,

        user_id=current_user.id
    )

    if not chunks:

        raise HTTPException(

            status_code=404,

            detail="Note not found"
        )

    return {

        "message": "Embeddings created",

        "chunks_created": len(chunks)
    }