from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw = ROOT / "data" / "raw"
    cp = ROOT / "data" / "checkpoints"
    gt = ROOT / "data" / "ground_truth"

    tickets = pd.read_csv(raw / "support_tickets.csv", dtype=str)
    orders = pd.read_csv(raw / "orders.csv", dtype=str)
    corrected = pd.read_csv(cp / "02_corrected_join.csv", dtype=str)
    row = corrected.loc[corrected.ticket_id == "TKT-260731-042"].iloc[0]
    assert row.order_id_clean == "ORD-260728-1842"
    assert row.export_status == "packed"
    assert set(orders.loc[orders.order_id.str.endswith("1842"), "order_id"]) >= {"ORD-260728-1842", "ORD-250101-1842"}
    assert tickets.loc[tickets.ticket_id == "TKT-260731-099", "order_reference"].iloc[0] == "ORD-UNKNOWN-77"
    assert len(pd.read_csv(cp / "quarantine_dates.csv")) >= 1
    assert len(pd.read_csv(cp / "quarantine_customer_candidates.csv")) == 2
    assert len(pd.read_csv(cp / "correction_log.csv")) >= 4

    expected = json.loads((gt / "expected_cases.json").read_text())
    api_orders = json.loads((ROOT / "api" / "fixtures" / "orders.json").read_text())
    assert api_orders["ORD-260728-1842"]["status"] == expected["TKT-260731-042"]["expected_current_status"]
    assert api_orders["ORD-260729-2095"]["status"] == expected["TKT-260731-117"]["expected_current_status"]

    for path in list((ROOT / "src").glob("*.py")) + list((ROOT / "api").glob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    notebook = json.loads((ROOT / "notebooks" / "class1_demo.ipynb").read_text(encoding="utf-8"))
    ids = [cell["id"] for cell in notebook["cells"]]
    assert len(ids) == len(set(ids))
    assert all(f"C1-{i:02d}" in ids or any(x.startswith(f"C1-{i:02d}") for x in ids) for i in range(1, 15))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]), filename=f"notebook:{cell['id']}")
    print("PASS: deterministic data, fixed scenarios, checkpoints, API fixtures, source syntax, and notebook code")


if __name__ == "__main__":
    main()
