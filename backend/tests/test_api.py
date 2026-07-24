import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200

# Test missing payloads
def test_chat_payload_validation():
    response = client.post("/api/chat", json={})
    assert response.status_code == 422