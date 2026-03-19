from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from src.core.llm.types import ChatMessage


@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: Optional[object] = None


class BaseLLM(ABC):
    """
    Interfaz estable para el LLM.

    El resto del sistema (por ejemplo el grafo) solo debe depender de esta clase.
    Cambiar de Gemini a SageMaker debe implicar solo cambiar el adapter concreto.
    """

    @abstractmethod
    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        raise NotImplementedError

    async def ainvoke(self, messages: List[ChatMessage]) -> LLMResponse:
        # implementacion de wrappers async por defecto
        return self.invoke(messages)


__all__ = ["BaseLLM", "LLMResponse"]

