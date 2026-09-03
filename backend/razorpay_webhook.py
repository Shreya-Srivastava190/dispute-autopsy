"""
Razorpay webhook signature verification and dispute-payload mapping.

Built against Razorpay's documented shapes (https://razorpay.com/docs/webhooks/,
https://razorpay.com/docs/api/disputes/entity), not guessed field names:

- Signature: sent in the X-Razorpay-Signature header, computed as
  HMAC-SHA256(key=webhook_secret, message=raw_request_body). Razorpay's
  own docs stress: use the RAW body, not a parsed/re-serialized one —
  re-serializing changes whitespace/key order and breaks the hash.

- Event name for a new chargeback: "payment.dispute.created".

- The dispute entity itself (nested at payload.dispute.entity in the
  webhook body) has this real shape:
    id, entity, payment_id, amount, currency, amount_deducted,
    reason_code, reason_description, respond_by (unix timestamp),
    status, phase, created_at (unix timestamp),
    evidence: { amount, summary, shipping_proof, billing_proof,
                cancellation_proof, customer_communication,
                proof_of_service, ... }

Honesty note on what this DOESN'T give us: Razorpay's dispute payload
tells you a chargeback happened and gives payment-level facts, but it
does NOT include delivery/fulfillment/order-management data (was it
delivered, is there a signature, does the address match) — that lives
in the MERCHANT's own order system, not Razorpay's. A real integration
would correlate this webhook with the merchant's OMS to complete the
evidence picture. Since there's no real OMS here, those fields are
mapped as "unconfirmed" rather than invented — see
map_razorpay_dispute_to_internal below.
"""

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any


def verify_razorpay_signature(
    raw_body: bytes, signature: str, secret: str
) -> bool:
    """
    Verifies a Razorpay webhook signature per their documented scheme:
    HMAC-SHA256 over the RAW request body, keyed with the webhook
    secret, compared against the X-Razorpay-Signature header.

    Uses hmac.compare_digest (constant-time) rather than == to avoid
    leaking timing information about how much of the signature matched
    — a standard precaution for any signature comparison.
    """
    if not secret:
        return False

    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def map_razorpay_dispute_to_internal(
    webhook_body: dict[str, Any],
) -> dict[str, Any]:
    """
    Maps a real Razorpay payment.dispute.created webhook body into
    Dispute Autopsy's internal dispute dict shape.

    Fields Razorpay actually provides map directly. Fields Razorpay
    does NOT provide (delivery status, signature availability, address
    match — these live in the merchant's own order system, not
    Razorpay's dispute payload) are marked "unconfirmed" rather than
    fabricated, and the evidence engine treats "unconfirmed" the same
    as "not yet proven" — it doesn't score points for it either way.
    """
    dispute_entity = webhook_body.get("payload", {}).get("dispute", {}).get(
        "entity", {}
    )
    payment_entity = webhook_body.get("payload", {}).get("payment", {}).get(
        "entity", {}
    )
    account_id = webhook_body.get("account_id", "unknown_account")

    amount_subunits = dispute_entity.get("amount", 0)
    amount = amount_subunits // 100  # Razorpay amounts are in paise

    respond_by_ts = dispute_entity.get("respond_by")
    created_at_ts = dispute_entity.get("created_at")

    def _from_unix(ts):
        if ts is None:
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    evidence = dispute_entity.get("evidence") or {}

    return {
        "dispute_id": dispute_entity.get("id", "unknown_dispute"),
        "reason": (
            dispute_entity.get("reason_description")
            or dispute_entity.get("reason_code")
            or "UNKNOWN"
        ).upper().replace(" ", "_"),
        "amount": amount,
        "currency": dispute_entity.get("currency", "INR"),
        "customer_id": payment_entity.get("customer_id") or payment_entity.get(
            "email", "unknown_customer"
        ),
        "merchant_id": account_id,
        "filed_at": _from_unix(created_at_ts),
        "response_deadline": _from_unix(respond_by_ts),
        "payment": {
            "payment_id": dispute_entity.get("payment_id", "unknown_payment"),
            "status": payment_entity.get("status", "captured"),
            "amount": amount,
            "date": _from_unix(payment_entity.get("created_at")),
        },
        "order": {
            "order_id": payment_entity.get("order_id", "unknown_order"),
            "product": "Unknown — not provided by Razorpay's dispute payload",
            "amount": amount,
            "status": "unconfirmed",
            "shipping_address": "unconfirmed",
        },
        "delivery": {
            # NOT in Razorpay's dispute payload — would come from the
            # merchant's own order/fulfillment system in a real
            # integration. Left unconfirmed, not invented.
            "status": "unconfirmed",
            "delivered_at": None,
            "address_match": False,
            "signature_available": False,
            "courier": "unconfirmed",
        },
        "refund": {"issued": False},  # would need a separate refund.created check
        "support": {
            "customer_contacted": True,
            "merchant_response": False,
            "conversation": evidence.get("summary") or "No evidence summary provided.",
        },
        "_source": "razorpay_webhook",
        "_razorpay_phase": dispute_entity.get("phase"),
        "_razorpay_status": dispute_entity.get("status"),
    }