"""Convenciones de nombres de claves Redis para FEAST (separado del checkpointer de LangGraph)."""

SESSION_PREFIX = "feast:v1:session"


def session_document_key(thread_id: str) -> str:
    """Documento JSON de sesion: carrito, fase de pedido, flags."""
    return f"{SESSION_PREFIX}:{thread_id}"


def session_key_pattern(thread_id: str) -> str:
    """Patron para TTL o limpieza relacionada con un hilo de Telegram."""
    return f"{SESSION_PREFIX}:{thread_id}*"
