from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ApiResult:
    ok: bool
    status_code: int | None
    data: dict[str, Any] | None
    error: str | None
    url: str


def get_json(path: str, base_url: str | None = None, timeout: float = 2.0) -> ApiResult:
    base = (base_url or os.getenv("BAANDEE_API_URL", "http://127.0.0.1:8000")).rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return ApiResult(True, 200, response.json(), None, url)
        detail = response.json().get("detail", response.text)
        return ApiResult(False, response.status_code, None, str(detail), url)
    except requests.RequestException as exc:
        return ApiResult(False, None, None, f"Service unavailable: {exc.__class__.__name__}", url)


def fetch_order(order_id: str, **kwargs) -> ApiResult:
    return get_json(f"orders/{order_id}", **kwargs)


def fetch_inventory(product_id: str, **kwargs) -> ApiResult:
    return get_json(f"inventory/{product_id}", **kwargs)


def fetch_ticket(ticket_id: str, **kwargs) -> ApiResult:
    return get_json(f"tickets/{ticket_id}", **kwargs)
