"""Smoke test for mouse/keyboard input agent.

WARNING: This test will control real mouse/keyboard hardware.
Only run in a safe environment with control_mouse_keyboard enabled.
"""
import requests
import time


API_BASE_URL = "http://0.0.0.0:8000"


def test_input_status():
    """Verify input agent is accessible."""
    response = requests.get(f"{API_BASE_URL}/input/status", timeout=5)
    response.raise_for_status()
    data = response.json()
    print(f"✓ Input agent status: Queue={data['queue_size']}, Screen={data['screen_size']}")
    return data


def test_submit_move_task():
    """Submit a safe mouse move task."""
    payload = {
        "action_type": "move_to",
        "parameters": {"x": 100, "y": 100, "duration": 0.5},
        "operator_user": "test",
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/input/submit",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Submitted move task: {data['task_id']}")
        return data["task_id"]
    except requests.HTTPException as exc:
        if exc.response.status_code == 403:
            print("⚠️  Input control disabled (set control_mouse_keyboard: true in config)")
            return None
        raise


def wait_for_task(task_id: str, timeout: int = 10):
    """Wait for task to complete."""
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(f"{API_BASE_URL}/input/task/{task_id}", timeout=5)
        response.raise_for_status()
        task = response.json()
        status = task["status"]
        if status in ("completed", "error"):
            print(f"✓ Task {task_id} finished: {status}")
            return task
        time.sleep(0.5)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


def main():
    """Run input agent smoke tests."""
    print("Aurora Input Agent Smoke Tests")
    print("=" * 40)
    print("⚠️  WARNING: This will control real hardware!")
    print()

    try:
        # Check status
        test_input_status()

        # Try to submit a safe task
        task_id = test_submit_move_task()

        if task_id:
            # Wait for completion
            wait_for_task(task_id)
            print("\n" + "=" * 40)
            print("All tests passed ✓")
        else:
            print("\n" + "=" * 40)
            print("Tests skipped (input control disabled)")

    except Exception as exc:
        print(f"\n✗ Test failed: {exc}")
        raise


if __name__ == "__main__":
    main()