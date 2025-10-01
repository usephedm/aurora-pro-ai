"""Global heartbeat and health monitoring system for Aurora Pro.

Periodically records system health metrics including:
- Agent statuses
- Queue depths
- Error counts
- Recovery events
- System uptime
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """Global health monitoring and heartbeat system."""

    HEARTBEAT_LOG_PATH = "/root/aurora_pro/logs/heartbeat.log"
    HEARTBEAT_INTERVAL = 60  # seconds
    RECOVERY_LOG_PATH = "/root/aurora_pro/logs/recovery_events.log"

    def __init__(self):
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._start_time = time.time()
        self._last_heartbeat = 0.0
        self._error_counts: Dict[str, int] = {}
        self._recovery_events: list = []

    async def start(self):
        """Start the heartbeat monitor."""
        if self._running:
            return

        self._running = True
        self._start_time = time.time()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Heartbeat monitor started")

    async def stop(self):
        """Stop the heartbeat monitor."""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat monitor stopped")

    async def record_error(self, component: str, error: str):
        """Record an error for a component."""
        self._error_counts[component] = self._error_counts.get(component, 0) + 1
        logger.warning(f"Error recorded for {component}: {error}")

    async def record_recovery(self, component: str, event_type: str, details: Optional[Dict] = None):
        """Record a recovery event."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        event = {
            "timestamp": timestamp,
            "component": component,
            "event_type": event_type,
            "details": details or {},
        }
        self._recovery_events.append(event)

        # Keep only last 100 recovery events in memory
        if len(self._recovery_events) > 100:
            self._recovery_events.pop(0)

        # Write to recovery log
        await self._write_recovery_log(event)
        logger.info(f"Recovery event: {component} - {event_type}")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        uptime = time.time() - self._start_time
        return {
            "uptime_seconds": round(uptime, 2),
            "last_heartbeat": self._last_heartbeat,
            "error_counts": dict(self._error_counts),
            "recent_recovery_events": self._recovery_events[-10:],
            "running": self._running,
        }

    async def get_component_health(
        self,
        cli_agent=None,
        input_agent=None,
        coordinator=None,
    ) -> Dict[str, Any]:
        """Gather health status from all components."""
        health = {
            "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "components": {},
        }

        # CLI Agent health
        if cli_agent:
            try:
                cli_status = cli_agent.status()
                health["components"]["cli_agent"] = {
                    "status": "healthy",
                    "agents": cli_status,
                }
            except Exception as exc:
                health["components"]["cli_agent"] = {
                    "status": "error",
                    "error": str(exc),
                }
                await self.record_error("cli_agent", str(exc))

        # Input Agent health
        if input_agent:
            try:
                input_health = input_agent.get_health_status()
                health["components"]["input_agent"] = {
                    "status": "healthy" if input_health["running"] else "stopped",
                    **input_health,
                }
            except Exception as exc:
                health["components"]["input_agent"] = {
                    "status": "error",
                    "error": str(exc),
                }
                await self.record_error("input_agent", str(exc))

        # Coordinator health
        if coordinator:
            try:
                snapshot = coordinator.snapshot()
                health["components"]["coordinator"] = {
                    "status": "healthy",
                    "tasks_queued": len(snapshot.get("tasks", [])),
                    "cli_agents": len(snapshot.get("cli", {})),
                }
            except Exception as exc:
                health["components"]["coordinator"] = {
                    "status": "error",
                    "error": str(exc),
                }
                await self.record_error("coordinator", str(exc))

        # Add error counts and recovery events
        health["error_counts"] = dict(self._error_counts)
        health["recent_recovery_events"] = self._recovery_events[-5:]

        return health

    async def _heartbeat_loop(self):
        """Periodic heartbeat loop."""
        while self._running:
            try:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

                # Update timestamp
                self._last_heartbeat = time.time()

                # Get health status
                health = await self.get_health_status()

                # Write heartbeat entry
                await self._write_heartbeat(health)

            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                raise
            except Exception as exc:
                logger.error(f"Heartbeat loop error: {exc}", exc_info=True)
                await asyncio.sleep(5)  # Brief pause on error

    async def _write_heartbeat(self, health: Dict[str, Any]):
        """Write heartbeat entry to log."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        entry = {
            "timestamp": timestamp,
            "type": "heartbeat",
            **health,
        }

        line = json.dumps(entry) + "\n"

        # Ensure log directory exists
        log_path = Path(self.HEARTBEAT_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.HEARTBEAT_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as exc:
            logger.error(f"Failed to write heartbeat: {exc}")

    async def _write_recovery_log(self, event: Dict[str, Any]):
        """Write recovery event to log."""
        line = json.dumps(event) + "\n"

        # Ensure log directory exists
        log_path = Path(self.RECOVERY_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.RECOVERY_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as exc:
            logger.error(f"Failed to write recovery log: {exc}")


# Global singleton
_monitor_instance: Optional[HeartbeatMonitor] = None


def get_heartbeat_monitor() -> HeartbeatMonitor:
    """Get or create the global heartbeat monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = HeartbeatMonitor()
    return _monitor_instance


__all__ = ["HeartbeatMonitor", "get_heartbeat_monitor"]