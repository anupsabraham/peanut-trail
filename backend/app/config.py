from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///../db.sqlite3"
    allow_origins: list[str] = ["http://localhost:5173"]
    min_category_suggestion_confidence: int = 25

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
