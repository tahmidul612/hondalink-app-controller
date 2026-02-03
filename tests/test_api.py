import pytest
from fastapi.testclient import TestClient

from hondalink.config import settings
from hondalink.main import app

# Force mock driver for tests
settings.use_mock_driver = True

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_status(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_locked" in data
    # Mock driver default for "Locked" text is not set unless registered.
    # In lifespan we registered "Locked", so it should return True?
    # Actually lifespan runs when TestClient enters context.
    # The mock setup in lifespan: driver.register_element("text=Locked")
    # controller.get_status checks find_by_text("Locked").exists()
    # MockElement defaults to exists=True if registered.
    assert data["is_locked"] is True

def test_execute_command(client):
    # lifespan registers "Start"
    response = client.post("/action/start")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_invalid_command(client):
    response = client.post("/action/invalid_cmd")
    assert response.status_code == 422 # Validation error

def test_get_hierarchy(client):
    response = client.get("/debug/hierarchy")
    assert response.status_code == 200
    assert response.content == b"<mock>hierarchy</mock>"
    assert response.headers["content-type"] == "application/xml"
