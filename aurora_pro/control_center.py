"""
Aurora Pro Control Center
Real-time visualization and control interface with WebSocket streaming

Features:
- Live agent status dashboard
- Real-time reasoning display (show what each agent is thinking)
- LLM selector (choose Claude, GPT-4, Gemini, local models)
- BIG RED STOP BUTTON (kill all operations instantly)
- Task queue visualization
- Live logs streaming
- System resource monitor (CPU, RAM, GPU)
- Agent communication graph
- Decision tree visualization
"""
import asyncio
import json
import logging
import os
import psutil
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set

import aiofiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from llm_orchestrator import get_llm_orchestrator, LLMProvider
from autonomous_engine import get_autonomous_engine
from reasoning_display import get_reasoning_display, ReasoningLevel
from multicore_manager import get_multicore_manager
from cache_manager import get_cache_manager
from vision_agent import get_vision_agent
from stealth_browser_agent import get_stealth_browser

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """Overall system status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    STOPPED = "stopped"


@dataclass
class SystemMetrics:
    """Real-time system metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    gpu_utilization: Optional[float] = None
    gpu_memory_used_gb: Optional[float] = None
    gpu_memory_total_gb: Optional[float] = None


@dataclass
class AgentStatus:
    """Status of a single agent."""
    name: str
    running: bool
    health: str  # healthy, degraded, critical, unknown
    tasks_active: int
    tasks_completed: int
    tasks_failed: int
    error_rate_percent: float
    average_latency_ms: float
    last_activity: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ControlCenter:
    """
    Real-Time Control Center for Aurora Pro.

    Provides live monitoring, control, and visualization of all system components.
    """

    LOG_PATH = "/root/aurora_pro/logs/control_center.log"
    METRICS_HISTORY_SIZE = 300  # Keep 5 minutes at 1s intervals

    def __init__(self):
        self._running = False
        self._emergency_stop_triggered = False
        self._lock = asyncio.Lock()

        # WebSocket connections
        self._ws_clients: Set[WebSocket] = set()

        # Metrics history
        self._metrics_history: Deque[SystemMetrics] = deque(maxlen=self.METRICS_HISTORY_SIZE)

        # Agent references
        self._llm = get_llm_orchestrator()
        self._autonomous = get_autonomous_engine()
        self._reasoning = get_reasoning_display()
        self._multicore = None
        self._cache = None
        self._vision = None
        self._browser = None

        # Tasks
        self._monitor_task: Optional[asyncio.Task] = None
        self._broadcast_task: Optional[asyncio.Task] = None

        # Process info
        self._process = psutil.Process()
        self._net_io_start = psutil.net_io_counters()

    async def start(self):
        """Initialize control center."""
        self._running = True
        self._emergency_stop_triggered = False

        # Get agent references
        self._multicore = get_multicore_manager()
        self._cache = get_cache_manager()
        self._vision = get_vision_agent()
        self._browser = get_stealth_browser()

        # Start background tasks
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())

        await self._audit_log("system", "Control Center started")
        logger.info("Control Center initialized")

    async def stop(self):
        """Shutdown control center."""
        self._running = False

        # Cancel background tasks
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._broadcast_task:
            self._broadcast_task.cancel()

        # Disconnect all WebSocket clients
        for client in list(self._ws_clients):
            try:
                await client.close()
            except:
                pass

        await self._audit_log("system", "Control Center stopped")

    async def emergency_stop(self, reason: str = "Manual trigger"):
        """
        EMERGENCY STOP - Kill all operations immediately.

        This is the BIG RED BUTTON.
        """
        async with self._lock:
            if self._emergency_stop_triggered:
                return  # Already stopping

            self._emergency_stop_triggered = True

        await self._audit_log("EMERGENCY_STOP", f"Reason: {reason}")
        logger.critical(f"EMERGENCY STOP TRIGGERED: {reason}")

        # Broadcast emergency stop to all clients
        await self._broadcast_to_clients({
            "type": "emergency_stop",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Stop all agents in parallel
        stop_tasks = []

        if self._autonomous and self._autonomous._running:
            stop_tasks.append(self._autonomous.stop())

        if self._multicore and self._multicore._running:
            stop_tasks.append(self._multicore.stop())

        if self._browser and self._browser._running:
            stop_tasks.append(self._browser.stop())

        if self._vision and self._vision._running:
            stop_tasks.append(self._vision.stop())

        if self._cache and self._cache._running:
            stop_tasks.append(self._cache.stop())

        if self._llm and self._llm._running:
            stop_tasks.append(self._llm.stop())

        # Execute all stops
        await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.critical("All agents stopped - Emergency stop complete")

    async def restart_system(self):
        """Restart all system components."""
        await self._audit_log("system", "System restart initiated")

        # Stop everything
        if not self._emergency_stop_triggered:
            await self.emergency_stop("System restart")

        # Wait a bit
        await asyncio.sleep(2)

        # Restart agents
        self._emergency_stop_triggered = False

        if self._llm:
            await self._llm.start()
        if self._autonomous:
            await self._autonomous.start()
        if self._multicore:
            await self._multicore.start()
        if self._cache:
            await self._cache.start()
        if self._vision:
            await self._vision.start()
        if self._browser:
            await self._browser.start()

        await self._audit_log("system", "System restart complete")

    async def _monitor_loop(self):
        """Background loop to collect system metrics."""
        while self._running:
            try:
                metrics = await self._collect_metrics()

                async with self._lock:
                    self._metrics_history.append(metrics)

                await asyncio.sleep(1.0)  # Collect every second

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5.0)

    async def _broadcast_loop(self):
        """Background loop to broadcast updates to WebSocket clients."""
        while self._running:
            try:
                # Collect comprehensive status
                status = await self._collect_full_status()

                # Broadcast to all connected clients
                await self._broadcast_to_clients({
                    "type": "status_update",
                    "data": status,
                    "timestamp": datetime.utcnow().isoformat(),
                })

                await asyncio.sleep(0.5)  # Broadcast twice per second

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Broadcast loop error: {e}")
                await asyncio.sleep(2.0)

    async def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU and Memory
        cpu_percent = self._process.cpu_percent(interval=0.1)
        mem_info = self._process.memory_info()
        mem_percent = self._process.memory_percent()

        # System memory
        sys_mem = psutil.virtual_memory()

        # Disk
        disk = psutil.disk_usage('/')

        # Network
        net_io = psutil.net_io_counters()
        net_sent_mb = (net_io.bytes_sent - self._net_io_start.bytes_sent) / (1024 * 1024)
        net_recv_mb = (net_io.bytes_recv - self._net_io_start.bytes_recv) / (1024 * 1024)

        # GPU (if available)
        gpu_util = None
        gpu_mem_used = None
        gpu_mem_total = None

        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_util = gpu.load * 100
                gpu_mem_used = gpu.memoryUsed / 1024  # Convert to GB
                gpu_mem_total = gpu.memoryTotal / 1024
        except:
            pass

        return SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=mem_percent,
            memory_used_gb=mem_info.rss / (1024 ** 3),
            memory_total_gb=sys_mem.total / (1024 ** 3),
            disk_percent=disk.percent,
            disk_used_gb=disk.used / (1024 ** 3),
            disk_total_gb=disk.total / (1024 ** 3),
            network_sent_mb=net_sent_mb,
            network_recv_mb=net_recv_mb,
            gpu_utilization=gpu_util,
            gpu_memory_used_gb=gpu_mem_used,
            gpu_memory_total_gb=gpu_mem_total,
        )

    async def _collect_full_status(self) -> Dict[str, Any]:
        """Collect comprehensive system status."""
        # Get latest metrics
        latest_metrics = None
        if self._metrics_history:
            latest_metrics = self._metrics_history[-1]

        # Collect agent statuses
        agents = {}

        # LLM Orchestrator
        if self._llm:
            llm_stats = self._llm.get_statistics()
            agents["llm_orchestrator"] = AgentStatus(
                name="LLM Orchestrator",
                running=self._llm._running,
                health="healthy" if self._llm._running else "stopped",
                tasks_active=0,
                tasks_completed=llm_stats["total_requests_all_providers"],
                tasks_failed=0,
                error_rate_percent=0.0,
                average_latency_ms=0.0,
                last_activity=None,
                metadata={"providers": llm_stats["providers"]},
            )

        # Autonomous Engine
        if self._autonomous:
            auto_status = self._autonomous.get_status()
            agents["autonomous_engine"] = AgentStatus(
                name="Autonomous Engine",
                running=auto_status["running"],
                health="healthy" if auto_status["running"] else "stopped",
                tasks_active=auto_status["active_workflows"],
                tasks_completed=auto_status["total_workflows"] - auto_status["active_workflows"],
                tasks_failed=0,
                error_rate_percent=0.0,
                average_latency_ms=0.0,
                last_activity=None,
                metadata=auto_status["agents_available"],
            )

        # Multicore Manager
        if self._multicore:
            mc_stats = self._multicore.get_statistics()
            agents["multicore"] = AgentStatus(
                name="Multicore Manager",
                running=self._multicore._running,
                health="healthy" if self._multicore._running else "stopped",
                tasks_active=mc_stats["pending"],
                tasks_completed=mc_stats["completed"],
                tasks_failed=mc_stats["failed"],
                error_rate_percent=mc_stats.get("success_rate_percent", 0.0),
                average_latency_ms=0.0,
                last_activity=None,
                metadata={"num_workers": mc_stats["num_workers"]},
            )

        # Cache Manager
        if self._cache:
            cache_stats = await self._cache.get_statistics()
            agents["cache"] = AgentStatus(
                name="Cache Manager",
                running=self._cache._running,
                health="healthy" if self._cache._running else "stopped",
                tasks_active=0,
                tasks_completed=cache_stats["memory"]["hits"],
                tasks_failed=cache_stats["memory"]["misses"],
                error_rate_percent=cache_stats["memory"]["hit_rate_percent"],
                average_latency_ms=0.0,
                last_activity=None,
                metadata=cache_stats,
            )

        # Vision Agent
        if self._vision:
            vision_status = self._vision.get_status()
            agents["vision"] = AgentStatus(
                name="Vision Agent",
                running=vision_status["running"],
                health="healthy" if vision_status["running"] else "stopped",
                tasks_active=0,
                tasks_completed=0,
                tasks_failed=0,
                error_rate_percent=0.0,
                average_latency_ms=0.0,
                last_activity=None,
                metadata=vision_status,
            )

        # Stealth Browser
        if self._browser:
            browser_status = self._browser.get_status()
            agents["browser"] = AgentStatus(
                name="Stealth Browser",
                running=browser_status["running"],
                health="healthy" if browser_status["running"] else "stopped",
                tasks_active=0,
                tasks_completed=0,
                tasks_failed=0,
                error_rate_percent=0.0,
                average_latency_ms=0.0,
                last_activity=None,
                metadata=browser_status,
            )

        # Reasoning Display
        if self._reasoning:
            reasoning_status = self._reasoning.get_status()
            recent_steps = self._reasoning.get_recent_steps(limit=10)
            agents["reasoning"] = AgentStatus(
                name="Reasoning Display",
                running=reasoning_status["running"],
                health="healthy" if reasoning_status["running"] else "stopped",
                tasks_active=reasoning_status["active_contexts"],
                tasks_completed=reasoning_status["total_contexts"],
                tasks_failed=0,
                error_rate_percent=0.0,
                average_latency_ms=0.0,
                last_activity=recent_steps[0]["timestamp"] if recent_steps else None,
                metadata={"recent_steps": recent_steps},
            )

        # Calculate overall system health
        system_health = self._calculate_system_health(agents, latest_metrics)

        return {
            "system_health": system_health.value,
            "emergency_stop_active": self._emergency_stop_triggered,
            "metrics": {
                "timestamp": latest_metrics.timestamp if latest_metrics else None,
                "cpu_percent": latest_metrics.cpu_percent if latest_metrics else 0,
                "memory_percent": latest_metrics.memory_percent if latest_metrics else 0,
                "memory_used_gb": latest_metrics.memory_used_gb if latest_metrics else 0,
                "memory_total_gb": latest_metrics.memory_total_gb if latest_metrics else 0,
                "disk_percent": latest_metrics.disk_percent if latest_metrics else 0,
                "gpu_utilization": latest_metrics.gpu_utilization if latest_metrics else None,
            } if latest_metrics else {},
            "agents": {
                name: {
                    "name": agent.name,
                    "running": agent.running,
                    "health": agent.health,
                    "tasks_active": agent.tasks_active,
                    "tasks_completed": agent.tasks_completed,
                    "tasks_failed": agent.tasks_failed,
                    "error_rate_percent": agent.error_rate_percent,
                    "metadata": agent.metadata,
                }
                for name, agent in agents.items()
            },
            "uptime_seconds": time.time() - self._process.create_time(),
        }

    def _calculate_system_health(
        self,
        agents: Dict[str, AgentStatus],
        metrics: Optional[SystemMetrics],
    ) -> SystemStatus:
        """Calculate overall system health."""
        if self._emergency_stop_triggered:
            return SystemStatus.STOPPED

        # Check if critical agents are running
        critical_agents = ["llm_orchestrator", "autonomous_engine"]
        for agent_name in critical_agents:
            if agent_name in agents and not agents[agent_name].running:
                return SystemStatus.CRITICAL

        # Check resource usage
        if metrics:
            if metrics.cpu_percent > 95 or metrics.memory_percent > 95:
                return SystemStatus.CRITICAL
            if metrics.cpu_percent > 80 or metrics.memory_percent > 80:
                return SystemStatus.DEGRADED

        # Check error rates
        for agent in agents.values():
            if agent.tasks_completed > 10:  # Only if enough data
                error_rate = (agent.tasks_failed / (agent.tasks_completed + agent.tasks_failed)) * 100
                if error_rate > 50:
                    return SystemStatus.CRITICAL
                if error_rate > 20:
                    return SystemStatus.DEGRADED

        return SystemStatus.HEALTHY

    async def _broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket clients."""
        dead_clients = set()

        for client in self._ws_clients:
            try:
                await client.send_json(message)
            except WebSocketDisconnect:
                dead_clients.add(client)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                dead_clients.add(client)

        # Remove dead clients
        for client in dead_clients:
            self._ws_clients.discard(client)

    async def add_websocket_client(self, websocket: WebSocket):
        """Add WebSocket client."""
        await websocket.accept()
        self._ws_clients.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self._ws_clients)}")

        # Send initial status
        status = await self._collect_full_status()
        await websocket.send_json({
            "type": "initial_status",
            "data": status,
        })

    async def remove_websocket_client(self, websocket: WebSocket):
        """Remove WebSocket client."""
        self._ws_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self._ws_clients)}")

    async def _audit_log(self, action: str, details: str):
        """Write audit log entry."""
        try:
            Path(self.LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().isoformat()
            log_entry = f"{timestamp} | {action} | {details}\n"

            async with aiofiles.open(self.LOG_PATH, "a") as f:
                await f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_metrics_history(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get historical metrics."""
        limit = minutes * 60  # 1 per second
        metrics = list(self._metrics_history)[-limit:]

        return [
            {
                "timestamp": m.timestamp,
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "memory_used_gb": m.memory_used_gb,
                "disk_percent": m.disk_percent,
                "gpu_utilization": m.gpu_utilization,
            }
            for m in metrics
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get control center status."""
        return {
            "running": self._running,
            "emergency_stop_active": self._emergency_stop_triggered,
            "websocket_clients": len(self._ws_clients),
            "metrics_history_size": len(self._metrics_history),
        }


# Singleton instance
_control_center: Optional[ControlCenter] = None


def get_control_center() -> ControlCenter:
    """Get singleton control center instance."""
    global _control_center
    if _control_center is None:
        _control_center = ControlCenter()
    return _control_center