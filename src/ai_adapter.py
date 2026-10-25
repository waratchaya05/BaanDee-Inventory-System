from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_prompt(evidence: dict) -> str:
    compact = {
        "ticket_id": evidence.get("ticket_id"),
        "customer_message": evidence.get("ticket", {}).get("message"),
        "order_verified": evidence.get("order_verified"),
        "order_id": evidence.get("order_id"),
        "current_order": evidence.get("current_order"),
        "policy": evidence.get("policy"),
    }
    return (
        "Draft a concise customer-support reply using only the verified evidence below. "
        "Do not invent dates, status, compensation, or completed actions. State uncertainty clearly.\n\n"
        + json.dumps(compact, ensure_ascii=False, indent=2)
    )


def draft_ai_response(evidence: dict, mode: str | None = None) -> tuple[str, str]:
    selected = (mode or os.getenv("BAANDEE_AI_MODE", "fixture")).lower()
    if selected != "live":
        fixtures = json.loads((ROOT / "data" / "ground_truth" / "ai_response_fixtures.json").read_text(encoding="utf-8"))
        return fixtures.get(evidence["ticket_id"], evidence["rule_response"]), "synthetic_fixture"
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is missing. Use fixture mode or set the environment variable.")
    from google import genai

    client = genai.Client()
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    interaction = client.interactions.create(model=model, input=build_prompt(evidence), store=False)
    return interaction.output_text, f"live:{model}"
