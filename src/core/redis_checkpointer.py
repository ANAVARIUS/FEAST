from __future__ import annotations

import os
from typing import Optional, Union

from dotenv import load_dotenv

load_dotenv()


def get_redis_url() -> str:
    """
    Redis URL usada por LangGraph Redis checkpointer.

    Espera una de estas variables de entorno:
    - REDIS_URL
    - REDIS_URI
    """
    # Preferir config central si existe
    try:
        from src.core.config import config

        return config.get_redis_conn_string()
    except Exception:
        return (
            os.getenv("REDIS_URL")
            or os.getenv("REDIS_URI")
            or "redis://localhost:6379/0"
        )


def thread_id_from_chat_id(chat_id: Union[int, str]) -> str:
    """
    En LangGraph, la persistencia por "chat_id" suele mapearse a thread_id.
    """
    return str(chat_id)


def create_redis_checkpointer(
    redis_url: Optional[str] = None,
    *,
    do_setup: bool = True,
):
    """
    Crea y (opcionalmente) inicializa un RedisSaver para persistencia.

    Nota: según la doc de LangGraph, para Redis debes ejecutar:
    - `checkpointer.setup()` la primera vez.
    """
    # Import lazy para que el proyecto arranque aunque falten dependencias aún.
    from langgraph.checkpoint.redis import RedisSaver

    url = redis_url or get_redis_url()
    checkpointer = RedisSaver.from_conn_string(url)
    if do_setup:
        checkpointer.setup()
    return checkpointer


async def create_async_redis_checkpointer(
    redis_url: Optional[str] = None,
    *,
    do_setup: bool = True,
):
    """
    Variante async del checkpointer de Redis.
    """
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    url = redis_url or get_redis_url()
    checkpointer = AsyncRedisSaver.from_conn_string(url)
    if do_setup:
        await checkpointer.asetup()
    return checkpointer


__all__ = [
    "get_redis_url",
    "thread_id_from_chat_id",
    "create_redis_checkpointer",
    "create_async_redis_checkpointer",
]

