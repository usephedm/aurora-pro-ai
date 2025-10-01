"""Proxy Rotation Manager for Aurora Pro - Residential proxy management.

This module provides proxy rotation with health checking, geographic selection,
and automatic failover. All features are gated by operator_enabled.yaml.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import aiohttp
import yaml

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    proxy_id: str
    url: str  # Format: protocol://user:pass@host:port or protocol://host:port
    country: Optional[str] = None
    city: Optional[str] = None
    provider: Optional[str] = None
    auth_user: Optional[str] = None
    auth_pass: Optional[str] = None


@dataclass
class ProxyHealth:
    """Proxy health status."""
    proxy_id: str
    is_healthy: bool
    last_check_time: float
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0


class ProxyManager:
    """
    Proxy rotation manager with health checking and failover.

    Features:
    - Residential proxy rotation
    - Geographic selection (country/city)
    - Health checking with automatic failover
    - Authentication support
    - Performance monitoring
    - Operator authorization gating
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/proxy_manager.log"
    CONFIG_PATH = "/root/aurora_pro/config/operator_enabled.yaml"
    PROXIES_CONFIG_PATH = "/root/aurora_pro/config/proxies.yaml"

    HEALTH_CHECK_URL = "https://httpbin.org/ip"
    HEALTH_CHECK_INTERVAL = 300  # 5 minutes
    MAX_CONSECUTIVE_FAILURES = 3

    def __init__(self):
        self._config: Dict = {}
        self._proxies: Dict[str, ProxyConfig] = {}
        self._health: Dict[str, ProxyHealth] = {}
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Initialize proxy manager."""
        self._running = True
        await self._load_config()
        await self._load_proxies()

        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        await self._audit_log("system", f"Proxy manager started with {len(self._proxies)} proxies")
        logger.info(f"Proxy manager started with {len(self._proxies)} proxies")

    async def stop(self):
        """Shutdown proxy manager."""
        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        await self._audit_log("system", "Proxy manager stopped")
        logger.info("Proxy manager stopped")

    async def _load_config(self):
        """Load operator configuration."""
        try:
            async with aiofiles.open(self.CONFIG_PATH, "r") as f:
                content = await f.read()
                self._config = yaml.safe_load(content)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {"operator_enabled": False, "features": {}}

    async def _load_proxies(self):
        """Load proxy configurations from file."""
        try:
            proxy_config_path = Path(self.PROXIES_CONFIG_PATH)
            if not proxy_config_path.exists():
                # Create example config
                example_config = {
                    "proxies": [
                        {
                            "proxy_id": "example_proxy_1",
                            "url": "http://proxy.example.com:8080",
                            "country": "US",
                            "city": "New York",
                            "provider": "example_provider",
                        }
                    ]
                }
                proxy_config_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(proxy_config_path, "w") as f:
                    await f.write(yaml.dump(example_config))
                logger.info(f"Created example proxy config at {proxy_config_path}")
                return

            async with aiofiles.open(proxy_config_path, "r") as f:
                content = await f.read()
                proxy_data = yaml.safe_load(content)

            for proxy_dict in proxy_data.get("proxies", []):
                proxy_config = ProxyConfig(
                    proxy_id=proxy_dict["proxy_id"],
                    url=proxy_dict["url"],
                    country=proxy_dict.get("country"),
                    city=proxy_dict.get("city"),
                    provider=proxy_dict.get("provider"),
                    auth_user=proxy_dict.get("auth_user"),
                    auth_pass=proxy_dict.get("auth_pass"),
                )
                self._proxies[proxy_config.proxy_id] = proxy_config

                # Initialize health status
                self._health[proxy_config.proxy_id] = ProxyHealth(
                    proxy_id=proxy_config.proxy_id,
                    is_healthy=True,  # Assume healthy until checked
                    last_check_time=time.time(),
                )

            logger.info(f"Loaded {len(self._proxies)} proxy configurations")

        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")

    def _check_authorization(self) -> bool:
        """Check if proxy rotation is authorized."""
        operator_enabled = self._config.get("operator_enabled", False)
        feature_enabled = self._config.get("features", {}).get("proxy_rotation", False)
        return operator_enabled and feature_enabled

    async def get_proxy(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        operator_user: Optional[str] = None,
    ) -> Optional[ProxyConfig]:
        """
        Get a healthy proxy, optionally filtered by geography.

        Args:
            country: Filter by country code (e.g., "US", "GB")
            city: Filter by city name
            operator_user: User requesting operation

        Returns:
            ProxyConfig or None if no healthy proxy available
        """
        if not self._check_authorization():
            raise PermissionError("Proxy rotation not authorized - check operator_enabled.yaml")

        async with self._lock:
            # Filter healthy proxies
            candidates = []

            for proxy_id, proxy_config in self._proxies.items():
                health = self._health.get(proxy_id)

                if not health or not health.is_healthy:
                    continue

                # Apply geographic filters
                if country and proxy_config.country != country:
                    continue

                if city and proxy_config.city != city:
                    continue

                candidates.append(proxy_config)

            if not candidates:
                logger.warning("No healthy proxies available")
                return None

            # Select random proxy from candidates
            selected = random.choice(candidates)

            await self._audit_log(
                "get_proxy",
                f"Selected proxy: {selected.proxy_id}",
                operator_user=operator_user,
                metadata={
                    "proxy_id": selected.proxy_id,
                    "country": selected.country,
                    "city": selected.city,
                    "candidates": len(candidates),
                },
            )

            return selected

    async def check_proxy_health(self, proxy_id: str) -> bool:
        """
        Check if a specific proxy is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if proxy_id not in self._proxies:
            return False

        proxy_config = self._proxies[proxy_id]
        health = self._health[proxy_id]

        start_time = time.time()

        try:
            # Test proxy with health check URL
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.HEALTH_CHECK_URL,
                    proxy=proxy_config.url,
                ) as response:
                    if response.status == 200:
                        response_time_ms = (time.time() - start_time) * 1000

                        # Update health status
                        health.is_healthy = True
                        health.last_check_time = time.time()
                        health.last_success_time = time.time()
                        health.consecutive_failures = 0
                        health.total_requests += 1
                        health.successful_requests += 1

                        # Update average response time
                        if health.average_response_time_ms == 0:
                            health.average_response_time_ms = response_time_ms
                        else:
                            # Exponential moving average
                            health.average_response_time_ms = (
                                0.7 * health.average_response_time_ms +
                                0.3 * response_time_ms
                            )

                        logger.debug(f"Proxy {proxy_id} health check passed ({response_time_ms:.0f}ms)")
                        return True

            # Non-200 status
            raise Exception(f"Health check returned status {response.status}")

        except Exception as e:
            logger.warning(f"Proxy {proxy_id} health check failed: {e}")

            # Update health status
            health.is_healthy = False
            health.last_check_time = time.time()
            health.last_failure_time = time.time()
            health.consecutive_failures += 1
            health.total_requests += 1
            health.failed_requests += 1

            # Mark as unhealthy if too many consecutive failures
            if health.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                health.is_healthy = False
                await self._audit_log(
                    "proxy_unhealthy",
                    f"Proxy {proxy_id} marked unhealthy after {health.consecutive_failures} failures",
                )

            return False

    async def _health_check_loop(self):
        """Background task to periodically check proxy health."""
        while self._running:
            try:
                # Check all proxies
                for proxy_id in list(self._proxies.keys()):
                    await self.check_proxy_health(proxy_id)
                    await asyncio.sleep(1)  # Small delay between checks

                # Wait for next interval
                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)

    async def report_proxy_result(
        self,
        proxy_id: str,
        success: bool,
        response_time_ms: Optional[float] = None,
    ):
        """
        Report the result of using a proxy.

        This allows external code to update proxy health based on actual usage.

        Args:
            proxy_id: Proxy ID
            success: Whether the request succeeded
            response_time_ms: Response time in milliseconds
        """
        if proxy_id not in self._health:
            return

        health = self._health[proxy_id]

        async with self._lock:
            health.total_requests += 1

            if success:
                health.successful_requests += 1
                health.last_success_time = time.time()
                health.consecutive_failures = 0

                if response_time_ms:
                    if health.average_response_time_ms == 0:
                        health.average_response_time_ms = response_time_ms
                    else:
                        health.average_response_time_ms = (
                            0.7 * health.average_response_time_ms +
                            0.3 * response_time_ms
                        )
            else:
                health.failed_requests += 1
                health.last_failure_time = time.time()
                health.consecutive_failures += 1

                # Mark as unhealthy if too many failures
                if health.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    health.is_healthy = False

    def get_statistics(self) -> Dict:
        """Get proxy usage statistics."""
        total_proxies = len(self._proxies)
        healthy_proxies = sum(1 for h in self._health.values() if h.is_healthy)

        total_requests = sum(h.total_requests for h in self._health.values())
        successful_requests = sum(h.successful_requests for h in self._health.values())

        success_rate = 0.0
        if total_requests > 0:
            success_rate = (successful_requests / total_requests) * 100

        return {
            "total_proxies": total_proxies,
            "healthy_proxies": healthy_proxies,
            "unhealthy_proxies": total_proxies - healthy_proxies,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate_percent": round(success_rate, 2),
        }

    def list_proxies(self) -> List[Dict]:
        """List all proxies with health status."""
        proxies = []

        for proxy_id, proxy_config in self._proxies.items():
            health = self._health.get(proxy_id)

            proxies.append({
                "proxy_id": proxy_id,
                "country": proxy_config.country,
                "city": proxy_config.city,
                "provider": proxy_config.provider,
                "is_healthy": health.is_healthy if health else False,
                "success_rate_percent": round(
                    (health.successful_requests / health.total_requests * 100)
                    if health and health.total_requests > 0 else 0.0,
                    2
                ),
                "average_response_time_ms": round(health.average_response_time_ms, 1) if health else 0.0,
            })

        return proxies

    def get_status(self) -> Dict:
        """Get proxy manager status."""
        return {
            "running": self._running,
            "authorized": self._check_authorization(),
            "statistics": self.get_statistics(),
            "proxies": self.list_proxies(),
        }

    async def _audit_log(
        self,
        action: str,
        message: str,
        operator_user: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Write audit log entry."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

        entry = {
            "timestamp": timestamp,
            "action": action,
            "message": message,
            "operator_user": operator_user or "system",
            "metadata": metadata or {},
        }

        line = json.dumps(entry) + "\n"

        log_path = Path(self.AUDIT_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Singleton instance
_proxy_manager_instance: Optional[ProxyManager] = None


def get_proxy_manager() -> ProxyManager:
    """Get or create proxy manager singleton."""
    global _proxy_manager_instance
    if _proxy_manager_instance is None:
        _proxy_manager_instance = ProxyManager()
    return _proxy_manager_instance


__all__ = ["ProxyManager", "get_proxy_manager", "ProxyConfig", "ProxyHealth"]