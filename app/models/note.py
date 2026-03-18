from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.base import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)

    # queries always filter by user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # titles will be searchable
    title = Column(Text, nullable=False, index=True)

    content = Column(Text, nullable=False)

    summary = Column(Text, nullable=True)

    # tags array
    tags = Column(ARRAY(Text), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_notes_user_created", "user_id", "created_at"),
    )