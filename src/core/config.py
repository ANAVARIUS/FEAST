"""Configuracion central (variables de entorno / `.env`)."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    """Configuración centralizada de la aplicación."""

    # Telegram
    telegram_token: str = Field(..., validation_alias="PAPI_BOT_KEY")

    # Uvicorn
    port: int = Field(8000, validation_alias="PORT")

    # Gemini
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field("models/gemini-2.0-flash", validation_alias="GEMINI_MODEL")
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048
    gemini_max_retries: int = 3

    # Llama / AWS Bedrock
    aws_region: str = Field(None, validation_alias="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(None, validation_alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, validation_alias="AWS_SECRET_ACCESS_KEY")
    llama_model: str = Field(None, validation_alias="LLAMA_MODEL")
    llama_temperature: float = 0.5
    llama_max_tokens: int = 512

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
