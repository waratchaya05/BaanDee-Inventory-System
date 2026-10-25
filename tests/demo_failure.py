"""Run directly during class. It is excluded from normal pytest discovery."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_prep import RAW, unsafe_digits_only_match

orders = pd.read_csv(RAW / "orders.csv", dtype=str)
matches = unsafe_digits_only_match("OD1842", orders)
print("Unsafe digit-only matches:", matches)
assert len(matches) == 1, "FAILED: suffix 1842 identifies more than one order"
