import pytest

from app.config import Config
from app.main import create_app


@pytest.fixture()
def client():
    app = create_app(Config(max_amount_sek=1000))
    app.testing = True
    return app.test_client()


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_readyz_ok_and_not_ready(client):
    assert client.get("/readyz").status_code == 200
    client.application.config["READY"] = False
    assert client.get("/readyz").status_code == 503


def test_metrics_exposed(client):
    client.get("/api/v1/orders")
    body = client.get("/metrics").get_data(as_text=True)
    assert "http_requests_total" in body
    assert "http_request_duration_seconds_bucket" in body


def test_create_get_list_order(client):
    r = client.post("/api/v1/orders", json={"item": "kanelbulle", "amount_sek": 35})
    assert r.status_code == 201
    order = r.get_json()
    assert order["item"] == "kanelbulle"
    assert client.get(f"/api/v1/orders/{order['id']}").get_json() == order
    assert order in client.get("/api/v1/orders").get_json()


def test_request_id_propagated(client):
    r = client.get("/healthz", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"item": "", "amount_sek": 10},
        {"item": "fika", "amount_sek": "10"},
        {"item": "fika", "amount_sek": True},
        {"item": "fika", "amount_sek": 0},
        {"item": "fika", "amount_sek": 1001},
    ],
)
def test_create_order_validation(client, payload):
    assert client.post("/api/v1/orders", json=payload).status_code == 400


def test_unknown_order_404(client):
    assert client.get("/api/v1/orders/does-not-exist").status_code == 404
