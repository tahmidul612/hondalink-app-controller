import secrets
import time

import pytest
from fastapi.testclient import TestClient

from hondalink.config import settings
from hondalink.main import app
from hondalink.security import RateLimiter, audit_logger

settings.use_mock_driver = True


@pytest.fixture
def client():
    settings.require_authentication = False
    settings.enable_rate_limiting = False
    settings.allowed_ips = ""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def secure_client():
    settings.require_authentication = True
    api_key = secrets.token_urlsafe(32)
    settings.api_keys = api_key
    settings.enable_rate_limiting = False
    settings.allowed_ips = ""
    with TestClient(app) as c:
        yield c, api_key


@pytest.fixture
def rate_limited_client():
    settings.require_authentication = False
    settings.enable_rate_limiting = True
    settings.api_rate_limit = 5
    settings.command_rate_limit = 3
    settings.allowed_ips = ""
    with TestClient(app) as c:
        yield c


def test_health_endpoint_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_key_required(secure_client):
    client, api_key = secure_client

    response = client.get("/status")
    assert response.status_code == 401
    assert "Missing API key" in response.json()["detail"]


def test_api_key_valid(secure_client):
    client, api_key = secure_client

    response = client.get("/status", headers={"X-API-Key": api_key})
    assert response.status_code == 200


def test_api_key_invalid(secure_client):
    client, api_key = secure_client

    response = client.get("/status", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


def test_ip_whitelist_allowed():
    settings.require_authentication = False
    settings.allowed_ips = "testclient"
    with TestClient(app) as client:
        response = client.get("/status")
        assert response.status_code == 200


def test_ip_whitelist_blocked():
    settings.require_authentication = False
    settings.allowed_ips = "192.168.1.100"
    with TestClient(app) as client:
        response = client.get("/status")
        assert response.status_code == 403
        assert "IP address not authorized" in response.json()["detail"]


def test_rate_limit_api_endpoint(rate_limited_client):
    client = rate_limited_client

    for i in range(5):
        response = client.get("/status")
        assert response.status_code == 200

    response = client.get("/status")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_rate_limit_command_endpoint(rate_limited_client):
    client = rate_limited_client

    for i in range(3):
        response = client.post("/action/lock")
        assert response.status_code == 200

    response = client.post("/action/lock")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_rate_limiter_class():
    limiter = RateLimiter(requests_per_minute=5)

    for i in range(5):
        assert limiter.is_allowed("test-ip") is True

    assert limiter.is_allowed("test-ip") is False

    remaining = limiter.get_remaining("test-ip")
    assert remaining == 0


def test_rate_limiter_window():
    limiter = RateLimiter(requests_per_minute=2)

    assert limiter.is_allowed("test-ip") is True
    assert limiter.is_allowed("test-ip") is True
    assert limiter.is_allowed("test-ip") is False

    time.sleep(61)

    assert limiter.is_allowed("test-ip") is True


def test_audit_logging(tmp_path, secure_client):
    client, api_key = secure_client

    log_file = tmp_path / "test_audit.jsonl"
    audit_logger.log_file = log_file

    response = client.post("/action/lock", headers={"X-API-Key": api_key})

    assert log_file.exists()
    logs = log_file.read_text().strip().split("\n")
    assert len(logs) >= 1

    import json

    events = [json.loads(log) for log in logs]
    command_events = [e for e in events if e["event_type"] == "vehicle_command"]
    assert len(command_events) >= 1
    assert command_events[0]["details"]["command"] == "lock"


def test_multiple_api_keys():
    settings.require_authentication = True
    key1 = secrets.token_urlsafe(32)
    key2 = secrets.token_urlsafe(32)
    settings.api_keys = f"{key1},{key2}"
    with TestClient(app) as client:
        response1 = client.get("/status", headers={"X-API-Key": key1})
        assert response1.status_code == 200

        response2 = client.get("/status", headers={"X-API-Key": key2})
        assert response2.status_code == 200

        response3 = client.get("/status", headers={"X-API-Key": "wrong-key"})
        assert response3.status_code == 401


def test_debug_hierarchy_requires_auth(secure_client):
    client, api_key = secure_client

    response = client.get("/debug/hierarchy")
    assert response.status_code == 401

    response = client.get("/debug/hierarchy", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
