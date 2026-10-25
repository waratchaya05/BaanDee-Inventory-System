from pathlib import Path

import pandas as pd

from src.data_prep import (
    GROUND_TRUTH,
    RAW,
    normalize_customer_id,
    normalize_order_reference,
    parse_mixed_date,
    unsafe_digits_only_match,
)


def test_customer_id_normalization_is_conservative():
    assert normalize_customer_id(" cus00842 ") == "CUS-00842"
    assert normalize_customer_id("842") is None
    assert normalize_customer_id("CUS-00842-DUP") is None


def test_order_reference_requires_approved_crosswalk():
    crosswalk = pd.read_csv(GROUND_TRUTH / "order_reference_crosswalk.csv", dtype=str)
    assert normalize_order_reference("OD1842", crosswalk) == "ORD-260728-1842"
    assert normalize_order_reference("ORD-260729-2095", crosswalk) == "ORD-260729-2095"
    assert normalize_order_reference("1842", crosswalk) is None


def test_digits_only_matching_is_ambiguous():
    orders = pd.read_csv(RAW / "orders.csv", dtype=str)
    matches = unsafe_digits_only_match("OD1842", orders)
    assert set(matches) >= {"ORD-260728-1842", "ORD-250101-1842"}


def test_ambiguous_date_is_quarantined():
    parsed, quality = parse_mixed_date("07/08/2026")
    assert parsed is None
    assert quality == "ambiguous"
