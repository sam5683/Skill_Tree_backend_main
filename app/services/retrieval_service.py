from sqlalchemy.orm import Session

from app.ai.chunking import chunk_text
from app.ai.embeddings import generate_embedding

from app.models.embedding_chunk import EmbeddingChunk
from app.models.note import Note


async def process_note_embeddings(db: Session,note_id: int,user_id: int):

    note = db.query(Note).filter(Note.id == note_id,Note.user_id == user_id).first()

    if not note:
        return None

    # delete old chunks first
    db.query(EmbeddingChunk).filter(EmbeddingChunk.note_id == note_id,EmbeddingChunk.user_id == user_id).delete()

    chunks = chunk_text(note.content)

    created_chunks = []

    for chunk in chunks:

        embedding = await generate_embedding(chunk)

        row = EmbeddingChunk(

            user_id=user_id,

            note_id=note_id,

            chunk_text=chunk,

            embedding=embedding
        )

        db.add(row)

        created_chunks.append(row)

    db.commit()

    return created_chunks