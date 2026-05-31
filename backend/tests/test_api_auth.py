from fastapi.testclient import TestClient
from app.core.config import get_settings
from app.main import app


def test_healthz():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["service"] == "subs"


def test_me_dev_auth():
    client = TestClient(app)
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "karpik"


def test_spoofed_user_header_rejected_without_internal_key(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_AUTH", "false")
    monkeypatch.setenv("SUBS_INTERNAL_API_KEY", "secret")
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/api/v1/me", headers={"x-user-id": "attacker", "x-username": "attacker"})
    assert response.status_code == 401
    get_settings.cache_clear()


def test_internal_user_header_allowed_with_internal_key(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_AUTH", "false")
    monkeypatch.setenv("SUBS_INTERNAL_API_KEY", "secret")
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/api/v1/me", headers={"x-user-id": "service-user", "x-username": "service", "x-internal-key": "secret"})
    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == "service-user"
    get_settings.cache_clear()
