from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.core.prompt_loader import build_recommendation_specialist_instructions
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.vector_repository import VectorRepository
from src.orchestrator.state import DeliveryState

logger = logging.getLogger(__name__)

async def recommendation_specialist_node(state: DeliveryState) -> Dict[str, Any]:
    """
    Busca recomendaciones en la base vectorial basada en el mensaje del usuario.
    Filtra los resultados por relevancia y los enriquece con datos de SQL.
    """
    thread_id = state.get("thread_id", "")
    messages = state.get("messages", [])
    
    # Obtener el último mensaje del usuario
    user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            user_message = msg.get("content", "")
            break
        if hasattr(msg, "type") and msg.type == "human":
            user_message = msg.content
            break

    logger.info("[worker:recommendation] thread=%s user_message=%r", thread_id, user_message)

    if not user_message:
        return {"menu_digest": "No se detectó un mensaje del usuario para recomendar."}

    # Búsqueda vectorial (en hilo para no bloquear)
    db_v = VectorRepository()
    try:
        results_v = await asyncio.to_thread(db_v.buscar, user_message)
    except Exception as e:
        logger.error("[worker:recommendation] vector search error: %s", e)
        results_v = []

    if not results_v:
        logger.info("[worker:recommendation] no matches found in vector DB")
        return {
            "menu_digest": "Lo siento, no encontré productos que coincidan con tu búsqueda.",
            "updated_at": datetime.now(timezone.utc)
        }

    # Filtrar resultados por score relativo al mejor (umbral del 70%)
    top_score = results_v[0].get("_score", 0)
    threshold = top_score * 0.7
    relevant_hits = [h for h in results_v if h.get("_score", 0) >= threshold]
    
    logger.info(
        "[worker:recommendation] found %d hits, %d are relevant (score >= %.4f)", 
        len(results_v), len(relevant_hits), threshold
    )

    db_s = MenuRepository()
    recommendations = []

    for hit in relevant_hits:
        source = hit["_source"]
        nombre = source.get("nombre", "")
        descripcion_v = source.get("descripcion", "")
        item_id_str = hit.get("_id")
        
        # Intentar obtener detalles por ID para ser precisos con SQL
        item_data = None
        if item_id_str:
            try:
                item_uuid = uuid.UUID(item_id_str)
                item_data = await asyncio.to_thread(db_s.get_item_details, item_uuid)
            except:
                pass
        
        # Si no se encuentra por ID, intentar por nombre (fallback)
        if not item_data:
            items_sql = await asyncio.to_thread(db_s.find_items_by_query, nombre)
            if items_sql:
                item_data = await asyncio.to_thread(db_s.get_item_details, items_sql[0].ItemID)

        if item_data:
            price = f"${float(item_data['price']):.2f}"
            ingredients = ""
            if item_data.get("ingredients"):
                ingredients = "\n  *Ingredientes:* " + ", ".join(item_data["ingredients"])
            
            recommendations.append(
                f"- **{item_data['name']}** | {item_data['category']} | {price}\n"
                f"  *Descripción:* {descripcion_v}{ingredients}"
            )
        else:
            # Solo datos vectoriales si no hay coincidencia en SQL
            recommendations.append(
                f"- **{nombre}**\n"
                f"  *Descripción:* {descripcion_v}\n"
                f"  (Precio no disponible en este momento)"
            )

    instructions = build_recommendation_specialist_instructions()
    prompt_block = (
        f"{instructions}\n\n"
        f"--- PRODUCTOS RECOMENDADOS ---\n"
        + "\n\n".join(recommendations)
    )

    now = datetime.now(timezone.utc)
    return {
        "menu_digest": prompt_block,
        "updated_at": now,
    }
