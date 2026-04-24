from __future__ import annotations

import logging
from typing import Callable, Optional

import redis.asyncio as redis_async

from src.core.config import config
from src.infrastructure.redis.keyspace import session_document_key
from src.infrastructure.redis.models import SessionPayload

logger = logging.getLogger(__name__)

_DEFAULT_TTL_SECONDS = 28800


class ConversationSessionStore:
    """
    Capa de acceso modular al documento de sesión en Redis.
    No mezcla responsabilidades con el checkpointer de LangGraph.
    """

    def __init__(self, ttl_seconds: int = _DEFAULT_TTL_SECONDS):
        self._ttl = ttl_seconds

    async def _client(self) -> redis_async.Redis:
        return redis_async.from_url(
            config.redis_connection_string,
            encoding="utf-8",
            decode_responses=True,
        )

    async def load(self, thread_id: str) -> SessionPayload:
        key = session_document_key(thread_id)
        client = await self._client()
        try:
            raw = await client.get(key)
            if not raw:
                return SessionPayload.empty()
            return SessionPayload.model_validate_json(raw)
        except Exception as e:
            logger.warning("Fallo al leer sesión Redis %s: %s", key, e)
            return SessionPayload.empty()
        finally:
            await client.aclose()

    async def save(self, thread_id: str, payload: SessionPayload) -> None:
        key = session_document_key(thread_id)
        client = await self._client()
        try:
            await client.set(key, payload.model_dump_json(), ex=self._ttl)
        finally:
            await client.aclose()

    async def merge_update(
        self,
        thread_id: str,
        *,
        mutator: Callable[[SessionPayload], None],
    ) -> SessionPayload:
        """
        Lee, aplica mutator(payload) -> None (mutación in-place), guarda.
        Reduce condiciones de carrera para un solo documento por thread.
        """
        payload = await self.load(thread_id)
        mutator(payload)
        await self.save(thread_id, payload)
        return payload

    async def touch_ttl(self, thread_id: str) -> Optional[int]:
        """Renueva TTL del documento de sesion si existe."""
        key = session_document_key(thread_id)
        client = await self._client()
        try:
            return await client.expire(key, self._ttl)
        finally:
            await client.aclose()
