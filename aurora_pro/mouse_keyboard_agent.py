"""Real mouse and keyboard control agent for Aurora Pro with self-healing.

This module provides direct hardware-level input control via pyautogui.
All actions are logged and gated behind operator_enabled.yaml configuration.
Includes retry logic, dependency checking, and automatic recovery.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import deque
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import yaml

logger = logging.getLogger(__name__)


class InputActionType(str, Enum):
    """Supported input action types."""
    CLICK = "click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    MOVE_TO = "move_to"
    TYPE_TEXT = "type_text"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    PRESS_KEY = "press_key"
    DRAG = "drag"


class InputTask:
    """Input control task specification with retry tracking."""

    def __init__(
        self,
        task_id: str,
        action_type: InputActionType,
        parameters: Dict,
        operator_user: Optional[str] = None,
    ):
        self.task_id = task_id
        self.action_type = action_type
        self.parameters = parameters
        self.operator_user = operator_user
        self.status = "queued"
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.error: Optional[str] = None
        self.result: Optional[str] = None
        self.retry_count = 0
        self.max_retries = 2

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "action_type": self.action_type.value,
            "parameters": self.parameters,
            "operator_user": self.operator_user,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "result": self.result,
            "retry_count": self.retry_count,
        }


class MouseKeyboardAgent:
    """
    Autonomous mouse and keyboard control agent with self-healing.

    Features:
    - Real hardware input control via pyautogui
    - Sequential task queue processing with retry logic
    - Automatic dependency checking and error recovery
    - Comprehensive audit logging
    - Operator authorization gating
    - Graceful degradation when dependencies missing
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/input_agent.log"
    CONFIG_PATH = "/root/aurora_pro/config/operator_enabled.yaml"
    HISTORY_MAX = 50
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0  # seconds

    def __init__(self):
        self._queue: asyncio.Queue[InputTask] = asyncio.Queue()
        self._history: deque = deque(maxlen=self.HISTORY_MAX)
        self._tasks: Dict[str, InputTask] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()
        self._pyautogui_available = False
        self._last_error: Optional[str] = None
        self._error_count = 0
        self._restart_count = 0

        # Check pyautogui availability
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if pyautogui and dependencies are available."""
        try:
            import pyautogui as pg
            self._pyautogui = pg
            # Configure safety settings
            pg.FAILSAFE = True
            pg.PAUSE = 0.1
            self._pyautogui_available = True
            logger.info("PyAutoGUI initialized successfully")
        except ImportError as exc:
            self._pyautogui_available = False
            self._last_error = f"PyAutoGUI not available: {exc}"
            logger.error(self._last_error)
        except Exception as exc:
            self._pyautogui_available = False
            self._last_error = f"PyAutoGUI initialization failed: {exc}"
            logger.error(self._last_error)

    async def start(self):
        """Start the input agent worker with supervision."""
        if self._running:
            logger.warning("Input agent already running")
            return

        if not self._pyautogui_available:
            logger.error(f"Cannot start input agent: {self._last_error}")
            await self._audit_log_event("startup_failed", error=self._last_error)
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._supervised_worker())
        await self._audit_log_event("started")
        logger.info("Input agent started successfully")

    async def stop(self):
        """Stop the input agent worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        await self._audit_log_event("stopped")
        logger.info("Input agent stopped")

    async def _supervised_worker(self):
        """Supervised worker that auto-restarts on crashes."""
        while self._running:
            try:
                await self._worker()
            except asyncio.CancelledError:
                logger.info("Input agent worker cancelled")
                raise
            except Exception as exc:
                self._error_count += 1
                self._restart_count += 1
                logger.error(f"Input agent worker crashed: {exc}", exc_info=True)
                await self._audit_log_event("worker_crashed", error=str(exc))

                if self._running:
                    logger.info(f"Restarting input agent worker (restart #{self._restart_count})")
                    await self._audit_log_event("worker_restarting", restart_count=self._restart_count)
                    await asyncio.sleep(2)  # Brief pause before restart
                else:
                    break

    async def submit_task(
        self,
        action_type: InputActionType,
        parameters: Dict,
        operator_user: Optional[str] = None,
    ) -> InputTask:
        """Submit a new input task to the queue with authorization check."""
        # Check if pyautogui is available
        if not self._pyautogui_available:
            raise RuntimeError(
                f"Input agent unavailable: {self._last_error}. "
                "Ensure pyautogui is installed and X11/Wayland display is accessible."
            )

        # Check authorization
        if not await self._check_authorization():
            raise PermissionError(
                "Mouse/keyboard control is disabled. "
                "Set operator_enabled: true AND features.control_mouse_keyboard: true "
                "in config/operator_enabled.yaml"
            )

        task_id = f"input_{uuid.uuid4().hex[:12]}"
        task = InputTask(task_id, action_type, parameters, operator_user)
        task.max_retries = self.MAX_RETRIES

        async with self._lock:
            self._tasks[task_id] = task
            self._history.append(task_id)

        await self._queue.put(task)
        await self._audit_log(task, "queued")
        logger.info(f"Task {task_id} queued: {action_type.value}")
        return task

    def get_task(self, task_id: str) -> Optional[InputTask]:
        """Retrieve task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 50) -> List[InputTask]:
        """List recent tasks."""
        task_ids = list(self._history)[-limit:]
        return [self._tasks[tid] for tid in task_ids if tid in self._tasks]

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def get_screen_size(self) -> tuple:
        """Get current screen dimensions."""
        if self._pyautogui_available:
            return self._pyautogui.size()
        return (0, 0)

    def get_mouse_position(self) -> tuple:
        """Get current mouse position."""
        if self._pyautogui_available:
            return self._pyautogui.position()
        return (0, 0)

    def get_health_status(self) -> dict:
        """Get agent health status."""
        return {
            "running": self._running,
            "pyautogui_available": self._pyautogui_available,
            "queue_size": self.get_queue_size(),
            "error_count": self._error_count,
            "restart_count": self._restart_count,
            "last_error": self._last_error,
        }

    async def _worker(self):
        """Background worker processing input tasks sequentially with retry logic."""
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            task.status = "running"
            task.started_at = time.time()
            await self._audit_log(task, "running")
            logger.info(f"Executing task {task.task_id}: {task.action_type.value}")

            # Retry loop
            success = False
            last_error = None

            for attempt in range(task.max_retries + 1):
                try:
                    # Execute in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self._execute_input_action, task)
                    task.result = result
                    task.status = "completed"
                    success = True
                    logger.info(f"Task {task.task_id} completed: {result}")
                    break

                except Exception as exc:
                    last_error = str(exc)
                    task.retry_count = attempt
                    logger.warning(f"Task {task.task_id} attempt {attempt + 1} failed: {exc}")

                    if attempt < task.max_retries:
                        await self._audit_log(task, "retrying", error=last_error)
                        await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    else:
                        task.status = "error"
                        task.error = f"Failed after {task.max_retries + 1} attempts: {last_error}"
                        self._error_count += 1
                        logger.error(f"Task {task.task_id} failed permanently: {task.error}")

            if success:
                await self._audit_log(task, "completed")
            else:
                await self._audit_log(task, "failed", error=task.error)

            task.finished_at = time.time()
            self._queue.task_done()

    def _execute_input_action(self, task: InputTask) -> str:
        """Execute the actual input action (runs in thread pool)."""
        if not self._pyautogui_available:
            raise RuntimeError("PyAutoGUI not available")

        action = task.action_type
        params = task.parameters
        pg = self._pyautogui

        try:
            if action == InputActionType.CLICK:
                x = params.get("x", 0)
                y = params.get("y", 0)
                button = params.get("button", "left")
                clicks = params.get("clicks", 1)
                pg.click(x=x, y=y, clicks=clicks, button=button)
                return f"Clicked {button} at ({x}, {y}) {clicks} time(s)"

            elif action == InputActionType.RIGHT_CLICK:
                x = params.get("x", 0)
                y = params.get("y", 0)
                pg.rightClick(x=x, y=y)
                return f"Right-clicked at ({x}, {y})"

            elif action == InputActionType.DOUBLE_CLICK:
                x = params.get("x", 0)
                y = params.get("y", 0)
                pg.doubleClick(x=x, y=y)
                return f"Double-clicked at ({x}, {y})"

            elif action == InputActionType.MOVE_TO:
                x = params.get("x", 0)
                y = params.get("y", 0)
                duration = params.get("duration", 0.0)
                pg.moveTo(x, y, duration=duration)
                return f"Moved to ({x}, {y}) in {duration}s"

            elif action == InputActionType.TYPE_TEXT:
                text = params.get("text", "")
                interval = params.get("interval", 0.0)
                pg.write(text, interval=interval)
                return f"Typed {len(text)} characters"

            elif action == InputActionType.HOTKEY:
                keys = params.get("keys", [])
                if isinstance(keys, str):
                    keys = [keys]
                pg.hotkey(*keys)
                return f"Pressed hotkey: {'+'.join(keys)}"

            elif action == InputActionType.SCROLL:
                amount = params.get("amount", 0)
                x = params.get("x")
                y = params.get("y")
                pg.scroll(amount, x=x, y=y)
                return f"Scrolled {amount} units"

            elif action == InputActionType.PRESS_KEY:
                key = params.get("key", "")
                presses = params.get("presses", 1)
                pg.press(key, presses=presses)
                return f"Pressed '{key}' {presses} time(s)"

            elif action == InputActionType.DRAG:
                x = params.get("x", 0)
                y = params.get("y", 0)
                duration = params.get("duration", 0.0)
                button = params.get("button", "left")
                pg.drag(x, y, duration=duration, button=button)
                return f"Dragged {button} to ({x}, {y}) in {duration}s"

            else:
                raise ValueError(f"Unknown action type: {action}")

        except Exception as exc:
            # Check for failsafe
            if "failsafe" in str(exc).lower():
                raise RuntimeError("PyAutoGUI failsafe triggered (mouse in corner)")
            raise RuntimeError(f"Input action failed: {exc}")

    async def _check_authorization(self) -> bool:
        """Check if mouse/keyboard control is authorized in config."""
        try:
            async with aiofiles.open(self.CONFIG_PATH, "r") as f:
                content = await f.read()
                config = yaml.safe_load(content)

            # Check main flag and feature flag
            if not config.get("operator_enabled", False):
                return False

            features = config.get("features", {})
            return features.get("control_mouse_keyboard", False)

        except FileNotFoundError:
            logger.error(f"Config file not found: {self.CONFIG_PATH}")
            return False
        except Exception as exc:
            logger.error(f"Error reading config: {exc}")
            return False

    async def _audit_log(self, task: InputTask, status: str, error: Optional[str] = None):
        """Write audit log entry for task."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

        entry = {
            "timestamp": timestamp,
            "task_id": task.task_id,
            "action": task.action_type.value,
            "parameters": task.parameters,
            "status": status,
            "operator_user": task.operator_user,
            "retry_count": task.retry_count,
            "error": error,
        }

        # Add duration if completed
        if task.started_at and task.finished_at:
            entry["duration_sec"] = round(task.finished_at - task.started_at, 3)

        await self._write_audit_log(entry)

    async def _audit_log_event(self, event: str, **kwargs):
        """Write audit log entry for agent event."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        entry = {
            "timestamp": timestamp,
            "event": event,
            **kwargs,
        }
        await self._write_audit_log(entry)

    async def _write_audit_log(self, entry: dict):
        """Write entry to audit log file."""
        line = json.dumps(entry) + "\n"

        # Ensure log directory exists
        log_path = Path(self.AUDIT_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as exc:
            logger.error(f"Failed to write audit log: {exc}")


# Global singleton instance
_agent_instance: Optional[MouseKeyboardAgent] = None


def get_input_agent() -> MouseKeyboardAgent:
    """Get or create the global input agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MouseKeyboardAgent()
    return _agent_instance


__all__ = ["MouseKeyboardAgent", "InputTask", "InputActionType", "get_input_agent"]