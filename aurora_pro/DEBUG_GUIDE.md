# Aurora Pro Debugging Guide

## Overview
Aurora Pro is now configured with professional-grade debugging tools for Python development.

## Debugging Tools Installed
- **debugpy**: Microsoft's Python debugger adapter (VS Code, PyCharm, etc.)
- **pytest**: Production-grade testing framework with async support
- **pytest-asyncio**: Async test support for FastAPI components
- **ipdb**: Interactive Python debugger for CLI debugging

## Quick Start

### 1. Visual Studio Code Debugging

#### Launch Configurations Available
Press `F5` or use the Debug panel to select:

1. **Aurora Pro: FastAPI Server (Debug)** - Main server with hot reload
2. **Aurora Pro: FastAPI Server (No Reload)** - For breakpoint debugging
3. **Aurora Pro: Streamlit Dashboard** - Debug the dashboard UI
4. **Aurora Pro: CLI Agent Test** - Debug CLI agent functionality
5. **Aurora Pro: Integration Tests** - Debug pytest integration tests
6. **Aurora Pro: Attach to Running Server** - Connect to running debug server
7. **Aurora Pro: Current File** - Debug whatever file is open
8. **Aurora Pro: Browser Agent** - Debug browser automation
9. **Aurora Pro: Vision Agent** - Debug vision/OCR functionality

#### Using the Debug Server
```bash
# Start server with remote debugging enabled
cd /root/aurora_pro
source venv/bin/activate
python debug_server.py

# Server starts on port 8000
# Debugpy listens on port 5678
# In VS Code: Run "Aurora Pro: Attach to Running Server"
```

### 2. Command Line Debugging

#### Using ipdb (Interactive Debugger)
```python
# Add to any file where you want to break
import ipdb; ipdb.set_trace()

# Then run normally:
python main.py
```

#### Using pytest with debugging
```bash
cd /root/aurora_pro
source venv/bin/activate

# Run all tests with verbose output
pytest -v

# Run specific test file
pytest test_cli_agent.py -v

# Run with print statements visible
pytest test_integration.py -s

# Stop on first failure
pytest --maxfail=1

# Run tests matching pattern
pytest -k "test_health" -v

# Drop into debugger on failures
pytest --pdb

# Show local variables on failure
pytest -l
```

### 3. Remote Debugging from VS Code

#### Step 1: Start debug server
```bash
cd /root/aurora_pro
source venv/bin/activate
python debug_server.py
```

#### Step 2: In VS Code
1. Open `/root/aurora_pro` as workspace
2. Press `F5` or click Debug panel
3. Select "Aurora Pro: Attach to Running Server"
4. Set breakpoints in any `.py` file
5. Trigger code path (API call, test, etc.)

### 4. Debugging FastAPI Endpoints

#### Method A: Direct Launch (Recommended)
```bash
# In VS Code: Press F5 → "Aurora Pro: FastAPI Server (No Reload)"
# Set breakpoints in main.py, cli_agent.py, etc.
# Make API calls to trigger breakpoints
```

#### Method B: Attach to Running Server
```bash
# Terminal 1: Start debug server
python debug_server.py

# Terminal 2: Make API calls
curl http://localhost:8000/health
curl -X POST http://localhost:8000/cli/command \
  -H "Content-Type: application/json" \
  -d '{"prompt": "echo test", "agent": "claude"}'

# VS Code: Attach debugger, set breakpoints, retry API call
```

### 5. Debugging Async Code

Aurora Pro uses asyncio extensively. Key tips:

```python
# Use pytest-asyncio for async tests
import pytest

@pytest.mark.asyncio
async def test_cli_agent():
    result = await some_async_function()
    assert result == expected

# Debug async code in ipdb
import ipdb; ipdb.set_trace()
# Use 's' to step into async calls
# Use 'n' to step over
```

### 6. Debugging Browser Automation

```bash
# Browser agent requires X11 display
export DISPLAY=:0

# Run with debugging
# In VS Code: F5 → "Aurora Pro: Browser Agent"

# Or command line
python browser_agent.py
```

### 7. Environment Variables for Debugging

```bash
# Enable debug mode
export DEBUG=1

# Set Python path
export PYTHONPATH=/root/aurora_pro

# Display for GUI components
export DISPLAY=:0

# Increase verbosity
export LOG_LEVEL=DEBUG
```

## Debugging Common Issues

### Issue: Debugger won't attach
**Solution:**
```bash
# Check debugpy is installed
pip list | grep debugpy

# Verify port 5678 is not in use
lsof -i :5678

# Try different port in debug_server.py
debugpy.listen(("0.0.0.0", 5679))
```

### Issue: Breakpoints not hitting
**Solution:**
1. Ensure `justMyCode: false` in launch.json (already configured)
2. Check file paths match exactly
3. Verify code is actually running (add print statement)
4. Disable hot reload: Use "No Reload" launch config

