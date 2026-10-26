import pytest
from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_login_page_loads(client):
    r = client.get("/")
    assert r.status_code == 200


def test_signup_needs_all_fields(client):
    r = client.post("/api/signup", json={"name": "Sara"})
    assert r.status_code == 400


def test_signup_and_verify(client):
    r = client.post("/api/signup", json={
        "name": "Sara", "email": "sara@example.com",
        "password": "secret123", "role": "student"})
    assert r.status_code == 200
    code = r.get_json()["otp"]
    r = client.post("/api/verify-otp",
                    json={"email": "sara@example.com", "code": code})
    assert r.status_code == 200


def test_metrics_page(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"flask_http_request_total" in r.data or b"flask_exporter_info" in r.data
