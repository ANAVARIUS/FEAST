import logging
from datetime import datetime, timezone
from src.core.services.trello_service import TrelloService
from src.orchestrator.state import DeliveryState

logger = logging.getLogger(__name__)

def build_order_handler_node():
    async def trello_notifier_node(state: DeliveryState) -> dict:
        trello_service = TrelloService()
        # Extraemos la información del estado
        # Asumo que 'cart' o un resumen del pedido vive en su DeliveryState
        order_id = state.get("thread_id", "Nuevo Pedido")
        raw_cart = state.get("cart", [])
        if raw_cart:
            rows = []
            for item in raw_cart:
                rows.append(f"- {item['name']} x{item['quantity']}")
            cart_summary = "\n".join(rows)
        else:
            cart_summary = "Carrito vacío o no recuperado."
        # Formateamos la descripción para la card
        description = (
            f"Fecha: {datetime.now(timezone.utc)}\n"
            f"Detalles:\n{cart_summary}"
        )
        logger.info(f"Description of order: {description}")
        # Ejecución (si su TrelloClient es síncrono, considere ejecutarlo en un thread pool
        # para no bloquear el bucle de eventos, aunque aquí lo simplificamos)
        trello_service.create_order(f"Pedido: {order_id}", description)

        return { "cart_digest": None }  # No necesitamos actualizar el estado necesariamente
    return trello_notifier_node