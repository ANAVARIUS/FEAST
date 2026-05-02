import logging

import redis.asyncio as redis_async
from fastapi import APIRouter, Request

import src.api.config as app_state
from src.api.Services.telegram_service import telegram_service_instance
from src.core.config import config as app_config
from src.infrastructure.redis.keyspace import session_key_pattern

logger = logging.getLogger(__name__)

webhook_router = APIRouter()


async def set_ttl_for_thread(thread_id: str, ttl_seconds: int = 28800):
    """Establece TTL en todas las claves de Redis relacionadas con el thread."""
    try:
        redis_client = redis_async.from_url(app_config.redis_connection_string)
        keys_cp = await redis_client.keys(f"*{thread_id}*")
        keys_sess = await redis_client.keys(session_key_pattern(thread_id))
        keys = list({*keys_cp, *keys_sess})
        if keys:
            async with redis_client.pipeline() as pipe:
                for key in keys:
                    pipe.expire(key, ttl_seconds)
                await pipe.execute()
            logger.info(
                "Redis TTL %ss aplicado a %d claves del thread %s",
                ttl_seconds,
                len(keys),
                thread_id,
            )
    except Exception as e:
        logger.error("Error al establecer TTL en Redis: %s", e, exc_info=True)


@webhook_router.post("/webhook")
async def message_recept(request: Request):
    update = await request.json()
    msg = update.get("message") or {}
    chat_hint = msg.get("chat", {}).get("id")
    logger.info(
        "Webhook Telegram: update_id=%s chat_id=%s tiene_texto=%s",
        update.get("update_id"),
        chat_hint,
        bool(msg.get("text")),
    )
    logger.debug("Webhook payload (truncado): %s", str(update)[:800])

    if "message" not in update:
        return {"status": "ok"}

    message = update["message"]
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "")
    if not text:
        logger.debug("Mensaje sin texto; ignorado chat_id=%s", chat_id)
        return {"status": "ok"}

    preview = text if len(text) <= 400 else text[:400] + "…"
    logger.info(
        "Usuario mensaje chat_id=%s chars=%d: %s",
        chat_id,
        len(text),
        preview,
    )

    user_message = {"role": "user", "content": text}
    thread_config = {"configurable": {"thread_id": chat_id}}
    initial_state = {
        "messages": [user_message],
        "thread_id": chat_id,
        "intent": None,
        "cart": None,
        "address": None,
        "total": None,
        "stock_validated": None,
        "address_valid": None,
        "created_at": None,
        "updated_at": None,
        "menu_digest": None,
        "cart_digest": None,
        "order_phase": None,
    }

    try:
        logger.info("Grafo: ainvoke inicio thread_id=%s", chat_id)
        final_state = await app_state.graph.ainvoke(initial_state, config=thread_config)
        logger.info(
            "Grafo: ainvoke fin thread_id=%s mensajes_en_estado=%d",
            chat_id,
            len(final_state.get("messages") or []),
        )

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
            logger.warning("Grafo: sin mensaje assistant en estado final chat_id=%s", chat_id)

        logger.debug(
            "Telegram send_message chat_id=%s respuesta_chars=%d",
            chat_id,
            len(last_response or ""),
        )
        telegram_service_instance.send_message(int(chat_id), last_response)

        await set_ttl_for_thread(chat_id)

    except Exception as e:
        logger.error("Error al procesar el grafo: %s", e, exc_info=True)
        telegram_service_instance.send_message(int(chat_id), "Ocurrio un error interno.")

    return {"status": "ok"}
