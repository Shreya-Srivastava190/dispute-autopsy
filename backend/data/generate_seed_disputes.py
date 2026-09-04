"""
Grows data/disputes.json from 6 hand-written demo cases to a larger,
still-hand-curated set with deliberately embedded patterns, so the
Dashboard / Triage / network-risk / courier-risk views have enough
volume to look like a real demo instead of a 6-row toy.

Honesty note: this is still synthetic, still small by production
standards, and the patterns below are DELIBERATELY planted (not
randomly emergent) so the UI has something to show. This is different
from eval_data.py's held-out set, which exists for measurement, not
demo narrative — don't conflate the two. Re-run with:
    python data/generate_seed_disputes.py
"""

import json
from datetime import datetime, timedelta

NOW = datetime(2026, 9, 4, 12, 0, 0)  # anchor near the actual current date
CURRENCY = "INR"


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def make_dispute(
    dispute_id,
    customer_id,
    merchant_id,
    amount,
    product,
    *,
    reason="ITEM_NOT_RECEIVED",
    payment_captured=True,
    order_fulfilled=True,
    delivered=True,
    address_match=True,
    signature_available=True,
    refund_issued=False,
    merchant_response=True,
    courier="BlueDart",
    filed_days_ago=5,
    deadline_days_from_now=3,
    conversation=None,
):
    filed_at = NOW - timedelta(days=filed_days_ago)
    delivered_at = filed_at - timedelta(days=2) if delivered else None
    deadline = NOW + timedelta(days=deadline_days_from_now)

    if conversation is None:
        conversation = (
            "Customer claimed the item was not received. Merchant provided "
            "delivery confirmation."
            if delivered
            else "Customer claimed the item was not received. No delivery "
            "confirmation on file."
        )

    return {
        "dispute_id": dispute_id,
        "reason": reason,
        "amount": amount,
        "currency": CURRENCY,
        "customer_id": customer_id,
        "merchant_id": merchant_id,
        "payment": {
            "payment_id": f"pay_{dispute_id}",
            "status": "captured" if payment_captured else "failed",
            "amount": amount,
            "date": _iso(filed_at - timedelta(days=3)),
        },
        "order": {
            "order_id": f"ORD_{dispute_id.upper()}",
            "product": product,
            "amount": amount,
            "status": "fulfilled" if order_fulfilled else "cancelled",
            "shipping_address": "Synthetic seed address",
        },
        "delivery": {
            "status": "delivered" if delivered else "not_delivered",
            "delivered_at": _iso(delivered_at) if delivered_at else None,
            "address_match": address_match,
            "signature_available": signature_available,
            "courier": courier,
        },
        "refund": {"issued": refund_issued},
        "support": {
            "customer_contacted": True,
            "merchant_response": merchant_response,
            "conversation": conversation,
        },
        "filed_at": _iso(filed_at),
        "response_deadline": _iso(deadline),
    }


