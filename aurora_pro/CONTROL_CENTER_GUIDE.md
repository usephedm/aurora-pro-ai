# Aurora Pro Control Center - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Web Control Panel](#web-control-panel)
4. [API Control Endpoints](#api-control-endpoints)
5. [Emergency Procedures](#emergency-procedures)
6. [Monitoring & Metrics](#monitoring--metrics)
7. [Task Submission](#task-submission)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Aurora Pro Control Center provides **real-time monitoring and control** of the entire autonomous AI system. It features:

- 📊 Live system metrics (CPU, RAM, GPU, Network)
- 🤖 Agent status dashboard
- 🚨 Emergency stop capability
- 📝 Task submission and tracking
- 📈 Performance analytics
- 🔍 Live reasoning display

---

## Quick Start

### 1. Start the API Server
```bash
cd /root/aurora_pro
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Launch the Web Control Panel
```bash
streamlit run web_control_panel.py --server.port 8501
```

### 3. Access the Control Panel
Open your browser and navigate to:
```
http://localhost:8501
```

### 4. Verify System Health
Check that all agents show as "Running" in the Agent Status section.

---

## Web Control Panel

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ⚙️ SIDEBAR                    📊 MAIN DASHBOARD            │
├─────────────────────┬───────────────────────────────────────┤
│                     │                                        │
│  🚨 EMERGENCY STOP  │  System Metrics:                      │
│  [BIG RED BUTTON]   │  ┌──────────┐  ┌──────────┐          │
│                     │  │ CPU Gauge│  │ RAM Gauge│          │
│  🔄 Restart System  │  └──────────┘  └──────────┘          │
│                     │                                        │
│  ───────────────    │  Agent Status:                        │
│                     │  ✅ LLM Orchestrator                   │
│  🔄 Refresh         │  ✅ Autonomous Engine                  │
│  ☑ Auto-refresh     │  ✅ Multicore Manager                 │
│  Interval: [2s]     │  ✅ Vision Agent                      │
│                     │  ✅ Cache Manager                     │
│  ───────────────    │  ...                                  │
│                     │                                        │
│  ℹ️ System Info      │  Recent Activity:                    │
│  Status: healthy    │  [timestamp] Task completed           │
│  Database: connected│  [timestamp] Vision analysis done     │
│                     │  [timestamp] Cache hit                │
└─────────────────────┴───────────────────────────────────────┘
```

### Key Features

#### 1. Emergency Stop Button
- **Location:** Top of sidebar
- **Color:** Red (impossible to miss)
- **Action:** Immediately halts ALL operations
- **Use when:**
  - System is behaving unexpectedly
  - Need to prevent further actions
  - Testing or maintenance required

**How to use:**
1. Click the "🛑 EMERGENCY STOP" button
2. Confirm the action (if prompted)
3. Wait for confirmation message
4. All agents will shut down within 2 seconds

#### 2. System Metrics

**CPU Gauge:**
- Green zone (0-50%): Normal operation
- Yellow zone (50-80%): High load
- Red zone (80-100%): Critical load

**Memory Gauge:**
- Shows current RAM usage
- Warning at 80%
- Critical at 90%

**Additional Metrics:**
- Memory Used (GB)
- Disk Usage (%)
- GPU Utilization (if available)
- Network I/O

#### 3. Agent Status Indicators
- ✅ Green checkmark = Running and healthy
- ❌ Red X = Stopped or failed
- ⚠️ Yellow warning = Degraded

**Agents monitored:**
- Multi-LLM Orchestrator
- Autonomous Engine
- Multicore Manager
- Cache Manager
- Vision Agent
- Stealth Browser
- Local Inference
- Proxy Manager

#### 4. Quick Actions
- **📸 Take Screenshot:** Capture current screen
- **🧹 Clear Cache:** Flush all cache tiers
- **📊 View Stats:** Open detailed statistics

#### 5. Task Submission Form

Submit autonomous tasks directly from the UI:

```
┌─────────────────────────────────────────────────┐
│ 📝 Submit Task                                  │
├─────────────────────────────────────────────────┤
│ Describe what you want Aurora to do:            │
│ ┌─────────────────────────────────────────────┐ │
│ │ Example: Research the top 5 AI coding      │ │
│ │ tools and create a comparison report       │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ Select LLM: [Auto (Intelligent Selection) ▼]   │
│                                                  │
│ Max Cost ($): [1.00]    Max Time (min): [10]   │
│                                                  │
│               [🚀 Submit Task]                   │
└─────────────────────────────────────────────────┘
```

**Fields:**
- **Task Description:** Natural language description
- **LLM:** Choose specific LLM or let system decide
- **Max Cost:** Budget constraint (in USD)
- **Max Time:** Time limit (in minutes)

#### 6. Statistics Tabs

**LLM Stats:**
- Total requests per provider
- Cost per provider
- Average latency
- Success rates

**Multicore Stats:**
- Workers active
- Tasks completed
- Queue depth
- Worker performance

**Cache Stats:**
- Hit/miss rates
- Memory usage
- Disk cache size
- Redis stats (if available)

**Vision Stats:**
- Screenshots taken
- OCR operations
- UI elements detected
- Average processing time

---

## API Control Endpoints

### System Control

#### Emergency Stop
```bash
curl -X POST http://localhost:8000/control/emergency-stop \
  -H "Content-Type: application/json" \
  -d '{"reason": "Manual intervention required"}'
```

**Response:**
```json
{
  "status": "stopped",
  "reason": "Manual intervention required"
}
```

#### Restart System
```bash
curl -X POST http://localhost:8000/control/restart
```

**Response:**
```json
{
  "status": "restarted"
}
```

### Monitoring

#### Get Current Metrics
```bash
curl http://localhost:8000/control/metrics
```

**Response:**
```json
{
  "system_health": "healthy",
  "emergency_stop_active": false,
  "metrics": {
    "cpu_percent": 25.3,
    "memory_percent": 45.2,
    "memory_used_gb": 3.6,
    "disk_percent": 55.1,
    "gpu_utilization": 12.5
  },
  "agents": {
    "llm_orchestrator": {
      "running": true,
      "health": "healthy",
      "tasks_active": 2,
      "tasks_completed": 125
    }
    // ... other agents
  },
  "uptime_seconds": 3625.5
}
```

#### Get Metrics History
```bash
curl "http://localhost:8000/control/metrics/history?minutes=5"
```

Returns last 5 minutes of metrics (1 per second = 300 data points).

#### Control Center Status
```bash
curl http://localhost:8000/control/status
```

**Response:**
```json
{
  "running": true,
  "emergency_stop_active": false,
  "websocket_clients": 3,
  "metrics_history_size": 300
}
```

---

## Emergency Procedures

### When to Trigger Emergency Stop

**Immediate Stop Required:**
- System is executing unwanted actions
- Infinite loop detected
- Resource exhaustion imminent
- Security concern identified
- Testing/maintenance needed

**How to Trigger:**

**Method 1: Web UI**
1. Open Control Panel (http://localhost:8501)
2. Click "🛑 EMERGENCY STOP" button in sidebar
3. Confirm action
4. Wait for "All systems halted" message

**Method 2: API**
```bash
curl -X POST http://localhost:8000/control/emergency-stop \
  -d '{"reason": "Security incident"}'
```

**Method 3: Terminal**
```bash
# If API is unresponsive, kill the process
pkill -f "uvicorn main:app"
```

### After Emergency Stop

**What happens:**
1. All active workflows immediately canceled
2. All agents shut down gracefully
3. WebSocket connections closed
4. No new tasks accepted
5. System enters safe mode

**To Resume:**
1. Investigate the issue
2. Fix any problems
3. Restart using:
   ```bash
   curl -X POST http://localhost:8000/control/restart
   ```
4. Or restart manually:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

---

## Monitoring & Metrics

### System Health Levels

**🟢 HEALTHY**
- All agents running
- CPU < 80%, RAM < 80%
- Error rate < 5%
- Response time < 200ms

**🟡 DEGRADED**
- Some agents slow
- CPU 80-95%, RAM 80-95%
- Error rate 5-20%
- Response time 200-500ms

**🔴 CRITICAL**
- Agents failing
- CPU > 95%, RAM > 95%
- Error rate > 20%
- Response time > 500ms

**⚫ STOPPED**
- Emergency stop active
- All agents halted

### Key Performance Indicators (KPIs)

Monitor these metrics:

1. **Agent Health:** All should be green (✅)
2. **CPU Usage:** Keep below 80%
3. **Memory Usage:** Keep below 80%
4. **Task Success Rate:** Aim for >95%
5. **Average Latency:** Keep below 200ms
6. **Error Rate:** Keep below 5%

### Alerts

Set up alerts for:
- CPU > 90% for 5 minutes
- Memory > 90% for 5 minutes
- Agent failure
- Error rate > 20%
- Emergency stop triggered

---

## Task Submission

### Submit Autonomous Task

**Via Web UI:**
1. Navigate to Control Panel
2. Scroll to "📝 Submit Task" section
3. Enter task description
4. Select LLM (or use Auto)
5. Set constraints
6. Click "🚀 Submit Task"

**Via API:**
```bash
curl -X POST http://localhost:8000/autonomous/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Research top 5 AI coding tools and create report",
    "max_actions": 50,
    "operator_user": "admin"
  }'
```

**Response:**
```json
{
  "workflow_id": "wf_20250930_143022_a3f2",
  "status": "executing",
  "total_actions": 12,
  "completed_actions": 0,
  "failed_actions": 0,
  "reasoning_chain": [
    "Analyzing request and creating execution plan...",
    "Created plan with 12 actions"
  ]
}
```

### Track Workflow Progress

```bash
curl http://localhost:8000/autonomous/workflow/{workflow_id}
```

### List Recent Workflows

```bash
curl "http://localhost:8000/autonomous/workflows?limit=20"
```

---

## Troubleshooting

### Issue: Control Panel Won't Load

**Symptoms:**
- Browser shows "Cannot connect"
- Page stuck loading

**Solutions:**
1. Verify API is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check Streamlit process:
   ```bash
   ps aux | grep streamlit
   ```

3. Restart Control Panel:
   ```bash
   pkill -f streamlit
   streamlit run web_control_panel.py --server.port 8501
   ```

### Issue: Emergency Stop Not Working

**Symptoms:**
- Button click has no effect
- System still executing tasks

**Solutions:**
1. Try API directly:
   ```bash
   curl -X POST http://localhost:8000/control/emergency-stop
   ```

2. If API unresponsive, force kill:
   ```bash
   pkill -9 -f "uvicorn main:app"
   ```

3. Restart system:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### Issue: Agents Showing as Stopped

**Symptoms:**
- Red X (❌) next to agent names
- Degraded or critical system health

**Solutions:**
1. Check logs:
   ```bash
   tail -f /root/aurora_pro/logs/*.log
   ```

2. Restart failed agent:
   ```bash
   # Via API (if available)
   curl -X POST http://localhost:8000/control/restart
   ```

3. Check dependencies:
   ```bash
   # Ollama for local inference
   systemctl status ollama

   # Redis for cache (optional)
   systemctl status redis
   ```

### Issue: High CPU/Memory Usage

**Symptoms:**
- Gauges in red zone
- System sluggish
- Timeouts

**Solutions:**
1. Check active workflows:
   ```bash
   curl http://localhost:8000/autonomous/workflows
   ```

2. Reduce multicore workers:
   - Default: 30 workers
   - Edit `main.py` line 175: `num_workers=15`

3. Clear cache:
   ```bash
   curl -X POST http://localhost:8000/cache/clear
   ```

4. Restart with fewer resources:
   ```bash
   # Reduce workers on restart
   # Edit main.py before restarting
   ```

### Issue: Tasks Failing

**Symptoms:**
- High error rate
- Tasks stuck in "executing"
- No progress

**Solutions:**
1. Check reasoning display:
   ```bash
   curl http://localhost:8000/reasoning/steps?limit=50
   ```

2. Check agent health:
   ```bash
   curl http://localhost:8000/control/metrics
   ```

3. Review workflow details:
   ```bash
   curl http://localhost:8000/autonomous/workflow/{id}
   ```

4. Check LLM API keys:
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $OPENAI_API_KEY
   ```

---

## Advanced Features

### WebSocket Real-Time Streaming

Connect to Control Center via WebSocket for real-time updates:

```python
import asyncio
import websockets
import json

async def monitor():
    uri = "ws://localhost:8000/ws/control"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Update: {data}")

asyncio.run(monitor())
```

### Custom Metrics Collection

Add custom metrics to the dashboard:

```python
# In your code
from control_center import get_control_center

control = get_control_center()
# Metrics automatically collected by background loop
```

### Programmatic Control

Control system programmatically:

```python
import asyncio
from control_center import get_control_center

async def main():
    control = get_control_center()
    await control.start()

    # Get current status
    status = await control._collect_full_status()
    print(f"System health: {status['system_health']}")

    # Emergency stop if needed
    if status['system_health'] == 'critical':
        await control.emergency_stop("Auto-triggered due to critical health")

    await control.stop()

asyncio.run(main())
```

---

## Best Practices

### 1. Monitor Regularly
- Check Control Panel at least once per hour
- Set up automated health checks
- Enable notifications for critical events

### 2. Use Emergency Stop Wisely
- Test emergency stop regularly
- Document when and why you trigger it
- Always investigate root cause

### 3. Resource Management
- Monitor CPU/RAM trends
- Adjust worker counts based on load
- Clear cache periodically

### 4. Task Organization
- Use descriptive task names
- Set appropriate time/cost limits
- Review completed workflows

### 5. Security
- Limit access to Control Panel
- Use strong API authentication
- Monitor for suspicious activity

---

## Keyboard Shortcuts

When Control Panel has focus:

- `R` - Manual refresh
- `E` - Toggle emergency stop confirmation
- `S` - Jump to statistics
- `T` - Focus task submission form
- `Esc` - Close modals

---

## Getting Help

### Documentation
- Full System Audit Report: `FULL_SYSTEM_AUDIT_REPORT.md`
- Production Deployment: `PRODUCTION_DEPLOYMENT.md`
- API Documentation: http://localhost:8000/docs

### Logs Location
```
/root/aurora_pro/logs/
├── control_center.log
├── llm_orchestrator.log
├── autonomous_engine.log
├── reasoning.log
├── multicore_manager.log
└── ... (other agent logs)
```

### Support
- GitHub Issues: (your-repo-url)
- Email: support@aurora-pro.ai
- Documentation: https://aurora-pro.ai/docs

---

**Last Updated:** 2025-09-30
**Version:** Aurora Pro 2.0.0
**Status:** Production Ready