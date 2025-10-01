# Aurora Pro - Stage 3 Manual Test Plan

## Prerequisites

- Kali Linux system with X11 or Wayland display
- Aurora Pro installed at `/root/aurora_pro`
- Python venv activated
- `claude` and `codex` CLI binaries in PATH (optional for full testing)

## Test Environment Setup

### 1. Enable Input Control

```bash
cd /root/aurora_pro
vi config/operator_enabled.yaml
```

Set:
```yaml
operator_enabled: true
features:
  control_mouse_keyboard: true
```

### 2. Start Aurora Pro

```bash
source venv/bin/activate
./run_aurora.sh
```

Wait for:
- FastAPI server on http://0.0.0.0:8000
- Streamlit dashboard on http://localhost:8501

---

## Test Suite 1: Basic Functionality

### Test 1.1: System Health Check

**Objective:** Verify all components are running

```bash
curl http://0.0.0.0:8000/health
curl http://0.0.0.0:8000/health/status
```

**Expected:**
- Status: `healthy`
- Components: cli_agent, input_agent, coordinator all present
- Uptime > 0

**Result:** ☐ PASS ☐ FAIL

---

### Test 1.2: Heartbeat Monitoring

**Objective:** Verify heartbeat system is active

```bash
curl http://0.0.0.0:8000/health/heartbeat
```

**Expected:**
- `running`: true
- `uptime_seconds` > 0
- `error_counts` present (may be empty)

**Wait 2 minutes, then check log:**
```bash
tail /root/aurora_pro/logs/heartbeat.log
```

**Expected:**
- At least 2 JSONL entries
- Valid JSON format
- `timestamp`, `uptime_seconds` fields

**Result:** ☐ PASS ☐ FAIL

---

### Test 1.3: CLI Agent Status

**Objective:** Verify CLI agents are initialized

```bash
curl http://0.0.0.0:8000/cli/status
```

**Expected:**
- `agents.claude` present
- `agents.codex` present
- Each has `available`, `running`, `tasks` fields

**Result:** ☐ PASS ☐ FAIL

---

### Test 1.4: Input Agent Status

**Objective:** Verify input agent is running

```bash
curl http://0.0.0.0:8000/input/status
```

**Expected:**
- `queue_size`: 0 (initially)
- `screen_size`: actual dimensions
- `mouse_position`: current position
- `recent_tasks`: [] (initially)

**Result:** ☐ PASS ☐ FAIL

---

## Test Suite 2: CLI Agent Functionality

### Test 2.1: Submit Claude Task

**Objective:** Submit and monitor CLI task

```bash
curl -X POST http://0.0.0.0:8000/cli/command \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is 2+2? Reply with just the number.",
    "agent": "claude",
    "timeout": 60,
    "metadata": {"operator_user": "test"}
  }'
```

**Expected:**
- HTTP 202
- Returns `task` object with `id`
- `agent`: "claude"

**Save task ID, then monitor:**
```bash
curl http://0.0.0.0:8000/cli/status
```

**Expected:**
- Task appears in `agents.claude.tasks`
- Status progresses: queued → running → completed/error

**Result:** ☐ PASS ☐ FAIL

---

### Test 2.2: CLI Audit Log

**Objective:** Verify structured audit logging

```bash
tail -5 /root/aurora_pro/logs/cli_agent_audit.log
```

**Expected:**
- Valid JSONL format
- Each line has: `timestamp`, `task_id`, `agent`, `prompt_sha256`, `status`

**Result:** ☐ PASS ☐ FAIL

---

### Test 2.3: Task-Specific Log

**Objective:** Verify per-task detailed logs

```bash
# Use task_id from Test 2.1
cat /root/aurora_pro/logs/tasks/<task_id>.log
```

**Expected:**
- Structured format with headers
- PROMPT section
- STDOUT section (with output)
- STDERR section (may be empty)
- No truncation

**Result:** ☐ PASS ☐ FAIL

---

### Test 2.4: Codex Activity Log

**Objective:** Test Codex-specific structured logging

**If codex binary available:**
```bash
curl -X POST http://0.0.0.0:8000/cli/command \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "print(\"hello\")",
    "agent": "codex",
    "timeout": 30
  }'
```

