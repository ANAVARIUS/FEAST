from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

from src.core.config import Config
from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage


def _messages_to_prompt(messages: List[ChatMessage]) -> str:
    parts: List[str] = []
    for msg in messages:
        role = (msg.get("role") or "user").upper()
        content = msg.get("content") or ""
        if content:
            parts.append(f"{role}: {content}")
    return "\n".join(parts).strip()


class GeminiLLMAdapter(BaseLLM):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "models/gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout_s: int = 30,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._temperature = float(temperature)
        self._max_tokens = max_tokens
        self._timeout_s = int(timeout_s)

    @classmethod
    def from_config(cls, cfg: Config) -> "GeminiLLMAdapter":
        return cls(
            api_key=cfg.gemini_api_key,
            model=cfg.gemini_model,
            temperature=cfg.gemini_temperature,
            max_tokens=cfg.gemini_max_tokens,
            timeout_s=cfg.gemini_timeout,
        )

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "google",
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }

    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        prompt = _messages_to_prompt(messages)
        if not prompt:
            logger.warning("GeminiAdapter: invoke con prompt vacío")
            return LLMResponse(text="", raw=None)

        logger.info(
            "GeminiAdapter: REST generateContent model=%s prompt_chars=%d",
            self._model,
            len(prompt),
        )
        logger.debug("GeminiAdapter: cabecera_prompt=%r", prompt[:200])
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self._model}:generateContent"
        )
        params = {"key": self._api_key}

        generation_config: Dict[str, Any] = {"temperature": self._temperature}
        if self._max_tokens is not None:
            generation_config["maxOutputTokens"] = int(self._max_tokens)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        resp = requests.post(url, params=params, json=payload, timeout=self._timeout_s)

        raw = resp.json() if resp.content else None
        if not resp.ok:
            logger.error(
                "GeminiAdapter: HTTP %s body=%s",
                resp.status_code,
                (resp.text or "")[:500],
            )
            return LLMResponse(text=f"LLM_ERROR {resp.status_code}: {resp.text}", raw=raw)

        try:
            candidates = raw.get("candidates") or []
            content = (candidates[0] or {}).get("content") or {}
            parts = content.get("parts") or []
            text = (parts[0] or {}).get("text") or ""
            logger.info("GeminiAdapter: texto_salida_chars=%d", len(text))
            return LLMResponse(text=text, raw=raw)
        except Exception as ex:
            logger.exception("GeminiAdapter: parseo de respuesta falló: %s", ex)
            return LLMResponse(text=json.dumps(raw, ensure_ascii=False), raw=raw)


__all__ = ["GeminiLLMAdapter"]
