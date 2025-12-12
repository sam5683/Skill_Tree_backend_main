from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:sam12345@localhost:5432/skilltree"

engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False  # change to True for SQL logging
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

Base = declarative_base()
