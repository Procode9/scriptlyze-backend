"""
Test suite for ScriptLyze API
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ==================== HEALTH TESTS ====================
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "app" in response.json()


# ==================== AUTH TESTS ====================
def test_signup():
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login():
    # First signup
    client.post(
        "/api/v1/auth/signup",
        json={"email": "login@example.com", "password": "testpass123"}
    )
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


# ==================== ANALYSIS TESTS ====================
@pytest.fixture
def auth_token():
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "analyze@example.com", "password": "testpass123"}
    )
    return response.json()["access_token"]


def test_analyze_script(auth_token):
    script = """
    Did you know that 95% of YouTubers quit before hitting 1000 subscribers?
    I was almost one of them. But then I discovered this simple trick that
    changed everything. In this video, I'll show you exactly what I did...
    """
    
    response = client.post(
        "/api/v1/analyze/analyze",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"script": script, "script_type": "tutorial"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert 0 <= data["overall_score"] <= 10


def test_get_history(auth_token):
    response = client.get(
        "/api/v1/analyze/history",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert "total" in response.json()


def test_unauthorized_access():
    response = client.get("/api/v1/analyze/history")
    assert response.status_code == 401
