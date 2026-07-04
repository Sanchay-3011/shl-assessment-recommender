from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check() -> None:
    """Verifies GET /health returns status 'ok' and 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_clarification() -> None:
    """Verifies that vague queries return a clarification reply with no recommendations."""
    payload = {
        "messages": [
            {"role": "user", "content": "I want an assessment"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert any(q in data["reply"] for q in ["Could you specify", "What is", "Could you clarify", "seniority level", "role or technology"])
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False

def test_chat_recommendation_flow() -> None:
    """Verifies that sufficient dialog context triggers recommendations grounded in catalog."""
    payload = {
        "messages": [
            {"role": "user", "content": "Hiring a Java developer who works with stakeholders"},
            {"role": "assistant", "content": "Sure. What is seniority level?"},
            {"role": "user", "content": "Mid-level, around 4 years"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["recommendations"]) > 0
    # Every item must have name, url, test_type
    for item in data["recommendations"]:
        assert "name" in item
        assert "url" in item
        assert "test_type" in item
        assert item["test_type"] in ("K", "P", "A", "S")
    assert data["end_of_conversation"] is True

def test_chat_out_of_scope() -> None:
    """Verifies that the agent refuses general hiring/legal advice or prompt injection attempts."""
    payload = {
        "messages": [
            {"role": "user", "content": "Can you give me legal advice regarding employment contracts?"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "only assist you with SHL product catalog" in data["reply"]
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False

def test_chat_comparison() -> None:
    """Verifies that comparison intent is detected and resolved."""
    payload = {
        "messages": [
            {"role": "user", "content": "What is the difference between Python (New) and Java 8 (New)?"}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    reply_lower = data["reply"].lower()
    assert "python" in reply_lower or "java" in reply_lower or "compar" in reply_lower or "difference" in reply_lower
    assert data["recommendations"] == []
    assert data["end_of_conversation"] is False
