from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Index
)

from sqlalchemy.dialects.postgresql import (
    ARRAY,
    JSONB
)

from sqlalchemy.sql import func

from app.db.base import Base


class Note(Base):

    __tablename__ = "notes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # -----------------------------------
    # OWNER
    # -----------------------------------

    user_id = Column(

        Integer,

        ForeignKey("users.id"),

        nullable=False,

        index=True
    )

    # -----------------------------------
    # NOTE DATA
    # -----------------------------------

    title = Column(
        Text,
        nullable=False,
        index=True
    )

    content = Column(
        JSONB,
        nullable=False
    )

    summary = Column(
        Text,
        nullable=True
    )

    # -----------------------------------
    # EMBEDDING CACHE
    # -----------------------------------

    last_embedded_text = Column(
        Text,
        nullable=True
    )

    last_embedded_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # -----------------------------------
    # SUMMARY CACHE
    # -----------------------------------

    last_summary_text = Column(
        Text,
        nullable=True
    )

    # -----------------------------------
    # TAGS
    # -----------------------------------

    tags = Column(
        ARRAY(Text),
        nullable=True
    )

    # -----------------------------------
    # TIMESTAMPS
    # -----------------------------------

    created_at = Column(

        DateTime(timezone=True),

        server_default=func.now(),

        index=True
    )

    updated_at = Column(

        DateTime(timezone=True),

        onupdate=func.now()
    )

    # -----------------------------------
    # INDEXES
    # -----------------------------------

    __table_args__ = (

        Index(
            "idx_notes_user_created",
            "user_id",
            "created_at"
        ),

    )