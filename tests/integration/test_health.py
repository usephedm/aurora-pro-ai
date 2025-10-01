import os
import pytest
import httpx


@pytest.mark.integration
def test_health_endpoint():
    base = os.getenv("API_BASE", "http://127.0.0.1:8000")
    try:
        r = httpx.get(f"{base}/health", timeout=2.0)
    except Exception:
        pytest.skip("API not running on this environment")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "healthy"

