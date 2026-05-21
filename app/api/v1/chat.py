from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user

from app.models.user import User

from app.schemas.chat import ChatRequest

from app.ai.rag import rag_answer


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("")
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    response = await rag_answer(
        db=db,
        query=payload.message,
        user_id=current_user.id
    )

    return response