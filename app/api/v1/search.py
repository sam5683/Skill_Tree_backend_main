from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.core.security import get_current_user

from app.models.user import User

from app.ai.retrieval import search_similar_chunks


router = APIRouter(

    prefix="/search",

    tags=["Search"]
)


@router.post("/")
async def semantic_search(

    query: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    results = await search_similar_chunks(

        db=db,

        query=query,

        user_id=current_user.id
    )

    formatted = []

    for row in results:

        formatted.append({

            "note_id": row.note_id,

            "chunk_text": row.chunk_text,

            "distance": row.distance
        })

    return formatted