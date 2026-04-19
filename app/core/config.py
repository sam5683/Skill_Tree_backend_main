from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:sam12345@localhost:5432/skilltree"

    GROQ_API_KEY: str  

    class Config:
        env_file = ".env"


settings = Settings()


# Auth config
SECRET_KEY = "CHANGE_THIS_IN_PROD"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60