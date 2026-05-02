from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.core.llm.base import BaseLLM
from src.core.prompt_loader import build_cart_planner_prompt
from src.infrastructure.redis import CartLine, ConversationSessionStore
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.orchestrator.state import DeliveryState

logger = logging.getLogger(__name__)
_store = ConversationSessionStore()


def _last_user_text(messages: List[Any]) -> str:
    for msg in reversed(messages or []):
        if isinstance(msg, dict) and msg.get("role") == "user":
            return str(msg.get("content", ""))
        role = getattr(msg, "type", None)
        if role == "human":
            return str(getattr(msg, "content", ""))
    return ""


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL | re.IGNORECASE)
    if fence:
        raw = fence.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _heuristic_plan(user_lower: str) -> Dict[str, Any]:
    if any(
        w in user_lower
        for w in ["carrito", "mi pedido", "qué llevo", "que llevo", "ver pedido", "mostrar carrito"]
    ):
        return {"action": "view", "query": "", "quantity": 1}
    if any(w in user_lower for w in ["vaciar", "borrar todo", "limpiar carrito", "quitar todo"]):
        return {"action": "clear", "query": "", "quantity": 1}
    if any(w in user_lower for w in ["agrega", "añade", "anade", "ponme", "quiero", "dame"]):
        return {"action": "add", "query": user_lower, "quantity": 1}
    if any(w in user_lower for w in ["quita", "saca", "elimina", "resta", "menos"]):
        return {"action": "remove", "query": user_lower, "quantity": 1}
    return {"action": "view", "query": "", "quantity": 1}


def _lines_to_cart_dicts(lines: List[CartLine]) -> List[Dict[str, Any]]:
    return [ln.model_dump() for ln in lines]


def _format_cart_digest(lines: List[CartLine], order_phase: str, note: str = "") -> str:
    if not lines:
        body = "Carrito vacío."
    else:
        rows = []
        total = 0.0
        for ln in lines:
            sub = ln.price * ln.quantity
            total += sub
            rows.append(f"- {ln.name} x{ln.quantity} (${ln.price:.2f} c/u) = ${sub:.2f}")
        body = "\n".join(rows) + f"\nTotal estimado: ${total:.2f}"
    parts = [
        "--- CONTEXTO CARRITO (Redis + estado) ---",
        f"Fase del pedido: {order_phase}",
        body,
    ]
    if note:
        parts.append(f"Nota operativa: {note}")
    return "\n".join(parts)


def _sync_catalog_names() -> str:
    items = MenuRepository.get_full_catalog()
    if not items:
        return "(sin productos en catálogo)"
    lines = [f"- {it.Name}" for it in items[:60]]
    return "\n".join(lines)


async def _plan_with_llm(llm: BaseLLM, user_message: str) -> Dict[str, Any]:
    catalog = await asyncio.to_thread(_sync_catalog_names)
    prompt = build_cart_planner_prompt(
        user_message=user_message,
        catalog_names=catalog,
    )
    logger.debug("CartPlanner: prompt_chars=%d", len(prompt))
    caps = llm.get_capabilities()
    logger.info(
        "CartPlanner: invocando LLM provider=%s model=%s",
        caps.get("provider"),
        caps.get("model"),
    )
    resp = await llm.ainvoke([{"role": "user", "content": prompt}])
    logger.debug("CartPlanner: respuesta_llm_chars=%d", len(resp.text or ""))
    parsed = _extract_json_object(resp.text)
    if parsed and isinstance(parsed, dict) and "action" in parsed:
        plan = {
            "action": str(parsed.get("action", "view")).lower(),
            "query": str(parsed.get("query", "")),
            "quantity": int(parsed.get("quantity", 1) or 1),
        }
        logger.info("CartPlanner: JSON parseado action=%s qty=%s query=%r", plan["action"], plan["quantity"], plan["query"][:120])
        return plan
    heur = _heuristic_plan(user_message.lower())
    logger.warning(
        "CartPlanner: fallback heurístico (JSON inválido o ausente) action=%s",
        heur.get("action"),
    )
    return heur


