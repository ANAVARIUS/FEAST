from __future__ import annotations

import logging
from typing import Optional, Union

from src.core.config import config
from langgraph.checkpoint.redis import RedisSaver


def get_redis_url() -> str:
    return config.redis_connection_string


def thread_id_from_chat_id(chat_id: Union[int, str]) -> str:
    return str(chat_id)


def create_redis_checkpointer(
    redis_url: Optional[str] = None,
    *,
    do_setup: bool = True,
) -> RedisSaver:
    """
    Crea y retorna un RedisSaver síncrono listo para usar en LangGraph.
    (No se usa en el flujo asíncrono, se mantiene por compatibilidad.)
    """
    url = redis_url or get_redis_url()
    saver = RedisSaver(redis_url=url)
    if do_setup and hasattr(saver, 'setup'):
        saver.setup()
    return saver


async def create_async_redis_checkpointer(
    redis_url: Optional[str] = None,
    *,
    do_setup: bool = True,
):
    """
    Crea y retorna un AsyncRedisSaver listo para usar en LangGraph asíncrono.
    """
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver
    url = redis_url or get_redis_url()
    # Crear el checkpointer asíncrono directamente con la URL
    saver = AsyncRedisSaver(redis_url=url)
    if do_setup and hasattr(saver, 'asetup'):
        await saver.asetup()
    return saver