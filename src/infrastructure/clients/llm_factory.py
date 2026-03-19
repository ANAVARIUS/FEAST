from __future__ import annotations

import os

from src.core.config import config
from src.core.llm.base import BaseLLM
from src.infrastructure.clients.gemini_llm_adapter import GeminiLLMAdapter


def get_llm() -> BaseLLM:
    """
    Fabrica de LLM via variable de entorno.
    Esto permite cambiar proveedor sin tocar la logica central.
    """
    provider = (os.getenv("LLM_PROVIDER") or "gemini").strip().lower()

    if provider == "gemini":
        return GeminiLLMAdapter.from_config(config)

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


__all__ = ["get_llm"]

