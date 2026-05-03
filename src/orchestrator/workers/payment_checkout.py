from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from src.core.config import config
from src.infrastructure.payments.stripe_checkout import create_checkout_session
from src.infrastructure.redis import ConversationSessionStore

logger = logging.getLogger(__name__)
_store = ConversationSessionStore()


def build_payment_checkout_node() -> Callable[..., Any]:
    async def payment_checkout_node(state: Dict[str, Any]) -> Dict[str, Any]:
        thread_id = str(state.get("thread_id") or "")
        payload = await _store.load(thread_id)
        lines = list(payload.cart)
        now = datetime.now(timezone.utc)

        if not lines:
            text = (
                "Tu carrito está vacío. Agrega productos al pedido antes de pagar; "
                "cuando esté listo, vuelve a pedir el enlace de pago."
            )
            return {
                "messages": [{"role": "assistant", "content": text}],
                "updated_at": now,
                "menu_digest": None,
                "cart_digest": None,
            }

        if not (config.stripe_secret_key or "").strip():
            text = (
                "El cobro con tarjeta no está activo en este entorno (falta configurar Stripe). "
                "Puedes seguir armando tu pedido por aquí; un administrador debe definir STRIPE_SECRET_KEY."
            )
            logger.warning("Checkout Stripe omitido: STRIPE_SECRET_KEY vacía")
            return {
                "messages": [{"role": "assistant", "content": text}],
                "updated_at": now,
                "menu_digest": None,
                "cart_digest": None,
            }

        try:

            def _run() -> str:
                session = create_checkout_session(lines, thread_id)
                return session.url or ""

            url = await asyncio.to_thread(_run)
        except Exception as e:
            logger.error("Stripe Checkout falló: %s", e, exc_info=True)
            text = (
                "No pude generar el enlace de pago en este momento. "
                "Revisa la configuración de Stripe y las URLs de éxito/cancelación, o inténtalo más tarde."
            )
            return {
                "messages": [{"role": "assistant", "content": text}],
                "updated_at": now,
                "menu_digest": None,
                "cart_digest": None,
            }

        if not url:
            text = "Stripe no devolvió un enlace de pago. Contacta soporte."
            return {
                "messages": [{"role": "assistant", "content": text}],
                "updated_at": now,
                "menu_digest": None,
                "cart_digest": None,
            }

        async def mutator(p):
            p.order_phase = "awaiting_payment"
            p.flags["stripe_checkout_url"] = url

        await _store.merge_update(thread_id, mutator=mutator)

        total = sum(ln.price * ln.quantity for ln in lines)
        text = (
            f"Listo. Tu total es ${total:.2f}.\n\n"
            f"Abre este enlace para pagar con tarjeta (Stripe Checkout):\n{url}\n\n"
            "Cuando termines, vuelve al chat si necesitas algo más."
        )
        logger.info("Checkout Stripe creado thread_id=%s", thread_id)
        return {
            "messages": [{"role": "assistant", "content": text}],
            "updated_at": now,
            "menu_digest": None,
            "cart_digest": None,
            "order_phase": "awaiting_payment",
        }

    return payment_checkout_node
