from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:sam12345@localhost:5432/skilltree"

    class Config:
        env_file = ".env"

settings = Settings()
