"""
Aurora Pro AI - Health Check Routes
"""
from fastapi import APIRouter, status
from typing import Dict, Any
from datetime import datetime

from ...cache.redis_cache import get_cache
from ...db.connection import engine
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger("api.health")


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns service status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "aurora-pro-ai"
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness() -> Dict[str, str]:
    """
    Kubernetes liveness probe
    
    Returns if the service is alive
    """
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness() -> Dict[str, Any]:
    """
    Kubernetes readiness probe
    
    Checks if all dependencies are healthy
    """
    checks = {
        "database": False,
        "cache": False
    }
    
    # Check database
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis cache
    try:
        cache = get_cache()
        checks["cache"] = cache.health_check()
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/startup", status_code=status.HTTP_200_OK)
async def startup() -> Dict[str, str]:
    """
    Kubernetes startup probe
    
    Returns if the service has started
    """
    return {"status": "started"}
