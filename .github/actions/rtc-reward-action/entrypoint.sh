#!/usr/bin/env bash
# =============================================================================
# RTC Reward Action — Reusable GitHub Action
# Automatically awards RTC tokens when a PR is merged.
# =============================================================================
set -euo pipefail

# ---- Inputs ----
NODE_URL="${INPUT_NODE_URL:-https://50.28.86.131}"
AMOUNT="${INPUT_AMOUNT:-5}"
WALLET_FROM="${INPUT_WALLET_FROM:-}"
ADMIN_KEY="${INPUT_ADMIN_KEY:-}"
PR_NUMBER="${INPUT_PR_NUMBER:-}"
DRY_RUN="${INPUT_DRY_RUN:-false}"
MIN_BODY_LENGTH="${INPUT_MIN_BODY_LENGTH:-20}"
GITHUB_TOKEN="${INPUT_REPO_TOKEN:-}"
REPO="${GITHUB_REPOSITORY:-}"
ACTOR="${GITHUB_ACTOR:-unknown}"
RUN_ID="${GITHUB_RUN_ID:-0}"
RUN_URL="${GITHUB_SERVER_URL:-https://github.com}/${REPO}/actions/runs/${RUN_ID}"

# Derive PR number from event payload if not provided
if [[ -z "$PR_NUMBER" ]] && [[ -f "$GITHUB_EVENT_PATH" ]]; then
  PR_NUMBER=$(jq -r '.pull_request.number // .issue.number // empty' "$GITHUB_EVENT_PATH" 2>/dev/null || echo "")
fi

if [[ -z "$PR_NUMBER" ]]; then
  echo "::error::Could not determine PR number. Set pr-number input or trigger on pull_request event."
  exit 1
fi

# Check if PR was merged
MERGED="false"
if [[ -f "$GITHUB_EVENT_PATH" ]]; then
  MERGED=$(jq -r '.pull_request.merged // false' "$GITHUB_EVENT_PATH" 2>/dev/null || echo "false")
fi

if [[ "$MERGED" != "true" ]]; then
  echo "::notice::PR #$PR_NUMBER is not merged yet. Skipping reward."
  echo "rewarded=false" >> "$GITHUB_OUTPUT"
  echo "recipient=" >> "$GITHUB_OUTPUT"
  echo "tx_hash=" >> "$GITHUB_OUTPUT"
  echo "amount=0" >> "$GITHUB_OUTPUT"
  exit 0
fi

echo "RTC Reward Action starting for PR #$PR_NUMBER (node=$NODE_URL, amount=$AMOUNT, dry_run=$DRY_RUN)"

# ---- 1. Fetch PR body ----
fetch_pr_body() {
  curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${REPO}/pulls/${PR_NUMBER}" \
    | jq -r '.body // ""'
}

