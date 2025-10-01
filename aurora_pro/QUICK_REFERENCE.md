# Aurora Pro - Quick Reference Card

## 🚀 Start System

```bash
cd /root/aurora_pro
source venv/bin/activate
./run_aurora.sh
```

**Endpoints:**
- API: `http://0.0.0.0:8000`
- Dashboard: `http://localhost:8501`
- API Docs: `http://0.0.0.0:8000/docs`

---

## 🎛️ Enable Input Control

```bash
vi config/operator_enabled.yaml
```

Set:
```yaml
operator_enabled: true
features:
  control_mouse_keyboard: true
```

---

## 🧪 Run Tests

```bash
# Comprehensive tests
python test_input_agent_comprehensive.py

# Integration tests
python test_integration.py

# Original tests
python test_cli_agent.py
python test_input_agent.py
```

---

## 📊 Health Monitoring

```bash
# Full health check
curl http://0.0.0.0:8000/health/status | jq

# Heartbeat status
curl http://0.0.0.0:8000/health/heartbeat | jq

# Watch logs
tail -f logs/heartbeat.log
tail -f logs/recovery_events.log
tail -f logs/input_agent.log
tail -f logs/cli_agent_audit.log
```

---

## 🤖 Submit CLI Task

```bash
curl -X POST http://0.0.0.0:8000/cli/command \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your prompt here",
    "agent": "claude",
    "timeout": 120,
    "metadata": {"operator_user": "username"}
  }'
```

**Check status:**
```bash
curl http://0.0.0.0:8000/cli/status | jq
```

---

## 🖱️ Submit Input Task

```bash
# Mouse move
curl -X POST http://0.0.0.0:8000/input/submit \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "move_to",
    "parameters": {"x": 500, "y": 500, "duration": 1.0},
    "operator_user": "username"
  }'

# Type text
curl -X POST http://0.0.0.0:8000/input/submit \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "type_text",
    "parameters": {"text": "Hello World", "interval": 0.05}
  }'

# Hotkey (Ctrl+C)
curl -X POST http://0.0.0.0:8000/input/submit \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "hotkey",
    "parameters": {"keys": ["ctrl", "c"]}
  }'
```

**Check status:**
```bash
curl http://0.0.0.0:8000/input/status | jq
```

---

## 📁 Log Locations

| Log File | Purpose |
|----------|---------|
| `logs/cli_agent_audit.log` | CLI task audit trail (JSONL) |
| `logs/codex_activity.log` | Codex structured activity (JSONL) |
| `logs/input_agent.log` | Input actions audit (JSONL) |
| `logs/heartbeat.log` | Periodic health snapshots (JSONL) |
| `logs/recovery_events.log` | Recovery events only (JSONL) |
| `logs/tasks/{task_id}.log` | Per-task detailed logs |

---

## 🔍 Check Specific Task

```bash
# CLI task
TASK_ID="<task_id>"
cat logs/tasks/$TASK_ID.log

# Input task
TASK_ID="<task_id>"
curl http://0.0.0.0:8000/input/task/$TASK_ID | jq
```

---

## 🛑 Emergency Stop

**Input Agent Failsafe:**
- Move mouse to top-left corner (0,0)
- PyAutoGUI will abort current action

**Stop System:**
```bash
# Find processes
ps aux | grep -E "uvicorn|streamlit"

# Kill gracefully
pkill -INT uvicorn
pkill -INT streamlit

# Or use Ctrl+C in terminal running ./run_aurora.sh
```

---

## 🔧 Troubleshooting

### Input agent not working
```bash
# Check pyautogui
pip list | grep pyautogui

# Check display
echo $DISPLAY

# Check logs
tail -20 logs/input_agent.log
```

### CLI tasks timing out
```bash
# Check binary
which claude
claude --version

# Increase timeout in request
"timeout": 300
```

### Dashboard not loading
```bash
# Check port
netstat -tulpn | grep 8501

# Restart
./run_aurora.sh
```

---

## 📖 Documentation

- `STAGE3_COMPLETE.md` - Full technical details
- `MANUAL_TEST_PLAN.md` - 23 test cases
- `IMPLEMENTATION_COMPLETE.md` - Stages 1 & 2
- `README.md` - General usage

---

## 🎯 Common Actions

### View Recent Tasks
```bash
curl http://0.0.0.0:8000/cli/logs?limit=10 | jq
curl http://0.0.0.0:8000/input/status | jq '.recent_tasks'
```

### Monitor Errors
```bash
grep '"error"' logs/input_agent.log | tail -5
grep '"status":"error"' logs/cli_agent_audit.log | tail -5
```

### Check System Uptime
```bash
curl http://0.0.0.0:8000/health/heartbeat | jq '.uptime_seconds'
```

### View Recovery Events
```bash
tail -10 logs/recovery_events.log | jq
```

---

## ⚙️ Configuration

**File:** `config/operator_enabled.yaml`

```yaml
operator_enabled: false  # Set to true to enable features

features:
  autonomous_browsing: false
  web_summarization: false
  auto_dependency_install: false
  mcp_extensions: false
  self_evolving_toolchain: false
  internet_access: false
  control_mouse_keyboard: false  # Set to true for input control
```

---

## 🚨 Safety Notes

1. **Input Control**
   - DISABLED by default
   - Requires explicit config flag
   - Move mouse to corner (0,0) to abort

2. **CLI Tasks**
   - 300s timeout enforced
   - 1 task per agent max concurrency
   - Shell-safe command construction

3. **Audit Trail**
   - All actions logged
   - operator_user tracked
   - Full JSONL audit logs

---

## 📞 Quick Help

**Test if system is running:**
```bash
curl http://0.0.0.0:8000/health
```

**Get component health:**
```bash
curl http://0.0.0.0:8000/health/status | jq '.components'
```

**Submit simple test task:**
```bash
curl -X POST http://0.0.0.0:8000/cli/command \
  -H "Content-Type: application/json" \
  -d '{"prompt": "echo test", "agent": "claude", "timeout": 10}'
```

---

**Aurora Pro v1.0 - Stage 3**
**System Engineer: Claude (Anthropic)**
**Status: ✅ PRODUCTION READY**