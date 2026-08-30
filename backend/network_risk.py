from typing import Any


# Thresholds are intentionally simple counts, not ML — a real risk team
# can see exactly why something was flagged, which matters more than
# marginal precision at this stage.
REPEAT_CUSTOMER_THRESHOLD = 2
REPEAT_MERCHANT_THRESHOLD = 2
CROSS_MERCHANT_THRESHOLD = 2  # distinct merchants disputed by one customer


def build_network_risk(dispute: dict[str, Any], all_disputes: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Looks across every dispute on file (not just this one) to check for
    patterns: the same customer filing repeated disputes, the same
    merchant getting repeated ITEM_NOT_RECEIVED-style claims, and —
    the platform-wide signal a single merchant could never see on their
    own — the same customer disputing multiple DIFFERENT merchants.

    This is a separate signal from the evidence score. A single dispute
    can have strong evidence (favoring the merchant) while still sitting
    inside a risky pattern that a human should know about.
    """

    customer_id = dispute.get("customer_id")
    merchant_id = dispute.get("merchant_id")

    customer_disputes = [
        d for d in all_disputes if d.get("customer_id") == customer_id
    ]
    merchant_disputes = [
        d for d in all_disputes if d.get("merchant_id") == merchant_id
    ]

    distinct_merchants = {
        d.get("merchant_id") for d in customer_disputes if d.get("merchant_id")
    }

    flags = []

    if len(customer_disputes) >= REPEAT_CUSTOMER_THRESHOLD:
        other_ids = [
            d["dispute_id"] for d in customer_disputes
            if d["dispute_id"] != dispute["dispute_id"]
        ]
        flags.append({
            "type": "repeat_customer",
            "finding": (
                f"This customer has filed {len(customer_disputes)} disputes "
                f"on record (also: {', '.join(other_ids)})."
            ),
        })

    if len(merchant_disputes) >= REPEAT_MERCHANT_THRESHOLD:
        other_ids = [
            d["dispute_id"] for d in merchant_disputes
            if d["dispute_id"] != dispute["dispute_id"]
        ]
        flags.append({
            "type": "repeat_merchant",
            "finding": (
                f"This merchant has {len(merchant_disputes)} disputes on "
                f"record (also: {', '.join(other_ids)})."
            ),
        })

    is_cross_merchant_serial = len(distinct_merchants) >= CROSS_MERCHANT_THRESHOLD

    if is_cross_merchant_serial:
        other_ids = [
            d["dispute_id"] for d in customer_disputes
            if d["dispute_id"] != dispute["dispute_id"]
        ]
        flags.append({
            "type": "cross_merchant_serial_disputer",
            "finding": (
                f"This customer has disputed {len(distinct_merchants)} "
                f"different merchants on the platform, not just this one "
                f"(also: {', '.join(other_ids)}). A single merchant's own "
                f"dashboard would never surface this pattern — it's only "
                f"visible with platform-wide dispute data."
            ),
        })

    # Cross-merchant serial disputing is the strongest signal — it means
    # this isn't a one-off complaint with one seller, it's a pattern
    # across the platform. That alone earns "high" regardless of the
    # other two checks.
    if is_cross_merchant_serial:
        risk_level = "high"
    elif len(customer_disputes) >= REPEAT_CUSTOMER_THRESHOLD and (
        len(merchant_disputes) >= REPEAT_MERCHANT_THRESHOLD
    ):
        risk_level = "high"
    elif flags:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "customer_dispute_count": len(customer_disputes),
        "merchant_dispute_count": len(merchant_disputes),
        "distinct_merchants_disputed": len(distinct_merchants),
        "flags": flags,
    }