from __future__ import annotations

import os
import redis
from typing import Optional, Union

from dotenv import load_dotenv
from langgraph.checkpoint.redis import RedisSaver

load_dotenv()


def get_redis_url() -> str:
    """Construye la URL de Redis a partir de variables de entorno"""
    url = os.getenv("REDIS_URL")
    if url and (url.startswith("redis://") or url.startswith("rediss://")):
        return url

    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    password = os.getenv("REDIS_PASSWORD")

    auth = f":{password}@" if password else ""
    return f"redis://{auth}{host}:{port}/{db}"


def thread_id_from_chat_id(chat_id: Union[int, str]) -> str:
    return str(chat_id)


def create_redis_checkpointer(
    redis_url: Optional[str] = None,
    *,
    expire_seconds: Optional[int] = 28800,  # 8 horas por defecto
    do_setup: bool = True,
) -> RedisSaver:
    """
    Crea y retorna un RedisSaver listo para usar en LangGraph.
    Si la versión de LangGraph lo soporta, se puede pasar expire_seconds para TTL.
    """
    url = redis_url or get_redis_url()
    # Verificar conexion (opcional)
    redis_client = redis.Redis.from_url(url, decode_responses=False)
    redis_client.ping()
    # Crear el checkpointer usando la URL (y opcionalmente expire_seconds)
    # El constructor acepta redis_url y otros parametros; algunos permiten expire_seconds
    try:
        # Intentar con expire_seconds
        saver = RedisSaver(redis_url=url, expire_seconds=expire_seconds)
    except TypeError:
        # Si no acepta expire_seconds, crearlo sin el
        saver = RedisSaver(redis_url=url)
    if do_setup and hasattr(saver, 'setup'):
        saver.setup()
    return saver


async def create_async_redis_checkpointer(
    redis_url: Optional[str] = None,
    *,
    expire_seconds: Optional[int] = 28800,
    do_setup: bool = True,
):
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    url = redis_url or get_redis_url()
    redis_client = redis.asyncio.from_url(url)
    # Verificar conexion
    await redis_client.ping()
    try:
        saver = AsyncRedisSaver(redis_url=url, expire_seconds=expire_seconds)
    except TypeError:
        saver = AsyncRedisSaver(redis_url=url)
    if do_setup and hasattr(saver, 'asetup'):
        await saver.asetup()
    return saver


__all__ = [
    "get_redis_url",
    "thread_id_from_chat_id",
    "create_redis_checkpointer",
    "create_async_redis_checkpointer",
]