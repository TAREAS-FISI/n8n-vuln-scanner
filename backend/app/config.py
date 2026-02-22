"""
Configuración del backend — Carga desde variables de entorno.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    postgres_user: str = "scanner"
    postgres_password: str = "scanner_secret_2026"
    postgres_db: str = "vulnscanner"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # n8n
    n8n_webhook_url: str = "http://n8n:5678/webhook/scan"

    # Ollama
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"

    # ZAP
    zap_url: str = "http://zap:8080"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
