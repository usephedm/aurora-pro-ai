"""Smoke test for CLI agent orchestration."""
import asyncio
import time

import requests


API_BASE_URL = "http://0.0.0.0:8000"


def test_health_check():
    """Verify API is accessible."""
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    response.raise_for_status()
    data = response.json()
    assert data["status"] == "healthy"
    print("✓ Health check passed")


def test_submit_claude_task():
    """Submit a simple prompt to Claude agent."""
    payload = {
        "prompt": "What is 2 + 2?",
        "agent": "claude",
        "timeout": 30,
    }
    response = requests.post(
        f"{API_BASE_URL}/cli/command",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    assert data["agent"] == "claude"
    assert "task" in data
    task_id = data["task"]["id"]
    print(f"✓ Submitted Claude task {task_id}")
    return task_id


def test_submit_codex_task():
    """Submit a simple prompt to Codex agent."""
    payload = {
        "prompt": "Print hello world in Python",
        "agent": "codex",
        "timeout": 30,
    }
    response = requests.post(
        f"{API_BASE_URL}/cli/command",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    assert data["agent"] == "codex"
    assert "task" in data
    task_id = data["task"]["id"]
    print(f"✓ Submitted Codex task {task_id}")
    return task_id


def test_fetch_status():
    """Fetch CLI status for all agents."""
    response = requests.get(f"{API_BASE_URL}/cli/status", timeout=5)
    response.raise_for_status()
    data = response.json()
    assert "agents" in data
    agents = data["agents"]
    assert "claude" in agents
    assert "codex" in agents
    print(f"✓ Status check passed: {len(agents)} agents")


def test_fetch_logs(agent: str, limit: int = 50):
    """Fetch recent logs for an agent."""
    params = {"agent": agent, "limit": limit}
    response = requests.get(f"{API_BASE_URL}/cli/logs", params=params, timeout=5)
    response.raise_for_status()
    data = response.json()
    assert "logs" in data
    logs = data["logs"]
    print(f"✓ Fetched {len(logs)} log entries for {agent}")
    return logs


def wait_for_task_completion(task_id: str, timeout: int = 60):
    """Poll status until task completes or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(f"{API_BASE_URL}/cli/status", timeout=5)
        response.raise_for_status()
        data = response.json()
        for agent_data in data["agents"].values():
            for task in agent_data.get("tasks", []):
                if task["id"] == task_id:
                    status = task["status"]
                    if status in ("completed", "error", "timeout"):
                        print(f"✓ Task {task_id} finished with status: {status}")
                        return task
        time.sleep(2)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


def main():
    """Run all smoke tests."""
    print("Aurora CLI Agent Smoke Tests")
    print("=" * 40)

    try:
        test_health_check()
        test_fetch_status()

        # Submit tasks
        claude_task_id = test_submit_claude_task()
        codex_task_id = test_submit_codex_task()

        # Wait for completion
        print("\nWaiting for tasks to complete...")
        wait_for_task_completion(claude_task_id, timeout=60)
        wait_for_task_completion(codex_task_id, timeout=60)

        # Fetch logs
        test_fetch_logs("claude")
        test_fetch_logs("codex")

        print("\n" + "=" * 40)
        print("All tests passed ✓")

    except Exception as exc:
        print(f"\n✗ Test failed: {exc}")
        raise


if __name__ == "__main__":
    main()