"""
Carga plantillas de prompts desde `prompt_templates.json` y construye texto para el LLM.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_JSON_PATH = Path(__file__).resolve().parent / "prompt_templates.json"


@lru_cache(maxsize=1)
def _templates() -> Dict[str, Any]:
    with open(_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    logger.debug("Plantillas de prompts cargadas desde %s", _JSON_PATH)
    return data


def reload_prompt_templates() -> None:
    """Invalida la caché (útil en tests)."""
    _templates.cache_clear()


def _bullets(title: str, items: List[str]) -> str:
    if not items:
        return ""
    body = "\n".join(f"- {x}" for x in items)
    return f"{title}\n{body}"


def build_menu_specialist_instructions() -> str:
    """Bloque de instrucciones (sin el digest de menú de BD)."""
    t = _templates()["menu_specialist"]
    parts: List[str] = [str(t.get("persona", "")).strip()]
    parts.append(_bullets("Tono:", list(t.get("tone") or [])))
    parts.append(_bullets("Reglas:", list(t.get("rules") or [])))
    parts.append(_bullets("Formato:", list(t.get("format") or [])))
    return "\n\n".join(p for p in parts if p).strip()


def build_router_prompt(user_message: str) -> str:
    t = _templates()["router"]
    labels = ", ".join(t.get("allowed_labels") or [])
    guide = t.get("label_guide") or {}
    guide_lines = [f"- {k}: {v}" for k, v in guide.items()]
    examples = "\n".join(f"- {x}" for x in (t.get("examples") or []))
    tmpl = str(t.get("template", "Mensaje: \"{user_message}\""))
    blocks = [
        str(t.get("instruction", "")).strip(),
        f"Etiquetas permitidas: {labels}",
        "Guía por etiqueta:",
        "\n".join(guide_lines),
        "Ejemplos:",
        examples,
        tmpl.format(user_message=user_message),
    ]
    return "\n\n".join(blocks).strip()


def build_cart_planner_prompt(user_message: str, catalog_names: str) -> str:
    t = _templates()["cart_planner"]
    schema = t.get("output_schema") or {}
    schema_txt = json.dumps(schema, ensure_ascii=False, indent=2)
    rules = "\n".join(f"- {r}" for r in (t.get("rules") or []))
    tmpl = str(t.get("template", "{catalog_names}\n{user_message}"))
    body = "\n\n".join(
        [
            str(t.get("instruction", "")).strip(),
            "Esquema de salida (JSON):",
            schema_txt,
            "Reglas:",
            rules,
        ]
    )
    return f"{body}\n\n{tmpl.format(catalog_names=catalog_names, user_message=user_message)}".strip()


# Instrucción de sistema por defecto para Bedrock (Llama) en el nodo general del grafo.
FEAST_BEDROCK_SYSTEM_INSTRUCTION = (
    "Eres el asistente virtual de FEAST: pedidos de comida por chat (cualquier platillo o categoría del menú, "
    "no un solo tipo de producto). Guías al cliente para ver el menú, armar o revisar el carrito, consultar "
    "precios, ingredientes, disponibilidad y tiempos, y confirmar el pedido. "
    "Tono amable y claro; emojis con moderación. Usa solo datos del contexto o del historial que te den; "
    "no inventes productos, precios ni promociones. "
    "Si la consulta no es de menú, pedido o del restaurante, recházala con cortesía y redirige al flujo del pedido. "
    "Responde siempre en el idioma del usuario."
)
