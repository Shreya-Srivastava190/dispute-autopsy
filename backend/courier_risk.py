from typing import Any


# Same philosophy as network_risk.py: simple counts, not ML. A merchant
# or Razorpay risk team should be able to see exactly why a courier was
# flagged without needing to trust a black-box score.
COURIER_DISPUTE_THRESHOLD = 2       # disputes before a courier gets flagged
COURIER_FAILURE_RATE_THRESHOLD = 0.5  # share of those disputes that were non-delivery
LOW_SAMPLE_SIZE_THRESHOLD = 5  # below this, say so honestly instead of implying certainty


def _confidence_label(count: int) -> str:
    return "low" if count < LOW_SAMPLE_SIZE_THRESHOLD else "moderate"


def build_courier_risk(dispute: dict[str, Any], all_disputes: list[dict[str, Any]]) -> dict[str, Any]:
    """
    This is a different KIND of signal from network_risk.py — it isn't
    about fraud, it's about fulfillment quality. A single merchant only
    ever sees their own shipments, so they can't tell whether a courier
    is uniquely unreliable or whether delivery problems are normal
    across the board. Aggregating across merchants is what makes this
    signal possible at all.
    """

    courier = dispute.get("delivery", {}).get("courier")

    if not courier:
        return {
            "courier": None,
            "risk_level": "low",
            "courier_dispute_count": 0,
            "non_delivery_count": 0,
            "flags": [],
        }

    courier_disputes = [
        d for d in all_disputes
        if d.get("delivery", {}).get("courier") == courier
    ]

    non_delivery_disputes = [
        d for d in courier_disputes
        if d.get("delivery", {}).get("status") != "delivered"
    ]

    failure_rate = (
        len(non_delivery_disputes) / len(courier_disputes)
        if courier_disputes else 0
    )

    flags = []

    if (
        len(courier_disputes) >= COURIER_DISPUTE_THRESHOLD
        and failure_rate >= COURIER_FAILURE_RATE_THRESHOLD
    ):
        other_ids = [
            d["dispute_id"] for d in courier_disputes
            if d["dispute_id"] != dispute["dispute_id"]
        ]
        confidence_note = (
            " Sample size is small, so treat this as an early signal, not "
            "a statistically confident finding."
            if _confidence_label(len(courier_disputes)) == "low"
            else ""
        )
        flags.append({
            "type": "courier_high_failure_rate",
            "finding": (
                f"{courier} is linked to {len(courier_disputes)} disputes "
                f"across merchants on file, {len(non_delivery_disputes)} of "
                f"which involved a non-delivery status (also: "
                f"{', '.join(other_ids)}). No single merchant using this "
                f"courier would see this pattern on their own — it only "
                f"shows up once disputes are compared across merchants."
                f"{confidence_note}"
            ),
        })

    risk_level = "high" if flags else "low"

    return {
        "courier": courier,
        "risk_level": risk_level,
        "courier_dispute_count": len(courier_disputes),
        "non_delivery_count": len(non_delivery_disputes),
        "confidence": _confidence_label(len(courier_disputes)),
        "flags": flags,
    }


def build_courier_breakdown(all_disputes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Aggregate per-courier stats for the dashboard — one row per courier
    with dispute count and non-delivery rate, so a risk team can scan
    for outliers at a glance instead of clicking into every dispute.
    """

    couriers: dict[str, list[dict[str, Any]]] = {}

    for d in all_disputes:
        courier = d.get("delivery", {}).get("courier")
        if not courier:
            continue
        couriers.setdefault(courier, []).append(d)

    rows = []
    for courier, courier_disputes in couriers.items():
        non_delivery = [
            d for d in courier_disputes
            if d.get("delivery", {}).get("status") != "delivered"
        ]
        failure_rate = (
            len(non_delivery) / len(courier_disputes) if courier_disputes else 0
        )
        rows.append({
            "courier": courier,
            "dispute_count": len(courier_disputes),
            "non_delivery_count": len(non_delivery),
            "failure_rate_pct": round(failure_rate * 100),
            "confidence": _confidence_label(len(courier_disputes)),
            "flagged": (
                len(courier_disputes) >= COURIER_DISPUTE_THRESHOLD
                and failure_rate >= COURIER_FAILURE_RATE_THRESHOLD
            ),
        })

    rows.sort(key=lambda r: r["failure_rate_pct"], reverse=True)
    return rows