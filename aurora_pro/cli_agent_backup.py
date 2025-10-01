"""CLI agent orchestrator for Aurora Pro with audit and task isolation."""
from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import os
import shlex
import time
import uuid
from collections import deque
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles


class AgentType(str, Enum):
    """Supported CLI agent types."""
    CLAUDE = "claude"
    CODEX = "codex"


@dataclasses.dataclass
class CLITask:
    """Task record for CLI agent execution."""
    id: str
    agent: AgentType
    prompt: str
    status: str = "queued"
    created_at: float = dataclasses.field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    timeout: int = 300
    result: Optional[str] = None
    error: Optional[str] = None
    logs: List[Dict[str, str]] = dataclasses.field(default_factory=list)
    operator_user: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent.value,
            "prompt": self.prompt,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "timeout": self.timeout,
            "result": self.result,
            "error": self.error,
            "logs": self.logs,
        }


class CLIAgent:
    """
    Manages CLI agent task execution with concurrency control, audit logging,
    and task-isolated log persistence.
    """

    HISTORY_MAX = 20
    TIMEOUT_DEFAULT = 300
    AUDIT_LOG_PATH = "/root/aurora_pro/logs/cli_agent_audit.log"
    CODEX_ACTIVITY_LOG = "/root/aurora_pro/logs/codex_activity.log"
    TASK_LOG_DIR = "/root/aurora_pro/logs/tasks"

    def __init__(self) -> None:
        self._agents: Dict[AgentType, asyncio.Semaphore] = {
            AgentType.CLAUDE: asyncio.Semaphore(1),
            AgentType.CODEX: asyncio.Semaphore(1),
        }
        self._history: deque = deque(maxlen=self.HISTORY_MAX)
        self._tasks: Dict[str, CLITask] = {}
        self._lock = asyncio.Lock()

    async def submit_task(
        self,
        prompt: str,
        agent: AgentType,
        *,
        timeout: Optional[int] = None,
        operator_user: Optional[str] = None,
    ) -> CLITask:
        """Submit a new CLI task; returns immediately with queued task."""
        task_id = str(uuid.uuid4())
        task = CLITask(
            id=task_id,
            agent=agent,
            prompt=prompt,
            timeout=timeout or self.TIMEOUT_DEFAULT,
            operator_user=operator_user,
        )
        async with self._lock:
            self._tasks[task_id] = task
            self._history.append(task_id)
        await self._audit_log(task, "queued")
        asyncio.create_task(self._execute_task(task))
        return task

    async def get_task(self, task_id: str) -> Optional[CLITask]:
        """Retrieve task by ID."""
        return self._tasks.get(task_id)

    async def list_tasks(self, agent: Optional[AgentType] = None) -> List[CLITask]:
        """List recent tasks, optionally filtered by agent."""
        tasks = [self._tasks[tid] for tid in self._history if tid in self._tasks]
        if agent:
            tasks = [t for t in tasks if t.agent == agent]
        return tasks

    def status(self) -> Dict[str, dict]:
        """Return status summary for all agents."""
        summary = {}
        for agent_type in AgentType:
            sem = self._agents[agent_type]
            tasks = [t for t in self._history if self._tasks.get(t, CLITask("", agent_type, "")).agent == agent_type]
            task_list = [self._tasks[tid].to_dict() for tid in tasks if tid in self._tasks]
            running = [t for t in task_list if t["status"] == "running"]
            summary[agent_type.value] = {
                "available": sem._value,
                "running": running[0]["id"] if running else None,
                "tasks": task_list,
            }
        return summary

    async def _execute_task(self, task: CLITask) -> None:
        """Execute task with semaphore-based concurrency control."""
        sem = self._agents[task.agent]
        async with sem:
            task.status = "running"
            task.started_at = time.time()
            await self._append_log(task, "system", "Task started")
            await self._audit_log(task, "running")

            try:
                await self._run_subprocess(task)
            except asyncio.TimeoutError:
                task.status = "timeout"
                task.error = "Execution timed out"
                await self._append_log(task, "system", f"Timeout after {task.timeout}s")
            except Exception as exc:
                task.status = "error"
                task.error = str(exc)
                await self._append_log(task, "system", f"Error: {exc}")
            finally:
                task.finished_at = time.time()
                await self._audit_log(task, task.status)
                await self._save_task_log(task)

    async def _run_subprocess(self, task: CLITask) -> None:
        """Spawn CLI subprocess and capture output."""
        command = self._build_command(task.agent)
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            raise RuntimeError(f"CLI binary '{task.agent.value}' not found in PATH")

        assert proc.stdin and proc.stdout and proc.stderr
        proc.stdin.write(task.prompt.encode("utf-8", errors="replace"))
        proc.stdin.write(b"\n")
        await proc.stdin.drain()
        proc.stdin.close()

        stdout_lines = []
        stderr_lines = []

        async def _read_stream(stream: asyncio.StreamReader, stream_name: str, collector: List[str]) -> None:
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                collector.append(text)
                await self._append_log(task, stream_name, text)

        stdout_task = asyncio.create_task(_read_stream(proc.stdout, "stdout", stdout_lines))
        stderr_task = asyncio.create_task(_read_stream(proc.stderr, "stderr", stderr_lines))

        try:
            await asyncio.wait_for(proc.wait(), timeout=task.timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        finally:
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

        exit_code = proc.returncode
        if exit_code == 0:
            task.status = "completed"
            task.result = "\n".join(stdout_lines)
            await self._append_log(task, "system", "Task completed successfully")
        else:
            task.status = "error"
            task.error = "\n".join(stderr_lines) or f"Exit code {exit_code}"
            await self._append_log(task, "system", f"Failed with exit code {exit_code}")

    def _build_command(self, agent: AgentType) -> List[str]:
        """Build shell-safe command list for agent."""
        env_key = f"{agent.value.upper()}_CLI_CMD"
        cmd_str = os.getenv(env_key, agent.value)
        return shlex.split(cmd_str)

    async def _write_codex_activity_log(
        self,
        task: CLITask,
        output_path: Path,
        stdout_lines: List[str],
        stderr_lines: List[str],
    ) -> None:
        """Write structured JSONL entry for Codex tasks."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        prompt_hash = hashlib.sha256(task.prompt.encode("utf-8")).hexdigest()

        # Calculate duration and exit code
        duration = 0.0
        if task.started_at and task.finished_at:
            duration = round(task.finished_at - task.started_at, 3)

        # Derive exit code from status
        exit_code = 0
        if task.status == "completed":
            exit_code = 0
        elif task.status == "error":
            exit_code = 1
        elif task.status == "timeout":
            exit_code = 124  # Standard timeout exit code

        # Input summary (first 10 words)
        words = task.prompt.split()[:10]
        input_summary = " ".join(words)

        # Elevation used (check if any special features were used)
        elevation_used = []
        # This would be populated if we tracked which operator features were active

        entry = {
            "timestamp": timestamp,
            "task_id": task.id,
            "agent": task.agent.value,
            "prompt_sha256": prompt_hash,
            "status": task.status,
            "duration_sec": duration,
            "exit_code": exit_code,
            "operator_user": task.operator_user or "unknown",
            "output_path": str(output_path),
            "elevation_used": elevation_used,
            "input_summary": input_summary,
            "stderr_lines": len(stderr_lines),
            "stdout_lines": len(stdout_lines),
        }

        line = json.dumps(entry) + "\n"

        # Ensure log exists
        log_path = Path(self.CODEX_ACTIVITY_LOG)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(self.CODEX_ACTIVITY_LOG, "a") as f:
            await f.write(line)

    async def _append_log(self, task: CLITask, stream: str, message: str) -> None:
        """Append log entry to task."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        entry = {"timestamp": timestamp, "stream": stream, "message": message}
        task.logs.append(entry)

    async def _audit_log(self, task: CLITask, status: str) -> None:
        """Write audit log entry."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        prompt_hash = hashlib.sha256(task.prompt.encode("utf-8")).hexdigest()
        duration = None
        if task.started_at and task.finished_at:
            duration = round(task.finished_at - task.started_at, 3)

        entry = {
            "timestamp": timestamp,
            "task_id": task.id,
            "agent": task.agent.value,
            "prompt_sha256": prompt_hash,
            "status": status,
            "duration_sec": duration,
            "operator_user": task.operator_user,
        }
        line = json.dumps(entry) + "\n"

        async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
            await f.write(line)

    async def _save_task_log(self, task: CLITask) -> None:
        """Persist full task logs to dedicated file with structured format."""
        log_path = Path(self.TASK_LOG_DIR) / f"{task.id}.log"

        # Separate stdout and stderr
        stdout_lines = [log["message"] for log in task.logs if log["stream"] == "stdout"]
        stderr_lines = [log["message"] for log in task.logs if log["stream"] == "stderr"]

        # Build structured log content
        content_parts = []
        content_parts.append("=" * 80)
        content_parts.append(f"TASK ID: {task.id}")
        content_parts.append(f"AGENT: {task.agent.value}")
        content_parts.append(f"STATUS: {task.status}")
        content_parts.append(f"CREATED: {datetime.utcfromtimestamp(task.created_at).isoformat()}Z")
        if task.started_at:
            content_parts.append(f"STARTED: {datetime.utcfromtimestamp(task.started_at).isoformat()}Z")
        if task.finished_at:
            content_parts.append(f"FINISHED: {datetime.utcfromtimestamp(task.finished_at).isoformat()}Z")
            duration = task.finished_at - task.started_at if task.started_at else 0
            content_parts.append(f"DURATION: {duration:.3f}s")
        content_parts.append(f"TIMEOUT: {task.timeout}s")
        content_parts.append(f"OPERATOR: {task.operator_user or 'N/A'}")
        content_parts.append("=" * 80)
        content_parts.append("")

        # Prompt (first 200 chars)
        content_parts.append("PROMPT:")
        content_parts.append(task.prompt[:500] + ("..." if len(task.prompt) > 500 else ""))
        content_parts.append("")

        # STDOUT section
        content_parts.append("=" * 80)
        content_parts.append("STDOUT")
        content_parts.append("=" * 80)
        if stdout_lines:
            content_parts.extend(stdout_lines)
        else:
            content_parts.append("(no stdout)")
        content_parts.append("")

        # STDERR section
        content_parts.append("=" * 80)
        content_parts.append("STDERR")
        content_parts.append("=" * 80)
        if stderr_lines:
            content_parts.extend(stderr_lines)
        else:
            content_parts.append("(no stderr)")
        content_parts.append("")

        # Result/Error
        if task.result:
            content_parts.append("=" * 80)
            content_parts.append("RESULT")
            content_parts.append("=" * 80)
            content_parts.append(task.result)
            content_parts.append("")

        if task.error:
            content_parts.append("=" * 80)
            content_parts.append("ERROR")
            content_parts.append("=" * 80)
            content_parts.append(task.error)
            content_parts.append("")

        # Write to file
        async with aiofiles.open(log_path, "w") as f:
            await f.write("\n".join(content_parts))

        # If Codex agent, write structured JSONL entry
        if task.agent == AgentType.CODEX and task.finished_at:
            await self._write_codex_activity_log(task, log_path, stdout_lines, stderr_lines)


__all__ = ["CLIAgent", "CLITask", "AgentType"]