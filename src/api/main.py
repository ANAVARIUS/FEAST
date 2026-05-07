import uvicorn
from src.api.config import app
from src.api.util import get_docker_ngrok_url
from src.api.endpoints.webhook_endpoint import webhook_router
from src.api.webhook import telegram_webhook_start
from src.core.config import config

if __name__ == '__main__':
    ngrok_url = get_docker_ngrok_url()
    telegram_webhook_start(ngrok_url)
    app.include_router(webhook_router)
    uvicorn.run(app, host="0.0.0.0", port=config.port)