from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class DeliveryState(TypedDict):
    """Estado de la conversacion."""
    messages: List[Dict[str, str]]
    thread_id: str
    intent: Optional[str]
    cart: Optional[List[Dict]]
    address: Optional[str]
    total: Optional[float]
    stock_validated: Optional[bool]
    address_valid: Optional[bool]
    created_at: datetime
    updated_at: datetime