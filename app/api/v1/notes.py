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

    return new_note

#----------------------------------------------------

@router.post("/{note_id}/index")
async def index_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    await process_note_embeddings(
        db,
        note_id,
        current_user.id
    )

    return {
        "message": "Indexed successfully"
    }    

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
        .order_by(Note.updated_at.desc())
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
async def update_note(

    note_id: int,

    background_tasks: BackgroundTasks,

    note_update: NoteUpdate,

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

        raise HTTPException(

            status_code=404,

            detail="Note not found"

        )

    # -----------------------------------
    # TITLE
    # -----------------------------------

    if note_update.title is not None:

        note.title = note_update.title

    # -----------------------------------
    # CONTENT
    # -----------------------------------

    if note_update.content is not None:

        # -----------------------------
        # MERGE CONTENT
        # -----------------------------

        if note.content is None:

            note.content = note_update.content

        else:

            merged = note.content.copy()

            merged.update(
                note_update.content
            )

            # Preserve files

            if (

                "files"
                not in note_update.content

                and "files"
                in note.content

            ):

                merged["files"] = (
                    note.content["files"]
                )

            # Preserve supabaseUrl

            if (

                "supabaseUrl"
                not in note_update.content

                and "supabaseUrl"
                in note.content

            ):

                merged["supabaseUrl"] = (
                    note.content["supabaseUrl"]
                )

            note.content = merged

        # -----------------------------
        # EXTRACT TEXT
        # -----------------------------

        elements = (
            note.content or {}
        ).get(
            "elements",
            []
        )

        text_parts = []

        for element in elements:

            if (
                element.get("type")
                != "text"
            ):
                continue

            text = (
                element
                .get("text", "")
                .strip()
            )

            if text:

                text_parts.append(text)

        combined_text = "\n".join(
            text_parts
        ).strip()

        # -----------------------------
        # AUTO SUMMARY
        # -----------------------------

        should_generate = False

        if len(combined_text) > 50:

            if not note.summary:

                should_generate = True

            elif not note.last_summary_text:

                should_generate = True

            else:

                previous_length = len(
                    note.last_summary_text
                )

                current_length = len(
                    combined_text
                )

                if (
                    current_length
                    - previous_length
                ) > 100:

                    should_generate = True

        if should_generate:

            note.summary = (
                await generate_summary(
                    note.content
                )
            )

            note.last_summary_text = (
                combined_text
            )

    # -----------------------------------
    # MANUAL SUMMARY
    # -----------------------------------

    if note_update.summary is not None:

        note.summary = note_update.summary

    # -----------------------------------
    # TAGS
    # -----------------------------------

    if note_update.tags is not None:

        note.tags = [

            t.strip().lower()

            for t in note_update.tags

        ]

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

@router.post(
    "/{note_id}/regenerate-summary",
    response_model=NoteOut
)
async def regenerate_summary(

    note_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
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

        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    """
    GENERATE SUMMARY
    """

    summary = await generate_summary(
        note.content
    )

    note.summary = summary

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