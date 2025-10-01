"""Natural language driven task coordination across Aurora subsystems."""
import asyncio
import contextlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

from analyzer import AIAnalyzer
from browser_agent import BrowserAgent
from database import Database
from system_controller import KaliSystemController
from cli_agent import CLIAgent, AgentType
from agent_router import AgentRouter

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a queued asynchronous task."""

    id: str
    description: str
    created_at: float = field(default_factory=time.time)
    status: str = "queued"
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    result: Optional[str] = None


class TaskQueue:
    """Simple background worker queue."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Tuple[Task, Callable[[], Awaitable[str]]]] = asyncio.Queue()
        self._worker: Optional[asyncio.Task] = None
        self._tasks: Dict[str, Task] = {}

    async def start(self) -> None:
        if self._worker and not self._worker.done():
            return
        self._worker = asyncio.create_task(self._work())

    async def stop(self) -> None:
        if self._worker:
            self._worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker
            self._worker = None

    async def _work(self) -> None:
        while True:
            task, coro_factory = await self._queue.get()
            task.status = "running"
            task.started_at = time.time()
            try:
                result = await coro_factory()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Task %s failed", task.id)
                task.result = f"error: {exc}"
                task.status = "failed"
            else:
                task.result = result
                task.status = "completed"
            finally:
                task.finished_at = time.time()
                self._queue.task_done()

    async def submit(self, description: str, coro_factory: Callable[[], Awaitable[str]]) -> Task:
        task = Task(id=str(uuid.uuid4()), description=description)
        self._tasks[task.id] = task
        await self._queue.put((task, coro_factory))
        return task

    def snapshot(self) -> List[dict]:
        return [task.__dict__ for task in self._tasks.values()]


class AICoordinator:
    """Routes natural language commands to browser/system capabilities."""

    def __init__(
        self,
        browser: BrowserAgent,
        system: KaliSystemController,
        database: Database,
        analyzer: AIAnalyzer,
    ) -> None:
        self.browser = browser
        self.system = system
        self.database = database
        self.analyzer = analyzer
        self.queue = TaskQueue()
        self.cli_agent = CLIAgent()
        self.agent_router = AgentRouter(self)
        self.context: Dict[str, str] = {
            "active_url": "",
            "working_directory": ".",
        }

    async def start(self) -> None:
        await self.queue.start()

    async def shutdown(self) -> None:
        await self.queue.stop()

    async def process_command(self, command: str) -> str:
        lowered = command.lower().strip()

        if lowered.startswith("browse"):
            url = command.split(" ", 1)[1] if " " in command else "https://"
            await self.browser.open_url(url)
            self.context["active_url"] = url
            return f"Navigating browser to {url}"

        if lowered.startswith("search "):
            query = command.split(" ", 1)[1]
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            await self.browser.open_url(url)
            self.context["active_url"] = url
            return f"Searching web for {query}"

        if lowered.startswith("command "):
            shell_cmd = command.split(" ", 1)[1]

            async def _runner() -> str:
                result = await self.system.run_command(shell_cmd)
                return result.stdout or result.stderr

            task = await self.queue.submit(f"shell: {shell_cmd}", _runner)
            return f"Queued shell command {task.id}"

        if lowered.startswith("nmap "):
            target = command.split(" ", 1)[1]
            result = await self.system.run_nmap(target)
            return result.stdout or result.stderr

        if lowered.startswith("processes"):
            processes = self.system.list_processes()[:20]
            return json.dumps(processes, indent=2)

        if lowered.startswith("report"):
            return await self.generate_report()

        if lowered.startswith("workspace"):
            return await self._workspace_command(lowered)

        if lowered.startswith("screenshot"):
            data = await self.browser.capture_screenshot()
            return f"Screenshot captured ({len(data)} bytes)"

        return "Command not recognized"

    async def generate_report(self) -> str:
        records = await self.database.list_evidence(limit=20)
        if not records:
            return "No evidence available yet."
        lines = ["Aurora Findings Report", "======================"]
        for record in records:
            lines.append(f"- {record['title'] or record['url']} (score: {record['score']:.1f})")
        return "\n".join(lines)

    async def _workspace_command(self, lowered: str) -> str:
        parts = lowered.split()
        if len(parts) == 1 or parts[1] == "list":
            workspaces = self.browser.list_workspaces()
            return json.dumps(workspaces, indent=2)
        if parts[1] == "switch" and len(parts) > 2:
            self.browser.activate_workspace(parts[2])
            return f"Activated workspace {parts[2]}"
        if parts[1] == "new" and len(parts) > 2:
            self.browser.activate_workspace(parts[2])
            await self.browser.new_tab()
            return f"Created workspace {parts[2]}"
        return "Workspace command not understood"

    def snapshot(self) -> Dict[str, object]:
        return {
            "context": dict(self.context),
            "tasks": self.queue.snapshot(),
            "cli": self.cli_agent.status(),
            "conversation": self.agent_router.snapshot(),
        }

    async def submit_cli_task(
        self,
        prompt: str,
        *,
        agent: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> dict:
        metadata = metadata or {}
        selected_agent = self._select_agent(prompt, metadata, agent)
        timeout = metadata.get("timeout")
        timeout_value: Optional[int] = None
        if timeout is not None:
            try:
                timeout_value = int(timeout)
            except (TypeError, ValueError):
                timeout_value = None
        operator_user = metadata.get("operator_user")
        task = await self.cli_agent.submit_task(
            prompt,
            AgentType(selected_agent),
            timeout=timeout_value,
            operator_user=operator_user,
        )
        return {"agent": selected_agent, "task": task.to_dict()}

    def cli_status(self) -> Dict[str, dict]:
        return self.cli_agent.status()

    async def cli_logs(self, agent: Optional[str] = None, limit: int = 100) -> List[dict]:
        agent_type = AgentType(agent) if agent else None
        tasks = await self.cli_agent.list_tasks(agent=agent_type)
        all_logs = []
        for task in tasks:
            all_logs.extend(task.logs[-limit:])
        return all_logs[-limit:]

    def _select_agent(
        self,
        prompt: str,
        metadata: Dict[str, str],
        explicit_agent: Optional[str],
    ) -> str:
        valid_agents = [a.value for a in AgentType]
        if explicit_agent:
            choice = explicit_agent.lower()
            if choice in valid_agents:
                return choice
        preferred = metadata.get("preferred_agent")
        if preferred and preferred.lower() in valid_agents:
            return preferred.lower()

        prompt_lower = prompt.lower()
        code_keywords = ("code", "bug", "function", "script", "stack trace", "compile", "refactor")
        if any(keyword in prompt_lower for keyword in code_keywords):
            return AgentType.CODEX.value
        return AgentType.CLAUDE.value

    async def handle_conversation(
        self,
        prompt: str,
        *,
        agent_preference: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, object]:
        return await self.agent_router.handle_message(
            prompt,
            agent_preference=agent_preference,
            metadata=metadata,
        )
