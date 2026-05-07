import logging
import sys
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.api.util import get_docker_ngrok_url

class Config(BaseSettings):
    """Configuracion centralizada de la aplicacion."""

    # Telegram
    telegram_token: str = Field(..., validation_alias="PAPI_BOT_KEY")

    # Database
    url_conexion: str = Field("", validation_alias="URL_CONEXION")
    url_connection: str = Field("", validation_alias="URL_CONNECTION")

    # Uvicorn
    port: int = Field(8000, validation_alias="PORT")

    # LLM
    llm_provider: str = Field("gemini", validation_alias="LLM_PROVIDER")
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field("models/gemini-2.0-flash", validation_alias="GEMINI_MODEL")
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048
    gemini_max_retries: int = 3
    gemini_timeout: int = Field(30, validation_alias="GEMINI_TIMEOUT")

    # AWS / Llama (Bedrock)
    aws_region: Optional[str] = Field(None, validation_alias="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(None, validation_alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, validation_alias="AWS_SECRET_ACCESS_KEY")
    llama_model: Optional[str] = Field(None, validation_alias="LLAMA_MODEL")
    llama_temperature: float = 0.5
    llama_max_tokens: int = 512
    llama_max_retries: int = 3

    # Redis
    redis_url: Optional[str] = Field(None, validation_alias="REDIS_URL")
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Stripe (checkout al finalizar pedido; opcional hasta configurar STRIPE_SECRET_KEY)
    stripe_secret_key: Optional[str] = Field(None, validation_alias="STRIPE_SECRET_KEY")
    stripe_currency: str = Field("mxn", validation_alias="STRIPE_CURRENCY")
    public_base_url: Optional[str] = get_docker_ngrok_url() or ""
    stripe_success_url: Optional[str] = Field(None, validation_alias="STRIPE_SUCCESS_URL")
    stripe_cancel_url: Optional[str] = Field(None, validation_alias="STRIPE_CANCEL_URL")
    stripe_webhook_secret: Optional[str] = Field(None, validation_alias="STRIPE_WEBHOOK_SECRET")

    # App (LOG_LEVEL en .env: DEBUG, INFO, WARNING, …)
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
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

config = Config()

# Instancia global para usar en toda la aplicación
config = Config()


def setup_logging() -> None:
    """Configura logging una vez (basicConfig). LOG_LEVEL vía .env."""
    name = (config.log_level or "INFO").upper()
    level = getattr(logging, name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    for noisy in (
        "httpx",
        "httpcore",
        "urllib3",
        "stripe",
        "botocore",
        "boto3",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)
