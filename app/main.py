from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.v1 import router as api_router
from app.db.session import engine
from app.db.base import Base
from app.core.config import settings
from app.models import user, note, flashcard
import time 
import logging


logger = logging.getLogger(__name__)

app = FastAPI(title="SkillTree API", version="1.0.0")


# -----------------------------
# Request Logging Middleware
# -----------------------------
@app.middleware("http")
async def log_requests(request, call_next):

    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        f"{request.method} "
        f"{request.url.path} "
        f"{response.status_code} "
        f"{duration:.2f}s"
    )

    return response


# -----------------------------
# Root
# -----------------------------

@app.get("/")
def root():
    return {"message": "API running"}

# -----------------------------
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://skill-tree-mocha.vercel.app",
        "https://earnest-tarsier-3c57db.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Session Middleware
# -----------------------------

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)


# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

except Exception as e:
    logger.error(f"DB connection failed: {str(e)}")

# Include API routers
app.include_router(api_router, prefix="/api/v1")