from datetime import datetime
from typing import Any


# A "spike" is about CLUSTERING in time, not just total count — two
# disputes against the same merchant six months apart is normal
# background noise; two disputes four days apart is a signal worth a
# human's attention. This is a different kind of pattern from
# network_risk.py's repeat-merchant check, which only looks at count.
SPIKE_WINDOW_DAYS = 14
SPIKE_MIN_COUNT = 2
LOW_SAMPLE_SIZE_THRESHOLD = 5  # below this, say so honestly instead of implying certainty


def _confidence_label(count: int) -> str:
    return "low" if count < LOW_SAMPLE_SIZE_THRESHOLD else "moderate"


def build_merchant_spike(
    dispute: dict[str, Any], all_disputes: list[dict[str, Any]]
) -> dict[str, Any]:
    merchant_id = dispute.get("merchant_id")

    merchant_disputes = [
        d for d in all_disputes
        if d.get("merchant_id") == merchant_id and d.get("filed_at")
    ]

    if len(merchant_disputes) < SPIKE_MIN_COUNT:
        return {
            "is_spike": False,
            "window_days": None,
            "dispute_count": len(merchant_disputes),
            "confidence": _confidence_label(len(merchant_disputes)),
        }

    filed_dates = sorted(
        datetime.fromisoformat(d["filed_at"]) for d in merchant_disputes
    )
    span_days = (filed_dates[-1] - filed_dates[0]).total_seconds() / 86400

    is_spike = (
        len(merchant_disputes) >= SPIKE_MIN_COUNT
        and span_days <= SPIKE_WINDOW_DAYS
    )

    result = {
        "is_spike": is_spike,
        "window_days": round(span_days, 1),
        "dispute_count": len(merchant_disputes),
        "confidence": _confidence_label(len(merchant_disputes)),
    }

    if is_spike:
        other_ids = [
            d["dispute_id"] for d in merchant_disputes
            if d["dispute_id"] != dispute["dispute_id"]
        ]
        confidence_note = (
            " (small sample size — treat as an early signal, not a "
            "statistically confident anomaly)"
            if result["confidence"] == "low"
            else ""
        )
        result["finding"] = (
            f"{len(merchant_disputes)} disputes filed against this merchant "
            f"within {round(span_days, 1)} days (also: {', '.join(other_ids)}) "
            f"— a tighter cluster than isolated, unrelated complaints would "
            f"produce{confidence_note}. Could indicate a fulfillment "
            f"problem, a product issue, or coordinated fraud targeting this "
            f"merchant."
        )

    return result


def build_merchant_spike_summary(all_disputes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dashboard-level view: which merchants are currently spiking."""
    seen_merchants = set()
    spikes = []

    for dispute in all_disputes:
        merchant_id = dispute.get("merchant_id")
        if merchant_id in seen_merchants:
            continue
        seen_merchants.add(merchant_id)

        spike = build_merchant_spike(dispute, all_disputes)
        if spike["is_spike"]:
            spikes.append({
                "merchant_id": merchant_id,
                "dispute_count": spike["dispute_count"],
                "window_days": spike["window_days"],
            })

    return spikes