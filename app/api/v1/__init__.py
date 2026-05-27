from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .notes import router as notes_router
from .flashcards import router as flashcards_router
from .search import router as search_router
from .rag import router as rag_router
from .chat import router as chat_router
from .uploads import router as uploads_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(notes_router)
router.include_router(flashcards_router)
router.include_router(search_router)
router.include_router(rag_router)
router.include_router(chat_router)
router.include_router(uploads_router)