**Wait for completion, then check:**
```bash
tail -1 /root/aurora_pro/logs/codex_activity.log
```

**Expected:**
- Valid JSON with fields:
  - `task_id`, `agent`: "codex"
  - `prompt_sha256`
  - `exit_code`, `duration_sec`
  - `stdout_lines`, `stderr_lines`
  - `input_summary` (first 10 words)

**Result:** ☐ PASS ☐ FAIL

---

## Test Suite 3: Input Agent Functionality

### Test 3.1: Mouse Movement (Safe)

**Objective:** Test basic input control

**⚠️ WARNING: This will move your mouse!**

```bash
curl -X POST http://0.0.0.0:8000/input/submit \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "move_to",
    "parameters": {"x": 500, "y": 500, "duration": 1.0},
    "operator_user": "test"
  }'
```

**Expected:**
- HTTP 202
- Returns `task_id`, `status`: "queued"
- Mouse moves to (500, 500) smoothly

**Check status:**
```bash
curl http://0.0.0.0:8000/input/status
```

**Expected:**
- `recent_tasks` contains the task
- Task status: "completed"

**Result:** ☐ PASS ☐ FAIL

---

### Test 3.2: Input Authorization

**Objective:** Test that disabling blocks actions

**Disable in config:**
```yaml
operator_enabled: false
# OR
features:
  control_mouse_keyboard: false
```

**Try to submit:**
```bash
curl -X POST http://0.0.0.0:8000/input/submit \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "click",
    "parameters": {"x": 100, "y": 100}
  }'
```

**Expected:**
- HTTP 403 Forbidden
- Error message about disabled control

**Re-enable config before continuing**

**Result:** ☐ PASS ☐ FAIL

---

### Test 3.3: Input Audit Log

**Objective:** Verify input action logging

```bash
tail -5 /root/aurora_pro/logs/input_agent.log
```

**Expected:**
- JSONL format
- Entries with: `timestamp`, `task_id`, `action`, `parameters`, `status`, `retry_count`

**Result:** ☐ PASS ☐ FAIL

---

### Test 3.4: Error Recovery (Failsafe)

**Objective:** Test PyAutoGUI failsafe

**Move mouse to top-left corner (0,0) during task execution**

```bash
curl -X POST http://0.0.0.0:8000/input/submit \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "drag",
    "parameters": {"x": 1000, "y": 1000, "duration": 5.0}
  }'
```

**Immediately move mouse to corner (0,0)**

