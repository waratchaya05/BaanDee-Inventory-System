import src.evidence as evidence_module
from src.api_client import ApiResult
from src.evidence import check_grounding


def fake_order(order_id, **kwargs):
    if order_id == "ORD-260728-1842":
        return ApiResult(True, 200, {
            "order_id": order_id,
            "status": "carrier_delay",
            "last_event": "Departed Bangkok hub late",
            "estimated_delivery": None,
            "as_of": "2026-07-31T11:45:00+07:00",
        }, None, "fixture://order")
    return ApiResult(False, 404, None, "Order not found", "fixture://order")


def fake_inventory(product_id, **kwargs):
    return ApiResult(True, 200, {"product_id": product_id, "available_qty": 3, "as_of": "2026-07-31T11:40:00+07:00"}, None, "fixture://inventory")


def test_main_case_uses_current_api_and_withholds_date(monkeypatch):
    monkeypatch.setattr(evidence_module, "fetch_order", fake_order)
    monkeypatch.setattr(evidence_module, "fetch_inventory", fake_inventory)
    evidence = evidence_module.build_case_evidence("TKT-260731-042")
    assert evidence["order_id"] == "ORD-260728-1842"
    assert evidence["order_export"]["export_status"] == "packed"
    assert evidence["current_order"]["status"] == "carrier_delay"
    assert "not yet available" in evidence["rule_response"]
    assert check_grounding(evidence["rule_response"], evidence)["passed"]


def test_unknown_reference_does_not_invent_status(monkeypatch):
    monkeypatch.setattr(evidence_module, "fetch_order", fake_order)
    evidence = evidence_module.build_case_evidence("TKT-260731-099")
    assert not evidence["order_verified"]
    assert "could not verify" in evidence["rule_response"]
    assert check_grounding(evidence["rule_response"], evidence)["passed"]


def test_grounding_flags_unsupported_promise(monkeypatch):
    monkeypatch.setattr(evidence_module, "fetch_order", fake_order)
    monkeypatch.setattr(evidence_module, "fetch_inventory", fake_inventory)
    evidence = evidence_module.build_case_evidence("TKT-260731-042")
    result = check_grounding("Order ORD-260728-1842 is carrier delay and will arrive tomorrow.", evidence)
    assert not result["passed"]
    assert "Unsupported delivery promise" in result["failures"]
