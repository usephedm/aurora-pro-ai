#!/usr/bin/env bash

cat << 'INSTRUCTIONS'

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║           🔑 GITHUB TOKEN CREATION - STEP BY STEP GUIDE 🔑                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

The current token lacks write permissions. Follow these steps to create a new one:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METHOD 1: CREATE CLASSIC TOKEN (RECOMMENDED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Open in browser: https://github.com/settings/tokens/new

2. Fill in the form:
   Note: "Aurora Pro AI - Full Access"
   Expiration: 90 days (or your preference)
   
3. Select these scopes:
   ✓ repo (Full control of private repositories)
   ✓ workflow (Update GitHub Action workflows)
   ✓ admin:repo_hook (Full control of repository hooks)
   ✓ delete_repo (Delete repositories)
   
4. Click "Generate token"

5. COPY THE TOKEN (you'll only see it once!)

6. Store it securely:
   cd /root/aurora-pro-ai
   ./SECRETS_QUICKREF.sh set GITHUB_TOKEN ghp_your_new_token_here

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METHOD 2: USE DEVICE CODE FLOW (ALTERNATIVE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run this command and follow the prompts:
   
   cd /root/aurora-pro-ai
   bash scripts/auth/gh_login.sh

   This will:
   - Show you a device code
   - Open browser to https://github.com/login/device
   - Grant full permissions automatically

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AFTER GETTING THE TOKEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Store the new token:
   ./SECRETS_QUICKREF.sh set GITHUB_TOKEN <your_new_token>

2. Authenticate gh CLI:
   echo "<your_new_token>" | gh auth login --with-token

3. Push to GitHub:
   git push -u origin main --force

4. Verify push succeeded:
   gh repo view usephedm/aurora-pro-ai

5. Import secrets to GitHub Actions:
   ./SECRETS_QUICKREF.sh github-secrets /path/to/credz.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUICK ONE-LINER (after you have the token):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOKEN="ghp_your_token_here"
./SECRETS_QUICKREF.sh set GITHUB_TOKEN $TOKEN && \
echo $TOKEN | gh auth login --with-token && \
git push -u origin main --force && \
echo "✅ Successfully pushed to GitHub!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTRUCTIONS

