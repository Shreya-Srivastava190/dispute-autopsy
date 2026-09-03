"""
Generates a synthetic held-out test set for evaluating the evidence
scoring engine (investigator.build_evidence_analysis).

Honesty notes, read before trusting the numbers this produces:

1. This is SYNTHETIC data, not real historical dispute outcomes. There
   is no real-world "ground truth" available for a hackathon prototype
   with no production data.

2. Ground truth is SCENARIO-DRIVEN, not formula-mirrored. Earlier
   versions of this file derived ground truth from a weighted sum of
   the same evidence booleans the scoring engine itself sums — which
   inflates agreement between "truth" and "prediction" simply because
   both are threshold functions on the same features. This version
   instead samples a business scenario (STRONG / WEAK / AMBIGUOUS
   evidence case) first, assigns that scenario's expected ground truth,
   and only THEN generates the underlying evidence fields to be
   consistent with that scenario. The label comes from "what kind of
   real-world situation is this," not from re-running a lookalike of
   the scoring formula.

3. Noise is injected on purpose. ~12% of cases have ground truth that
   contradicts what the visible evidence suggests (signature fraud, a
   falsely-scanned "delivered" status, etc). A model that gets 100% on
   a held-out set is almost always a sign of a leaky or too-easy test
   set, not a great model — this dataset is built to avoid that trap.

4. This is a genuine held-out set: none of these examples were used to
   design, tune, or threshold investigator.py's scoring weights.
"""

import random
from datetime import datetime, timedelta
from typing import Any

SCENARIO_WEIGHTS = {
    "strong": 0.45,   # clear-cut, should CONTEST
    "weak": 0.25,     # clear-cut, should ACCEPT
    "ambiguous": 0.30,  # genuinely mixed, should REVIEW
}


def _pick_scenario(rng: random.Random) -> str:
    r = rng.random()
    if r < SCENARIO_WEIGHTS["strong"]:
        return "strong"
    if r < SCENARIO_WEIGHTS["strong"] + SCENARIO_WEIGHTS["weak"]:
        return "weak"
    return "ambiguous"


def _generate_evidence_for_scenario(scenario: str, rng: random.Random) -> dict:
    """
    Evidence fields are generated to be CONSISTENT with the scenario,
    not the other way around — the scenario (and its expected truth)
    is decided first, independent of any scoring formula.
    """
    if scenario == "strong":
        return {
            "payment_ok": rng.random() > 0.02,
            "order_ok": rng.random() > 0.03,
            "delivered": rng.random() > 0.05,
            "address_match": rng.random() > 0.08,
            "signature_available": rng.random() > 0.15,
        }
    if scenario == "weak":
        return {
            "payment_ok": rng.random() > 0.05,
            "order_ok": rng.random() > 0.1,
            "delivered": rng.random() > 0.85,
            "address_match": rng.random() > 0.9,
            "signature_available": rng.random() > 0.9,
        }
    # ambiguous: deliberately mixed — some strong signals, some missing,
    # picked to NOT cleanly resemble either the strong or weak profile
    return {
        "payment_ok": rng.random() > 0.03,
        "order_ok": rng.random() > 0.05,
        "delivered": rng.random() > 0.4,
        "address_match": rng.choice([True, False]),
        "signature_available": rng.choice([True, False, False]),
    }


def _make_dispute(i: int, rng: random.Random) -> tuple[dict[str, Any], str]:
    amount = rng.choice([3000, 6500, 9200, 14000, 18500, 25000, 32000, 45000])
    reason = "ITEM_NOT_RECEIVED"
    refund_issued = rng.random() < 0.08

    if refund_issued:
        scenario = "weak"  # refund already resolves it, regardless of delivery evidence
        evidence = _generate_evidence_for_scenario("weak", rng)
        base_truth = "ACCEPT"
    else:
        scenario = _pick_scenario(rng)
        evidence = _generate_evidence_for_scenario(scenario, rng)
        base_truth = {"strong": "CONTEST", "weak": "ACCEPT", "ambiguous": "REVIEW"}[
            scenario
        ]

    # Inject noise: ~12% of cases the true outcome contradicts the
    # scenario's expected label (signature fraud, spoofed address match,
    # a genuinely lost package despite a false "delivered" scan, etc).
    if rng.random() < 0.12:
        ground_truth = rng.choice(
            [x for x in ["CONTEST", "REVIEW", "ACCEPT"] if x != base_truth]
        )
    else:
        ground_truth = base_truth

    payment_ok = evidence["payment_ok"]
    order_ok = evidence["order_ok"]
    delivered = evidence["delivered"]
    address_match = evidence["address_match"] and delivered
    signature_available = evidence["signature_available"] and delivered

    filed_at = datetime(2026, 1, 1) + timedelta(days=rng.randint(0, 240))

    dispute = {
        "dispute_id": f"eval_{i:04d}",
        "reason": reason,
        "amount": amount,
        "currency": "INR",
        "customer_id": f"eval_cust_{rng.randint(1, 300)}",
        "merchant_id": f"eval_merch_{rng.randint(1, 60)}",
        "filed_at": filed_at.isoformat(),
        "payment": {
            "payment_id": f"eval_pay_{i}",
            "status": "captured" if payment_ok else "failed",
            "amount": amount,
            "date": filed_at.isoformat(),
        },
        "order": {
            "order_id": f"EVAL_ORD_{i}",
            "product": "Evaluation item",
            "amount": amount,
            "status": "fulfilled" if order_ok else "cancelled",
            "shipping_address": "Synthetic address",
        },
        "delivery": {
            "status": "delivered" if delivered else "not_delivered",
            "delivered_at": filed_at.isoformat() if delivered else None,
            "address_match": address_match,
            "signature_available": signature_available,
            "courier": rng.choice(["BlueDart", "SpeedEx", "Delhivery"]),
        },
        "refund": {"issued": refund_issued},
        "support": {
            "customer_contacted": True,
            "merchant_response": rng.random() > 0.2,
            "conversation": "Synthetic evaluation record.",
        },
    }

    return dispute, ground_truth


def generate_holdout_set(n: int = 200, seed: int = 42) -> list[tuple[dict, str]]:
    """
    Returns a reproducible (fixed seed) list of (dispute, ground_truth)
    pairs. Reproducible so re-running this doesn't silently shift the
    numbers between runs.
    """
    rng = random.Random(seed)
    return [_make_dispute(i, rng) for i in range(n)]