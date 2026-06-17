#!/usr/bin/env bash
# PostToolUseFailure(Bash|Edit|MultiEdit): nudge toward the diagnose skill after
# repeated failures. Fires once per session after THRESHOLD failures. Additive only.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "PostToolUseFailure"' "$INPUT" "PostToolUseFailure")
TOOL=$(safe_jq '.tool_name // ""' "$INPUT")
SESSION=$(safe_jq '.session_id // "unknown"' "$INPUT" "unknown")

STARTED=$(date +%s%3N)

case "$TOOL" in
  Bash|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

STATE=".claude/state/diagnose-nudge.jsonl"
THRESHOLD=2
WINDOW=2000
MAX_STATE=2000

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Record this failure
append_jsonl "$STATE" "$(jq -n --arg ts "$TS" --arg s "$SESSION" '{ts:$ts,session:$s}')"
trim_jsonl "$STATE" "$MAX_STATE"

# Read session records from tail
TAIL=$(read_jsonl_tail "$STATE" "$WINDOW" 2>/dev/null || true)
if [[ -z "$TAIL" ]]; then
  write_telemetry "diagnose-nudge" "onFailure" "$EVENT" "0" "success"
  exit 0
fi

# Slurp all session records into a JSON array for reliable counting
ALL_RECORDS=$(printf '%s\n' "$TAIL" \
  | jq -cs --arg s "$SESSION" '[.[] | select(.session == $s)]' 2>/dev/null || echo "[]")

IS_NUDGED=$(jq 'map(select(.nudged == true)) | length > 0' <<< "$ALL_RECORDS")
if [[ "$IS_NUDGED" == "true" ]]; then
  write_telemetry "diagnose-nudge" "onFailure" "$EVENT" "0" "success"
  exit 0
fi

FAILURE_COUNT=$(jq 'map(select(.nudged != true)) | length' <<< "$ALL_RECORDS")
if (( FAILURE_COUNT < THRESHOLD )); then
  write_telemetry "diagnose-nudge" "onFailure" "$EVENT" "0" "success"
  exit 0
fi

# Mark as nudged
append_jsonl "$STATE" "$(jq -n --arg ts "$TS" --arg s "$SESSION" '{ts:$ts,session:$s,nudged:true}')"

# Extract error excerpt (first 3 non-empty lines, max 240 chars)
EXCERPT=$(jq -r '
  (.tool_response // "") |
  if type == "string" then .
  elif type == "object" then (.error // .stderr // .output // "")
  else "" end |
  split("\n") | map(select(length > 0)) | .[0:3] | join(" ⏎ ") | .[0:240]
' <<< "$INPUT" 2>/dev/null || true)

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

MSG='Multiple Bash failures this session. Consider the `diagnose` skill — reproduce → isolate → hypothesize → fix, rather than retrying variants.'
if [[ -n "$EXCERPT" ]]; then
  MSG="${MSG}
Last error: ${EXCERPT}"
fi

emit_context "$EVENT" "$MSG"
write_telemetry "diagnose-nudge" "onFailure" "$EVENT" "$DURATION" "success"
exit 0
