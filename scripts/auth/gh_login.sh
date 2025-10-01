#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI not installed. See https://cli.github.com/" >&2
  exit 2
fi

if gh auth status >/dev/null 2>&1; then
  echo "gh already authenticated"
else
  gh auth login -h github.com --web
fi

gh auth status || exit 1
echo "✅ gh auth ready"

