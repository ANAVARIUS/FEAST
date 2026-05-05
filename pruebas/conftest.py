"""Utilidades compartidas para la suite bajo `pruebas/` (STD)."""

from __future__ import annotations

import os

# Evita fallo de importacion al cargar SQLAlchemy sin `.env` en CI / local.
os.environ.setdefault("URL_CONEXION", "sqlite+pysqlite:///:memory:")

from typing import Any, Dict, List

from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage


class FakeLLM(BaseLLM):
    """LLM secuencial para pruebas: cada `ainvoke` consume el siguiente texto."""

    def __init__(self, texts: List[str]) -> None:
        self._texts = list(texts)
        self._idx = 0

    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        if self._idx >= len(self._texts):
            text = self._texts[-1]
        else:
            text = self._texts[self._idx]
            self._idx += 1
        return LLMResponse(text=text)

    async def ainvoke(self, messages: List[ChatMessage]) -> LLMResponse:
        return self.invoke(messages)

    def get_capabilities(self) -> Dict[str, Any]:
        return {"provider": "fake", "name": "FakeLLM"}


def assistant_texts_from_messages(messages: List[Any]) -> List[str]:
    """Textos del asistente en historial (dict LangChain-like u objetos con type/content)."""
    out: List[str] = []
    for m in messages:
        if isinstance(m, dict) and m.get("role") in ("assistant", "ai"):
            c = m.get("content")
            if isinstance(c, str):
                out.append(c)
        elif hasattr(m, "type") and getattr(m, "type", None) in ("assistant", "ai"):
            out.append(str(getattr(m, "content", "")))
    return out


def initial_state_stub(user_text: str, thread_id: str = "test-thread") -> Dict[str, Any]:
    """Estado inicial minimo alineado con `webhook_endpoint` (mensaje de usuario)."""
    return {
        "messages": [{"role": "user", "content": user_text}],
        "thread_id": thread_id,
        "created_at": None,
        "updated_at": None,
    }
