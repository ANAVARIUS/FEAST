from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.llm.types import ChatMessage

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    """Respuesta del LLM."""
    text: str
    raw: Optional[Any] = None


class BaseLLM(ABC):
    """Interfaz abstracta para cualquier modelo de lenguaje."""

    @abstractmethod
    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        """Invoca el modelo de manera síncrona."""
        raise NotImplementedError

    async def ainvoke(self, messages: List[ChatMessage]) -> LLMResponse:
        """Invoca el modelo de manera asíncrona. Por defecto llama a invoke en un hilo."""
        import asyncio

        _log.debug(
            "BaseLLM.ainvoke: impl=%s mensajes=%d",
            self.__class__.__name__,
            len(messages or []),
        )
        return await asyncio.to_thread(self.invoke, messages)

    def __call__(self, messages: List[ChatMessage]) -> LLMResponse:
        """Atajo para invoke."""
        return self.invoke(messages)

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Retorna información sobre el modelo (nombre, proveedor, etc.)."""
        raise NotImplementedError