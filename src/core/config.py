"""Configuracion central (variables de entorno / `.env`)."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Ajustes de aplicacion alineados con el despliegue y el STD."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url_conexion: str = Field(
        default="",
        description="URL SQLAlchemy (MySQL, SQLite, etc.); en .env suele llamarse URL_CONEXION.",
    )
    port: int = Field(default=8000, description="Puerto HTTP de la API.")
    telegram_token: str = Field(default="", description="Token del bot de Telegram.")
    redis_connection_string: str = Field(
        default="redis://localhost:6379/0",
        description="URL de Redis (checkpointer / TTL).",
    )
    gemini_api_key: str = Field(default="", description="Clave API de Google AI (Gemini).")
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Nombre del modelo (sin prefijo models/ en .env; el SDK lo normaliza).",
    )
    gemini_max_retries: int = Field(default=3, ge=1)
    gemini_temperature: float = Field(default=0.7)
    gemini_max_tokens: int = Field(default=8192, ge=1)
    gemini_timeout: int = Field(
        default=60,
        ge=1,
        description="Timeout en segundos para el adaptador REST (si se usa).",
    )


config = Config()
