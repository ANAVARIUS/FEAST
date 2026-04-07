from src.orchestrator.workers.menu_specialist import menu_specialist_node
from langgraph.graph import StateGraph, END
from src.orchestrator.state import DeliveryState
from src.core.llm.base import BaseLLM
from datetime import datetime, timezone
from typing import Optional, Any


def create_graph(llm: BaseLLM, checkpointer: Optional[Any] = None) -> StateGraph:
    workflow = StateGraph(state_schema=DeliveryState)

    async def llm_node(state: DeliveryState) -> DeliveryState:
        messages = state.get("messages", [])
        print(f"DEBUG: Numero de mensajes en estado antes de LLM: {len(messages)}")
        for i, msg in enumerate(messages):
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "type", "unknown")
                content = getattr(msg, "content", "")
            print(f"  Mensaje {i}: role={role}, content={content[:100]}")

        response = await llm.ainvoke(messages)
        new_messages = messages + [{"role": "assistant", "content": response.text}]
        now = datetime.now(timezone.utc)
        updates = {
            "messages": new_messages,
            "updated_at": now,
        }
        if state.get("created_at") is None:
            updates["created_at"] = now
        return updates

    workflow.add_node("llm", llm_node)
    workflow.add_node("menu_specialist", menu_specialist_node)
    workflow.set_entry_point("llm")
    workflow.add_edge("llm", END)

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()