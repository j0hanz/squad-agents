#!/usr/bin/env bash
# PreToolUse(WebFetch): serve from cache if HTTP 304 confirms content unchanged.
# This is the one handler that can block — it returns decision:block with the
# cached content so the agent uses it without making a real network request.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "PreToolUse"' "$INPUT" "PreToolUse")
URL=$(safe_jq '.tool_input.url // ""' "$INPUT")

STARTED=$(date +%s%3N)

if [[ -z "$URL" ]]; then
  write_telemetry "webcache" "check" "$EVENT" "0" "success"
  exit 0
fi

CACHE_DIR="${PROJECT_DIR}/.claude/webcache"
HASH=$(printf '%s' "$URL" | sha256sum | cut -c1-32)
CACHE_FILE="${CACHE_DIR}/${HASH}.json"

if [[ ! -f "$CACHE_FILE" ]]; then
  write_telemetry "webcache" "check" "$EVENT" "0" "success"
  exit 0
fi

ETAG=$(jq -r '.etag // empty' "$CACHE_FILE" 2>/dev/null || true)
LAST_MOD=$(jq -r '.last_modified // empty' "$CACHE_FILE" 2>/dev/null || true)
CONTENT=$(jq -r '.content // ""' "$CACHE_FILE" 2>/dev/null || true)

# Convert fetched_at (epoch ms number or ISO string) to a readable timestamp
FETCHED_AT=$(jq -r '
  .fetched_at |
  if type == "number" then . / 1000 | floor | todate
  else .
  end
' "$CACHE_FILE" 2>/dev/null || echo "unknown")

if [[ -z "$ETAG" && -z "$LAST_MOD" ]]; then
  write_telemetry "webcache" "check" "$EVENT" "0" "success"
  exit 0
fi

# Build conditional HEAD request
CURL_ARGS=(-sI --max-time 4 "$URL")
[[ -n "$ETAG" ]]     && CURL_ARGS+=(-H "If-None-Match: ${ETAG}")
[[ -n "$LAST_MOD" ]] && CURL_ARGS+=(-H "If-Modified-Since: ${LAST_MOD}")

HTTP_STATUS=$(curl "${CURL_ARGS[@]}" 2>/dev/null | head -1 | grep -oE '[0-9]{3}' | head -1 || true)

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

if [[ "$HTTP_STATUS" == "304" ]]; then
  REASON="[webcache] Cache hit for ${URL}

Revalidated via HTTP 304; content unchanged since ${FETCHED_AT}.

${CONTENT}"
  jq -n --arg reason "$REASON" '{decision:"block",reason:$reason}'
fi

write_telemetry "webcache" "check" "$EVENT" "$DURATION" "success"
exit 0
