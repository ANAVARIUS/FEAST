import logging
from datetime import datetime, timezone
from typing import Any, Optional

from langgraph.graph import END, StateGraph

from src.core.llm.base import BaseLLM
from src.core.prompt_loader import build_router_prompt
from src.orchestrator.state import DeliveryState
from src.orchestrator.workers.cart_manager import build_cart_manager_node
from src.orchestrator.workers.menu_specialist import menu_specialist_node
from src.orchestrator.workers.payment_checkout import build_payment_checkout_node

logger = logging.getLogger(__name__)


def _clip(s: str, n: int = 280) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def create_graph(llm: BaseLLM, checkpointer: Optional[Any] = None) -> StateGraph:
    workflow = StateGraph(state_schema=DeliveryState)
    cart_manager_node = build_cart_manager_node(llm)
    payment_checkout_node = build_payment_checkout_node()

    async def router_node(state: DeliveryState) -> dict:
        messages = state.get("messages", [])
        thread_id = state.get("thread_id", "")

        last_message = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
            if hasattr(msg, "type") and msg.type == "human":
                last_message = msg.content
                break

        logger.info(
            "[graph:router] thread=%s user_chars=%d user=%r",
            thread_id,
            len(last_message),
            _clip(last_message, 200),
        )

        prompt = build_router_prompt(user_message=last_message)
        caps = llm.get_capabilities()
        logger.debug(
            "[graph:router] llm provider=%s model=%s",
            caps.get("provider"),
            caps.get("model"),
        )
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        raw = (response.text or "").upper()
        logger.info("[graph:router] raw_reply=%r", _clip(raw, 200))

        prev_intent = state.get("intent")

        intent = "GENERAL"
        if "FALLBACK" in raw or "UNKNOWN" in raw:
            intent = "FALLBACK"
        elif "CART" in raw:
            intent = "CART"
        elif "MENU" in raw:
            intent = "MENU"
        elif "CHECKOUT" in raw:
            intent = "CHECKOUT"
        elif "PAYMENT" in raw:
            intent = "PAYMENT"

        changed = intent != prev_intent
        logger.info(
            "[graph:intent] thread=%s detected=%s previous=%s changed=%s",
            thread_id,
            intent,
            prev_intent,
            changed,
        )
        return {"intent": intent}

    def route_intent(state: DeliveryState) -> str:
        return state.get("intent", "GENERAL")

    async def decline_node(state: DeliveryState) -> dict:
        logger.info(
            "[graph:decline] thread=%s intent=FALLBACK",
            state.get("thread_id", ""),
        )
        text = (
            "No puedo ayudarte con eso. Soy el asistente de FEAST para pedidos de comida: "
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
        thread_id = state.get("thread_id", "")
        intent = state.get("intent", "GENERAL")

        grounding_parts = []
        if state.get("menu_digest"):
            grounding_parts.append(state["menu_digest"])
            logger.debug(
                "[graph:llm] menu_digest chars=%d",
                len(state["menu_digest"]),
            )
        if state.get("cart_digest"):
            grounding_parts.append(state["cart_digest"])
            logger.debug(
                "[graph:llm] cart_digest chars=%d",
                len(state["cart_digest"]),
            )
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
                        "[Contexto operativo FEAST (menú / carrito / pedido) — no es el mensaje del cliente; "
                        "úsalo solo para fundamentar tu respuesta al historial real.]\n\n"
                        + block
                    ),
                }
            ] + invoke_messages
            logger.info(
                "[graph:llm] thread=%s intent=%s hist_msgs=%d context=yes",
                thread_id,
                intent,
                len(messages),
            )
        else:
            logger.info(
                "[graph:llm] thread=%s intent=%s hist_msgs=%d context=no",
                thread_id,
                intent,
                len(messages),
            )

        caps = llm.get_capabilities()
        logger.debug("[graph:llm] caps=%s", caps)
        response = await llm.ainvoke(invoke_messages)
        logger.info(
            "[graph:llm] thread=%s assistant_chars=%d assistant=%r",
            thread_id,
            len(response.text or ""),
            _clip(response.text or "", 320),
        )
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
    workflow.add_node("payment_checkout", payment_checkout_node)
    workflow.add_node("decline", decline_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_intent,
        {
            "MENU": "menu_specialist",
            "CART": "cart_manager",
            "GENERAL": "llm",
            "PAYMENT": "llm",
            "CHECKOUT": "payment_checkout",
            "FALLBACK": "decline",
        },
    )

    workflow.add_edge("menu_specialist", "llm")
    workflow.add_edge("cart_manager", "llm")
    workflow.add_edge("payment_checkout", END)
    workflow.add_edge("llm", END)
    workflow.add_edge("decline", END)
    if checkpointer:
        logger.info("[graph] compile checkpointer=redis")
        return workflow.compile(checkpointer=checkpointer)
    logger.info("[graph] compile checkpointer=none")
    return workflow.compile()
