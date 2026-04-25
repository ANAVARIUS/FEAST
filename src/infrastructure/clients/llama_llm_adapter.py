from __future__ import annotations

import json
from typing import List, Optional

import boto3

from src.core.config import Config
from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage


def _messages_to_prompt(messages: List[ChatMessage]) -> str:
    # Formato de instrucciones nativo para Llama
    parts: List[str] = ["<|begin_of_text|>"]
    for m in messages:
        role = m.get("role") or "user"
        content = m.get("content") or ""
        if not content:
            continue
        parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n{content}\n<|eot_id|>\n")
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n")
    return "".join(parts)


class LlamaLLMAdapter(BaseLLM):
    def __init__(
        self,
        *,
        region: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        model: str = "meta.llama3-70b-instruct-v1:0",
        temperature: float = 0.5,
        max_tokens: Optional[int] = 512,
    ):
        self._region = region
        self._model = model
        self._temperature = float(temperature)
        self._max_tokens = max_tokens

        client_kwargs = {"region_name": self._region}
        if access_key and secret_key:
            client_kwargs["aws_access_key_id"] = access_key
            client_kwargs["aws_secret_access_key"] = secret_key

        self._client = boto3.client("bedrock-runtime", **client_kwargs)

    @classmethod
    def from_config(cls, cfg: Config) -> "LlamaLLMAdapter":
        return cls(
            region=cfg.aws_region,
            access_key=cfg.aws_access_key_id,
            secret_key=cfg.aws_secret_access_key,
            model=cfg.llama_model,
            temperature=cfg.llama_temperature,
            max_tokens=cfg.llama_max_tokens,
        )

    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        prompt = _messages_to_prompt(messages)
        if not prompt:
            return LLMResponse(text="", raw=None)

        payload = {
            "prompt": prompt,
            "temperature": self._temperature
        }
        if self._max_tokens is not None:
            payload["max_gen_len"] = int(self._max_tokens)

        try:
            response = self._client.invoke_model(
                modelId=self._model,
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = response["body"].read()
            response_json = json.loads(response_body.decode("utf-8"))
            
            response_text = response_json.get("generation") or ""
            return LLMResponse(text=response_text, raw=response_json)
            
        except Exception as e:
            error_message = f"LLM_ERROR: Can't invoke '{self._model}'. Reason: {str(e)}"
            return LLMResponse(text=error_message, raw=None)


__all__ = ["LlamaLLMAdapter"]
