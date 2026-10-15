import os
import socket
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "dev")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# In-memory store (stateless demo app, data resets on restart)
items = {}
next_id = 1

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)


def _endpoint_label():
    return request.url_rule.rule if request.url_rule else "unmatched"


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    endpoint = _endpoint_label()
    elapsed = time.perf_counter() - g.get("start_time", time.perf_counter())
    REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint).observe(elapsed)
    return response


@app.get("/")
def index():
    return jsonify(
        service="ecs-demo-app",
        version=APP_VERSION,
        environment=ENVIRONMENT,
        hostname=socket.gethostname(),
    )


@app.get("/health")
def health():
    # Set BREAK_HEALTH=true to simulate a bad release (used to test rollback)
    if os.getenv("BREAK_HEALTH", "false").lower() == "true":
        return jsonify(status="unhealthy", version=APP_VERSION), 500
    return jsonify(status="ok", version=APP_VERSION), 200


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.get("/api/items")
def list_items():
    return jsonify(list(items.values()))


@app.post("/api/items")
def create_item():
    global next_id
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify(error="'name' is required"), 400
    item = {"id": next_id, "name": name}
    items[next_id] = item
    next_id += 1
    return jsonify(item), 201


@app.get("/api/items/<int:item_id>")
def get_item(item_id):
    item = items.get(item_id)
    if item is None:
        return jsonify(error="item not found"), 404
    return jsonify(item)


@app.delete("/api/items/<int:item_id>")
def delete_item(item_id):
    if items.pop(item_id, None) is None:
        return jsonify(error="item not found"), 404
    return "", 204