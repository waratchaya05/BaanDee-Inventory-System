from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_policy() -> dict:
    return json.loads((ROOT / "data" / "raw" / "delay_policy.json").read_text(encoding="utf-8"))


def evaluate_delay_policy(evidence: dict) -> dict:
    if not evidence.get("order_verified"):
        return {
            "decision": "human_follow_up",
            "allowed": ["Acknowledge the request", "Ask an agent to verify the order reference"],
            "prohibited": ["State an order status", "Promise a delivery date", "Offer compensation"],
        }
    allowed = ["State the verified current status", "Explain the latest verified event"]
    prohibited = ["Offer compensation", "Claim the message was sent"]
    if evidence.get("estimated_delivery"):
        allowed.append("State the API-supplied estimated delivery date as an estimate")
    else:
        prohibited.append("Promise or invent a delivery date")
    return {"decision": "draft_reply", "allowed": allowed, "prohibited": prohibited}


def draft_rule_response(evidence: dict) -> str:
    if not evidence.get("order_verified"):
        return (
            "Thank you for contacting BaanDee Living. We could not verify the order reference "
            f"for ticket {evidence['ticket_id']}. A support agent needs to confirm the order before "
            "we state its status or delivery date."
        )
    current = evidence["current_order"]
    status = current["status"].replace("_", " ")
    parts = [
        "Thank you for contacting BaanDee Living.",
        f"We verified order {evidence['order_id']}. Its current status is {status}.",
        f"The latest update is: {current['last_event']} (as of {current['as_of']}).",
    ]
    if current.get("estimated_delivery"):
        parts.append(f"The current estimated delivery date is {current['estimated_delivery']}; this remains an estimate.")
    else:
        parts.append("A new delivery date is not yet available, so a support agent will follow up when the carrier provides one.")
    return " ".join(parts)
