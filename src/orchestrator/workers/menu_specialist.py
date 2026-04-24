from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.core.prompts import MENU_SPECIALIST_PROMPT
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.orchestrator.state import DeliveryState


def _format_menu_digest(items: List[Any]) -> str:
    if not items:
        return (
            "--- MENÚ (BD) ---\n"
            "No hay productos registrados en este momento."
        )
    lines: List[str] = ["--- MENÚ (BD) — usar solo estos datos ---"]
    max_items = 80
    by_cat: Dict[str, List[str]] = {}
    for item in items[:max_items]:
        cat = getattr(item, "Category", "?") or "?"
        line = f"- {item.Name} | {cat} | ${float(item.Price):.2f} | id={item.ItemID}"
        by_cat.setdefault(cat, []).append(line)
    for cat in sorted(by_cat.keys()):
        lines.append(f"\n[{cat}]")
        lines.extend(by_cat[cat])
    if len(items) > max_items:
        lines.append(f"\n… y {len(items) - max_items} productos más (truncado por tamaño).")
    return "\n".join(lines)


async def menu_specialist_node(state: DeliveryState) -> Dict[str, Any]:
    """
    Carga el catálogo desde BD y expone un `menu_digest` efímero para el nodo LLM.
    No apila SystemMessage en el historial (evita inflar tokens y checkpoints).
    """
    items = await asyncio.to_thread(MenuRepository.get_full_catalog)
    digest = _format_menu_digest(items)
    prompt_block = f"{MENU_SPECIALIST_PROMPT}\n\n{digest}"

    now = datetime.now(timezone.utc)
    updates: Dict[str, Any] = {
        "menu_digest": prompt_block,
        "cart_digest": None,
        "updated_at": now,
    }
    if state.get("created_at") is None:
        updates["created_at"] = now
    return updates
