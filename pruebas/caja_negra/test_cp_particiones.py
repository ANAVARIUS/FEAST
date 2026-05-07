"""CP-STOCK-EQ / CP-CART-EQ - reglas como indica el STD 4.5 (funciones puras)."""

from __future__ import annotations


def stock_decision(cantidad: int, stock: int) -> str:
    """Clases CE1-CE4 del STD (simplificado a etiqueta estable)."""
    if cantidad <= 0:
        return "error_validacion"
    if stock == 0:
        return "rechazo"
    if cantidad > stock:
        return "rechazo"
    return "exito"


def cart_quantity_action(cantidad: int, stock: int) -> str:
    """CP-CART-EQ-01 simplificado: actualizar / eliminar / error / stock."""
    if cantidad < 0:
        return "error"
    if cantidad == 0:
        return "elimina"
    if cantidad > stock:
        return "rechazo"
    return "actualiza"


def test_cp_stock_eq_representatives() -> None:
    assert stock_decision(2, 5) == "exito"
    assert stock_decision(5, 2) == "rechazo"
    assert stock_decision(1, 0) == "rechazo"
    assert stock_decision(-3, 10) == "error_validacion"


def test_cp_cart_eq_representatives() -> None:
    assert cart_quantity_action(2, 99) == "actualiza"
    assert cart_quantity_action(0, 99) == "elimina"
    assert cart_quantity_action(-1, 99) == "error"
    assert cart_quantity_action(50, 10) == "rechazo"
