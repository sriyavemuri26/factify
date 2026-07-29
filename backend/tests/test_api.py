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

def test_get_mcp_tools():
    response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tool_names = [tool["name"] for tool in data["tools"]]
    assert "semantic_search" in tool_names
    assert "fetch_news_articles" in tool_names