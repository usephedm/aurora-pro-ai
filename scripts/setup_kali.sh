#!/usr/bin/env bash
set -euo pipefail

echo "[kali] System optimization and prerequisites"

if [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
  echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null || true
fi

sudo sysctl -w vm.swappiness=10 || true
sudo systemctl disable bluetooth cups avahi-daemon 2>/dev/null || true

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    python3-venv python3-pip tesseract-ocr jq curl git redis-server
fi

echo "[kali] Done"

