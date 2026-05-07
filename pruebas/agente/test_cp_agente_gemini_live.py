"""CP-LLM-* con modelo real (smoke): requiere `RUN_LLM_AGENT_TESTS=1` y clave en `.env`.

DeepEval / juez LLM fino queda documentado en CASOS.md; aqui se valida integracion real
sin mocks del LLM (menu sigue pudiendo simularse para catalogo fijo).
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from pruebas.conftest import assistant_texts_from_messages, initial_state_stub


def _agent_tests_enabled() -> bool:
    return os.environ.get("RUN_LLM_AGENT_TESTS", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _gemini_configured() -> bool:
    from src.core.config import config

    return bool(config.gemini_api_key and config.gemini_api_key.strip())


@pytest.mark.asyncio
@pytest.mark.skipif(
    not _agent_tests_enabled(),
    reason="Definir RUN_LLM_AGENT_TESTS=1 para ejecutar pruebas con API real.",
)
@pytest.mark.skipif(
    not _gemini_configured(),
    reason="Falta GEMINI_API_KEY (o campo vacio) en entorno / .env.",
)
async def test_cp_llm_smoke_general_saludo() -> None:
    from src.core.llm.gemini import GeminiLLM
    from src.orchestrator.graph import create_graph

    llm = GeminiLLM()
    graph = create_graph(llm)
    with patch("src.orchestrator.workers.menu_specialist.get_menu") as gm:
        gm.invoke.return_value = "---\n"
        final = await graph.ainvoke(
            initial_state_stub("Hola, solo saludo breve."),
            config={"configurable": {"thread_id": "live-gen-01"}},
        )
    assert final.get("intent") == "GENERAL"
    texts = assistant_texts_from_messages(final["messages"])
    joined = " ".join(texts).strip()
    assert len(joined) >= 8
    assert "LLM_ERROR" not in joined


@pytest.mark.asyncio
@pytest.mark.skipif(
    not _agent_tests_enabled(),
    reason="Definir RUN_LLM_AGENT_TESTS=1 para ejecutar pruebas con API real.",
)
@pytest.mark.skipif(
    not _gemini_configured(),
    reason="Falta GEMINI_API_KEY (o campo vacio) en entorno / .env.",
)
async def test_cp_llm_menu_incluye_precio_del_catalogo_mockeado() -> None:
    from src.core.llm.gemini import GeminiLLM
    from src.orchestrator.graph import create_graph

    catalogo = (
        "Plato CP-LLM-TEST | Categoria: Pruebas | Precio: $42.42\n"
        "Otro item | Categoria: X | Precio: $1.00\n"
    )
    llm = GeminiLLM()
    graph = create_graph(llm)
    with patch("src.orchestrator.workers.menu_specialist.get_menu") as gm:
        gm.invoke.return_value = catalogo
        final = await graph.ainvoke(
            initial_state_stub("Que tienen de comer? Dame precios del menu."),
            config={"configurable": {"thread_id": "live-menu-01"}},
        )
    assert final.get("intent") == "MENU"
    texts = assistant_texts_from_messages(final["messages"])
    blob = " ".join(texts).lower()
    assert "42.42" in blob or "42,42" in blob
