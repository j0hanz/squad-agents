#!/usr/bin/env bash
# hooks/lib.sh — shared helpers sourced by every hook handler script.
# Source via: source "${BASH_SOURCE[0]%/*}/../lib.sh"

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

debug() {
  [[ "${CLAUDE_HOOKS_DEBUG:-0}" == "1" ]] && printf '[hook] %s\n' "$*" >&2
}

# safe_jq <filter> <json> [default]
# jq wrapper that survives malformed/empty JSON under `set -e` instead of
# aborting the caller — falls back to <default> (empty string if omitted).
safe_jq() {
  local filter="$1" json="$2" default="${3:-}"
  jq -r "$filter" <<< "$json" 2>/dev/null || printf '%s' "$default"
}

# ---------------------------------------------------------------------------
# JSONL file helpers
# ---------------------------------------------------------------------------

# _jsonl_lock <file>  — acquire a short-lived mutex for <file> via atomic mkdir.
# Echoes 1 on success, 0 on failure (caller should proceed best-effort either way).
_jsonl_lock() {
  local file="$1" lockdir="${1}.lockdir" tries=0
  while ! mkdir "$lockdir" 2>/dev/null; do
    # Break a stale lock (older than 5s — these critical sections are sub-millisecond).
    if [[ -d "$lockdir" ]]; then
      local age
      age=$(( $(date +%s) - $(stat -c %Y "$lockdir" 2>/dev/null || stat -f %m "$lockdir" 2>/dev/null || echo 0) ))
      if (( age > 5 )); then
        rmdir "$lockdir" 2>/dev/null || true
        continue
      fi
    fi
    tries=$(( tries + 1 ))
    (( tries > 100 )) && { echo 0; return; }
    sleep 0.02
  done
  echo 1
}

_jsonl_unlock() {
  rmdir "${1}.lockdir" 2>/dev/null || true
}

# append_jsonl <rel_path> <json_line>
append_jsonl() {
  local rel="$1" line="$2"
  local file="${PROJECT_DIR}/${rel}"
  mkdir -p "$(dirname "$file")" 2>/dev/null || true
  local locked
  locked=$(_jsonl_lock "$file")
  printf '%s\n' "$line" >> "$file" || true
  [[ "$locked" == "1" ]] && _jsonl_unlock "$file"
}

# read_jsonl_tail <rel_path> <n>  — prints up to n last non-empty lines
read_jsonl_tail() {
  local rel="$1" n="$2"
  local file="${PROJECT_DIR}/${rel}"
  [[ -f "$file" ]] || return 0
  grep -v '^[[:space:]]*$' "$file" 2>/dev/null | tail -n "$n" || true
}

# trim_jsonl <rel_path> <max>
trim_jsonl() {
  local rel="$1" max="$2"
  local file="${PROJECT_DIR}/${rel}"
  [[ -f "$file" ]] || return 0
  local locked
  locked=$(_jsonl_lock "$file")
  local count
  count=$(grep -c . "$file" 2>/dev/null || echo 0)
  if (( count > max )); then
    local tmp="${file}.tmp.$$"
    tail -n "$max" "$file" > "$tmp" && mv "$tmp" "$file" || rm -f "$tmp"
  fi
  [[ "$locked" == "1" ]] && _jsonl_unlock "$file"
}

# ---------------------------------------------------------------------------
# Hook output helpers
# ---------------------------------------------------------------------------

CONTEXT_EVENTS="SessionStart UserPromptSubmit PreToolUse PostToolUse PostToolUseFailure"

# emit_context <event_name> <text>
# Emits hookSpecificOutput JSON if the event supports additionalContext.
emit_context() {
  local event="$1" text="$2"
  [[ -z "$text" ]] && return
  if printf '%s\n' "$CONTEXT_EVENTS" | grep -qw "$event"; then
    jq -n --arg e "$event" --arg t "$text" \
      '{hookSpecificOutput:{hookEventName:$e,additionalContext:$t}}'
  fi
}

# emit_block <reason>  — for PreToolUse / Stop decisions
emit_block() {
  jq -n --arg r "$1" '{decision:"block",reason:$r}'
}

# emit_allow
emit_allow() {
  printf '{"decision":"allow"}\n'
}

# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

# write_telemetry <domain> <action> <event> <duration_ms> <status> [error_msg]
write_telemetry() {
  [[ "${AGENT_DEV_TELEMETRY:-1}" == "0" ]] && return
  local domain="$1" action="$2" event="$3" duration="$4" status="$5" err="${6:-}"
  local ts
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local record
  if [[ -n "$err" ]]; then
    record=$(jq -n \
      --arg ts "$ts" --arg domain "$domain" --arg action "$action" \
      --arg event "$event" --argjson dur "$duration" --arg status "$status" \
      --arg err "$err" \
      '{timestamp:$ts,domain:$domain,action:$action,event:$event,duration:$dur,status:$status,error:$err}')
  else
    record=$(jq -n \
      --arg ts "$ts" --arg domain "$domain" --arg action "$action" \
      --arg event "$event" --argjson dur "$duration" --arg status "$status" \
      '{timestamp:$ts,domain:$domain,action:$action,event:$event,duration:$dur,status:$status}')
  fi
  append_jsonl ".claude/telemetry.log" "$record"
}
