import uvicorn
from src.api.config import get_ngrok_tunnel_url, app
from src.api.endpoints.webhook_endpoint import webhook_router
from src.api.webhook import telegram_webhook_start
from src.core.config import config

if __name__ == '__main__':
    ngrok_url = get_ngrok_tunnel_url()
    telegram_webhook_start(ngrok_url)
    app.include_router(webhook_router)
    uvicorn.run(app, host="0.0.0.0", port=config.port)