def build_dataset():
    disputes = []

    # --- Original 6 hand-written demo cases, kept as-is for continuity ---
    disputes.append(make_dispute(
        "disp_001", "cust_101", "merch_501", 25000, "iPhone 15",
        delivered=True, address_match=True, signature_available=True,
        filed_days_ago=20, deadline_days_from_now=-6,
    ))
    disputes.append(make_dispute(
        "disp_002", "cust_102", "merch_502", 8500, "Bluetooth Speaker",
        delivered=False, address_match=False, signature_available=False,
        courier="SpeedEx", filed_days_ago=18, deadline_days_from_now=-2,
    ))
    disputes.append(make_dispute(
        "disp_003", "cust_103", "merch_503", 14200, "Running Shoes",
        delivered=True, address_match=True, signature_available=True,
        filed_days_ago=16, deadline_days_from_now=1,
    ))
    disputes.append(make_dispute(
        "disp_004", "cust_101", "merch_501", 32000, "MacBook Sleeve",
        delivered=True, refund_issued=True,
        filed_days_ago=14, deadline_days_from_now=2,
    ))
    disputes.append(make_dispute(
        "disp_005", "cust_104", "merch_502", 11000, "Desk Lamp",
        delivered=False, address_match=False, signature_available=False,
        courier="SpeedEx", filed_days_ago=12, deadline_days_from_now=4,
    ))
    disputes.append(make_dispute(
        "disp_006", "cust_103", "merch_504", 6200, "Yoga Mat",
        delivered=True, courier="Delhivery",
        filed_days_ago=10, deadline_days_from_now=6,
    ))

    # --- Pattern: cross-merchant serial disputer (cust_101 already hits
    # merch_501 twice above; add a THIRD, different merchant so
    # network_risk.py's cross-merchant flag fires clearly in the demo) ---
    disputes.append(make_dispute(
        "disp_007", "cust_101", "merch_505", 9800, "Wireless Mouse",
        delivered=False, address_match=False, signature_available=False,
        courier="SpeedEx", filed_days_ago=8, deadline_days_from_now=1,
        conversation="Customer says this never arrived either — third merchant this month.",
    ))

    # --- Pattern: merchant spike (merch_506 gets 4 disputes in under 2 weeks) ---
    spike_customers = ["cust_201", "cust_202", "cust_203", "cust_204"]
    for i, cust in enumerate(spike_customers):
        disputes.append(make_dispute(
            f"disp_10{i}", cust, "merch_506", 15000 + i * 1000, "Air Fryer",
            delivered=False, address_match=False, signature_available=False,
            courier="SpeedEx", filed_days_ago=9 - i, deadline_days_from_now=2 + i,
            conversation="Multiple customers reporting the same issue with this merchant recently.",
        ))

    # --- Pattern: risky courier concentration (SpeedEx already implicated
    # above via disp_002, disp_005, disp_007, disp_100-103 — add two more
    # non-delivery cases with DIFFERENT merchants so courier_risk.py's
    # cross-merchant signal is unambiguous) ---
    disputes.append(make_dispute(
        "disp_110", "cust_301", "merch_507", 7200, "Kettle",
        delivered=False, address_match=False, signature_available=False,
        courier="SpeedEx", filed_days_ago=6, deadline_days_from_now=5,
    ))
    disputes.append(make_dispute(
        "disp_111", "cust_302", "merch_508", 21000, "Office Chair",
        delivered=False, address_match=False, signature_available=False,
        courier="SpeedEx", filed_days_ago=4, deadline_days_from_now=7,
    ))

    # --- Assorted clean CONTEST-worthy cases (strong evidence) ---
    strong_cases = [
        ("disp_120", "cust_401", "merch_509", 18500, "Smartwatch", "BlueDart"),
        ("disp_121", "cust_402", "merch_510", 42000, "Gaming Monitor", "Delhivery"),
        ("disp_122", "cust_403", "merch_511", 6800, "Backpack", "BlueDart"),
        ("disp_123", "cust_404", "merch_512", 12500, "Blender", "Delhivery"),
        ("disp_124", "cust_405", "merch_513", 27500, "Tablet", "BlueDart"),
    ]
    for i, (did, cust, merch, amt, product, courier) in enumerate(strong_cases):
        disputes.append(make_dispute(
            did, cust, merch, amt, product, courier=courier,
            delivered=True, address_match=True, signature_available=True,
            filed_days_ago=15 - i, deadline_days_from_now=3 + i,
        ))

    # --- Assorted ambiguous REVIEW cases (mixed evidence) ---
    review_cases = [
        ("disp_130", "cust_501", "merch_514", 9200, "Sneakers", "BlueDart", True, False),
        ("disp_131", "cust_502", "merch_515", 15800, "Coffee Maker", "Delhivery", False, True),
        ("disp_132", "cust_503", "merch_516", 5400, "Water Bottle", "SpeedEx", True, True),
        ("disp_133", "cust_504", "merch_517", 22000, "Headphones", "BlueDart", False, False),
    ]
    for i, (did, cust, merch, amt, product, courier, addr, sig) in enumerate(review_cases):
        disputes.append(make_dispute(
            did, cust, merch, amt, product, courier=courier,
            delivered=True, address_match=addr, signature_available=sig,
            filed_days_ago=11 - i, deadline_days_from_now=1 + i,
        ))

    # --- Assorted clean ACCEPT cases (weak/no evidence, or refund already issued) ---
    accept_cases = [
        ("disp_140", "cust_601", "merch_518", 8900, "Charger", "Delhivery", False, False),
        ("disp_141", "cust_602", "merch_519", 13400, "Notebook Set", "BlueDart", False, True),
        ("disp_142", "cust_603", "merch_520", 30500, "Drone", "SpeedEx", None, None),
    ]
    for i, (did, cust, merch, amt, product, courier, _, _) in enumerate(accept_cases[:2]):
        disputes.append(make_dispute(
            did, cust, merch, amt, product, courier=courier,
            delivered=False, address_match=False, signature_available=False,
            filed_days_ago=7 - i, deadline_days_from_now=4 + i,
        ))
    disputes.append(make_dispute(
        "disp_142", "cust_603", "merch_520", 30500, "Drone", courier="SpeedEx",
        delivered=True, address_match=True, signature_available=True,
        refund_issued=True, filed_days_ago=5, deadline_days_from_now=8,
    ))

    return disputes


if __name__ == "__main__":
    dataset = build_dataset()
    out_path = "disputes.json"
    with open(out_path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"Wrote {len(dataset)} disputes to {out_path}")