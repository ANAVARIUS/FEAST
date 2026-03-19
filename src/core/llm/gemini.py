"""
Modulo para interactuar con Gemini API implementando la interfaz BaseLLM
"""

import os
import logging
import time
from typing import List, Optional

from google import genai
from google.genai import types
from google.api_core.exceptions import GoogleAPIError, RetryError, DeadlineExceeded

from src.core.llm.base import BaseLLM, LLMResponse
from src.core.llm.types import ChatMessage

logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    """
    Adaptador concreto para el modelo Gemini de Google
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_retries: int = 3,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> None:
        """
        Inicializa el cliente de Gemini
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No se tiene API key y la variable GEMINI_API_KEY no esta definida"
            )

        model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not model.startswith("models/"):
            model = f"models/{model}"
        self.model_name = model

        self.max_retries = max_retries
        self.temperature = temperature or float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
        self.max_output_tokens = max_output_tokens or int(os.getenv("GEMINI_MAX_TOKENS", "2048"))

        self.client = genai.Client(api_key=self.api_key)
        logger.info("Cliente Gemini inicializado con modelo: %s", self.model_name)

    def invoke(self, messages: List[ChatMessage]) -> LLMResponse:
        """
        Genera una respuesta usando la API de Gemini con mensajes estructurados.
        """
        return self._invoke_with_retries(messages)

    async def ainvoke(self, messages: List[ChatMessage]) -> LLMResponse:
        """
        Version asincrona de invoke
        """
        import asyncio
        return await asyncio.to_thread(self.invoke, messages)

    def _invoke_with_retries(self, messages: List[ChatMessage]) -> LLMResponse:
        """
        Llama a Gemini con reintentos y manejo de errores.
        """
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # Convertir mensajes al formato de Gemini
                contents = self._convert_messages(messages)
                # Configuración con instrucción de sistema
                config = types.GenerateContentConfig(
                    max_output_tokens=self.max_output_tokens,
                    temperature=self.temperature,
                    # system_instruction="Eres un asistente conversacional útil. Debes recordar toda la información proporcionada por el usuario a lo largo de la conversación y usarla para responder de manera coherente. Responde en el mismo idioma que el usuario."
                    # system_instruction="Eres un asistente conversacional útil. Debes recordar toda la información proporcionada por el usuario a lo largo de la conversación y usarla para responder de manera coherente. Responde en el mismo idioma que el usuario."
                    system_instruction=(
                        "Eres un asistente con memoria perfecta. "
                        "Debes recordar toda la información que el usuario te haya dicho en esta conversación. "
                        "El historial completo de mensajes se te proporciona a continuación. "
                        "Cuando el usuario pregunte algo como '¿cuál es mi color favorito?', debes responder basándote en lo que él mismo dijo antes, por ejemplo: "
                        "Si el usuario dijo 'mi color favorito es azul', y luego pregunta '¿cuál es mi color favorito?', debes responder 'Tu color favorito es azul'. "
                        "No digas que no tienes memoria ni que no puedes acceder a información personal; toda la información está en el historial. "
                        "Responde en el mismo idioma que el usuario."
                    )
                )
                logger.debug("Intento %d Enviando %d mensajes...", attempt, len(contents))

                logger.debug(f"Mensajes enviados a Gemini: {contents}")

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
                if not response or not response.text:
                    raise ValueError("Respuesta vacia de Gemini")
                logger.info("Respuesta recibida correctamente")
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

    def _convert_messages(self, messages: List[ChatMessage]) -> List[dict]:
        """
        Convierte los mensajes al formato que espera Gemini
        Roles: "user" y "model" (para el asistente)
        """
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Mapear "assistant" a "model"
            gemini_role = "model" if role == "assistant" else role
            converted.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
        return converted

    def list_available_models(self) -> List[str]:
        """
        Lista de modelos disponibles en la API
        """
        try:
            models = self.client.models.list()
            return [model.name for model in models]
        except (GoogleAPIError, RetryError, DeadlineExceeded) as e:
            logger.error("No se pudo listar modelos: %s", e)
            return []