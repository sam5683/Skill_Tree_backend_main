from pydantic import BaseModel
from datetime import datetime
from typing import Literal
from pydantic import Field

class FlashcardBase(BaseModel):
    question: str = Field(max_length=500)
    answer: str   = Field(max_length=5000) 


class FlashcardResponse(FlashcardBase):
    id: int
    due_date: datetime

    class Config:
        from_attributes = True


class FlashcardReview(BaseModel):
    rating: Literal["again", "hard", "good", "easy"]
    