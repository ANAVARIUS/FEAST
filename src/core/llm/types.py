from typing import Literal, Optional, TypedDict

Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(TypedDict, total=False):
    role: Role
    content: str
    name: Optional[str]


__all__ = ["Role", "ChatMessage"]