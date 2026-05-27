from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.core.config import settings


engine = create_engine(

    settings.DATABASE_URL,

    future=True,

    echo=False,

    pool_pre_ping=True,

    pool_size=5,

    max_overflow=10,

    pool_timeout=30,

    pool_recycle=1800
)

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine,

    future=True
)


# Dependency for FastAPI

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()