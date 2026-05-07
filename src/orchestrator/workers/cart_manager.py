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


async def _plan_with_llm(llm: BaseLLM, user_message: str) -> List[Dict[str, Any]]:
    catalog = await asyncio.to_thread(_sync_catalog_names)
    prompt = build_cart_planner_prompt(
        user_message=user_message,
        catalog_names=catalog,
    )
    logger.debug("[worker:cart:plan] prompt_chars=%d", len(prompt))
    caps = llm.get_capabilities()

    resp = await llm.ainvoke([{"role": "user", "content": prompt}])
    logger.info("[worker:cart:plan] plan=%d", str(resp.text or ""))

    parsed = _extract_json_object(resp.text)

    # Extraemos la lista de operaciones
    if parsed and isinstance(parsed, dict) and "operations" in parsed:
        plans = []
        for op in parsed.get("operations", []):
            plan = {
                "action": str(op.get("action", "view")).lower(),
                "query": str(op.get("query", "")),
                "quantity": int(op.get("quantity", 1) or 1),
            }
            logger.info(
                "[worker:cart:plan] action=%s qty=%s query=%r",
                plan["action"],
                plan["quantity"],
                plan["query"][:120],
            )
            plans.append(plan)

        if plans:
            return plans

    # Fallback si falla la estructura
    heur = _heuristic_plan(user_message.lower())
    logger.warning("[worker:cart:plan] heuristic_fallback action=%s", heur.get("action"))
    return [heur]  # Lo devolvemos como lista para mantener la consistencia


def _mutate_cart(
        lines: List[CartLine],
        operations: List[Dict[str, Any]],
) -> tuple[List[CartLine], str]:
    # Creamos una copia del estado actual del carrito
    new_lines = [ln.model_copy(deep=True) for ln in lines]
    notes = []

    for op in operations:
        action = op.get("action", "view")
        query = op.get("query", "")
        qty = max(1, op.get("quantity", 1))

        if action == "view":
            if not notes:  # Evita saturar si hay múltiples operaciones
                notes.append("Consulta de carrito.")
            continue

        if action == "clear":
            new_lines = []
            notes.append("Carrito vaciado.")
            continue

        matches = MenuRepository.find_items_by_query(query, limit=5) if query else []

        if action == "add":
            if not matches:
                notes.append(f"No se encontró: '{query}'.")
                continue

            item = matches[0]
            if len(matches) > 1:
                # Opcional: Podrías hacer logging aquí en lugar de mostrárselo al usuario
                pass

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
            notes.append(f"Agregado: {qty}x {item.Name}.")

        elif action == "remove":
            if not query.strip():
                notes.append("Indica qué producto quitar.")
                continue

            if not new_lines:
                notes.append("El carrito ya estaba vacío.")
                continue

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
                notes.append(f"No hay '{query}' en el carrito.")
            else:
                notes.append(f"Removido: {qty}x {query}.")

            new_lines = out

    final_note = " | ".join(notes) if notes else "Acción de carrito procesada."
    return new_lines, final_note


def build_cart_manager_node(llm: BaseLLM) -> Callable[..., Any]:
    async def cart_manager_node(state: DeliveryState) -> Dict[str, Any]:
        thread_id = state.get("thread_id") or ""
        user_message = _last_user_text(state.get("messages", []))
        logger.info(
            "[worker:cart] thread=%s user_chars=%d",
            thread_id,
            len(user_message),
        )

        operations = await _plan_with_llm(llm, user_message)

        def mutator(payload):
            new_lines, op_note = _mutate_cart(
                list(payload.cart),
                operations
            )
            payload.cart = new_lines
            has_mutations = any(op.get("action") in ("add", "remove") for op in operations)
            if not new_lines:
                payload.order_phase = "idle"
            elif has_mutations and new_lines:
                payload.order_phase = "cart_building"

            if op_note:
                payload.flags["last_cart_op"] = op_note

        payload = await _store.merge_update(str(thread_id), mutator=mutator)
        logger.info(
            "[worker:cart] thread=%s cart=%s total=%.2f phase=%s",
            thread_id,
            str(payload.cart),
            sum(ln.price * ln.quantity for ln in payload.cart),
            payload.order_phase,
        )

        digest = _format_cart_digest(
            payload.cart,
            payload.order_phase,
            note=str(payload.flags.get("last_cart_op", "")),
        )
        logging.info("[worker:cart] digest=%s", digest)
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
