from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def md(cell_id: str, source: str) -> dict:
    return {"cell_type":"markdown","id":cell_id,"metadata":{},"source":source.splitlines(True)}


def code(cell_id: str, source: str) -> dict:
    return {"cell_type":"code","execution_count":None,"id":cell_id,"metadata":{},"outputs":[],"source":source.splitlines(True)}


cells = [
    md("C1-01", """# BaanDee Living: Messy Company to Working MVP

Instructor-led walkthrough using synthetic data. Follow the numbered cells with the Class 1 slides. The application is read-only."""),
    code("C1-02", """# Tool boundary: Python loads the project; helper code remains in reusable modules.
from pathlib import Path
import json, sys, subprocess
import pandas as pd
import requests

ROOT = Path.cwd()
if ROOT.name == "notebooks": ROOT = ROOT.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
RAW = ROOT / "data" / "raw"
CP = ROOT / "data" / "checkpoints"
print("Project root:", ROOT)
print("Synthetic fixture mode is the default; no secret is displayed.")"""),
    md("C1-03-note", "## Inspect before cleaning\nWhich defects can change the customer response?"),
    code("C1-03", """files = ["customers.csv", "orders.csv", "inventory_snapshot.csv", "support_tickets.csv"]
profile = []
for name in files:
    df = pd.read_csv(RAW / name, dtype=str)
    profile.append({"file": name, "rows": len(df), "columns": len(df.columns), "missing_cells": int(df.isna().sum().sum())})
display(pd.DataFrame(profile))
tickets_raw = pd.read_csv(RAW / "support_tickets.csv", dtype=str)
display(tickets_raw.loc[tickets_raw.ticket_id.isin(["TKT-260731-042", "TKT-260731-099", "TKT-260731-117"])])"""),
    md("C1-04-note", "## A clean-looking join can still fail\nThe ticket uses an alias from another system."),
    code("C1-04", """orders_raw = pd.read_csv(RAW / "orders.csv", dtype=str)
naive = tickets_raw.merge(orders_raw, left_on="order_reference", right_on="order_id", how="left")
display(naive.loc[naive.ticket_id == "TKT-260731-042", ["ticket_id", "order_reference", "order_id", "export_status"]])"""),
    code("C1-05", """from src.data_prep import unsafe_digits_only_match
matches = unsafe_digits_only_match("OD1842", orders_raw)
print("Digit-only/suffix matches:", matches)
print("Conclusion: digits alone cannot prove which order belongs to the ticket.")"""),
    md("C1-06-note", "## Conservative correction\nUse known formats and an approved source crosswalk; retain ambiguity."),
    code("C1-06", """from src.data_prep import normalize_customer_id, normalize_order_reference, build_checkpoints, GROUND_TRUTH
crosswalk = pd.read_csv(GROUND_TRUTH / "order_reference_crosswalk.csv", dtype=str)
print('customer:', normalize_customer_id(' cus00842 '))
print('order:', normalize_order_reference('OD1842', crosswalk))
report = build_checkpoints()
print('join quality:', report)"""),
    code("C1-07", """corrected = pd.read_csv(CP / "02_corrected_join.csv", dtype=str)
display(corrected.loc[corrected.ticket_id == "TKT-260731-042", ["ticket_id", "order_reference", "order_id_clean", "order_id", "export_status"]])
print("Quarantined date records:")
display(pd.read_csv(CP / "quarantine_dates.csv", dtype=str)[["source", "order_date", "created_at"]].fillna(""))
print("Ambiguous customer candidates:")
display(pd.read_csv(CP / "quarantine_customer_candidates.csv", dtype=str)[["customer_id", "customer_name", "email", "phone"]])"""),
    md("C1-08-note", "## A real HTTP boundary\nFastAPI owns the current operational fixture. `requests` crosses the boundary and returns HTTP status plus JSON."),
    code("C1-08", """# Important client lines; the API must be running in another terminal.
url = "http://127.0.0.1:8000/orders/ORD-260728-1842"
response = requests.get(url, timeout=2)
print("URL:", url)
print("HTTP status:", response.status_code)
display(response.json())"""),
    code("C1-09", """from src.api_client import fetch_order
valid = fetch_order("ORD-260728-1842")
unknown = fetch_order("ORD-UNKNOWN-77")
unavailable = fetch_order("ORD-260728-1842", base_url="http://127.0.0.1:8999", timeout=0.2)
display(pd.DataFrame([
    {"case":"valid", "status":valid.status_code, "ok":valid.ok, "error":valid.error},
    {"case":"unknown", "status":unknown.status_code, "ok":unknown.ok, "error":unknown.error},
    {"case":"unavailable", "status":unavailable.status_code, "ok":unavailable.ok, "error":unavailable.error},
]))"""),
    md("C1-10-note", "## Evidence before language\nCurrent API status wins over an older export, but both remain visible."),
    code("C1-10", """from src.evidence import build_case_evidence
evidence = build_case_evidence("TKT-260731-042")
display({
    "ticket_id": evidence["ticket_id"],
    "order_id": evidence["order_id"],
    "export_status": evidence["order_export"]["export_status"],
    "exported_at": evidence["order_export"]["exported_at"],
    "current_status": evidence["current_order"]["status"],
    "current_as_of": evidence["current_order"]["as_of"],
    "estimated_delivery": evidence["estimated_delivery"],
    "source_decision": evidence["source_decision"],
})
print("Deterministic baseline:\\n", evidence["rule_response"])"""),
    md("C1-11-note", "## What does AI add?\nThe model receives a bounded evidence object. Fixture mode is synthetic and does not prove live model quality."),
    code("C1-11", """from src.ai_adapter import build_prompt, draft_ai_response
from src.evidence import check_grounding
print(build_prompt(evidence))
ai_text, source = draft_ai_response(evidence, mode="fixture")
print("\\nSource:", source)
print(ai_text)
print("Grounding check:", check_grounding(ai_text, evidence))"""),
    md("C1-12-note", "## From button to business logic\nGradio supplies the interface; the event calls the same functions used above."),
    code("C1-12", """from src.app import load_case_for_ui
summary, policy, rule, ai, evaluation = load_case_for_ui("TKT-260731-099", "fixture")
display(summary)
print(rule)
display(evaluation)
print("UI binding in src/app.py: button.click(fn=load_case_for_ui, inputs=[ticket, mode], outputs=[...])")"""),
    md("C1-13-note", "## A failure becomes a safeguard\nThe contained demo fails; the normal suite protects the corrected behavior."),
    code("C1-13", """demo = subprocess.run([sys.executable, str(ROOT / "tests" / "demo_failure.py")], cwd=ROOT, capture_output=True, text=True)
print(demo.stdout)
print(demo.stderr.splitlines()[-1])
assert demo.returncode != 0, "The contained unsafe-match demonstration should fail"
suite = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
print(suite.stdout)
assert suite.returncode == 0, suite.stderr"""),
    md("C1-14", """## Working MVP, known limits

The application can assemble evidence and prepare a grounded draft. It still lacks real authentication, write-action approval, systematic AI evaluation, production monitoring, and operational validation. Those questions begin Class 2."""),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
        "language_info": {"name":"python","version":"3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
path = ROOT / "notebooks" / "class1_demo.ipynb"
path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
print("Built", path)
