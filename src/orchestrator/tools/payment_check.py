from __future__ import annotations

from typing import Iterable

from langchain_core.tools import tool

from src.infrastructure.redis.models import CartLine


def compute_payment_summary(lines: Iterable[CartLine]) -> str:
    cart = list(lines)
    if not cart:
        return "No hay productos en el carrito. Total actual: $0.00"
    total = sum(line.price * line.quantity for line in cart)
    items = sum(line.quantity for line in cart)
    return f"Total actual: ${total:.2f} por {items} producto(s)."


@tool
def payment_check(cart_lines: list[dict]) -> str:
    """
    Calcula un resumen de pago con base en el estado del carrito.
    Usa esta herramienta para responder preguntas de total o costo acumulado.
    """
    lines = [CartLine.model_validate(line) for line in cart_lines]
    return compute_payment_summary(lines)
