"""
Tests for FastAPI Health Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "aurora-pro-ai"
    assert data["status"] == "running"


def test_health_check():
    """Test basic health check"""
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_liveness_probe():
    """Test liveness probe"""
    response = client.get("/health/live")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "alive"


def test_readiness_probe():
    """Test readiness probe"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_startup_probe():
    """Test startup probe"""
    response = client.get("/health/startup")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "started"
