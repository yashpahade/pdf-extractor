from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    sql_echo: bool = False

    # ChromaDB
    chroma_persist_directory: Path = Path("./data/chroma")
    chroma_collection_name: str = "document_chunks"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]

    # LLM providers
    groq_api_key: str = ""
    gemini_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    gemini_model: str = "gemini-flash-latest"

    # Upload
    upload_max_bytes: int = 20 * 1024 * 1024  # 20 MB
    upload_dir: Path = Path("./data/uploads")

    # Chunking
    chunk_size: int = 2000
    chunk_overlap: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
