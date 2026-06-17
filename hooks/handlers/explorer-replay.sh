#!/usr/bin/env bash
# SessionStart: surface recent exploration breadcrumbs as context so the agent
# doesn't re-search things it already found in this or the previous session.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "SessionStart"' "$INPUT" "SessionStart")
SESSION=$(safe_jq '.session_id // "unknown"' "$INPUT" "unknown")

STARTED=$(date +%s%3N)

TRAIL=".claude/explorer-breadcrumbs.log"

RECENT=$(read_jsonl_tail "$TRAIL" 12 2>/dev/null || true)
if [[ -z "$RECENT" ]]; then
  write_telemetry "explorer" "replay" "$EVENT" "0" "success"
  exit 0
fi

# Prefer current-session entries, fall back to all recent
CURRENT=$(printf '%s\n' "$RECENT" \
  | jq -c --arg s "$SESSION" 'select(.session == $s)' 2>/dev/null || true)
ENTRIES="${CURRENT:-$RECENT}"
[[ -z "$ENTRIES" ]] && ENTRIES="$RECENT"

# De-duplicate notes preserving recency (most recent wins), then restore
# chronological order for display. Extract note + time together.
# Build "note [HH:MM:SS]" lines, reverse, dedup on note, take 10, re-reverse.
LINES=$(printf '%s\n' "$ENTRIES" | jq -r '
  .note as $n |
  (.ts // "" | gsub(".*T"; "") | gsub("Z$"; "") | .[0:8]) as $t |
  if $t != "" then "\($n) [\($t)]" else $n end
' 2>/dev/null || true)

if [[ -z "$LINES" ]]; then
  write_telemetry "explorer" "replay" "$EVENT" "0" "success"
  exit 0
fi

# Dedup by note prefix (everything before " ["), keep most-recent, restore order
DEDUPED=$(printf '%s\n' "$LINES" \
  | tac \
  | awk -F ' \[' '!seen[$1]++' \
  | head -10 \
  | tac)

if [[ -z "$DEDUPED" ]]; then
  write_telemetry "explorer" "replay" "$EVENT" "0" "success"
  exit 0
fi

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

CTX="## Recently explored (this project)"$'\n'
while IFS= read -r note_line; do
  CTX+="  ${note_line}"$'\n'
done <<< "$DEDUPED"

emit_context "$EVENT" "$CTX"
write_telemetry "explorer" "replay" "$EVENT" "$DURATION" "success"
exit 0
