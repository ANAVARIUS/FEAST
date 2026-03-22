from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
from langgraph.graph.message import add_messages


class DeliveryState(TypedDict):
    messages: Annotated[List[Dict[str, str]], add_messages]
    thread_id: str
    intent: Optional[str]
    cart: Optional[List[Dict]]
    address: Optional[str]
    total: Optional[float]
    stock_validated: Optional[bool]
    address_valid: Optional[bool]
    created_at: datetime
    updated_at: datetime