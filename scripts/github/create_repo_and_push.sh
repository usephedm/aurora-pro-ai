#!/usr/bin/env bash
set -euo pipefail

# Usage: OWNER=usephedm REPO=aurora-pro-ai GITHUB_TOKEN=xxxx scripts/github/create_repo_and_push.sh

OWNER="${OWNER:?set OWNER}"
REPO="${REPO:?set REPO}"
TOKEN="${GITHUB_TOKEN:?set GITHUB_TOKEN}"

API="https://api.github.com"

echo "[github] Creating repo $OWNER/$REPO (if not exists)"
status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOKEN" "$API/repos/$OWNER/$REPO" || true)
if [ "$status" != "200" ]; then
  curl -s -H "Authorization: token $TOKEN" \
       -H "Accept: application/vnd.github+json" \
       -d "{\"name\":\"$REPO\",\"private\":false}" \
       "$API/user/repos" >/dev/null
  echo "[github] Created $OWNER/$REPO"
else
  echo "[github] Repo exists"
fi

git remote remove origin >/dev/null 2>&1 || true
git remote add origin "https://github.com/$OWNER/$REPO.git"
git push -u origin main

echo "[github] Pushed main to $OWNER/$REPO"

