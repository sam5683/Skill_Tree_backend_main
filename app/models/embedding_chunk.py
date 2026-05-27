from sqlalchemy import Column, Integer, Text, ForeignKey
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class EmbeddingChunk(Base):

    __tablename__ = "embedding_chunks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    note_id = Column(
       Integer,
       ForeignKey("notes.id", ondelete="CASCADE"),
       nullable=False
)

    chunk_text = Column(
        Text,
        nullable=False
    )

    embedding = Column(
        Vector(3072),
        nullable=False
    )