from pydantic_settings import BaseSettings

from datetime import timedelta
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:sam12345@localhost:5432/skilltree"

    class Config:
        env_file = ".env"

settings = Settings()

SECRET_KEY = "CHANGE_THIS_IN_PROD"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