def _mutate_cart(
    lines: List[CartLine],
    action: str,
    query: str,
    quantity: int,
) -> tuple[List[CartLine], str]:
    qty = max(1, quantity)
    note = ""

    if action == "view":
        return lines, "Solo consulta de carrito."

    if action == "clear":
        return [], "Carrito vaciado."

    matches = MenuRepository.find_items_by_query(query, limit=5) if query else []

    if action == "add":
        if not matches:
            return lines, "No se encontró un producto en el catálogo con esa descripción."
        item = matches[0]
        if len(matches) > 1:
            note = f"Varias coincidencias; se usó: {item.Name}. Otras: {', '.join(m.Name for m in matches[1:3])}."
        new_lines = [ln.model_copy(deep=True) for ln in lines]
        found = False
        for ln in new_lines:
            if ln.item_id == str(item.ItemID):
                ln.quantity += qty
                found = True
                break
        if not found:
            new_lines.append(
                CartLine(
                    item_id=str(item.ItemID),
                    name=item.Name,
                    price=float(item.Price),
                    quantity=qty,
                )
            )
        return new_lines, note or "Producto agregado al carrito."

    if action == "remove":
        if not query.strip():
            return lines, "Indica qué producto quitar del carrito."
        new_lines = [ln.model_copy(deep=True) for ln in lines]
        if not new_lines:
            return new_lines, "El carrito ya estaba vacío."
        qlow = query.lower()
        removed = False
        out: List[CartLine] = []
        for ln in new_lines:
            if removed or not (qlow in ln.name.lower() or ln.name.lower() in qlow):
                out.append(ln)
                continue
            removed = True
            remaining = ln.quantity - qty
            if remaining > 0:
                ln.quantity = remaining
                out.append(ln)
        if not removed:
            return lines, "No hay ese producto en el carrito (revisa el nombre)."
        return out, "Producto actualizado en el carrito."

    return lines, "Acción de carrito no reconocida; pide aclaración al usuario."


def build_cart_manager_node(llm: BaseLLM) -> Callable[..., Any]:
    async def cart_manager_node(state: DeliveryState) -> Dict[str, Any]:
        thread_id = state.get("thread_id") or ""
        user_message = _last_user_text(state.get("messages", []))
        logger.info(
            "CartManager: thread_id=%s user_chars=%d",
            thread_id,
            len(user_message),
        )

        plan = await _plan_with_llm(llm, user_message)
        if plan["quantity"] < 1:
            plan["quantity"] = 1

        def mutator(payload):
            new_lines, op_note = _mutate_cart(
                list(payload.cart),
                plan["action"],
                plan["query"],
                plan["quantity"],
            )
            payload.cart = new_lines
            if not new_lines:
                payload.order_phase = "idle"
            elif plan["action"] in ("add", "remove") and new_lines:
                payload.order_phase = "cart_building"
            if op_note:
                payload.flags["last_cart_op"] = op_note

        payload = await _store.merge_update(str(thread_id), mutator=mutator)
        logger.info(
            "CartManager: carrito_actual lineas=%d total=%.2f fase=%s",
            len(payload.cart),
            sum(ln.price * ln.quantity for ln in payload.cart),
            payload.order_phase,
        )

        digest = _format_cart_digest(
            payload.cart,
            payload.order_phase,
            note=str(payload.flags.get("last_cart_op", "")),
        )

        now = datetime.now(timezone.utc)
        updates: Dict[str, Any] = {
            "cart": _lines_to_cart_dicts(payload.cart),
            "cart_digest": digest,
            "menu_digest": None,
            "order_phase": payload.order_phase,
            "total": sum(ln.price * ln.quantity for ln in payload.cart),
            "updated_at": now,
        }
        if state.get("created_at") is None:
            updates["created_at"] = now
        return updates

    return cart_manager_node
