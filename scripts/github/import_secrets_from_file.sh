#!/usr/bin/env bash
set -euo pipefail

# Import KEY=VALUE pairs from a file into GitHub repository secrets using gh CLI.
# Usage:
#   OWNER=usephedm REPO=aurora-pro-ai FILE=/home/v/Desktop/credz.md ./scripts/github/import_secrets_from_file.sh

OWNER="${OWNER:?set OWNER}"
REPO="${REPO:?set REPO}"
FILE="${FILE:?set FILE}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not installed. Install from https://cli.github.com/ and run 'gh auth login'." >&2
  exit 2
fi

if [ ! -f "$FILE" ]; then
  echo "Input file not found: $FILE" >&2
  exit 3
fi

echo "Importing secrets into $OWNER/$REPO from $FILE"

# Read only lines of the form KEY=VALUE with uppercase keys.
while IFS= read -r line; do
  [ -z "$line" ] && continue
  case "$line" in 
    \#*) continue;;
  esac
  if echo "$line" | grep -qE '^[A-Z0-9_]+=.+$'; then
    key="$(printf '%s' "$line" | cut -d= -f1)"
    val="$(printf '%s' "$line" | cut -d= -f2- )"
    # Do not echo value; pass via stdin
    printf '%s' "$val" | gh secret set "$key" -R "$OWNER/$REPO" -b-
    echo "Set secret: $key"
  fi
done < "$FILE"

echo "Done. Verify at https://github.com/$OWNER/$REPO/settings/secrets/actions"

