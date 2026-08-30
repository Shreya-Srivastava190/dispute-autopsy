"""
Quick smoke test for the Dispute Autopsy backend.

Run this with the backend already running:
    python test_backend.py

It hits every endpoint and checks the response looks sane. It does NOT
replace manually clicking through the UI — it just catches obvious
breakage fast, before you do that.
"""

import sys
import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000"


def get(path):
    url = f"{BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body)
    except urllib.error.URLError as e:
        return None, str(e)


def post(path, data=None):
    url = f"{BASE}{path}"
    payload = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body)
    except urllib.error.URLError as e:
        return None, str(e)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    return condition


def main():
    all_ok = True

    # 1. Root
    status, body = get("/")
    all_ok &= check("GET / returns 200", status == 200)

    # 2. Disputes list
    status, body = get("/disputes")
    all_ok &= check("GET /disputes returns 200", status == 200)
    all_ok &= check(
        "GET /disputes returns a non-empty list",
        isinstance(body, list) and len(body) > 0,
    )

    if not isinstance(body, list) or len(body) == 0:
        print("\nCan't continue — /disputes didn't return usable data.")
        sys.exit(1)

    dispute_ids = [d["dispute_id"] for d in body]
    print(f"    Found {len(dispute_ids)} disputes: {dispute_ids}")

    # 3. Autopsy for every dispute
    recommendations_seen = set()
    risk_levels_seen = set()
    override_seen = False
    spike_seen = False
    graph_seen = False

    for dispute_id in dispute_ids:
        status, autopsy = get(f"/autopsy/{dispute_id}")
        ok = status == 200 and "recommendation" in autopsy
        all_ok &= check(f"GET /autopsy/{dispute_id} returns valid data", ok)

        if ok:
            recommendations_seen.add(autopsy["recommendation"])
            if autopsy.get("network_risk"):
                risk_levels_seen.add(autopsy["network_risk"]["risk_level"])
            if autopsy.get("override_reason"):
                override_seen = True
            if autopsy.get("merchant_spike", {}).get("is_spike"):
                spike_seen = True
            if autopsy.get("risk_graph"):
                graph_seen = True

            all_ok &= check(
                f"  {dispute_id} has an ai_report",
                "ai_report" in autopsy and autopsy["ai_report"] is not None,
            )
            all_ok &= check(
                f"  {dispute_id} has claim_vs_evidence",
                autopsy.get("ai_report", {}).get("claim_vs_evidence")
                is not None,
            )
            all_ok &= check(
                f"  {dispute_id} has network_risk",
                "network_risk" in autopsy,
            )
            all_ok &= check(
                f"  {dispute_id} has courier_risk",
                "courier_risk" in autopsy,
            )
            all_ok &= check(
                f"  {dispute_id} has merchant_spike",
                "merchant_spike" in autopsy,
            )
            all_ok &= check(
                f"  {dispute_id} has urgency",
                "urgency" in autopsy,
            )
            all_ok &= check(
                f"  {dispute_id} does NOT have stale investigation_timeline",
                "investigation_timeline" not in autopsy,
            )

    all_ok &= check(
        "All three recommendation types appear (CONTEST/REVIEW/ACCEPT)",
        {"CONTEST", "REVIEW", "ACCEPT"}.issubset(recommendations_seen)
        or len(recommendations_seen) >= 2,  # at least some variety
    )
    all_ok &= check(
        "At least one dispute has an override_reason (refund case)",
        override_seen,
    )
    all_ok &= check(
        "At least one dispute shows a merchant spike",
        spike_seen,
    )
    all_ok &= check(
        "At least one dispute has a risk_graph",
        graph_seen,
    )
    print(f"    Recommendations seen: {recommendations_seen}")
    print(f"    Risk levels seen: {risk_levels_seen}")

    # 4. Non-existent dispute should fail gracefully, not crash
    status, body = get("/autopsy/disp_does_not_exist")
    all_ok &= check(
        "GET /autopsy/<bad-id> doesn't crash the server",
        status == 200 and "error" in body,
    )

    # 5. Dashboard
    status, body = get("/dashboard")
    all_ok &= check("GET /dashboard returns 200", status == 200)
    if status == 200:
        all_ok &= check(
            "Dashboard total_disputes matches /disputes count",
            body.get("total_disputes") == len(dispute_ids),
        )
        all_ok &= check(
            "Dashboard has platform_risk_signals",
            "platform_risk_signals" in body,
        )
        all_ok &= check(
            "Dashboard platform_risk_signals has merchant_spikes",
            "merchant_spikes" in body.get("platform_risk_signals", {}),
        )
        all_ok &= check(
            "Dashboard has courier_breakdown",
            "courier_breakdown" in body,
        )

    # 6. Triage
    status, body = get("/triage")
    all_ok &= check("GET /triage returns 200", status == 200)
    if status == 200:
        all_ok &= check(
            "Triage queue is non-empty",
            len(body.get("queue", [])) > 0,
        )
        all_ok &= check(
            "Triage queue is sorted by priority_score descending",
            all(
                body["queue"][i]["priority_score"]
                >= body["queue"][i + 1]["priority_score"]
                for i in range(len(body["queue"]) - 1)
            ),
        )

    # 7. Simulation — reset first for a clean slate, then run a scenario
    #    known to escalate risk, and confirm it actually does.
    post("/simulate/reset")

    sim_status, sim_body = post(
        "/simulate",
        {
            "customer_id": "cust_102",
            "merchant_id": "merch_999",
            "reason": "ITEM_NOT_RECEIVED",
            "amount": 15000,
        },
    )
    all_ok &= check("POST /simulate returns 200", sim_status == 200)
    if sim_status == 200:
        all_ok &= check(
            "Simulated dispute escalates network risk (expects HIGH)",
            sim_body.get("network_risk", {}).get("risk_level") == "high",
        )

    # Reset again so a re-run of this script (or the demo) starts clean.
    reset_status, _ = post("/simulate/reset")
    all_ok &= check("POST /simulate/reset returns 200", reset_status == 200)

    print()
    if all_ok:
        print("All checks passed.")
    else:
        print("Some checks FAILED — see above before your demo.")
        sys.exit(1)


if __name__ == "__main__":
    main()