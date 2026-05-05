from __future__ import annotations

import json
import logging
import time
from typing import List, Optional, Any, Dict

import boto3
from botocore.exceptions import ClientError

from src.core.config import config, Config
from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage

logger = logging.getLogger(__name__)


def _messages_to_prompt(messages: List[ChatMessage]) -> str:
    """
    Formato de instrucciones nativo para Llama 3.
    Soporta tanto diccionarios como objetos (ej. HumanMessage de LangChain).
    """
    system_instruction = (
        "Eres un asistente conversacional que recibe pedidos de una gran variedad de sucursales,se útil y natural. "
        "Tienes acceso al historial completo de la conversación, pero debes usarlo únicamente para entender el contexto y responder de manera coherente. "
        "No menciones información del historial a menos que sea directamente relevante para la pregunta actual o que el usuario te lo pida explícitamente. "
        "Responde como lo haría un humano que recuerda la conversación pero no repite constantemente lo que ya sabe. "
        "Responde en el mismo idioma que el usuario."
        "Preséntate como 'Yu Delivery Bot' y explica brevemente que eres un asistente para realizar pedidos en restaurantes con múltiples sucursales"
    )
    
    parts: List[str] = ["<|begin_of_text|>"]
    
    # Agregar instrucción de sistema al inicio
    parts.append(f"<|start_header_id|>system<|end_header_id|>\n{system_instruction}\n<|eot_id|>\n")
    
    for m in messages:
        if isinstance(m, dict):
            role = m.get("role") or "user"
            content = m.get("content") or ""
        else:
            # Soporte para objetos como HumanMessage, AIMessage, etc.
            # LangChain usa 'type' o 'role' según la versión/clase.
            # Intentamos obtener el rol de varias maneras comunes.
            role = getattr(m, "role", None) or getattr(m, "type", "user")
            content = getattr(m, "content", "")
            
        if not content:
            continue
            
        # Normalizar roles de LangChain a roles de Llama
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"
            
        parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n{content}\n<|eot_id|>\n")
        
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n")
    return "".join(parts)


class LlamaLLMAdapter(BaseLLM):
    """
    Adaptador concreto para el modelo Llama de Meta vía AWS Bedrock.
    Implementado para ser consistente con GeminiLLM.
    """
    def __init__(
        self,
        region: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: Optional[int] = 3,
    ):
        self._region = region or config.aws_region
        self._model = model or config.llama_model
        self._temperature = float(temperature if temperature is not None else config.llama_temperature)
        self._max_tokens = max_tokens or config.llama_max_tokens
        self._max_retries = int(max_retries)

        client_kwargs = {"region_name": self._region}
        
        # Usar keys de config si no se proveen
        aws_id = access_key or config.aws_access_key_id
        aws_secret = secret_key or config.aws_secret_access_key
        
        if aws_id and aws_secret:
            client_kwargs["aws_access_key_id"] = aws_id
            client_kwargs["aws_secret_access_key"] = aws_secret

        try:
            self._client = boto3.client("bedrock-runtime", **client_kwargs)
            logger.info(f"Llama client initialized with model: {self._model} in region: {self._region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise

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

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "model": self._model,
            "provider": "meta (aws bedrock)",
            "region": self._region,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "max_retries": self._max_retries,
        }

    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        return self._invoke_with_retries(messages)

    def _invoke_with_retries(self, messages: List[ChatMessage]) -> LLMResponse:
        # 1. Definir las instrucciones de sistema en el formato Converse
        system_instruction = (
            "Eres un asistente conversacional útil y natural. "
            "Tienes acceso al historial completo de la conversación, pero debes usarlo únicamente para entender el contexto y responder de manera coherente. "
            "No menciones información del historial a menos que sea directamente relevante para la pregunta actual o que el usuario te lo pida explícitamente. "
            "Responde como lo haría un humano que recuerda la conversación pero no repite constantemente lo que ya sabe. "
            "Responde en el mismo idioma que el usuario."
        )
        system_prompts = [{"text": system_instruction}]

        # 2. Convertir tu historial de mensajes al formato estandarizado de Bedrock
        bedrock_messages = []
        for m in messages:
            if isinstance(m, dict):
                role = m.get("role") or "user"
                content = m.get("content") or ""
            else:
                role = getattr(m, "role", None) or getattr(m, "type", "user")
                content = getattr(m, "content", "")

            if not content:
                continue

            # Normalizar roles
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            elif role == "system":
                # Si tienes mensajes de sistema en el historial, ponlos con el system_prompt
                system_prompts.append({"text": content})
                continue

            bedrock_messages.append({
                "role": role,
                "content": [{"text": content}]
            })

        if not bedrock_messages:
            return LLMResponse(text="", raw=None)

        # 3. Configurar parámetros
        inference_config = {"temperature": self._temperature}
        if self._max_tokens is not None:
            inference_config["maxTokens"] = int(self._max_tokens)

        last_exception = None
        for attempt in range(1, self._max_retries + 1):
            try:
                # 4. Usar la API converse en lugar de invoke_model
                response = self._client.converse(
                    modelId=self._model,  # ¡Recuerda pasar "us.meta.llama4..." aquí!
                    messages=bedrock_messages,
                    system=system_prompts,
                    inferenceConfig=inference_config
                )

                # Extraer el texto de la respuesta estructurada
                response_text = response["output"]["message"]["content"][0]["text"]
                logger.info(f"Llama response received successfully (attempt {attempt})")
                return LLMResponse(text=response_text, raw=response)

            except (ClientError, Exception) as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed for Llama: {e}")
                if attempt < self._max_retries:
                    sleep_time = 2 ** attempt
                    logger.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)

        error_msg = f"LLM_ERROR: After {self._max_retries} attempts, can't invoke '{self._model}'. Reason: {str(last_exception)}"
        logger.error(error_msg)
        return LLMResponse(text=error_msg, raw=None)


__all__ = ["LlamaLLMAdapter"]
