import logging

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

    def send_message(self, chat_id: int, texto: str):
        url = f"{self.telegram_api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "HTML"
        }
        logger.info(
            "Telegram API sendMessage chat_id=%s texto_chars=%d",
            chat_id,
            len(texto or ""),
        )
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        if not response.ok or not data.get("ok"):
            logger.error(
                "Telegram API error HTTP=%s ok=%s description=%s",
                response.status_code,
                data.get("ok"),
                data.get("description"),
            )
        else:
            logger.debug("Telegram API message_id=%s", data.get("result", {}).get("message_id"))
        return data


telegram_service_instance = TelegramService()