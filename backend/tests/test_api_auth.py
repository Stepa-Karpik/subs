from fastapi.testclient import TestClient
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
