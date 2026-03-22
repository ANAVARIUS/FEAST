import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuración centralizada de la aplicación."""

    # Telegram
    telegram_token: str = Field(..., validation_alias="PAPI_BOT_KEY")

    # Ngrok
    ngrok_token: str = Field(..., validation_alias="NGROK_TOKEN")
    port: int = Field(8000, validation_alias="PORT")

    # Gemini
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field("models/gemini-2.0-flash", validation_alias="GEMINI_MODEL")
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048
    gemini_max_retries: int = 3

    # Redis
    redis_url: Optional[str] = Field(None, validation_alias="REDIS_URL")
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # App
    log_level: str = "INFO"
    max_history_length: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def redis_connection_string(self) -> str:
        """Construye la URL de Redis a partir de componentes o devuelve REDIS_URL si existe."""
        if self.redis_url:
            return self.redis_url
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Instancia global para usar en toda la aplicación
config = Config()