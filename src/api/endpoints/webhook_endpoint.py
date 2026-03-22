from fastapi import APIRouter, Request
import src.api.config as config
from src.api.Services.telegram_service import telegram_service_instance
import logging

webhook_router = APIRouter()
logging.basicConfig(level=logging.INFO)

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
        # Extraer último mensaje del asistente (puede ser objeto o dict)
        # Después de obtener final_state
        assistant_messages = []
        for m in final_state["messages"]:
            if isinstance(m, dict):
                role = m.get("role")
                content = m.get("content")
            else:
                # Es un objeto de LangGraph (HumanMessage, AIMessage, etc.)
                role = getattr(m, "type", None)      # "human", "ai", etc.
                content = getattr(m, "content", "")
            if role == "assistant" or role == "ai":  # LangGraph usa "ai" para el asistente
                assistant_messages.append(content)

        if assistant_messages:
            last_response = assistant_messages[-1]
        else:
            last_response = "Lo siento, no pude generar una respuesta."
        telegram_service_instance.send_message(int(chat_id), last_response)
    except Exception as e:
        logging.error(f"Error al procesar el grafo: {e}", exc_info=True)
        telegram_service_instance.send_message(int(chat_id), "Ocurrio un error interno.")

    return {"status": "ok"}