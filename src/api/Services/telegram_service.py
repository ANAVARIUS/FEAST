import logging
from typing import Optional

import requests

from src.core.config import config

logger = logging.getLogger(__name__)


class TelegramService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.token = config.telegram_token
            cls._instance.telegram_api_url = f"https://api.telegram.org/bot{cls._instance.token}"
            cls._instance.telegram_webhook_url = f"{cls._instance.telegram_api_url}/setWebhook"
        return cls._instance

    def send_message(
        self,
        chat_id: int,
        texto: str,
        *,
        parse_mode: Optional[str] = "HTML",
    ) -> bool:
        """Devuelve True si Telegram aceptó el mensaje."""
        url = f"{self.telegram_api_url}/sendMessage"
        payload: dict = {"chat_id": chat_id, "text": texto or ""}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        logger.info(
            "[service:telegram] sendMessage chat=%s chars=%d parse_mode=%s",
            chat_id,
            len(texto or ""),
            parse_mode or "plain",
        )
        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
        except Exception as e:
            logger.error("[service:telegram] request failed: %s", e, exc_info=True)
            return False
        if not response.ok or not data.get("ok"):
            logger.error(
                "[service:telegram] error http=%s ok=%s desc=%s body=%s",
                response.status_code,
                data.get("ok"),
                data.get("description"),
                data,
            )
            return False
        logger.info(
            "[service:telegram] delivered chat=%s message_id=%s",
            chat_id,
            data.get("result", {}).get("message_id"),
        )
        return True


telegram_service_instance = TelegramService()