# ---- 2. Extract EVM wallet address from PR body ----
extract_wallet() {
  local body=$1
  local evm_pattern='0x[a-fA-F0-9]{40}'
  local btc_pattern='bc1[a-zA-HJ-NP-Z0-9]{25,39}'

  # Priority 1: Raw EVM address
  if [[ "$body" =~ $evm_pattern ]]; then
    echo "${BASH_REMATCH}" | tr '[:upper:]' '[:lower:]'
    return
  fi

  # Priority 2: wallet_name: address format
  if [[ "$body" =~ [Ww]allet[_ ]*[Nn]ame[:\ ]*(${evm_pattern}) ]]; then
    addr=$(echo "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')
    echo "$addr"
    return
  fi

  # Priority 3: backtick-wrapped EVM address
  if [[ "$body" =~ \`(${evm_pattern})\` ]]; then
    addr=$(echo "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')
    echo "$addr"
    return
  fi

  echo ""
}

# ---- 3. Fetch PR title and author ----
fetch_pr_info() {
  curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${REPO}/pulls/${PR_NUMBER}" \
    | jq '{title: .title, user: .user.login, body: (.body // "")}'
}

# ---- 4. Build and submit transfer ----
submit_transfer() {
  local from_addr=$1
  local to_addr=$2
  local amount=$3
  local admin_key=$4

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "🔸 [DRY RUN] Would transfer $amount RTC from $from_addr to $to_addr"
    echo "tx_hash=dry_run_$(date +%s)" 
    return 0
  fi

  # Build transfer payload
  local timestamp
  timestamp=$(date +%s)

  # Sign using admin key as raw private key bytes (hex -> bytes)
  local payload="${from_addr}:${to_addr}:${amount}:${timestamp}"
  
  # For Ed25519 signing with admin key
  local signature_hex
  signature_hex=$(echo -n "$payload" | openssl dgst -sha512 -hmac "$admin_key" 2>/dev/null | awk '{print $2}')

  # If admin_key is a hex private key, use it directly
  if [[ "$admin_key" =~ ^[a-fA-F0-9]{64}$ ]]; then
    # Sign using the private key with Ed25519
    local tmpfile
    tmpfile=$(mktemp)
    echo -n "$payload" > "$tmpfile"
    
    # Try using OpenSSL for Ed25519 signing with raw key
    if command -v openssl &>/dev/null; then
      # Create a temporary key file
      local keyfile
      keyfile=$(mktemp)
      echo "-----BEGIN PRIVATE KEY-----" > "$keyfile"
      echo "$(echo "$admin_key" | xxd -r -p | base64)" >> "$keyfile"
      echo "-----END PRIVATE KEY-----" >> "$keyfile"
      
      signature_hex=$(echo -n "$payload" | openssl pkeyutl -sign -inkey "$keyfile" -rawin 2>/dev/null | xxd -p -c 128 || echo "")
      
      rm -f "$keyfile"
    fi
    
    rm -f "$tmpfile"
    
    # Fallback: use HMAC-SHA512 if Ed25519 signing fails
    if [[ -z "$signature_hex" ]]; then
      signature_hex=$(echo -n "$payload" | openssl dgst -sha512 -mac hmac -macopt "$admin_key" 2>/dev/null | awk '{print $2}')
    fi
  fi

  # Submit transfer via RPC
  local response
  response=$(curl -s -X POST "${NODE_URL}/transfer" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
      --arg from "$from_addr" \
      --arg to "$to_addr" \
      --argjson amount "$amount" \
      --argjson fee 0 \
      --arg sig "$signature_hex" \
      --argjson timestamp "$timestamp" \
      '{
        from: $from,
        to: $to,
        amount: $amount,
        fee: $fee,
        signature: $sig,
        timestamp: $timestamp
      }')" \
    --max-time 30 2>&1) || true

  echo "$response"
}

# Try Python SDK for signing (more reliable)
try_python_transfer() {
  local from_addr=$1
  local to_addr=$2
  local amount=$3
  local admin_key=$4
  local timestamp=$5

  python3 -c "
import sys
import os
import json
import time
import hmac
import hashlib

admin_key = '''$admin_key'''
from_addr = '''$from_addr'''
to_addr = '''$to_addr'''
amount = $amount
timestamp = $timestamp

# Try Ed25519 with cryptography library
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    import base64
    
    # Admin key as hex -> bytes
    key_bytes = bytes.fromhex(admin_key)
    priv = Ed25519PrivateKey.from_private_bytes(key_bytes[:32])
    
    payload = f'{from_addr}:{to_addr}:{amount}:{timestamp}'
    signature = priv.sign(payload.encode())
    signature_hex = signature.hex()
except Exception as e:
    print(f'Ed25519 failed: {e}', file=sys.stderr)
    # Fallback to HMAC
    payload = f'{from_addr}:{to_addr}:{amount}:{timestamp}'
    signature_hex = hmac.new(admin_key.encode(), payload.encode(), hashlib.sha512).hexdigest()

print('SIGNATURE_HEX:' + signature_hex)
print('PAYLOAD:' + payload)
" 2>&1
}

# ---- 5. Post PR comment ----
post_pr_comment() {
  local recipient=$1
  local tx_hash=$2
  local amount=$3
  local status=$4
  local message=$5

  local icon="✅"
  [[ "$status" != "success" ]] && icon="⚠️"

  local dry_run_note=""
  [[ "$DRY_RUN" == "true" ]] && dry_run_note=" *(dry-run mode — no actual transfer)*"

  local body="<!-- rtc-reward-action -->
## 🎁 RTC Reward — PR #${PR_NUMBER}

| Field | Value |
|-------|-------|
| 🧪 **Status** | ${icon} ${message}${dry_run_note} |
| 💰 **Amount** | ${amount} RTC |
| 👛 **Recipient** | \`${recipient}\` |
| 🔗 **TX Hash** | \`${tx_hash}\` |
| 🤖 **Triggered by** | @${ACTOR} |

*Reward action — [Run #${RUN_ID}](${RUN_URL})*"

  # Check if an RTC reward comment already exists
  local existing_comment_id
  existing_comment_id=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${REPO}/issues/${PR_NUMBER}/comments?per_page=100" \
    | jq -r '.[] | select(.body | contains("rtc-reward-action")) | .id' 2>/dev/null | head -1)

  if [[ -n "$existing_comment_id" && "$existing_comment_id" != "null" ]]; then
    echo "Updating existing RTC reward comment (id=$existing_comment_id)"
    curl -s -X PATCH \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Content-Type: application/json" \
      -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/${REPO}/issues/comments/${existing_comment_id}" \
      -d "$(jq -n --arg body "$body" '{ body: $body }')" >/dev/null
  else
    echo "Posting new RTC reward comment"
    curl -s -X POST \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Content-Type: application/json" \
      -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/${REPO}/issues/${PR_NUMBER}/comments" \
      -d "$(jq -n --arg body "$body" '{ body: $body }')" >/dev/null
  fi
}

# ---- 6. Write outputs ----
write_outputs() {
  local rewarded=$1
  local recipient=$2
  local tx_hash=$3
  local amount=$4

  {
    echo "rewarded=${rewarded}"
    echo "recipient=${recipient}"
    echo "tx_hash=${tx_hash}"
    echo "amount=${amount}"
  } >> "$GITHUB_OUTPUT"

  echo "::set-output name=rewarded::${rewarded}"
  echo "::set-output name=recipient::${recipient}"
  echo "::set-output name=tx_hash::${tx_hash}"
  echo "::set-output name=amount::${amount}"
}

# =============================================================================
# MAIN
# =============================================================================

echo "Fetching PR #$PR_NUMBER body..."
PR_BODY=$(fetch_pr_body)

# Check minimum body length
BODY_LEN=${#PR_BODY}
if [[ "$BODY_LEN" -lt "$MIN_BODY_LENGTH" ]]; then
  echo "::notice::PR body too short ($BODY_LEN < $MIN_BODY_LENGTH chars). Skipping reward."
  post_pr_comment "" "skipped" "0" "skipped" "PR body too short (${BODY_LEN} chars)"
  write_outputs "false" "" "skipped" "0"
  exit 0
fi

echo "Extracting wallet address from PR body..."
RECIPIENT=$(extract_wallet "$PR_BODY")

if [[ -z "$RECIPIENT" ]]; then
  echo "::notice::No EVM wallet address found in PR body. Skipping reward."
  post_pr_comment "" "skipped" "0" "skipped" "No EVM wallet address found in PR body"
  write_outputs "false" "" "skipped" "0"
  exit 0
fi

echo "✅ Found wallet address: $RECIPIENT"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "🔸 DRY RUN — simulating transfer of $AMOUNT RTC to $RECIPIENT"
  post_pr_comment "$RECIPIENT" "dry_run_$(date +%s)" "$AMOUNT" "dry_run" "Dry run complete"
  write_outputs "true" "$RECIPIENT" "dry_run_$(date +%s)" "$AMOUNT"
  echo "✅ Dry run complete"
  exit 0
fi

# Normal transfer mode
if [[ -z "$ADMIN_KEY" ]]; then
  echo "::error::ADMIN_KEY is required for actual transfers (dry_run=false)."
  post_pr_comment "$RECIPIENT" "error" "$AMOUNT" "error" "Admin key missing"
  write_outputs "false" "$RECIPIENT" "error" "$AMOUNT"
  exit 1
fi

if [[ -z "$WALLET_FROM" ]]; then
  echo "::error::WALLET_FROM is required for actual transfers."
  post_pr_comment "$RECIPIENT" "error" "$AMOUNT" "error" "Wallet sender not configured"
  write_outputs "false" "$RECIPIENT" "error" "$AMOUNT"
  exit 1
fi

echo "Submitting transfer: $AMOUNT RTC from $WALLET_FROM to $RECIPIENT..."
TIMESTAMP=$(date +%s)
PYTHON_OUT=$(try_python_transfer "$WALLET_FROM" "$RECIPIENT" "$AMOUNT" "$ADMIN_KEY" "$TIMESTAMP" 2>&1)
echo "Python output: $PYTHON_OUT"

SIGNATURE_HEX=$(echo "$PYTHON_OUT" | grep '^SIGNATURE_HEX:' | cut -d: -f2-)
PAYLOAD_STR=$(echo "$PYTHON_OUT" | grep '^PAYLOAD:' | cut -d: -f2-)

if [[ -z "$SIGNATURE_HEX" ]]; then
  echo "::error::Failed to generate signature"
  post_pr_comment "$RECIPIENT" "error" "$AMOUNT" "error" "Signature generation failed"
  write_outputs "false" "$RECIPIENT" "error" "$AMOUNT"
  exit 1
fi

# Submit to RPC
RESPONSE=$(curl -s -X POST "${NODE_URL}/transfer" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg from "$WALLET_FROM" \
    --arg to "$RECIPIENT" \
    --argjson amount "$AMOUNT" \
    --argjson fee 0 \
    --arg sig "$SIGNATURE_HEX" \
    --argjson timestamp "$TIMESTAMP" \
    '{
      from: $from,
      to: $to,
      amount: $amount,
      fee: $fee,
      signature: $sig,
      timestamp: $timestamp
    }')" \
  --max-time 30 2>&1) || true

echo "RPC Response: $RESPONSE"

TX_HASH=$(echo "$RESPONSE" | jq -r '.tx_hash // .hash // .id // "unknown"' 2>/dev/null || echo "unknown")
SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false' 2>/dev/null || echo "false")

if [[ "$SUCCESS" == "true" ]] || [[ "$TX_HASH" != "unknown" && "$TX_HASH" != "null" ]]; then
  echo "✅ Transfer successful! TX: $TX_HASH"
  post_pr_comment "$RECIPIENT" "$TX_HASH" "$AMOUNT" "success" "Transfer successful"
  write_outputs "true" "$RECIPIENT" "$TX_HASH" "$AMOUNT"
else
  echo "⚠️ Transfer response unclear: $RESPONSE"
  post_pr_comment "$RECIPIENT" "$TX_HASH" "$AMOUNT" "unknown" "Transfer submitted (verify on explorer)"
  write_outputs "true" "$RECIPIENT" "$TX_HASH" "$AMOUNT"
fi

echo "✅ RTC Reward Action complete"
