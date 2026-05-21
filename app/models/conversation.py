from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from datetime import datetime
from app.db.base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    title = Column(String, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )