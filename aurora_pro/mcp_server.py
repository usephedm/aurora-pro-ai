from __future__ import annotations

import asyncio
import json
import os
import shlex
import subprocess
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP


def get_env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")


ALLOW_SHELL = get_env_bool("AURORA_MCP_ALLOW_SHELL", True)
BASE_API = os.getenv("AURORA_API_BASE", "http://127.0.0.1:8000")
VLLM_BASE = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8002/v1")
STREAMLIT_BASE = os.getenv("AURORA_GUI_BASE", "http://127.0.0.1:8501")

server = FastMCP("aurora-pro")


@server.tool()
async def health() -> dict:
    """Return Aurora API health summary (from /health)."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_API}/health", timeout=5)
        r.raise_for_status()
        return r.json()


@server.tool()
async def vllm_models() -> dict:
    """List models from the vLLM OpenAI-compatible endpoint."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{VLLM_BASE.rstrip('/')}/models", timeout=5)
        r.raise_for_status()
        return r.json()


@server.tool()
async def gui_health() -> dict:
    """Check Streamlit core health endpoint."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{STREAMLIT_BASE}/_stcore/health", timeout=5)
        r.raise_for_status()
        return {"ok": r.text.strip() == "ok"}


@server.tool()
async def http_get(url: str, timeout: float = 10.0) -> dict:
    """Fetch a URL (simple GET), returning status and first 8KB of text."""
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=timeout)
        text = r.text[:8192]
        return {"status": r.status_code, "text": text}


@server.tool()
async def shell_run(cmd: str, timeout: float = 30.0) -> dict:
    """Run a shell command (operator gated)."""
    if not ALLOW_SHELL:
        return {"error": "shell tool disabled by policy"}
    args = shlex.split(cmd)
    try:
        completed = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=timeout,
        )
    except Exception as e:
        return {"error": str(e)}
    stdout, stderr = await completed.communicate()
    return {
        "returncode": completed.returncode,
        "stdout": stdout.decode(errors="ignore")[:8192],
        "stderr": stderr.decode(errors="ignore")[:8192],
    }


def main() -> None:
    # Run as stdio server by default
    server.run()


if __name__ == "__main__":
    main()

