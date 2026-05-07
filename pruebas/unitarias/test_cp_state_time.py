"""CP-UNIT-STATE-* - timestamps (STD 4.2)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.llm.base import LLMResponse
from src.orchestrator.graph import create_graph


@pytest.mark.asyncio
async def test_cp_unit_state_02_llm_node_timestamps_iso_utc() -> None:
    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        side_effect=[
            LLMResponse(text="GENERAL"),
            LLMResponse(text="Hola."),
        ]
    )

    graph = create_graph(llm)
    with patch("src.orchestrator.workers.menu_specialist.get_menu") as gm:
        gm.invoke.return_value = "menu vacio"
        final = await graph.ainvoke(
            {
                "messages": [{"role": "user", "content": "hola"}],
                "thread_id": "t-ts",
                "created_at": None,
                "updated_at": None,
            },
            config={"configurable": {"thread_id": "t-ts"}},
        )
    created = final.get("created_at")
    updated = final.get("updated_at")
    assert created is not None and updated is not None
    assert "+00:00" in created.isoformat()
    assert "+00:00" in updated.isoformat()
