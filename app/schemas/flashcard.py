from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class FlashcardBase(BaseModel):
    question: str
    answer: str


class FlashcardResponse(FlashcardBase):
    id: int
    due_date: datetime

    class Config:
        from_attributes = True


class FlashcardReview(BaseModel):
    rating: Literal["again", "hard", "good", "easy"]
    