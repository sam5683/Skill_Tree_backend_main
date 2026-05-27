from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):

    message: str

    conversation_id: Optional[int] = None

    note_id: Optional[int] = None