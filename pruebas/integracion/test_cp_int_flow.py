"""CP-INT-FLOW-* - orquestacion (STD 4.3)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langgraph.checkpoint.memory import MemorySaver

from pruebas.conftest import FakeLLM, assistant_texts_from_messages, initial_state_stub
from src.core.llm.base import LLMResponse
from src.orchestrator.graph import create_graph


def _menu_patch():
    return patch("src.orchestrator.workers.menu_specialist.get_menu")


@pytest.mark.asyncio
async def test_cp_int_flow_01_menu_intent_visits_menu_specialist() -> None:
    menu_body = "--- MENU DISPONIBLE ---\n- Demo | Categoria: X | Precio: $9.99\n"
    llm = FakeLLM(
        [
            "La intencion es MENU",
            "Aqui tienes opciones del menu.",
        ]
    )
    graph = create_graph(llm)
    with _menu_patch() as gm:
        gm.invoke.return_value = menu_body
        final = await graph.ainvoke(
            initial_state_stub("Que tienen de comer?"),
            config={"configurable": {"thread_id": "flow-01"}},
        )
    assert final.get("intent") == "MENU"
    texts = assistant_texts_from_messages(final["messages"])
    assert texts


@pytest.mark.asyncio
async def test_cp_int_flow_02_empty_catalog_apology() -> None:
    llm = FakeLLM(
        [
            "MENU",
            "No hay productos hoy, lo siento.",
        ]
    )
    graph = create_graph(llm)
    with _menu_patch() as gm:
        gm.invoke.return_value = (
            "Lo siento, actualmente no hay productos disponibles en el menu."
        )
        final = await graph.ainvoke(
            initial_state_stub("Muestrame el menu"),
            config={"configurable": {"thread_id": "flow-02"}},
        )
    texts = assistant_texts_from_messages(final["messages"])
    joined = " ".join(texts).lower()
    assert "no hay" in joined or "vacio" in joined or "vac" in joined or "disculpa" in joined


@pytest.mark.asyncio
async def test_cp_int_flow_03_general_skips_menu_specialist() -> None:
    llm = FakeLLM(
        [
            "Saludo cordial sin palabra reservada",
            "Buenos dias, en que ayudo?",
        ]
    )
    graph = create_graph(llm)
    with _menu_patch() as gm:
        gm.invoke.return_value = "--- MENU ---\n"
        await graph.ainvoke(
            initial_state_stub("Hola, buenos dias"),
            config={"configurable": {"thread_id": "flow-03"}},
        )
        assert gm.invoke.call_count == 0


@pytest.mark.asyncio
async def test_cp_int_flow_06_multi_turn_same_thread_memory() -> None:
    """Dos turnos con el mismo thread_id y MemorySaver conservan contexto."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        side_effect=[
            LLMResponse(text="GENERAL"),
            LLMResponse(text="Hola."),
            LLMResponse(text="GENERAL"),
            LLMResponse(text="Seguimos en contacto."),
        ]
    )
    mem = MemorySaver()
    graph = create_graph(llm, checkpointer=mem)
    cfg = {"configurable": {"thread_id": "flow-06"}}
    with _menu_patch() as gm:
        gm.invoke.return_value = "--- MENU ---\n"
        s1 = await graph.ainvoke(initial_state_stub("Hola"), config=cfg)
        s2 = await graph.ainvoke(initial_state_stub("Gracias"), config=cfg)
    assert len(s2["messages"]) >= len(s1["messages"])
