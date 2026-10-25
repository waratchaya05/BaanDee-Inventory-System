from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .api_client import fetch_inventory, fetch_order
from .policy import draft_rule_response, evaluate_delay_policy

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "data" / "checkpoints"


def _row_dict(row: pd.Series) -> dict:
    return {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}


def build_case_evidence(ticket_id: str, base_url: str | None = None) -> dict:
    tickets = pd.read_csv(CP / "tickets_clean.csv", dtype=str)
    orders = pd.read_csv(CP / "orders_clean.csv", dtype=str)
    lines = pd.read_csv(CP / "order_lines_clean.csv", dtype=str)
    inventory = pd.read_csv(CP / "inventory_snapshot_clean.csv", dtype=str)

    match = tickets.loc[tickets["ticket_id"] == ticket_id]
    if match.empty:
        return {"ticket_id": ticket_id, "ticket_found": False, "order_verified": False, "error": "Ticket not found"}
    ticket = _row_dict(match.iloc[0])
    order_id = ticket.get("order_id_clean")
    if pd.isna(order_id):
        order_id = None
    evidence = {"ticket_id": ticket_id, "ticket_found": True, "ticket": ticket, "order_id": order_id}
    if not order_id:
        evidence.update({"order_verified": False, "uncertainty": "Order reference could not be verified"})
        evidence["policy"] = evaluate_delay_policy(evidence)
        evidence["rule_response"] = draft_rule_response(evidence)
        return evidence

    order_rows = orders.loc[orders["order_id_clean"] == order_id]
    api_order = fetch_order(order_id, base_url=base_url)
    if order_rows.empty or not api_order.ok:
        evidence.update({
            "order_verified": False,
            "uncertainty": api_order.error or "Order missing from export",
            "api_status": api_order.status_code,
        })
        evidence["policy"] = evaluate_delay_policy(evidence)
        evidence["rule_response"] = draft_rule_response(evidence)
        return evidence

    order = _row_dict(order_rows.iloc[0])
    line_rows = lines.loc[lines["order_id"] == order_id]
    product_ids = line_rows["product_id"].tolist()
    current_inventory = []
    snapshot_inventory = []
    for product_id in product_ids:
        snap = inventory.loc[inventory["product_id"] == product_id]
        if not snap.empty:
            snapshot_inventory.append(_row_dict(snap.iloc[0]))
        api_inv = fetch_inventory(product_id, base_url=base_url)
        if api_inv.ok:
            current_inventory.append(api_inv.data)

    evidence.update({
        "order_verified": True,
        "order_export": order,
        "current_order": api_order.data,
        "estimated_delivery": api_order.data.get("estimated_delivery"),
        "product_ids": product_ids,
        "inventory_snapshot": snapshot_inventory,
        "current_inventory": current_inventory,
        "source_decision": "Current API is authoritative for order status; exports remain visible for comparison.",
    })
    evidence["policy"] = evaluate_delay_policy(evidence)
    evidence["rule_response"] = draft_rule_response(evidence)
    return evidence


def check_grounding(text: str, evidence: dict) -> dict:
    failures = []
    if evidence.get("order_verified"):
        if evidence["order_id"] not in text:
            failures.append("Missing verified order ID")
        current = evidence["current_order"]
        if current["status"].replace("_", " ") not in text.lower():
            failures.append("Missing verified current status")
        if not current.get("estimated_delivery") and any(word in text.lower() for word in ["tomorrow", "will arrive", "guaranteed"]):
            failures.append("Unsupported delivery promise")
    else:
        if any(word in text.lower() for word in ["shipped", "packed", "delivered"]):
            failures.append("Status stated for unverified order")
    return {"passed": not failures, "failures": failures}


def evidence_json(evidence: dict) -> str:
    return json.dumps(evidence, indent=2, ensure_ascii=False)
