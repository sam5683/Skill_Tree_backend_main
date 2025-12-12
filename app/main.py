from fastapi import FastAPI
from app.db.init_db import init_db
from app.api.v1 import router as api_router

app = FastAPI(title="SkillTree API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    init_db()

# include all v1 API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "SkillTree Backend is running"}
