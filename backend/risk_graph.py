from typing import Any


def build_risk_graph(dispute: dict[str, Any], all_disputes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Returns graph data (nodes + edges) ONLY when this customer has
    disputed more than one distinct merchant — i.e. only when the graph
    actually shows something a plain sentence couldn't. If the customer
    has just one merchant relationship, this returns None on purpose:
    a graph with one node and one edge is not an insight, it's noise.
    """
    customer_id = dispute.get("customer_id")

    customer_disputes = [
        d for d in all_disputes if d.get("customer_id") == customer_id
    ]

    distinct_merchants = sorted({
        d.get("merchant_id") for d in customer_disputes if d.get("merchant_id")
    })

    if len(distinct_merchants) < 2:
        return None

    nodes = [
        {"id": customer_id, "type": "customer", "label": customer_id}
    ]
    for merchant_id in distinct_merchants:
        nodes.append(
            {"id": merchant_id, "type": "merchant", "label": merchant_id}
        )

    edges = []
    for d in customer_disputes:
        edges.append({
            "source": customer_id,
            "target": d["merchant_id"],
            "dispute_id": d["dispute_id"],
            "reason": d["reason"],
            "is_current": d["dispute_id"] == dispute["dispute_id"],
        })

    return {"nodes": nodes, "edges": edges}