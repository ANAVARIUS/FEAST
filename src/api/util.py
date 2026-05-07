import time
import logging
import requests
logger = logging.getLogger(__name__)

def get_docker_ngrok_url(retries=5):
    time.sleep(1)
    try:
        response = requests.get("http://ngrok:4040/api/tunnels")
        data = response.json()
        url = data["tunnels"][0]["public_url"]
        logger.info("[app] ngrok %s", url)
        return url
    except Exception as e:
        logger.warning("[app] ngrok error: %s", e)
        return None
