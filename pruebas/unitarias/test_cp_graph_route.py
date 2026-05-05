"""CP-UNIT-GRAPH-* - enrutamiento (STD 4.2)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.graph import create_graph, route_intent


def test_cp_unit_graph_01_route_intent_menu() -> None:
    assert route_intent({"intent": "MENU"}) == "MENU"


def test_cp_unit_graph_02_route_intent_default_general() -> None:
    assert route_intent({}) == "GENERAL"


@pytest.mark.asyncio
async def test_cp_unit_graph_03_router_empty_messages_no_crash() -> None:
    from src.core.llm.base import LLMResponse

    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        side_effect=[
            LLMResponse(text="GENERAL"),
            LLMResponse(text="Listo."),
        ]
    )

    compiled = create_graph(llm)
    state = {
        "messages": [],
        "thread_id": "t-empty",
        "created_at": None,
        "updated_at": None,
    }
    with patch("src.orchestrator.workers.menu_specialist.get_menu") as gm:
        gm.invoke.return_value = "--- MENU ---\n"
        final = await compiled.ainvoke(
            state,
            config={"configurable": {"thread_id": "t-empty"}},
        )
    assert final.get("intent") in ("GENERAL", "MENU")
    assert "messages" in final
