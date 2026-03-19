from langgraph.graph import StateGraph, END
from src.orchestrator.state import DeliveryState
from src.core.llm.base import BaseLLM
from datetime import datetime
from typing import Optional, Any


def create_graph(llm: BaseLLM, checkpointer: Optional[Any] = None) -> StateGraph:
    """
    Construye el grafo principal de la conversacion
    - llm: instancia de BaseLLM 
    - checkpointer: opcional, para persistencia (RedisSaver, MemorySaver, etc.)
    """
    workflow = StateGraph(state_schema=DeliveryState)

    # Nodo que usa el LLM
    async def llm_node(state: DeliveryState) -> DeliveryState:
        messages = state.get("messages", [])
        response = await llm.ainvoke(messages)
        new_messages = messages + [{"role": "assistant", "content": response.text}]
        now = datetime.utcnow()
        updates = {
            "messages": new_messages,
            "updated_at": now,
        }
        if state.get("created_at") is None:
            updates["created_at"] = now
        return updates

    workflow.add_node("llm", llm_node)
    workflow.set_entry_point("llm")
    workflow.add_edge("llm", END)

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()