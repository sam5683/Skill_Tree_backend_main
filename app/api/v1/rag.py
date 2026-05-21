from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.core.security import get_current_user

from app.models.user import User

from app.ai.rag import rag_answer


router = APIRouter(

    prefix="/rag",

    tags=["RAG"]
)


@router.post("/")
async def ask_rag(

    query: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    response = await rag_answer(

        db=db,

        query=query,

        user_id=current_user.id
    )

    return response