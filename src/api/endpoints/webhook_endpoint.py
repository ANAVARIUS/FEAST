from fastapi import APIRouter, Request
from src.api.config import app

webhook_router = APIRouter()


@webhook_router.post("/webhook")
async def message_recept(request: Request):
    update = await request.json()
    print(update)
    return {"status": "ok"}
