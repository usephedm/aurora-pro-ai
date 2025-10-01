#!/usr/bin/env bash
# Quick Reference for Aurora Pro AI Secrets Management

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔐 Aurora Pro AI - Secrets Management Quick Reference"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

ACTION="${1:-menu}"

case "$ACTION" in
  import)
    echo "📥 Import secrets from file to OS keyring..."
    FILE="${2:-/home/v/Desktop/credz.md}"
    if [ ! -f "$FILE" ]; then
      echo "❌ File not found: $FILE"
      echo "Usage: $0 import /path/to/credz.md"
      exit 1
    fi
    FILE="$FILE" bash scripts/setup/import_local_secrets.sh
    ;;
    
  wizard)
    echo "🧙 Running secret wizard to prompt for missing keys..."
    PYTHONPATH="$(pwd)" python3 scripts/setup/secret_wizard.py
    ;;
    
  get)
    KEY="${2:?Usage: $0 get KEY_NAME}"
    echo "🔑 Retrieving secret: $KEY"
    PYTHONPATH="$(pwd)" python3 -c "from aurora_pro.secrets_loader import get_secret; v = get_secret('$KEY'); print(v if v else '(not set)')"
    ;;
    
  set)
    KEY="${2:?Usage: $0 set KEY_NAME value}"
    VALUE="${3:?Usage: $0 set KEY_NAME value}"
    echo "💾 Storing secret: $KEY"
    PYTHONPATH="$(pwd)" python3 -c "from aurora_pro.secrets_loader import set_secret; set_secret('$KEY', '$VALUE'); print('✓ Stored')"
    ;;
    
  list)
    echo "📋 Checking status of required secrets..."
    PYTHONPATH="$(pwd)" python3 << 'PY'
from aurora_pro.secrets_loader import get_secret
import yaml

with open('configs/required_secrets.yaml') as f:
    data = yaml.safe_load(f)
    
for item in data.get('secrets', []):
    key = item['key']
    required = item.get('required', False)
    val = get_secret(key)
    status = '✓' if val else '✗'
    req_marker = '(required)' if required else '(optional)'
    print(f'{status} {key:25s} {req_marker}')
PY
    ;;
    
  github-push)
    echo "🚀 Pushing to GitHub..."
    echo "⚠️  Note: This requires a GitHub token with 'repo' scope"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Cancelled."
      exit 0
    fi
    export OWNER=usephedm REPO=aurora-pro-ai
    PYTHONPATH="$(pwd)" GITHUB_TOKEN=$(python3 -c "from aurora_pro.secrets_loader import get_secret; print(get_secret('GITHUB_TOKEN'))") \
      bash scripts/github/create_repo_and_push.sh
    ;;
    
  github-secrets)
    echo "📤 Importing secrets to GitHub Actions..."
    echo "⚠️  Note: This requires a GitHub token with 'workflow' scope"
    FILE="${2:-/tmp/credz_formatted.txt}"
    if [ ! -f "$FILE" ]; then
      echo "❌ File not found: $FILE"
      echo "Usage: $0 github-secrets /path/to/credz.txt"
      exit 1
    fi
    export OWNER=usephedm REPO=aurora-pro-ai
    FILE="$FILE" bash scripts/github/import_secrets_from_file.sh
    ;;
    
  verify)
    echo "🔍 Verification Report"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "1. Secrets in keyring:"
    $0 list
    echo
    echo "2. .env file status:"
    if [ -f .env ]; then
      echo "   ✓ Exists ($(wc -l < .env) keys)"
      echo "   Sample: $(head -1 .env)"
    else
      echo "   ✗ Not found"
    fi
    echo
    echo "3. GitHub CLI:"
    if gh auth status 2>/dev/null | grep -q "Logged in"; then
      echo "   ✓ Authenticated ($(gh auth status 2>&1 | grep account | awk '{print $5}'))"
    else
      echo "   ✗ Not authenticated"
    fi
    echo
    echo "4. Git status:"
    echo "   $(git status --porcelain | wc -l) uncommitted changes"
    echo
    ;;
    
  menu|*)
    echo "Available commands:"
    echo
    echo "  📥 import [file]       Import KEY=VALUE pairs from file to keyring"
    echo "  🧙 wizard              Prompt for missing required secrets"
    echo "  🔑 get <KEY>           Retrieve a secret value"
    echo "  💾 set <KEY> <value>   Store a secret"
    echo "  📋 list                Show status of all required secrets"
    echo "  🔍 verify              Run full verification check"
    echo "  🚀 github-push         Create/push repo to GitHub"
    echo "  📤 github-secrets [f]  Import secrets to GitHub Actions"
    echo
    echo "Examples:"
    echo "  $0 import /home/v/Desktop/credz.md"
    echo "  $0 wizard"
    echo "  $0 get GITHUB_TOKEN"
    echo "  $0 set NEW_KEY 'secret-value'"
    echo "  $0 list"
    echo "  $0 verify"
    echo
    echo "For detailed documentation, see: SECRETS_SETUP_COMPLETE.md"
    ;;
esac
