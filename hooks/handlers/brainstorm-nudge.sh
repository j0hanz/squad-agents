#!/usr/bin/env bash
# UserPromptSubmit: nudge toward brainstorming on apparent new-build prompts.
# Fires at most once per session. Additive only.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

[[ "${AGENT_DEV_BRAINSTORM_NUDGE:-1}" == "0" ]] && exit 0

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "UserPromptSubmit"' "$INPUT" "UserPromptSubmit")
PROMPT=$(safe_jq '.prompt // ""' "$INPUT")
PROMPT="${PROMPT#"${PROMPT%%[![:space:]]*}"}"  # ltrim
PROMPT="${PROMPT%"${PROMPT##*[![:space:]]}"}"  # rtrim
SESSION=$(safe_jq '.session_id // "unknown"' "$INPUT" "unknown")

STARTED=$(date +%s%3N)

STATE=".claude/state/brainstorm-nudge.jsonl"
WINDOW=2000
MAX_STATE=2000

# Skip slash commands and empty prompts
if [[ -z "$PROMPT" ]] || [[ "$PROMPT" == /* ]]; then
  exit 0
fi

# "Start a build" intent: imperative verb aimed at a unit of work
INTENT_PAT='(build|implement|create|add|develop|design|scaffold|write).{0,60}(feature|component|module|endpoint|api|app|system|service|class|tool|command|hook|skill|agent|page|screen|integration|workflow|pipeline)'

# Signals the user is already past discovery — don't nudge
ALREADY_PAT='(brainstorm|spec|specs|plan|requirements?|design doc|already (designed|planned|scoped))'

if ! echo "$PROMPT" | grep -qiE "$INTENT_PAT"; then exit 0; fi
if   echo "$PROMPT" | grep -qiE "$ALREADY_PAT"; then exit 0; fi

# Check if already nudged this session
TAIL=$(read_jsonl_tail "$STATE" "$WINDOW" 2>/dev/null || true)
if [[ -n "$TAIL" ]]; then
  ALREADY=$(printf '%s\n' "$TAIL" | jq -s --arg s "$SESSION" 'map(select(.session == $s)) | length > 0' 2>/dev/null || echo "false")
  if [[ "$ALREADY" == "true" ]]; then exit 0; fi
fi

# Record nudge and trim
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
append_jsonl "$STATE" "$(jq -n --arg ts "$TS" --arg s "$SESSION" '{ts:$ts,session:$s}')"
trim_jsonl "$STATE" "$MAX_STATE"

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

MSG='Note: this looks like a new build. Consider a quick `brainstorming` pass (requirements + design) before implementing — it catches ambiguity early. Skip if the design is already clear.'
emit_context "$EVENT" "$MSG"

write_telemetry "brainstorm-nudge" "nudge" "$EVENT" "$DURATION" "success"
exit 0
