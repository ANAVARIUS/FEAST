from langgraph.graph import StateGraph, END
from src.orchestrator.state import DeliveryState
from src.core.llm.base import BaseLLM
from datetime import datetime, timezone
from typing import Optional, Any

from src.orchestrator.workers.menu_specialist import menu_specialist_node
from src.core.prompts import ROUTER_PROMPT # Importacion del prompt few-shot


def route_intent(state: DeliveryState) -> str:
    """Enruta segun `intent` del estado (router -> nodo siguiente). Expuesto para pruebas (STD CP-UNIT-GRAPH-*)."""
    return state.get("intent", "FALLBACK")


def create_graph(llm: BaseLLM, checkpointer: Optional[Any] = None) -> Any:
    workflow = StateGraph(state_schema=DeliveryState)

    # Nodo de clasificacion: Determina la intencion del usuario
    async def router_node(state: DeliveryState) -> dict:
        messages = state.get("messages", [])
        
        # 1. Recupera el mensaje mas reciente enviado por el humano
        last_message = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
            elif hasattr(msg, "type") and msg.type == "human":
                last_message = msg.content
                break

        # 2. Formatea el prompt con la tecnica Few-Shot
        prompt = ROUTER_PROMPT.format(user_message=last_message)
        
        # 3. Consulta al modelo de lenguaje (LLM)
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        
        # 4. Extrae la intencion detectada
        res_text = response.text.upper()
        if "MENU" in res_text:
            intent = "MENU"
        elif "GENERAL" in res_text:
            intent = "GENERAL"
        else:
            intent = "FALLBACK"  # Si no es nada de lo anterior o el LLM detecta abuso

        return {"intent": intent}

    # Nodo generador: Redacta la respuesta final al cliente
    async def llm_node(state: DeliveryState) -> dict:
        messages = state.get("messages", [])
        
        response = await llm.ainvoke(messages)
        new_messages = messages + [{"role": "assistant", "content": response.text}]
        now = datetime.now(timezone.utc)
        
        updates = {
            "messages": new_messages,
            "updated_at": now,
        }
        if state.get("created_at") is None:
            updates["created_at"] = now
        return updates

    async def fallback_node(state: DeliveryState) -> dict:
        fallback_message = {
            "role": "assistant",
            "content": "Lo siento, no puedo ayudarte con ese tema, ya que mi especialidad es gestionar tus pedidos. Pero no te preocupes, podemos continuar con tu orden justo donde la dejaste. ¿Deseas ver el menú o revisar tu carrito?"
        }

        return {
            "messages": state.get("messages", []) + [fallback_message],
            "updated_at": datetime.now(timezone.utc)
        }

    # Configuracion de la estructura del grafo
    workflow.add_node("router", router_node)
    workflow.add_node("llm", llm_node)
    workflow.add_node("menu_specialist", menu_specialist_node)
    workflow.add_node("fallback", fallback_node)

    # Punto de entrada inicial
    workflow.set_entry_point("router")

    # Definicion de caminos condicionales basados en el analisis del router
    workflow.add_conditional_edges(
        "router",
        route_intent,
        {
            "MENU": "menu_specialist", # Consultas de productos o precios
            "GENERAL": "llm", # Consultas generales o saludos
            "FALLBACK": "fallback" # Nueva ruta de seguridad
        }
    )

    # El especialista inyecta contexto del menu y luego deriva al LLM para responder
    workflow.add_edge("menu_specialist", "llm")
    
    # El flujo finaliza tras la respuesta del LLM
    workflow.add_edge("llm", END)

    workflow.add_edge("fallback", END)

    # Compilacion del grafo con persistencia opcional
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()