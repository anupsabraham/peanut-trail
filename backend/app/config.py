from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///../db.sqlite3"
    allow_origins: list[str] = ["http://localhost:5173", ]

    class Config:
        env_file = ".env"

settings = Settings()
