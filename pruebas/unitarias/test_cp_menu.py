"""CP-UNIT-TOOL-* - herramienta get_menu (STD 4.2)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.orchestrator.tools.menu_tools import get_menu


class DatabaseError(Exception):
    """Error simulado de acceso a datos (STD CP-UNIT-TOOL-03)."""


def _item(name: str, category: str, price: float) -> SimpleNamespace:
    return SimpleNamespace(Name=name, Category=category, Price=price)


@patch("src.orchestrator.tools.menu_tools.MenuRepository")
def test_cp_unit_tool_01_get_menu_success(mock_repo_class) -> None:
    mock_repo = mock_repo_class.return_value
    mock_repo.get_full_catalog.return_value = [
        _item("Hamburguesa Clasica", "Plato", 120.0),
        _item("Agua", "Bebida", 25.5),
    ]
    out = get_menu.invoke({})
    assert "--- MENU DISPONIBLE ---" in out
    assert "Hamburguesa Clasica" in out
    assert "$120.00" in out
    assert "Agua" in out
    assert "$25.50" in out


@patch("src.orchestrator.tools.menu_tools.MenuRepository")
def test_cp_unit_tool_02_get_menu_empty_catalog(mock_repo_class) -> None:
    mock_repo = mock_repo_class.return_value
    mock_repo.get_full_catalog.return_value = []
    out = get_menu.invoke({})
    assert out == "Lo siento, actualmente no hay productos disponibles en el menu."


@patch("src.orchestrator.tools.menu_tools.MenuRepository")
def test_cp_unit_tool_03_get_menu_database_error(mock_repo_class) -> None:
    mock_repo = mock_repo_class.return_value
    mock_repo.get_full_catalog.side_effect = DatabaseError("sin conexion")
    with pytest.raises(DatabaseError):
        get_menu.invoke({})