### Issue: Async tests failing
**Solution:**
```bash
# Check pytest-asyncio installed
pip list | grep pytest-asyncio

# Verify pytest.ini has asyncio_mode = auto
cat pytest.ini | grep asyncio_mode

# Run with explicit async mode
pytest --asyncio-mode=auto
```

### Issue: Import errors in tests
**Solution:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/root/aurora_pro

# Or run pytest from project root
cd /root/aurora_pro
pytest
```

## Production Readiness Verification

### Pre-Production Checklist
```bash
cd /root/aurora_pro
source venv/bin/activate

# 1. Check dependencies
pip check
# Output: No broken requirements found. ✅

# 2. Verify configuration
cat config/operator_enabled.yaml
# operator_enabled: true ✅

# 3. Test imports
python -c "import main, cli_agent, browser_agent, vision_agent"
# No errors = ✅

# 4. Check services
curl -s http://0.0.0.0:8000/health | jq
# {"status":"healthy","database":"connected"} ✅

# 5. Run integration tests
pytest test_integration.py -v
# Tests pass ✅
```

### Production Debugging Best Practices

1. **Never use debugpy.wait_for_client() in production**
   - Server will hang waiting for debugger
   - Only use in local development

2. **Disable hot reload in production**
   - Use "No Reload" config or disable --reload flag
   - Hot reload can cause race conditions

3. **Use logging instead of print statements**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.debug("Debug message")
   logger.info("Info message")
   logger.error("Error message")
   ```

4. **Enable audit logging**
   - Already configured in `/root/aurora_pro/logs/`
   - CLI agent: `logs/cli_agent_audit.log`
   - Input agent: `logs/input_agent.log`
   - Heartbeat: `logs/heartbeat.log`

5. **Monitor health endpoints**
   ```bash
   # Component health
   curl http://0.0.0.0:8000/health/status | jq

   # Heartbeat monitoring
   curl http://0.0.0.0:8000/health/heartbeat | jq
   ```

## Advanced Debugging Techniques

### 1. Conditional Breakpoints
In VS Code, right-click breakpoint → Edit Breakpoint:
```python
# Break only when specific condition is true
task_id == "specific_task_123"
len(queue) > 10
error_count > 0
```

### 2. Logpoints (No-Stop Breakpoints)
Right-click line → Add Logpoint:
```
Processing task {task_id} with status {status}
```

### 3. Debug Console Evaluation
While paused at breakpoint, use Debug Console:
```python
# Inspect variables
task_id
len(history)

# Call functions
await some_async_function()

# Modify state
status = "completed"
```

### 4. Post-Mortem Debugging
```bash
# Run with post-mortem on crash
python -m pdb debug_server.py

# Or in pytest
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

### 5. Performance Profiling
```bash
# Profile with cProfile
python -m cProfile -o profile.stats debug_server.py

# Analyze results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# Or use py-spy (install first)
pip install py-spy
py-spy top --pid $(pgrep -f uvicorn)
```

## File Structure

```
/root/aurora_pro/
├── .vscode/
│   ├── launch.json          # Debug configurations
│   └── settings.json        # Editor settings
├── debug_server.py          # Debugpy-enabled server
├── pytest.ini               # Pytest configuration
├── DEBUG_GUIDE.md          # This file
├── logs/                   # Audit logs
│   ├── cli_agent_audit.log
│   ├── input_agent.log
│   ├── heartbeat.log
│   └── tasks/              # Per-task logs
├── config/
│   └── operator_enabled.yaml
└── [all other Aurora Pro files]
```

## Testing Commands Reference

```bash
# All tests
pytest

# Verbose with output
pytest -v -s

# Specific file
pytest test_cli_agent.py

# Specific test
pytest test_cli_agent.py::test_health_check

# With markers
pytest -m integration
pytest -m "not slow"

# Coverage report
pytest --cov=. --cov-report=html
firefox htmlcov/index.html

# Parallel execution (install pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Next Steps

1. **Start debugging immediately:**
   ```bash
   cd /root/aurora_pro
   source venv/bin/activate
   python debug_server.py
   ```

2. **Open VS Code:**
   ```bash
   code /root/aurora_pro
   ```

3. **Attach debugger:**
   - Press F5
   - Select "Aurora Pro: Attach to Running Server"

4. **Set breakpoints and test:**
   - Open `main.py`
   - Set breakpoint on line with `@app.get("/health")`
   - Run: `curl http://localhost:8000/health`
   - Breakpoint hits!

## Support

- Configuration files: `/root/aurora_pro/.vscode/`
- Logs: `/root/aurora_pro/logs/`
- Documentation: `/root/aurora_pro/*.md`
- Setup log: `/home/v/Desktop/codex_setup_log.txt`

**Aurora Pro is production-ready and debugging-enabled. Happy debugging! 🐛🔍**
