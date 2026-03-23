from fastapi import APIRouter, Request
import src.api.config as config
from src.api.Services.telegram_service import telegram_service_instance
import logging
import redis.asyncio as redis_async
from src.core.config import config as app_config

webhook_router = APIRouter()
logging.basicConfig(level=logging.INFO)


async def set_ttl_for_thread(thread_id: str, ttl_seconds: int = 28800):
    """Establece TTL en todas las claves de Redis relacionadas con el thread."""
    try:
        redis_client = redis_async.from_url(app_config.redis_connection_string)
        keys = await redis_client.keys(f"*{thread_id}*")
        if keys:
            # Usar pipeline para mayor eficiencia
            async with redis_client.pipeline() as pipe:
                for key in keys:
                    pipe.expire(key, ttl_seconds)
                await pipe.execute()
            logging.info(f"TTL de {ttl_seconds}s aplicado a {len(keys)} claves del thread {thread_id}")
    except Exception as e:
        logging.error(f"Error al establecer TTL en Redis: {e}")


@webhook_router.post("/webhook")
async def message_recept(request: Request):
    update = await request.json()
    logging.info(f"Update recibido: {update}")

    if "message" not in update:
        return {"status": "ok"}

    message = update["message"]
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "")
    if not text:
        return {"status": "ok"}

    user_message = {"role": "user", "content": text}
    thread_config = {"configurable": {"thread_id": chat_id}}
    initial_state = {
        "messages": [user_message],
        "thread_id": chat_id,
        "created_at": None,
        "updated_at": None,
    }

    try:
        final_state = await config.graph.ainvoke(initial_state, config=thread_config)

        # Extraer ultimo mensaje del asistente (puede ser objeto o dict)
        assistant_messages = []
        for m in final_state["messages"]:
            if isinstance(m, dict):
                role = m.get("role")
                content = m.get("content")
            else:
                role = getattr(m, "type", None)
                content = getattr(m, "content", "")
            if role == "assistant" or role == "ai":
                assistant_messages.append(content)

        if assistant_messages:
            last_response = assistant_messages[-1]
        else:
            last_response = "Lo siento, no pude generar una respuesta."

        # Enviar respuesta a Telegram
        telegram_service_instance.send_message(int(chat_id), last_response)

        # Establecer TTL en Redis para las claves del thread (8 horas)
        await set_ttl_for_thread(chat_id)

    except Exception as e:
        logging.error(f"Error al procesar el grafo: {e}", exc_info=True)
        telegram_service_instance.send_message(int(chat_id), "Ocurrio un error interno.")

    return {"status": "ok"}