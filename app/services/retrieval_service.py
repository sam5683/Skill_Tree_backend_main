from sqlalchemy.orm import Session

from app.ai.chunking import chunk_text
from app.ai.embeddings import generate_embedding

from datetime import datetime

from app.models.embedding_chunk import EmbeddingChunk
from app.models.note import Note


async def process_note_embeddings(
    db: Session,
    note_id: int,
    user_id: int
):

    note = (
        db.query(Note)
        .filter(
            Note.id == note_id,
            Note.user_id == user_id
        )
        .first()
    )

    if not note:
        return None

    """
    EXTRACT TEXT
    Supports:
    - Excalidraw notes
    - Plain text notes
    """

    content = note.content or {}

    combined_text = ""

    # ---------------------------------
    # Plain text note
    # ---------------------------------

    if isinstance(content, dict) and "text" in content:

        combined_text = (
            content.get("text", "")
            .strip()
        )

    # ---------------------------------
    # Excalidraw note
    # ---------------------------------

    else:

        elements = content.get(
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
        )

        combined_text = (
            combined_text.strip()
        )

    print(
        f"EMBEDDING TEXT LENGTH: {len(combined_text)}"
    )

    """
    NO TEXT FOUND
    """

    if not combined_text:

        return []

    """
    SKIP IF ALREADY INDEXED
    """

    if note.last_embedded_text == combined_text:

        print(
            "SKIPPING EMBEDDING - NO CHANGES"
        )

        return []

    """
    DELETE OLD CHUNKS
    """

    (
        db.query(EmbeddingChunk)
        .filter(
            EmbeddingChunk.note_id == note_id,
            EmbeddingChunk.user_id == user_id
        )
        .delete()
    )

    """
    CHUNK TEXT
    """

    chunks = chunk_text(
        combined_text
    )

    print(
        f"CHUNKS CREATED: {len(chunks)}"
    )

    created_chunks = []

    for chunk in chunks:

        embedding = await generate_embedding(
            chunk
        )

        row = EmbeddingChunk(

            user_id=user_id,

            note_id=note_id,

            chunk_text=chunk,

            embedding=embedding
        )

        db.add(row)

        created_chunks.append(row)

    """
    SAVE EMBEDDING STATE
    """

    note.last_embedded_text = (
        combined_text
    )

    note.last_embedded_at = (
        datetime.utcnow()
    )

    db.commit()

    return created_chunks