**Expected:**
- Task fails with "failsafe triggered" error
- Agent continues running (doesn't crash)
- Error logged in audit log

**Result:** ☐ PASS ☐ FAIL

---

## Test Suite 4: Dashboard Integration

### Test 4.1: Dashboard Accessible

**Objective:** Verify Streamlit dashboard loads

**Open browser:** http://localhost:8501

**Expected:**
- Dashboard loads without errors
- Tabs visible: Agent Chat, Evidence Overview, Submit Task, Claude CLI Output, Codex CLI Output, Input Agent

**Result:** ☐ PASS ☐ FAIL

---

### Test 4.2: Input Agent Tab

**Objective:** Test Input Agent UI

**Navigate to "Input Agent" tab**

**Expected:**
- Live metrics: Queue Size, Screen Size, Mouse Position
- Warning banner about hardware control
- Submit form with action type dropdown
- Recent tasks display

**Submit a task via dashboard:**
- Select "move_to"
- Set X: 300, Y: 300, Duration: 0.5
- Click "Execute Input Action"

**Expected:**
- Success message with task_id
- Task appears in "Recent Tasks" section
- Mouse moves to position

**Result:** ☐ PASS ☐ FAIL

---

### Test 4.3: CLI Monitoring

**Objective:** Test CLI output tabs

**Navigate to "Submit Task" tab**

**Submit a task:**
- Prompt: "Say hello"
- Agent: Claude
- Click submit

**Navigate to "Claude CLI Output" tab**

**Expected:**
- Log entries appear
- Status shows current/recent task
- Auto-refresh updates display

**Result:** ☐ PASS ☐ FAIL

---

## Test Suite 5: Self-Healing & Recovery

### Test 5.1: Input Agent Crash Recovery

**Objective:** Verify auto-restart on crash

**This requires injecting a crash - for manual testing, observe logs**

```bash
tail -f /root/aurora_pro/logs/input_agent.log
```

**Look for:**
- `"event": "worker_crashed"`
- `"event": "worker_restarting"`
- System continues functioning

**Result:** ☐ PASS ☐ FAIL (or N/A)

---

### Test 5.2: Retry Logic

**Objective:** Observe retry behavior

**Check audit log for tasks with retries:**
```bash
grep '"retry_count"' /root/aurora_pro/logs/input_agent.log
```

**If retries present:**
- Verify exponential backoff (1s, 2s delays)
- Verify max 2 retries + original attempt
- Verify final status after max retries

**Result:** ☐ PASS ☐ FAIL (or N/A if no retries)

---

### Test 5.3: Recovery Events Log

**Objective:** Verify recovery event logging

```bash
cat /root/aurora_pro/logs/recovery_events.log
```

**Expected (if any crashes occurred):**
- JSONL format
- `component`, `event_type`, `timestamp` fields

**Result:** ☐ PASS ☐ FAIL (or N/A)

---

## Test Suite 6: Automated Test Scripts

### Test 6.1: Comprehensive Input Tests

```bash
cd /root/aurora_pro
python test_input_agent_comprehensive.py
```

**Expected:**
- All tests pass (or skip if disabled)
- Clear output showing pass/fail for each test

**Result:** ☐ PASS ☐ FAIL

---

### Test 6.2: Integration Tests

```bash
python test_integration.py
```

**Expected:**
- Phase 1 (System Checks): All pass
- Phase 2 (Logging & Monitoring): All pass
- Summary shows 0 failed

**Result:** ☐ PASS ☐ FAIL

---

## Test Suite 7: Stress & Load Testing

### Test 7.1: Multiple Concurrent CLI Tasks

**Objective:** Test queue handling

```bash
for i in {1..5}; do
  curl -X POST http://0.0.0.0:8000/cli/command \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Task $i\", \"agent\": \"claude\", \"timeout\": 30}" &
done
wait
```

**Expected:**
- All 5 tasks accepted
- Tasks process sequentially (1 at a time per agent)
- All complete or timeout appropriately

**Result:** ☐ PASS ☐ FAIL

---

### Test 7.2: Input Agent Queue

**Objective:** Test sequential input processing

```bash
for i in {1..10}; do
  curl -X POST http://0.0.0.0:8000/input/submit \
    -H "Content-Type: application/json" \
    -d "{\"action_type\": \"move_to\", \"parameters\": {\"x\": $((100+i*50)), \"y\": 500, \"duration\": 0.2}}" &
done
wait
```

**Expected:**
- All tasks queued
- Mouse moves sequentially through positions
- `queue_size` increases then decreases
- All tasks complete

**Result:** ☐ PASS ☐ FAIL

---

## Summary

**Total Tests:** 23

**Results:**
- Passed: ___
- Failed: ___
- N/A: ___

**Critical Issues:**
```
(List any failures or concerns)
```

**Notes:**
```
(Additional observations)
```

**Tester:** _______________
**Date:** _______________
**System:** _______________

---

## Troubleshooting

### Input agent fails to start
- Check pyautogui installed: `pip list | grep pyautogui`
- Check X11/Wayland display: `echo $DISPLAY`
- Check logs: `tail /root/aurora_pro/logs/input_agent.log`

### CLI tasks timeout
- Verify `claude`/`codex` binaries in PATH
- Check binary permissions: `which claude && claude --version`
- Increase timeout in request

### Dashboard not loading
- Check Streamlit process: `ps aux | grep streamlit`
- Check port 8501 available: `netstat -tulpn | grep 8501`
- Restart: `./run_aurora.sh`

### Logs missing
- Check directory exists: `ls -la /root/aurora_pro/logs/`
- Check permissions: `ls -l /root/aurora_pro/logs/`
- Create if needed: `mkdir -p /root/aurora_pro/logs/tasks`

---

**End of Manual Test Plan**