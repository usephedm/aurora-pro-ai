"""System-wide control helpers for the Aurora Comet GUI."""
import asyncio
import json
import logging
import os
import pathlib
import shlex
import time
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

import imageio
import mss
import numpy as np
import psutil

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Structured container for command execution results."""

    command: str
    stdout: str
    stderr: str
    returncode: int
    started_at: float
    finished_at: float

    @property
    def duration(self) -> float:
        return self.finished_at - self.started_at


class KaliSystemController:
    """Executes and observes system operations in a controlled way."""

    # Command whitelist for safety
    ALLOWED_COMMANDS = {
        "nmap", "netstat", "apt-cache", "pip", "git", "ls", "cat", "grep",
        "find", "ps", "top", "df", "du", "systemctl", "journalctl", "curl",
        "wget", "python3", "bash", "sh"
    }

    def __init__(self, allow_all_commands: bool = False) -> None:
        self._default_env = {
            "LANG": "C",
            "LC_ALL": "C",
        }
        self._allow_all = allow_all_commands
        self._allowed_paths = {pathlib.Path("/root/aurora_pro"), pathlib.Path("/tmp")}

    def _validate_command(self, command: str) -> None:
        """Validate command against whitelist."""
        if self._allow_all:
            return

        parts = shlex.split(command)
        if not parts:
            raise ValueError("Empty command")

        base_command = pathlib.Path(parts[0]).name
        if base_command not in self.ALLOWED_COMMANDS:
            raise ValueError(f"Command not allowed: {base_command}")

    async def run_command(self, command: str, timeout: Optional[int] = 120) -> CommandResult:
        """Run a shell command and capture output."""
        self._validate_command(command)

        started = time.time()
        env = os.environ.copy()
        env.update(self._default_env)

        # Parse command safely
        try:
            cmd_parts = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")

        # Use exec instead of shell
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        finished = time.time()
        return CommandResult(
            command=command,
            stdout=stdout.decode(errors="ignore"),
            stderr=stderr.decode(errors="ignore"),
            returncode=process.returncode,
            started_at=started,
            finished_at=finished,
        )

    async def run_command_stream(self, command: str) -> AsyncGenerator[str, None]:
        """Yield incremental output for long running commands."""
        self._validate_command(command)

        env = os.environ.copy()
        env.update(self._default_env)

        try:
            cmd_parts = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")

        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )

        assert process.stdout
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line.decode(errors="ignore")

        await process.wait()

    def _validate_path(self, path: pathlib.Path) -> None:
        """Validate path is within allowed directories."""
        resolved = path.resolve()
        if not any(resolved.is_relative_to(allowed) or resolved == allowed
                   for allowed in self._allowed_paths):
            raise ValueError(f"Path not in allowed directories: {resolved}")

    def list_directory(self, path: str) -> Dict[str, List[dict]]:
        """List directory contents with metadata."""
        target = pathlib.Path(path).expanduser().resolve()
        self._validate_path(target)

        if not target.exists():
            raise FileNotFoundError(f"Path not found: {target}")

        entries: List[dict] = []
        for entry in target.iterdir():
            info = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": info.st_size,
                    "modified": info.st_mtime,
                }
            )
        return {
            "path": str(target),
            "entries": sorted(entries, key=lambda item: (not item["is_dir"], item["name"].lower())),
        }

    def read_file(self, path: str, limit: int = 100_000) -> str:
        target = pathlib.Path(path).expanduser().resolve()
        self._validate_path(target)
        data = target.read_text(encoding="utf-8", errors="ignore")
        return data[:limit]

    def tail_file(self, path: str, lines: int = 200) -> str:
        target = pathlib.Path(path).expanduser().resolve()
        self._validate_path(target)
        content = target.read_text(encoding="utf-8", errors="ignore")
        return "\n".join(content.splitlines()[-lines:])

    def list_processes(self) -> List[dict]:
        results: List[dict] = []
        for proc in psutil.process_iter(attrs=["pid", "name", "username", "cpu_percent", "memory_info"]):
            info = proc.info
            results.append(
                {
                    "pid": info["pid"],
                    "name": info.get("name", ""),
                    "user": info.get("username", ""),
                    "cpu": info.get("cpu_percent", 0.0),
                    "rss": getattr(info.get("memory_info"), "rss", 0),
                }
            )
        return sorted(results, key=lambda item: item["cpu"], reverse=True)

    def process_details(self, pid: int) -> dict:
        proc = psutil.Process(pid)
        return {
            "pid": proc.pid,
            "name": proc.name(),
            "cmdline": " ".join(proc.cmdline()),
            "status": proc.status(),
            "create_time": proc.create_time(),
            "cpu_percent": proc.cpu_percent(interval=0.1),
            "memory_info": proc.memory_info()._asdict(),
            "open_files": [file.path for file in proc.open_files()],
            "connections": [conn._asdict() for conn in proc.connections()],
        }

    def terminate_process(self, pid: int, sig: str = "TERM") -> None:
        proc = psutil.Process(pid)
        if sig.upper() == "KILL":
            proc.kill()
        else:
            proc.terminate()

    async def run_nmap(self, target: str, options: str = "-T4 -F") -> CommandResult:
        command = f"nmap {options} {shlex.quote(target)}"
        return await self.run_command(command, timeout=300)

    async def netstat(self, options: str = "-tulnp") -> CommandResult:
        command = f"netstat {options}"
        return await self.run_command(command, timeout=60)

    async def package_info(self, package: str) -> CommandResult:
        command = f"apt-cache policy {shlex.quote(package)}"
        return await self.run_command(command, timeout=60)

    async def pip_list(self, search: Optional[str] = None) -> CommandResult:
        command = "pip list"
        if search:
            command += f" | grep -i {shlex.quote(search)}"
        return await self.run_command(command, timeout=60)

    async def git_status(self, repo_path: str) -> CommandResult:
        command = f"cd {shlex.quote(repo_path)} && git status --short --branch"
        return await self.run_command(command, timeout=60)

    def serialize_processes(self) -> str:
        return json.dumps(self.list_processes(), indent=2)

    async def execute_plugin(self, script_path: str, args: Optional[List[str]] = None) -> CommandResult:
        path = pathlib.Path(script_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Plugin not found: {path}")
        if not path.is_file():
            raise ValueError("Plugin path must be a file")
        command = " ".join([shlex.quote(str(path))] + [shlex.quote(arg) for arg in args or []])
        return await self.run_command(command, timeout=600)


    async def record_screen(self, duration: int = 5, interval: float = 0.5) -> pathlib.Path:
        """Capture a short screen recording and return the MP4 path."""
        frame_interval = max(interval, 0.1)
        end_time = time.time() + max(duration, 1)
        frames = []
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            while time.time() < end_time:
                grab = sct.grab(monitor)
                frame = np.array(grab)[:, :, :3][:, :, ::-1]
                frames.append(frame)
                await asyncio.sleep(frame_interval)
        if not frames:
            raise RuntimeError("Screen capture produced no frames")
        output_dir = pathlib.Path(tempfile.gettempdir())
        filename = output_dir / f"aurora_recording_{datetime.utcnow():%Y%m%dT%H%M%S}.mp4"
        with imageio.get_writer(filename, fps=int(1 / frame_interval)) as writer:
            for frame in frames:
                writer.append_data(frame)
        return filename
