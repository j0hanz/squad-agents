#!/usr/bin/env bash
# PreToolUse(Grep|Glob|Read|WebFetch|WebSearch): record what the agent explored.
# Pure side effect — no stdout. Async hook.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "PreToolUse"' "$INPUT" "PreToolUse")
TOOL=$(safe_jq '.tool_name // ""' "$INPUT")
SESSION=$(safe_jq '.session_id // "unknown"' "$INPUT" "unknown")

STARTED=$(date +%s%3N)

TRAIL=".claude/explorer-breadcrumbs.log"

note=""
case "$TOOL" in
  Grep)
    PATTERN=$(jq -r '.tool_input.pattern // ""' <<< "$INPUT")
    PATH_ARG=$(jq -r '.tool_input.path // ""' <<< "$INPUT")
    if [[ -n "$PATTERN" ]]; then
      note="grep /${PATTERN}/${PATH_ARG:+ in $PATH_ARG}"
    fi
    ;;
  Glob)
    PATTERN=$(jq -r '.tool_input.pattern // ""' <<< "$INPUT")
    [[ -n "$PATTERN" ]] && note="glob ${PATTERN}"
    ;;
  Read)
    FILE=$(jq -r '.tool_input.file_path // ""' <<< "$INPUT")
    [[ -n "$FILE" ]] && note="read ${FILE}"
    ;;
  WebFetch)
    URL=$(jq -r '.tool_input.url // ""' <<< "$INPUT")
    [[ -n "$URL" ]] && note="fetch ${URL}"
    ;;
  WebSearch)
    QUERY=$(jq -r '.tool_input.query // ""' <<< "$INPUT")
    [[ -n "$QUERY" ]] && note="search \"${QUERY}\""
    ;;
esac

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

if [[ -n "$note" ]]; then
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  append_jsonl "$TRAIL" "$(jq -n --arg ts "$TS" --arg n "$note" --arg s "$SESSION" \
    '{ts:$ts,note:$n,session:$s}')"
fi

write_telemetry "explorer" "breadcrumb" "$EVENT" "$DURATION" "success"
exit 0
