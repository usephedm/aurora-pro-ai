"""Integration test suite for Aurora Pro.

Tests combined behavior of:
- CLI agents (Claude/Codex)
- Input agent
- Heartbeat monitor
- Audit logging
- Error recovery
"""
import json
import time
from pathlib import Path

import requests


API_BASE_URL = "http://0.0.0.0:8000"


class IntegrationTestRunner:
    """Integration test runner for Aurora Pro."""

    def __init__(self):
        self.results = []
        self.task_ids = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append((test_name, passed, message))
        print(f"{status} | {test_name}")
        if message:
            print(f"        {message}")

    def test_system_health(self):
        """Test that all system components are healthy."""
        try:
            response = requests.get(f"{API_BASE_URL}/health/status", timeout=5)
            response.raise_for_status()
            data = response.json()

            components = data.get("components", {})
            all_healthy = True

            for name, status in components.items():
                if status.get("status") not in ("healthy", "stopped"):
                    all_healthy = False
                    self.log_result(
                        f"System Health - {name}",
                        False,
                        f"Status: {status.get('status')}, Error: {status.get('error')}"
                    )

            if all_healthy:
                self.log_result("System Health Check", True, f"{len(components)} components healthy")
            else:
                self.log_result("System Health Check", False, "Some components unhealthy")

        except Exception as exc:
            self.log_result("System Health Check", False, str(exc))

    def test_cli_agent_submission(self):
        """Test CLI agent task submission."""
        try:
            payload = {
                "prompt": "What is 1+1? Respond with just the number.",
                "agent": "claude",
                "timeout": 60,
                "metadata": {"operator_user": "integration_test"},
            }

            response = requests.post(
                f"{API_BASE_URL}/cli/command",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            task_id = data.get("task", {}).get("id")
            if task_id:
                self.task_ids.append(("cli", task_id))
                self.log_result("CLI Agent Submission", True, f"Task ID: {task_id}")
            else:
                self.log_result("CLI Agent Submission", False, "No task ID returned")

        except Exception as exc:
            self.log_result("CLI Agent Submission", False, str(exc))

    def test_cli_status(self):
        """Test CLI status endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/cli/status", timeout=5)
            response.raise_for_status()
            data = response.json()

            agents = data.get("agents", {})
            if "claude" in agents and "codex" in agents:
                self.log_result("CLI Status Endpoint", True, f"{len(agents)} agents reported")
            else:
                self.log_result("CLI Status Endpoint", False, "Missing agent data")

        except Exception as exc:
            self.log_result("CLI Status Endpoint", False, str(exc))

    def test_input_agent_status(self):
        """Test input agent status."""
        try:
            response = requests.get(f"{API_BASE_URL}/input/status", timeout=5)
            response.raise_for_status()
            data = response.json()

            if "queue_size" in data and "screen_size" in data:
                self.log_result("Input Agent Status", True, f"Queue: {data['queue_size']}")
            else:
                self.log_result("Input Agent Status", False, "Incomplete status data")

        except Exception as exc:
            self.log_result("Input Agent Status", False, str(exc))

    def test_heartbeat_monitoring(self):
        """Test heartbeat monitoring system."""
        try:
            response = requests.get(f"{API_BASE_URL}/health/heartbeat", timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("running") and "uptime_seconds" in data:
                uptime = data["uptime_seconds"]
                self.log_result("Heartbeat Monitoring", True, f"Uptime: {uptime:.1f}s")
            else:
                self.log_result("Heartbeat Monitoring", False, "Heartbeat not running")

        except Exception as exc:
            self.log_result("Heartbeat Monitoring", False, str(exc))

    def test_audit_logs_exist(self):
        """Test that audit logs are being created."""
        log_files = [
            "/root/aurora_pro/logs/cli_agent_audit.log",
            "/root/aurora_pro/logs/heartbeat.log",
        ]

        for log_path in log_files:
            path = Path(log_path)
            if path.exists():
                size = path.stat().st_size
                self.log_result(f"Audit Log - {path.name}", True, f"Size: {size} bytes")
            else:
                self.log_result(f"Audit Log - {path.name}", False, "File does not exist")

    def test_cli_logs_endpoint(self):
        """Test CLI logs retrieval."""
        try:
            response = requests.get(
                f"{API_BASE_URL}/cli/logs",
                params={"agent": "claude", "limit": 10},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

            logs = data.get("logs", [])
            self.log_result("CLI Logs Endpoint", True, f"{len(logs)} log entries")

        except Exception as exc:
            self.log_result("CLI Logs Endpoint", False, str(exc))

    def test_wait_for_cli_task_completion(self):
        """Wait for CLI tasks to complete."""
        if not self.task_ids:
            self.log_result("CLI Task Completion", False, "No tasks submitted")
            return

        for task_type, task_id in self.task_ids:
            if task_type != "cli":
                continue

            print(f"   Waiting for task {task_id}...")
            completed = False

            for attempt in range(30):  # 30 seconds max
                try:
                    response = requests.get(f"{API_BASE_URL}/cli/status", timeout=5)
                    response.raise_for_status()
                    data = response.json()

                    # Check all agents for the task
                    for agent_data in data.get("agents", {}).values():
                        for task in agent_data.get("tasks", []):
                            if task.get("id") == task_id:
                                status = task.get("status")
                                if status in ("completed", "error", "timeout"):
                                    self.log_result(
                                        f"CLI Task {task_id[:8]} Completion",
                                        status == "completed",
                                        f"Status: {status}"
                                    )
                                    completed = True
                                    break

                    if completed:
                        break

                    time.sleep(1)

                except Exception as exc:
                    print(f"   Error checking task: {exc}")

            if not completed:
                self.log_result(f"CLI Task {task_id[:8]} Completion", False, "Timeout waiting")

    def test_structured_logs_format(self):
        """Verify structured log formats (JSONL)."""
        log_files = [
            ("/root/aurora_pro/logs/cli_agent_audit.log", "CLI Audit"),
            ("/root/aurora_pro/logs/heartbeat.log", "Heartbeat"),
        ]

        for log_path, log_name in log_files:
            path = Path(log_path)
            if not path.exists():
                self.log_result(f"Structured Log - {log_name}", False, "Log file missing")
                continue

            try:
                with open(path, "r") as f:
                    lines = f.readlines()

                if not lines:
                    self.log_result(f"Structured Log - {log_name}", False, "Log is empty")
                    continue

                # Check last line is valid JSON
                last_line = lines[-1].strip()
                entry = json.loads(last_line)

                if "timestamp" in entry:
                    self.log_result(f"Structured Log - {log_name}", True, f"{len(lines)} entries")
                else:
                    self.log_result(f"Structured Log - {log_name}", False, "Missing timestamp")

            except json.JSONDecodeError:
                self.log_result(f"Structured Log - {log_name}", False, "Invalid JSON format")
            except Exception as exc:
                self.log_result(f"Structured Log - {log_name}", False, str(exc))

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
            response.raise_for_status()

            # Check for some expected metrics
            content = response.text
            if "aurora_requests_total" in content:
                self.log_result("Metrics Endpoint", True, "Prometheus metrics available")
            else:
                self.log_result("Metrics Endpoint", False, "Expected metrics missing")

        except Exception as exc:
            self.log_result("Metrics Endpoint", False, str(exc))

    def run_all_tests(self):
        """Run all integration tests."""
        print("=" * 70)
        print("Aurora Pro - Integration Test Suite")
        print("=" * 70)
        print()

        tests = [
            ("System Health", self.test_system_health),
            ("CLI Agent Submission", self.test_cli_agent_submission),
            ("CLI Status", self.test_cli_status),
            ("Input Agent Status", self.test_input_agent_status),
            ("Heartbeat Monitoring", self.test_heartbeat_monitoring),
            ("Audit Logs Exist", self.test_audit_logs_exist),
            ("CLI Logs Endpoint", self.test_cli_logs_endpoint),
            ("Wait for CLI Tasks", self.test_wait_for_cli_task_completion),
            ("Structured Logs Format", self.test_structured_logs_format),
            ("Metrics Endpoint", self.test_metrics_endpoint),
        ]

        print("[Phase 1: System Checks]")
        print("-" * 70)
        for name, test_func in tests[:5]:
            test_func()

        print()
        print("[Phase 2: Logging & Monitoring]")
        print("-" * 70)
        for name, test_func in tests[5:]:
            test_func()

        # Summary
        print()
        print("=" * 70)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = sum(1 for _, p, _ in self.results if not p)

        print(f"Results: {passed} passed, {failed} failed out of {len(self.results)} tests")

        if failed == 0:
            print("✓ All integration tests passed!")
            return 0
        else:
            print(f"✗ {failed} test(s) failed")
            print()
            print("Failed tests:")
            for name, passed, message in self.results:
                if not passed:
                    print(f"  - {name}: {message}")
            return 1


def main():
    """Run integration tests."""
    runner = IntegrationTestRunner()
    return runner.run_all_tests()


if __name__ == "__main__":
    exit(main())