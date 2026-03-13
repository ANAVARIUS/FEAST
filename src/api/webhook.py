import requests
import time
from config import Telegram_key


def telegram_webhook_start(url: str):
    webhook_url = f"{url}/webhook"
    telegram_url = f"https://api.telegram.org/bot{Telegram_key}/setWebhook"

    payload = {"url": webhook_url}

    response = requests.post(telegram_url, json=payload)

    if response.status_code == 200 and response.json().get("ok"):
        time.sleep(3)
        print("Webhook running...")
    else:
        print("ERROR: ", response.text)




