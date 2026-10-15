import pytest

from app import main


@pytest.fixture(autouse=True)
def reset_state():
    main.items.clear()
    main.next_id = 1
    yield


@pytest.fixture
def client():
    main.app.config["TESTING"] = True
    return main.app.test_client()


def test_index_returns_service_info(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_json()
    assert body["service"] == "ecs-demo-app"
    assert "version" in body
    assert "hostname" in body


def test_health_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_health_fails_when_broken(client, monkeypatch):
    monkeypatch.setenv("BREAK_HEALTH", "true")
    res = client.get("/health")
    assert res.status_code == 500
    assert res.get_json()["status"] == "unhealthy"


def test_create_and_get_item(client):
    res = client.post("/api/items", json={"name": "first"})
    assert res.status_code == 201
    item_id = res.get_json()["id"]

    res = client.get(f"/api/items/{item_id}")
    assert res.status_code == 200
    assert res.get_json()["name"] == "first"


def test_create_item_requires_name(client):
    res = client.post("/api/items", json={})
    assert res.status_code == 400


def test_list_items(client):
    client.post("/api/items", json={"name": "a"})
    client.post("/api/items", json={"name": "b"})
    res = client.get("/api/items")
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_delete_item(client):
    item_id = client.post("/api/items", json={"name": "temp"}).get_json()["id"]
    assert client.delete(f"/api/items/{item_id}").status_code == 204
    assert client.get(f"/api/items/{item_id}").status_code == 404


def test_missing_item_returns_404(client):
    assert client.get("/api/items/999").status_code == 404


def test_metrics_endpoint(client):
    client.get("/health")
    res = client.get("/metrics")
    assert res.status_code == 200
    assert b"http_requests_total" in res.data