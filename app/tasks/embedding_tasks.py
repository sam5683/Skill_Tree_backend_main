import asyncio

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.retrieval_service import process_note_embeddings


@celery_app.task
def process_embedding_task(
    note_id: int,
    user_id: int
):

    db = SessionLocal()

    try:

        asyncio.run(
            process_note_embeddings(
                db=db,
                note_id=note_id,
                user_id=user_id
            )
        )

    finally:

        db.close()