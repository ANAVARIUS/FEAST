import os
from dotenv import load_dotenv
from pydantic import BaseSettings, Field
from typing import Optional

load_dotenv()

class Config(BaseSettings):
    """Configuracion centralizada de la aplicacion."""
    
    # Telegram
    telegram_token: str = Field(..., env="PAPI_BOT_KEY")
    
    # Gemini
    gemini_api_key: str = Field(..., env='GEMINI_API_KEY')
    gemini_model: str = "gemini-pro"
    gemini_temperature: float = 0.7
    gemini_max_tokens: Optional[int] = None
    gemini_timeout: int = 30
    
    # Redis
    # Puede ser URI completa (recomendado) o solo host (compatibilidad)
    redis_url: str = Field("redis://localhost:6379/0", env='REDIS_URL')
    redis_port: int = Field(6379, env='REDIS_PORT')
    redis_db: int = Field(0, env='REDIS_DB')
    redis_password: Optional[str] = Field(None, env='REDIS_PASSWORD')

    def get_redis_conn_string(self) -> str:
        """
        Devuelve una URI valida para Redis (redis://...).

        - Si REDIS_URL ya viene como URI (redis:// o rediss://) la retorna tal cual.
        - Si REDIS_URL viene como host (por ejemplo "localhost"), la construye usando
          REDIS_PORT, REDIS_DB y REDIS_PASSWORD.
        """
        raw = (self.redis_url or "").strip()
        if raw.startswith("redis://") or raw.startswith("rediss://"):
            return raw

        host = raw or "localhost"
        password = (self.redis_password or "").strip()
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{host}:{int(self.redis_port)}/{int(self.redis_db)}"
    
    # App
    log_level: str = Field("INFO", env='LOG_LEVEL')
    max_history_length: int = 50  # Número máximo de mensajes a mantener en contexto
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton de configuración
config = Config()