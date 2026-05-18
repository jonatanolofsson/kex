"""Smoke tests for the FastAPI entrypoint."""

from fastapi.testclient import TestClient

from kex.main import app

client = TestClient(app)


def test_healthz() -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_version_endpoint() -> None:
    r = client.get("/api/version")
    assert r.status_code == 200
    assert "version" in r.json()
