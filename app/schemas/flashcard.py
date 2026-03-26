from pydantic import BaseModel
from datetime import datetime


class FlashcardBase(BaseModel):
    question: str
    answer: str


class FlashcardResponse(FlashcardBase):
    id: int
    due_date: datetime

    class Config:
        from_attributes = True


class FlashcardReview(BaseModel):
    rating: str
    