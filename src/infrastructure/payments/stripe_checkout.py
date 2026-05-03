"""Creación de sesiones Stripe Checkout (síncrono; invocar con asyncio.to_thread desde nodos async)."""

from __future__ import annotations

from typing import List, Tuple

import stripe

from src.core.config import config
from src.infrastructure.redis.models import CartLine


def resolve_checkout_urls() -> Tuple[str, str] | Tuple[None, None]:
    """URLs de redirección post-pago. Requiere STRIPE_* o PUBLIC_BASE_URL (ver RESOURCES/STRIPE.md)."""
    if config.stripe_success_url and config.stripe_cancel_url:
        return config.stripe_success_url.strip(), config.stripe_cancel_url.strip()
    base = (config.public_base_url or "").strip().rstrip("/")
    if base:
        return f"{base}/pay/success", f"{base}/pay/cancel"
    return None, None


def _with_session_token(url: str) -> str:
    token = "{CHECKOUT_SESSION_ID}"
    if token in url:
        return url
    join = "&" if "?" in url else "?"
    return f"{url}{join}session_id={token}"


def create_checkout_session(
    cart_lines: List[CartLine],
    thread_id: str,
) -> stripe.checkout.Session:
    secret = (config.stripe_secret_key or "").strip()
    if not secret:
        raise ValueError("STRIPE_SECRET_KEY no configurada")

    success, cancel = resolve_checkout_urls()
    if not success or not cancel:
        raise ValueError(
            "Faltan URLs de redirección: define STRIPE_SUCCESS_URL y STRIPE_CANCEL_URL, "
            "o PUBLIC_BASE_URL apuntando a esta API (p. ej. URL pública de ngrok)."
        )

    stripe.api_key = secret
    currency = (config.stripe_currency or "mxn").lower()
    line_items = []
    for ln in cart_lines:
        unit = int(round(float(ln.price) * 100))
        if unit < 1:
            unit = 1
        line_items.append(
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": ln.name},
                    "unit_amount": unit,
                },
                "quantity": int(ln.quantity),
            }
        )

    return stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=_with_session_token(success),
        cancel_url=cancel,
        client_reference_id=thread_id[:255],
        metadata={"telegram_chat_id": thread_id[:500]},
    )
