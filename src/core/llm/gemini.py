"""
Modulo para interactuar con Gemini API implementando la interfaz BaseLLM
"""

import os
import logging
import time
from typing import List, Optional, Union, Any, Dict

from google import genai
from google.genai import types
from google.api_core.exceptions import GoogleAPIError, RetryError, DeadlineExceeded

from src.core.config import config
from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage

logger = logging.getLogger(__name__)

class GeminiLLM(BaseLLM):
    """
    Adaptador concreto para el modelo Gemini de Google
    """
    def __init__(self, api_key=None, model_name=None, max_retries=None, temperature=None, max_output_tokens=None):
        self.api_key = api_key or config.gemini_api_key
        if not self.api_key:
            raise ValueError("No se tiene API key...")
        model = model_name or config.gemini_model
        if not model.startswith("models/"):
            model = f"models/{model}"
        self.model_name = model
        self.max_retries = max_retries or config.gemini_max_retries
        self.temperature = temperature or config.gemini_temperature
        self.max_output_tokens = max_output_tokens or config.gemini_max_tokens
        self.client = genai.Client(api_key=self.api_key)
        logger.info("Cliente Gemini inicializado con modelo: %s", self.model_name)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "provider": "Google",
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
        }
    
    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        return self._invoke_with_retries(messages)

    async def ainvoke(self, messages: List[ChatMessage]) -> LLMResponse:
        import asyncio
        return await asyncio.to_thread(self.invoke, messages)

    def _invoke_with_retries(self, messages: List[ChatMessage]) -> LLMResponse:
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # Convertir mensajes a diccionarios primero
                dict_messages = self._convert_to_dict(messages)
                contents = self._build_contents(dict_messages)
                logger.debug(
                    "Gemini: intento=%d/%d mensajes=%d roles=%s",
                    attempt,
                    self.max_retries,
                    len(dict_messages),
                    [m.get("role") for m in dict_messages],
                )
                config = types.GenerateContentConfig(
                    max_output_tokens=self.max_output_tokens,
                    temperature=self.temperature,
                    system_instruction=(
                        "Eres un asistente conversacional útil y natural. "
                        "Tienes acceso al historial completo de la conversación, pero debes usarlo únicamente para entender el contexto y responder de manera coherente. "
                        "No menciones información del historial a menos que sea directamente relevante para la pregunta actual o que el usuario te lo pida explícitamente. "
                        "Responde como lo haría un humano que recuerda la conversación pero no repite constantemente lo que ya sabe. "
                        "Por ejemplo, si el usuario dice 'mi color favorito es azul' y luego pregunta '¿qué hora es?', no debes mencionar el color. "
                        "Si pregunta '¿cuál es mi color favorito?', entonces sí debes responder basándote en el historial. "
                        "Responde en el mismo idioma que el usuario."
                    )
                )
                if logger.isEnabledFor(logging.DEBUG):
                    preview = []
                    for c in contents[:6]:
                        parts = c.get("parts") or []
                        t = (parts[0].get("text") if parts else "") or ""
                        preview.append(
                            {"role": c.get("role"), "text_chars": len(t), "text_head": t[:120]}
                        )
                    logger.debug("Gemini: contenido_compacto=%s", preview)
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
                if not response or not response.text:
                    raise ValueError("Respuesta vacia de Gemini")
                logger.info(
                    "Gemini: respuesta OK chars=%d modelo=%s",
                    len(response.text),
                    self.model_name,
                )
                return LLMResponse(text=response.text, raw=response)
            except (GoogleAPIError, RetryError, DeadlineExceeded) as e:
                last_exception = e
                logger.warning("Intento %d fallo (error de API): %s", attempt, e)
            except Exception as e:
                last_exception = e
                logger.error("Intento %d fallo con excepcion: %s", attempt, e)

            if attempt < self.max_retries:
                sleep_time = 2 ** attempt
                logger.info("Reintentando en %ds...", sleep_time)
                time.sleep(sleep_time)

        error_msg = f"Error despues de {self.max_retries} intentos: {last_exception}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from last_exception

    def _convert_to_dict(self, messages: List[ChatMessage]) -> List[dict]:
        """Convierte cada mensaje a un diccionario estándar."""
        dict_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                dict_messages.append(msg)
            else:
                dict_messages.append({
                    "role": getattr(msg, "role", "user"),
                    "content": getattr(msg, "content", "")
                })
        return dict_messages

    def _build_contents(self, messages: List[dict]) -> List[dict]:
        """Construye el formato de contenido para Gemini."""
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            gemini_role = "model" if role == "assistant" else role
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
        return contents

    def list_available_models(self) -> List[str]:
        try:
            models = self.client.models.list()
            return [model.name for model in models]
        except (GoogleAPIError, RetryError, DeadlineExceeded) as e:
            logger.error("No se pudo listar modelos: %s", e)
            return []