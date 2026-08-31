import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_investigator import generate_ai_report
from investigator import build_evidence_analysis
from network_risk import build_network_risk
from courier_risk import build_courier_risk, build_courier_breakdown
from triage import build_triage_queue, get_urgency
from merchant_spike import build_merchant_spike, build_merchant_spike_summary
from risk_graph import build_risk_graph
from evaluate import run_evaluation
import simulation


app = FastAPI(title="Dispute Autopsy Agent")

# Frontend origin(s) allowed to call this API. Override with a comma
# separated FRONTEND_ORIGINS env var when deploying instead of editing this.
origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_disputes():
    with open("data/disputes.json", "r") as file:
        return json.load(file)


def get_dispute_by_id(dispute_id: str):
    disputes = load_disputes()
    return next(
        (d for d in disputes if d["dispute_id"] == dispute_id),
        None,
    )


def build_flagged_customers(disputes: list) -> list:
    """
    Platform-wide view: which customers show up disputing more than one
    DISTINCT merchant. Computed once across the whole dataset rather than
    per-dispute, since this is a dashboard-level summary, not something
    tied to one dispute.
    """
    by_customer: dict[str, list] = {}
    for d in disputes:
        customer_id = d.get("customer_id")
        if not customer_id:
            continue
        by_customer.setdefault(customer_id, []).append(d)

    flagged = []
    for customer_id, customer_disputes in by_customer.items():
        distinct_merchants = {
            d.get("merchant_id") for d in customer_disputes if d.get("merchant_id")
        }
        if len(distinct_merchants) >= 2:
            flagged.append({
                "customer_id": customer_id,
                "dispute_ids": [d["dispute_id"] for d in customer_disputes],
                "distinct_merchants": len(distinct_merchants),
            })

    return flagged


@app.get("/")
def home():
    return {
        "message": "Dispute Autopsy Agent is running"
    }


@app.get("/disputes")
def list_disputes():
    """Summary list for the inbox view — not the full evidence payload."""
    disputes = load_disputes()
    return [
        {
            "dispute_id": d["dispute_id"],
            "amount": d["amount"],
            "currency": d["currency"],
            "reason": d["reason"],
        }
        for d in disputes
    ]


@app.get("/dashboard")
def dashboard():
    """
    Aggregate view across every dispute on file. Deliberately skips the
    AI narrative step (generate_ai_report) — that's slow and per-dispute
    detail isn't needed here, just the deterministic scoring + risk
    pattern check, run once per dispute.
    """
    disputes = load_disputes()

    total_amount = 0
    by_recommendation = {"CONTEST": 0, "REVIEW": 0, "ACCEPT": 0}
    flagged_risk_count = 0
    rows = []

    for dispute in disputes:
        analysis = build_evidence_analysis(dispute)
        risk = build_network_risk(dispute, disputes)

        total_amount += dispute["amount"]
        by_recommendation[analysis["recommendation"]] = (
            by_recommendation.get(analysis["recommendation"], 0) + 1
        )

        if risk["risk_level"] != "low":
            flagged_risk_count += 1

        rows.append({
            "dispute_id": dispute["dispute_id"],
            "amount": dispute["amount"],
            "currency": dispute["currency"],
            "evidence_score": analysis["evidence_score"],
            "recommendation": analysis["recommendation"],
            "risk_level": risk["risk_level"],
        })

    courier_breakdown = build_courier_breakdown(disputes)
    flagged_customers = build_flagged_customers(disputes)
    merchant_spikes = build_merchant_spike_summary(disputes)

    return {
        "total_disputes": len(disputes),
        "total_amount": total_amount,
        "currency": disputes[0]["currency"] if disputes else "INR",
        "by_recommendation": by_recommendation,
        "flagged_risk_count": flagged_risk_count,
        "disputes": rows,
        "courier_breakdown": courier_breakdown,
        "platform_risk_signals": {
            "flagged_customers": flagged_customers,
            "flagged_couriers": [
                row for row in courier_breakdown if row["flagged"]
            ],
            "merchant_spikes": merchant_spikes,
        },
    }


