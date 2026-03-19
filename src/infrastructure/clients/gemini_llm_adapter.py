from __future__ import annotations

import json
from typing import List, Optional

import requests

from src.core.config import Config
from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage


def _messages_to_prompt(messages: List[ChatMessage]) -> str:
    # hacemos uso de un prompt simple para no acoplar el resto del sistema a un formato particular.
    # para la integracion con gemini debe soporta "contents", pero aqui normalizamos a texto.
    parts: List[str] = []
    for m in messages:
        role = (m.get("role") or "user").upper()
        content = m.get("content") or ""
        if not content:
            continue
        parts.append(f"{role}: {content}")
    return "\n".join(parts).strip()


class GeminiLLMAdapter(BaseLLM):
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-pro",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout_s: int = 30,
    ):
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

    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        prompt = _messages_to_prompt(messages)
        if not prompt:
            return LLMResponse(text="", raw=None)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self._model}:generateContent"
        )
        params = {"key": self._api_key}

        generation_config = {"temperature": self._temperature}
        if self._max_tokens is not None:
            generation_config["maxOutputTokens"] = int(self._max_tokens)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }

        resp = requests.post(
            url,
            params=params,
            json=payload,
            timeout=self._timeout_s,
        )

        raw = resp.json() if resp.content else None
        if not resp.ok:
            # dejamos eel error como texto para que la capa superior decida que hacer.
            return LLMResponse(
                text=f"LLM_ERROR {resp.status_code}: {resp.text}",
                raw=raw,
            )

        # debe devolver un texto plano , "una respuesta tipica"
        # { "candidates": [ { "content": { "parts": [ {"text": "..."} ] } } ] }
        try:
            candidates = raw.get("candidates") or []
            content = (candidates[0] or {}).get("content") or {}
            parts = content.get("parts") or []
            text = (parts[0] or {}).get("text") or ""
            return LLMResponse(text=text, raw=raw)
        except Exception:
            return LLMResponse(text=json.dumps(raw, ensure_ascii=False), raw=raw)


__all__ = ["GeminiLLMAdapter"]

