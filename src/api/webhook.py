import requests
import time
from config import Telegram_key
from src.api.Services.telegram_service import telegram_service_instance


def telegram_webhook_start(url: str):
    webhook_url = f"{url}/webhook"
    telegram_url = telegram_service_instance.telegram_webhook_url

    payload = {"url": webhook_url}

    response = requests.post(telegram_url, json=payload)

    if response.status_code == 200 and response.json().get("ok"):
        time.sleep(3)
        print("Webhook running...")
    else:
        print("ERROR: ", response.text)




