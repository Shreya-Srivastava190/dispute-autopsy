from datetime import datetime
from typing import Any


# Honesty note: this priority formula is a simple, transparent heuristic
# for demo purposes — NOT a calibrated model. It's presented that way in
# the UI. The goal is to show believable triage behavior (big money +
# tight deadline + weak evidence should float to the top), not to claim
# statistical rigor we haven't earned.


def get_urgency(deadline_str: str, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    deadline = datetime.fromisoformat(deadline_str)
    hours_remaining = (deadline - now).total_seconds() / 3600

    if hours_remaining < 24:
        level = "red"
    elif hours_remaining <= 72:
        level = "yellow"
    else:
        level = "green"

    return {
        "hours_remaining": round(hours_remaining, 1),
        "level": level,
    }


def build_triage_queue(
    disputes: list[dict[str, Any]],
    analyses: dict[str, dict[str, Any]],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    analyses: dispute_id -> the evidence analysis dict already computed
    for that dispute (reused, not recomputed, to avoid doing the work
    twice for the same dispute in the same request).
    """
    rows = []

    for dispute in disputes:
        dispute_id = dispute["dispute_id"]
        analysis = analyses[dispute_id]
        deadline_str = dispute.get("response_deadline")

        urgency = (
            get_urgency(deadline_str, now)
            if deadline_str
            else {"hours_remaining": None, "level": "green"}
        )

        evidence_gap = 100 - analysis["evidence_score"]

        urgency_weight = {"red": 3, "yellow": 2, "green": 1}[urgency["level"]]
        # Amount is normalized against a rough reference ceiling so one
        # huge dispute doesn't make the score meaningless for the rest.
        amount_weight = min(dispute["amount"] / 10000, 5)

        priority_score = round(
            amount_weight * urgency_weight * (1 + evidence_gap / 100), 1
        )

        rows.append({
            "dispute_id": dispute_id,
            "amount": dispute["amount"],
            "currency": dispute["currency"],
            "evidence_score": analysis["evidence_score"],
            "recommendation": analysis["recommendation"],
            "urgency_level": urgency["level"],
            "hours_remaining": urgency["hours_remaining"],
            "priority_score": priority_score,
        })

    rows.sort(key=lambda r: r["priority_score"], reverse=True)
    return rows