from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_and_valid_order():
    assert client.get("/health").status_code == 200
    response = client.get("/orders/ORD-260728-1842")
    assert response.status_code == 200
    assert response.json()["status"] == "carrier_delay"


def test_unknown_order_returns_404():
    response = client.get("/orders/ORD-UNKNOWN-77")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"
