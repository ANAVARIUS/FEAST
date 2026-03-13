import os
from dotenv import load_dotenv
from pyngrok import ngrok
from fastapi import FastAPI

load_dotenv()

app = FastAPI()

Telegram_key = os.getenv("PAPI_BOT_KEY")
Ngrok_token = os.getenv("NGROK_TOKEN")
Port = os.getenv("PORT")


def get_ngrok_tunnel_url() -> str:
    ngrok.kill()
    ngrok.set_auth_token(Ngrok_token)
    http_tunel = ngrok.connect(Port)
    return http_tunel.public_url



