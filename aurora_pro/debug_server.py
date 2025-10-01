#!/usr/bin/env python3
"""
Aurora Pro Debug Server
Starts FastAPI with debugpy enabled for remote debugging
"""
import debugpy
import uvicorn
import sys
from pathlib import Path

# Enable debugpy on port 5678
debugpy.listen(("0.0.0.0", 5678))
print("⚙️  Debugpy listening on 0.0.0.0:5678", file=sys.stderr)
print("🔌 Attach your debugger to continue...", file=sys.stderr)
print("💡 In VS Code: Run 'Aurora Pro: Attach to Running Server'", file=sys.stderr)

# Uncomment to wait for debugger to attach before starting
# print("⏸️  Waiting for debugger to attach...", file=sys.stderr)
# debugpy.wait_for_client()
# print("✅ Debugger attached!", file=sys.stderr)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True
    )
