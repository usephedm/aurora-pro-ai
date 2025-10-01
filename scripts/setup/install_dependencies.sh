#!/usr/bin/env bash
set -euo pipefail

echo "[deps] Installing system packages"
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    python3-venv python3-pip tesseract-ocr jq curl git
fi

echo "[deps] Creating venv and installing Python deps"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
python3 -m venv venv || true
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || true

echo "[deps] Done"

