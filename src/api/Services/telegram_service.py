import requests
from src.api.config import Telegram_key


# Clase de servicion de telegram singletone
class TelegramService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.token = Telegram_key
            cls._instance.telegram_api_url = f"https://api.telegram.org/bot{cls._instance.token}"
            cls._instance.telegram_webhook_url = f"https://api.telegram.org/bot{cls._instance.token}/setWebhook"
        return cls._instance

    def send_message(self, chat_id: int, texto: str):
        url = f"{self.telegram_api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload)
        return response.json()


telegram_service_instance = TelegramService()
