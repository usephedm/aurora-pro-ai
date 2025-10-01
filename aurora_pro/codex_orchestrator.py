import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class CodexCLIOrchestrator:
    def __init__(self, workspace: str = "aurora_pro"):
        self.workspace = Path(workspace).resolve()
        self.config_path = self.workspace / ".codex" / "config.json"
        self.model = "gpt-5-codex"

    def ensure_workspace(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self.config_path.write_text(
                json.dumps(
                    {
                        "approval_mode": "auto",
                        "memory_persistence": True,
                        "model": self.model,
                        "reasoning_effort": "high",
                        "tool_access": ["shell", "file", "network"],
                        "working_directory": ".",
                    },
                    indent=2,
                )
            )

    async def execute_command(
        self,
        prompt: str,
        reasoning: str = "high",
        approval: str = "auto",
    ) -> Dict:
        """Execute Codex CLI with streaming output. Returns result dict."""

        self.ensure_workspace()
        # Prefer `codex exec` when available; fall back to `codex` direct
        cmd = [
            "codex",
            "exec",
            "--approval-mode",
            approval,
            "-m",
            self.model,
            "-c",
            f"model_reasoning_effort={reasoning}",
            prompt,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace),
        )

        stdout, stderr = await process.communicate()

        return {
            "exit_code": process.returncode,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def infrastructure_deployment(self, tasks: List[str]) -> Dict:
        """Execute a series of Codex CLI tasks, logging each result."""
        results: List[Dict] = []
        for task in tasks:
            print(f"[CODEX] Executing: {task.strip().splitlines()[0][:80]}")
            result = await self.execute_command(task, reasoning="high")
            results.append(result)
            self._log_to_coordination(task, result)
        return {"tasks_completed": len(results), "results": results}

    def _log_to_coordination(self, task: str, result: Dict) -> None:
        """Append progress to shared Claude coordination log."""
        log_path = Path("/home/v/Desktop/codex_setup_log.txt")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().isoformat()
        lines = [
            f"{ts} | CODEX TASK: {task.strip().splitlines()[0]}",
            f"Exit Code: {result['exit_code']}",
            "Status: SUCCESS ✅" if result["exit_code"] == 0 else "Status: FAILED ❌",
        ]
        if result.get("stderr") and result["exit_code"] != 0:
            lines.append(f"Error: {result['stderr']}")
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write("\n" + "\n".join(lines) + "\n")

