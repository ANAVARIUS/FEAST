from langgraph.graph import StateGraph, END
from src.orchestrator.state import DeliveryState
from src.core.llm.base import BaseLLM
from datetime import datetime, timezone
from typing import Optional, Any

from src.orchestrator.workers.menu_specialist import menu_specialist_node
from src.orchestrator.workers.cart_manager import build_cart_manager_node
from src.core.prompts import ROUTER_PROMPT


def create_graph(llm: BaseLLM, checkpointer: Optional[Any] = None) -> StateGraph:
    workflow = StateGraph(state_schema=DeliveryState)
    cart_manager_node = build_cart_manager_node(llm)

    async def router_node(state: DeliveryState) -> dict:
        messages = state.get("messages", [])

        last_message = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
            elif hasattr(msg, "type") and msg.type == "human":
                last_message = msg.content
                break

        prompt = ROUTER_PROMPT.format(user_message=last_message)
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        raw = (response.text or "").upper()

        intent = "GENERAL"
        if "UNKNOWN" in raw:
            intent = "UNKNOWN"
        elif "CART" in raw:
            intent = "CART"
        elif "MENU" in raw:
            intent = "MENU"

        return {"intent": intent}

    def route_intent(state: DeliveryState) -> str:
        return state.get("intent", "GENERAL")

    async def decline_node(state: DeliveryState) -> dict:
        text = (
            "No puedo ayudarte con eso. Soy el asistente de FEAST Burgers: "
            "puedo mostrarte el menú, armar tu carrito (agregar o quitar productos) "
            "y resolver dudas del restaurante."
        )
        now = datetime.now(timezone.utc)
        return {
            "messages": [{"role": "assistant", "content": text}],
            "updated_at": now,
            "menu_digest": None,
            "cart_digest": None,
        }

    async def llm_node(state: DeliveryState) -> dict:
        messages = state.get("messages", [])

        grounding_parts = []
        if state.get("menu_digest"):
            grounding_parts.append(state["menu_digest"])
        if state.get("cart_digest"):
            grounding_parts.append(state["cart_digest"])
        if state.get("order_phase"):
            grounding_parts.append(
                f"Estado del pedido (para alinear tu respuesta): {state['order_phase']}"
            )

        invoke_messages = list(messages)
        if grounding_parts:
            block = "\n\n".join(grounding_parts)
            invoke_messages = [
                {
                    "role": "user",
                    "content": (
                        "[Contexto operativo FEAST — no es el cliente; "
                        "úsalo solo para fundamentar tu respuesta al historial real.]\n\n"
                        + block
                    ),
                }
            ] + invoke_messages

        response = await llm.ainvoke(invoke_messages)
        now = datetime.now(timezone.utc)

        updates = {
            "messages": [{"role": "assistant", "content": response.text}],
            "updated_at": now,
            "menu_digest": None,
            "cart_digest": None,
        }
        if state.get("created_at") is None:
            updates["created_at"] = now
        return updates

    workflow.add_node("router", router_node)
    workflow.add_node("llm", llm_node)
    workflow.add_node("menu_specialist", menu_specialist_node)
    workflow.add_node("cart_manager", cart_manager_node)
    workflow.add_node("decline", decline_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_intent,
        {
            "MENU": "menu_specialist",
            "CART": "cart_manager",
            "GENERAL": "llm",
            "UNKNOWN": "decline",
        },
    )

    workflow.add_edge("menu_specialist", "llm")
    workflow.add_edge("cart_manager", "llm")
    workflow.add_edge("llm", END)
    workflow.add_edge("decline", END)

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()
