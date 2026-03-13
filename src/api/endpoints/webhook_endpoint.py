from fastapi import APIRouter, Request
from src.api.config import app

webhook_router = APIRouter()


# Vela el mandar mensajes es por aqui(importa la instancia del servicio de telegram como en el webhook.py
# para usar la funcion de enviar mensaje)
@webhook_router.post("/webhook")
async def message_recept(request: Request):
    update = await request.json()
    print(update)
    return {"status": "ok"}
