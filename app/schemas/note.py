from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class NoteCreate(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    summary: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
