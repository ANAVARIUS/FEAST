"""Webhook de Stripe: notifica por Telegram pago completado o fallido."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import stripe
from fastapi import APIRouter, HTTPException, Request
from stripe.error import SignatureVerificationError

from src.api.Services.telegram_service import telegram_service_instance
from src.core.config import config
from src.infrastructure.redis import ConversationSessionStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])
_store = ConversationSessionStore()


def _stripe_obj_to_plain_dict(obj: Any) -> Dict[str, Any]:
    """stripe.StripeObject / dict -> dict plano (metadata, etc.)."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            d = to_dict()
            if isinstance(d, dict):
                return dict(d)
        except Exception:
            pass
    try:
        return {k: obj[k] for k in obj.keys()}  # type: ignore[attr-defined]
    except Exception:
        return {}


def _chat_id_from_session(session_obj: Dict[str, Any]) -> Optional[int]:
    meta = _stripe_obj_to_plain_dict(session_obj.get("metadata"))
    raw = meta.get("telegram_chat_id") or session_obj.get("client_reference_id")
    if not raw:
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _chat_id_from_payment_intent(pi_obj: Dict[str, Any]) -> Optional[int]:
    meta = _stripe_obj_to_plain_dict(pi_obj.get("metadata"))
    raw = meta.get("telegram_chat_id")
    if not raw:
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _session_obj_to_chat_payload(sess: Any) -> Dict[str, Any]:
    """Normaliza un stripe.checkout.Session a dict para _chat_id_from_session."""
    meta = _stripe_obj_to_plain_dict(getattr(sess, "metadata", None))
    return {
        "id": getattr(sess, "id", None),
        "metadata": meta,
        "client_reference_id": getattr(sess, "client_reference_id", None),
        "payment_status": getattr(sess, "payment_status", None),
    }


def _chat_id_from_stripe_session(sess: Any) -> Optional[int]:
    cid = _chat_id_from_session(_session_obj_to_chat_payload(sess))
    if cid:
        return cid
    pi = getattr(sess, "payment_intent", None)
    if pi is None or isinstance(pi, str):
        return None
    return _chat_id_from_payment_intent({"metadata": getattr(pi, "metadata", None)})


async def notify_telegram_if_checkout_paid(session_id: str) -> None:
    """
    Tras redirección a /pay/success con session_id: verifica pago en Stripe y avisa por Telegram.
    Idempotente con el webhook (misma _notify_success y flag stripe_notified_success).
    """
    secret = (config.stripe_secret_key or "").strip()
    sid = (session_id or "").strip()
    logger.info("[pay:success] begin session_id=%s has_stripe_key=%s", sid, bool(secret))
    if not secret:
        logger.error(
            "[pay:success] STRIPE_SECRET_KEY vacía en el proceso; no se puede confirmar el pago",
        )
        return
    if not sid:
        return

    def _retrieve() -> Any:
        stripe.api_key = secret
        return stripe.checkout.Session.retrieve(sid, expand=["payment_intent"])

    try:
        sess = await asyncio.to_thread(_retrieve)
    except stripe.error.StripeError as e:
        logger.warning("[pay:success] stripe retrieve failed session=%s: %s", sid, e)
        return

    pay_st = (getattr(sess, "payment_status", None) or "").lower()
    sess_st = (getattr(sess, "status", None) or "").lower()
    logger.info(
        "[pay:success] stripe session=%s status=%s payment_status=%s",
        sid,
        sess_st or "?",
        pay_st or "?",
    )
    if pay_st not in ("paid", "no_payment_required"):
        logger.info(
            "[pay:success] session=%s payment_status=%s (skip notify)",
            sid,
            pay_st or "?",
        )
        return

    chat_id = _chat_id_from_stripe_session(sess)
    if not chat_id:
        meta = _session_obj_to_chat_payload(sess).get("metadata")
        logger.warning(
            "[pay:success] no chat_id session=%s metadata_keys=%s ref=%s",
            sid,
            list(meta.keys()) if isinstance(meta, dict) else meta,
            getattr(sess, "client_reference_id", None),
        )
        return

    resolved_id = str(getattr(sess, "id", None) or sid)
    await _notify_success(chat_id, resolved_id)


