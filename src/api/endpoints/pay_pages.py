"""Páginas mínimas de redirección tras Stripe Checkout (éxito / cancelación)."""

import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.api.endpoints.stripe_webhook import notify_telegram_if_checkout_paid

pay_router = APIRouter(tags=["payments"])
logger = logging.getLogger(__name__)


@pay_router.get("/pay/success", response_class=HTMLResponse)
async def pay_success(session_id: Optional[str] = None) -> HTMLResponse:
    """Stripe sustituye {CHECKOUT_SESSION_ID} en la URL; con eso confirmamos pago y avisamos a Telegram."""
    if session_id:
        logger.info("[pay:success] page hit session_id=%s...", session_id[:24])
        try:
            await notify_telegram_if_checkout_paid(session_id)
        except Exception as e:
            logger.error("[pay:success] notify error: %s", e, exc_info=True)
    else:
        logger.warning(
            "[pay:success] sin session_id en la URL; no se puede notificar Telegram "
            "(revisa STRIPE_SUCCESS_URL / PUBLIC_BASE_URL con ?session_id={CHECKOUT_SESSION_ID})",
        )

    body = """
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="utf-8"/><title>Pago — FEAST</title></head>
    <body style="font-family: system-ui, sans-serif; max-width: 32rem; margin: 2rem auto;">
      <h1>Pago recibido</h1>
      <p>Gracias. Puedes cerrar esta ventana y volver a Telegram para seguir hablando con FEAST.</p>
    </body>
    </html>
    """
    return HTMLResponse(body)


@pay_router.get("/pay/cancel", response_class=HTMLResponse)
async def pay_cancel() -> HTMLResponse:
    body = """
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="utf-8"/><title>Pago cancelado — FEAST</title></head>
    <body style="font-family: system-ui, sans-serif; max-width: 32rem; margin: 2rem auto;">
      <h1>Pago cancelado</h1>
      <p>No se completó el cobro. Vuelve al bot y pide de nuevo el enlace si quieres intentarlo otra vez.</p>
    </body>
    </html>
    """
    return HTMLResponse(body)
