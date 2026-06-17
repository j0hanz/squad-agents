#!/usr/bin/env bash
# PostToolUse(WebFetch): cache fetched content with ETag/Last-Modified headers.
# Pure side effect — no stdout output. Async hook.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "PostToolUse"' "$INPUT" "PostToolUse")
URL=$(safe_jq '.tool_input.url // ""' "$INPUT")

STARTED=$(date +%s%3N)

if [[ -z "$URL" ]]; then
  write_telemetry "webcache" "store" "$EVENT" "0" "success"
  exit 0
fi

CONTENT=$(jq -r '
  (.tool_response.result // .tool_response // "") |
  if type == "string" then . else "" end
' <<< "$INPUT" 2>/dev/null || true)

if [[ -z "$CONTENT" ]]; then
  write_telemetry "webcache" "store" "$EVENT" "0" "success"
  exit 0
fi

# HEAD request to get caching headers
HEADERS=$(curl -sI --max-time 5 "$URL" 2>/dev/null || true)
ETAG=$(printf '%s\n' "$HEADERS" \
  | grep -i '^etag:' | head -1 \
  | sed 's/^[Ee][Tt][Aa][Gg]:[[:space:]]*//' | tr -d '\r' || true)
LAST_MOD=$(printf '%s\n' "$HEADERS" \
  | grep -i '^last-modified:' | head -1 \
  | sed 's/^[Ll][Aa][Ss][Tt]-[Mm][Oo][Dd][Ii][Ff][Ii][Ee][Dd]:[[:space:]]*//' | tr -d '\r' || true)

if [[ -z "$ETAG" && -z "$LAST_MOD" ]]; then
  write_telemetry "webcache" "store" "$EVENT" "0" "success"
  exit 0
fi

CACHE_DIR="${PROJECT_DIR}/.claude/webcache"
HASH=$(printf '%s' "$URL" | sha256sum | cut -c1-32)
mkdir -p "$CACHE_DIR" 2>/dev/null || true

FETCHED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jq -n \
  --arg url "$URL" \
  --arg etag "${ETAG:-}" \
  --arg lm "${LAST_MOD:-}" \
  --arg content "$CONTENT" \
  --arg fa "$FETCHED_AT" \
  '{
    url: $url,
    etag: (if $etag == "" then null else $etag end),
    last_modified: (if $lm == "" then null else $lm end),
    content: $content,
    fetched_at: $fa
  }' > "${CACHE_DIR}/${HASH}.json" || true

debug "webcache stored ${URL}"

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

write_telemetry "webcache" "store" "$EVENT" "$DURATION" "success"
exit 0