@app.get("/triage")
def triage():
    """
    A prioritized action queue, not just a list. Sorted by a simple,
    transparent heuristic — amount, deadline urgency, and evidence gap —
    documented in triage.py. Not a calibrated model; presented as a demo
    heuristic in the UI, not a claim of predictive accuracy.
    """
    disputes = load_disputes()
    analyses = {
        d["dispute_id"]: build_evidence_analysis(d) for d in disputes
    }
    return {"queue": build_triage_queue(disputes, analyses)}


@app.get("/evaluation")
def evaluation():
    """
    Runs the evidence-scoring engine against a held-out synthetic test
    set (see eval_data.py) and returns precision/recall/F1 per class,
    a confusion matrix, and false-positive/false-negative cost in INR.

    This set was never used to design the scoring rules in
    investigator.py — see eval_data.py's docstring for exactly how
    ground truth is generated and why it isn't artificially perfect.
    """
    return run_evaluation(n=200, seed=42)


class SimulateRequest(BaseModel):
    customer_id: str
    merchant_id: str
    reason: str = "ITEM_NOT_RECEIVED"
    amount: int


@app.post("/simulate")
def simulate_dispute(body: SimulateRequest):
    """
    Demo sandbox: create a synthetic dispute and see how it changes the
    network risk picture in real time, combined with real seed data.
    Never writes to disputes.json — resets whenever the server restarts.
    """
    real_disputes = load_disputes()
    return simulation.add_simulated_dispute(
        customer_id=body.customer_id,
        merchant_id=body.merchant_id,
        reason=body.reason,
        amount=body.amount,
        real_disputes=real_disputes,
    )


@app.get("/simulate")
def get_simulation():
    real_disputes = load_disputes()
    return simulation.get_simulation_state(real_disputes)


@app.post("/simulate/reset")
def reset_simulation():
    simulation.reset_simulation()
    return {"message": "Simulation reset."}


@app.get("/dispute/{dispute_id}")
def get_dispute(dispute_id: str):
    dispute = get_dispute_by_id(dispute_id)

    if dispute is None:
        return {"error": "Dispute not found"}

    return dispute


@app.get("/investigate/{dispute_id}")
def investigate_dispute(dispute_id: str):
    dispute = get_dispute_by_id(dispute_id)

    if dispute is None:
        return {"error": "Dispute not found"}

    return build_evidence_analysis(dispute)


@app.get("/autopsy/{dispute_id}")
def autopsy(dispute_id: str):
    dispute = get_dispute_by_id(dispute_id)

    if dispute is None:
        return {"error": "Dispute not found"}

    analysis = build_evidence_analysis(dispute)
    all_disputes = load_disputes()
    network_risk = build_network_risk(dispute, all_disputes)
    courier_risk = build_courier_risk(dispute, all_disputes)
    merchant_spike = build_merchant_spike(dispute, all_disputes)
    risk_graph = build_risk_graph(dispute, all_disputes)
    urgency = (
        get_urgency(dispute["response_deadline"])
        if dispute.get("response_deadline")
        else None
    )
    ai_report = generate_ai_report(dispute, analysis)

    return {
        "dispute_id": dispute["dispute_id"],
        "amount": dispute["amount"],
        "currency": dispute["currency"],
        "reason": dispute["reason"],
        "evidence_score": analysis["evidence_score"],
        "recommendation": analysis["recommendation"],
        "override_reason": analysis.get("override_reason"),
        "timeline": analysis["timeline"],
        "evidence": analysis["evidence"],
        "network_risk": network_risk,
        "courier_risk": courier_risk,
        "merchant_spike": merchant_spike,
        "risk_graph": risk_graph,
        "urgency": urgency,
        "ai_report": ai_report,
    }