"""Páginas mínimas de redirección tras Stripe Checkout (éxito / cancelación)."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

pay_router = APIRouter(tags=["payments"])


@pay_router.get("/pay/success", response_class=HTMLResponse)
async def pay_success() -> HTMLResponse:
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