async def _notify_success(chat_id: int, session_id: str) -> None:
    existing = await _store.load(str(chat_id))
    if existing.flags.get("stripe_notified_success") == session_id:
        logger.info(
            "[webhook:stripe] idempotent success chat=%s session=%s",
            chat_id,
            session_id,
        )
        return

    text = (
        "Pago completado correctamente. Gracias por tu compra en FEAST. "
        "Si necesitas algo más, escribe aquí."
    )
    sent = telegram_service_instance.send_message(chat_id, text, parse_mode=None)
    if not sent:
        logger.error(
            "[webhook:stripe] telegram no entregó mensaje chat=%s session=%s (reintenta abriendo /pay/success de nuevo)",
            chat_id,
            session_id,
        )
        return

    def _mut(p):
        p.order_phase = "payment_completed"
        p.cart = []
        p.flags["stripe_last_event"] = "payment_success"
        p.flags["stripe_session_id"] = session_id
        p.flags["payment_pending"] = False
        p.flags["stripe_notified_success"] = session_id

    await _store.merge_update(str(chat_id), mutator=_mut)
    logger.info("[webhook:stripe] notify success chat=%s session=%s", chat_id, session_id)


async def _notify_payment_pending(
    chat_id: int,
    reason: str,
    detail: str = "",
) -> None:
    body = (
        "No se completó el pago. Tu pedido sigue pendiente: puedes intentar de nuevo "
        "con una tarjeta válida o pedir de nuevo el enlace de pago desde el chat."
    )
    if detail:
        body = f"{body}\n\nDetalle: {detail}"
    sent = telegram_service_instance.send_message(chat_id, body, parse_mode=None)
    if not sent:
        logger.error(
            "[webhook:stripe] telegram pending/fail not delivered chat=%s reason=%s",
            chat_id,
            reason,
        )
        return

    def _mut(p):
        p.order_phase = "awaiting_payment"
        p.flags["stripe_last_event"] = reason
        p.flags["payment_pending"] = True

    await _store.merge_update(str(chat_id), mutator=_mut)
    logger.info(
        "[webhook:stripe] notify pending/fail chat=%s reason=%s",
        chat_id,
        reason,
    )


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request) -> dict:
    secret = (config.stripe_webhook_secret or "").strip()
    if not secret:
        logger.error("[webhook:stripe] STRIPE_WEBHOOK_SECRET missing")
        raise HTTPException(status_code=503, detail="Webhook no configurado")

    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    if not sig:
        raise HTTPException(status_code=400, detail="Falta Stripe-Signature")

    stripe.api_key = (config.stripe_secret_key or "").strip()
    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except ValueError as e:
        logger.warning("[webhook:stripe] bad payload: %s", e)
        raise HTTPException(status_code=400, detail="Payload inválido") from e
    except SignatureVerificationError as e:
        logger.warning("[webhook:stripe] bad signature: %s", e)
        raise HTTPException(status_code=400, detail="Firma inválida") from e

    etype = event.get("type")
    data = (event.get("data") or {}).get("object") or {}

    logger.info("[webhook:stripe] event type=%s id=%s", etype, event.get("id"))

    if etype == "checkout.session.completed":
        session_id = data.get("id") or ""
        status = (data.get("payment_status") or "").lower()
        chat_id = _chat_id_from_session(data)
        if not chat_id:
            logger.warning(
                "[webhook:stripe] checkout.completed no chat_id session=%s",
                session_id,
            )
            return {"received": True}

        if status == "paid":
            await _notify_success(chat_id, session_id)
        elif status == "unpaid":
            logger.info(
                "[webhook:stripe] checkout.completed unpaid deferred chat=%s",
                chat_id,
            )
        return {"received": True}

    if etype == "checkout.session.async_payment_succeeded":
        session_id = data.get("id") or ""
        chat_id = _chat_id_from_session(data)
        if chat_id:
            await _notify_success(chat_id, session_id)
        return {"received": True}

    if etype == "checkout.session.async_payment_failed":
        chat_id = _chat_id_from_session(data)
        if chat_id:
            await _notify_payment_pending(
                chat_id,
                "checkout.session.async_payment_failed",
                detail="El pago asíncrono no se completó.",
            )
        return {"received": True}

    if etype == "checkout.session.expired":
        chat_id = _chat_id_from_session(data)
        if chat_id:
            await _notify_payment_pending(
                chat_id,
                "checkout.session.expired",
                detail="La sesión de pago expiró. Pide un nuevo enlace en el chat.",
            )
        return {"received": True}

    if etype == "payment_intent.payment_failed":
        pi_id = data.get("id") or ""
        chat_id = _chat_id_from_payment_intent(data)
        err = (data.get("last_payment_error") or {}).get("message") or ""
        if chat_id:
            await _notify_payment_pending(
                chat_id,
                "payment_intent.payment_failed",
                detail=err or f"Intent {pi_id}",
            )
        else:
            logger.warning(
                "[webhook:stripe] payment_failed no chat_id intent=%s",
                pi_id,
            )
        return {"received": True}

    return {"received": True}
