import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

# Prefer backend/.env, then fallback to project root .env.
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env", override=False)


@dataclass
class Settings:
    pg_host: str = os.getenv("PG_HOST", "localhost")
    pg_port: int = int(os.getenv("PG_PORT", "5432"))
    pg_user: str = os.getenv("PG_USER", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "postgres")
    pg_database: str = os.getenv("PG_DATABASE", "postgres")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", os.getenv("EMBED_MODEL", "bge-m3:latest"))
    ollama_llm_model: str = os.getenv("OLLAMA_LLM_MODEL", os.getenv("LLM_MODEL", "llama3.2"))

    # bge-m3 thường 1024, nomic-embed-text thường 768.
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1024"))
    chunk_top_k: int = int(os.getenv("CHUNK_TOP_K", "5"))

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )


settings = Settings()
