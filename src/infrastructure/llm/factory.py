from __future__ import annotations

import logging

from src.core.config import config
from src.core.llm.base import BaseLLM
from src.infrastructure.llm.gemini_adapter import GeminiLLMAdapter
from src.infrastructure.llm.llama_adapter import LlamaLLMAdapter

logger = logging.getLogger(__name__)


def get_llm() -> BaseLLM:
    provider = (config.llm_provider or "gemini").strip().lower()
    logger.info("Factory LLM: proveedor solicitado=%s", provider)
    if provider == "gemini":
        llm = GeminiLLMAdapter.from_config(config)
        logger.info("Factory LLM: instancia Gemini model=%s", getattr(llm, "_model", "?"))
        return llm
    if provider == "llama":
        llm = LlamaLLMAdapter.from_config(config)
        logger.info("Factory LLM: instancia Llama/Bedrock model=%s", getattr(llm, "_model", "?"))
        return llm
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


__all__ = ["get_llm"]
