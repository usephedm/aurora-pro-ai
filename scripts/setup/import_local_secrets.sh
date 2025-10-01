#!/usr/bin/env bash
set -euo pipefail

# Import KEY=VALUE pairs from file to OS keyring and .env placeholders.
# Usage: FILE=/home/v/Desktop/credz.md scripts/setup/import_local_secrets.sh

FILE="${FILE:?set FILE}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ ! -f "$FILE" ]; then
  echo "Input file not found: $FILE" >&2
  exit 2
fi

python3 - <<'PY'
import os, sys
from pathlib import Path
from aurora_pro.secrets_loader import set_secret

file = os.environ.get('FILE')
env_lines = []
with open(file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        # Store safely in keyring
        try:
            set_secret(k, v)
            print(f"stored:{k}")
        except Exception as e:
            print(f"warn: failed to store {k}: {e}", file=sys.stderr)
        env_lines.append(f"{k}=")

repo = Path(os.environ.get('ROOT_DIR', '.'))
out = repo / '.env'
try:
    out.write_text('\n'.join(env_lines) + '\n')
    print(f"wrote:{out}")
except Exception as e:
    print(f"warn: failed writing .env: {e}", file=sys.stderr)
PY

echo "Done. Values saved in OS keyring; .env placeholders written."

