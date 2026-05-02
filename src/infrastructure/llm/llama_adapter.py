from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.core.config import Config
from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage

logger = logging.getLogger(__name__)


class LlamaLLMAdapter(BaseLLM):
    def __init__(
        self,
        *,
        region: str,
        model: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 512,
        max_retries: int = 3,
    ) -> None:
        self._region = region
        self._model = model
        self._temperature = float(temperature)
        self._max_tokens = int(max_tokens)
        self._max_retries = int(max_retries)

        kwargs: Dict[str, Any] = {"region_name": self._region}
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
        self._client = boto3.client("bedrock-runtime", **kwargs)

    @classmethod
    def from_config(cls, cfg: Config) -> "LlamaLLMAdapter":
        if not cfg.aws_region or not cfg.llama_model:
            raise ValueError("LLAMA_PROVIDER requiere AWS_REGION y LLAMA_MODEL")
        return cls(
            region=cfg.aws_region,
            model=cfg.llama_model,
            access_key=cfg.aws_access_key_id,
            secret_key=cfg.aws_secret_access_key,
            temperature=cfg.llama_temperature,
            max_tokens=cfg.llama_max_tokens,
            max_retries=cfg.llama_max_retries,
        )

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": "meta-bedrock",
            "model": self._model,
            "region": self._region,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "max_retries": self._max_retries,
        }

    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        logger.info(
            "LlamaAdapter: converse model=%s region=%s mensajes_entrada=%d",
            self._model,
            self._region,
            len(messages),
        )
        system_prompts = [{"text": "Eres un asistente conversacional de FEAST. Responde con precision y en el idioma del usuario."}]
        bedrock_messages: List[Dict[str, Any]] = []
        for msg in messages:
            role = (msg.get("role") or "user").lower()
            content = msg.get("content") or ""
            if not content:
                continue
            if role == "system":
                system_prompts.append({"text": content})
                continue
            if role == "human":
                role = "user"
            if role == "ai":
                role = "assistant"
            bedrock_messages.append({"role": role, "content": [{"text": content}]})

        if not bedrock_messages:
            logger.warning("LlamaAdapter: sin mensajes usuario/asistente tras filtrar")
            return LLMResponse(text="", raw=None)

        logger.debug(
            "LlamaAdapter: system_blocks=%d user_turns=%d",
            len(system_prompts),
            len(bedrock_messages),
        )
        inference = {"temperature": self._temperature, "maxTokens": self._max_tokens}
        last_error: Optional[Exception] = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.converse(
                    modelId=self._model,
                    messages=bedrock_messages,
                    system=system_prompts,
                    inferenceConfig=inference,
                )
                text = response["output"]["message"]["content"][0]["text"]
                logger.info("LlamaAdapter: respuesta OK chars=%d", len(text))
                return LLMResponse(text=text, raw=response)
            except (ClientError, Exception) as err:
                last_error = err
                logger.warning("Llama attempt %s failed: %s", attempt, err)
                if attempt < self._max_retries:
                    time.sleep(2**attempt)

        return LLMResponse(
            text=f"LLM_ERROR: No fue posible invocar {self._model}: {last_error}",
            raw=None,
        )


__all__ = ["LlamaLLMAdapter"]
