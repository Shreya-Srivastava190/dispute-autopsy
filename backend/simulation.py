from datetime import datetime
from typing import Any

from network_risk import build_network_risk
from merchant_spike import build_merchant_spike


# Simulated disputes live ONLY in memory, in this list. They are never
# written to disputes.json, so the real seed data used everywhere else
# in the app (Inbox, Dashboard, Triage) can never be corrupted by a
# simulation run. This resets to empty every time the server restarts —
# that's intentional, not a bug: a demo sandbox should always start clean.
_simulated_disputes: list[dict[str, Any]] = []

_next_id = 1


def reset_simulation() -> None:
    global _simulated_disputes, _next_id
    _simulated_disputes = []
    _next_id = 1


def add_simulated_dispute(
    customer_id: str,
    merchant_id: str,
    reason: str,
    amount: int,
    real_disputes: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Builds a plausible synthetic dispute and computes how it changes the
    network risk picture for this customer, combining real + simulated
    data. Deliberately gives the new dispute WEAK delivery evidence (not
    delivered, no signature) — a simulation is meant to model "a new
    complaint just came in," which is more useful for demoing risk
    escalation than a slam-dunk CONTEST case.
    """
    global _next_id

    now = datetime.now().isoformat()
    dispute_id = f"sim_{_next_id:03d}"
    _next_id += 1

    dispute = {
        "dispute_id": dispute_id,
        "reason": reason,
        "amount": amount,
        "currency": "INR",
        "customer_id": customer_id,
        "merchant_id": merchant_id,
        "filed_at": now,
        "response_deadline": now,
        "payment": {
            "payment_id": f"pay_{dispute_id}",
            "status": "captured",
            "amount": amount,
            "date": now,
        },
        "order": {
            "order_id": f"ORD_{dispute_id}",
            "product": "Simulated order",
            "amount": amount,
            "status": "fulfilled",
            "shipping_address": "Simulated address",
        },
        "delivery": {
            "status": "not_delivered",
            "delivered_at": None,
            "address_match": False,
            "signature_available": False,
            "courier": "Simulated Courier",
        },
        "refund": {"issued": False},
        "support": {
            "customer_contacted": True,
            "merchant_response": False,
            "conversation": "Simulated dispute created for demo purposes.",
        },
        "_simulated": True,
    }

    _simulated_disputes.append(dispute)

    combined = real_disputes + _simulated_disputes
    network_risk = build_network_risk(dispute, combined)
    merchant_spike = build_merchant_spike(dispute, combined)

    return {
        "dispute": dispute,
        "network_risk": network_risk,
        "merchant_spike": merchant_spike,
        "total_simulated": len(_simulated_disputes),
    }


def get_simulation_state(real_disputes: list[dict[str, Any]]) -> dict[str, Any]:
    combined = real_disputes + _simulated_disputes
    rows = []
    for d in _simulated_disputes:
        rows.append({
            "dispute_id": d["dispute_id"],
            "customer_id": d["customer_id"],
            "merchant_id": d["merchant_id"],
            "amount": d["amount"],
            "reason": d["reason"],
            "network_risk": build_network_risk(d, combined),
        })
    return {"simulated_disputes": rows}