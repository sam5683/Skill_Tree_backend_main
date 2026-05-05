from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_router
from app.db.session import engine
from app.db.base import Base

# Register models so Alembic sees them
from app.models import user, note, flashcard

app = FastAPI(title="SkillTree API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "API running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://skill-tree-mocha.vercel.app", 
        "https://earnest-tarsier-3c57db.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=86400,
)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print("DB connection failed:", e)

# Include API routers
app.include_router(api_router, prefix="/api/v1")