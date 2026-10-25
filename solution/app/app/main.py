"""orders-service: a tiny Flask API made production-ready."""

import logging
import threading
import time
import uuid

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.config import Config
from app.logging_setup import setup_logging

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
ORDERS_CREATED = Counter("orders_created_total", "Orders created")


class OrderStore:
    """In-memory store. In production this would be PostgreSQL (e.g. RDS)."""

    def __init__(self) -> None:
        self._orders: dict[str, dict] = {}
        self._lock = threading.Lock()

    def list(self) -> list[dict]:
        with self._lock:
            return list(self._orders.values())

    def get(self, order_id: str) -> dict | None:
        with self._lock:
            return self._orders.get(order_id)

    def create(self, item: str, amount_sek: float) -> dict:
        order = {"id": str(uuid.uuid4()), "item": item, "amount_sek": amount_sek}
        with self._lock:
            self._orders[order["id"]] = order
        return order


def create_app(config: Config | None = None) -> Flask:
    config = config or Config()
    setup_logging(config.log_level)
    log = logging.getLogger("orders")

    app = Flask(__name__)
    store = OrderStore()
    app.config["READY"] = True  # flipped to False during shutdown / dependency failure

    @app.before_request
    def _start_timer():
        g.start = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    @app.after_request
    def _record(response: Response):
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        duration = time.perf_counter() - g.start
        if endpoint != "/metrics":
            REQUESTS.labels(request.method, endpoint, response.status_code).inc()
            LATENCY.labels(request.method, endpoint).observe(duration)
        response.headers["X-Request-ID"] = g.request_id
        if endpoint not in ("/healthz", "/readyz", "/metrics"):
            log.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "request_id": g.request_id,
                },
            )
        return response

    # ---- operational endpoints -------------------------------------------
    @app.get("/healthz")
    def healthz():
        # Liveness: is the process alive? Never check dependencies here.
        return jsonify(status="ok")

    @app.get("/readyz")
    def readyz():
        # Readiness: can we serve traffic? Check DB/cache connectivity here.
        if not app.config["READY"]:
            return jsonify(status="not ready"), 503
        return jsonify(status="ready", version=config.version)

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    # ---- business endpoints ----------------------------------------------
    @app.get("/api/v1/orders")
    def list_orders():
        return jsonify(store.list())

    @app.get("/api/v1/orders/<order_id>")
    def get_order(order_id: str):
        order = store.get(order_id)
        if order is None:
            return jsonify(error="not found"), 404
        return jsonify(order)

    @app.post("/api/v1/orders")
    def create_order():
        body = request.get_json(silent=True) or {}
        item = body.get("item")
        amount = body.get("amount_sek")
        if not isinstance(item, str) or not item.strip():
            return jsonify(error="'item' must be a non-empty string"), 400
        if isinstance(amount, bool) or not isinstance(amount, int | float):
            return jsonify(error="'amount_sek' must be a number"), 400
        if not 0 < amount <= config.max_amount_sek:
            return jsonify(error=f"'amount_sek' must be in (0, {config.max_amount_sek}]"), 400
        order = store.create(item.strip(), float(amount))
        ORDERS_CREATED.inc()
        return jsonify(order), 201

    return app


if __name__ == "__main__":  # local dev only; containers use gunicorn
    cfg = Config()
    create_app(cfg).run(host="0.0.0.0", port=cfg.port)
