from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CartLine(BaseModel):
    item_id: str
    name: str
    price: float
    quantity: int = Field(default=1, ge=1)


class SessionPayload(BaseModel):
    """
    Snapshot de negocio persistido en Redis por conversación (thread_id = chat_id).
    Complementa el checkpoint de LangGraph, que guarda el grafo y mensajes.
    """

    cart: List[CartLine] = Field(default_factory=list)
    order_phase: str = Field(
        default="idle",
        description="idle | cart_building | ready_for_checkout (extensible a pago)",
    )
    flags: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def empty(cls) -> "SessionPayload":
        return cls()
