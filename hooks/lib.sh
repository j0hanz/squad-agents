#!/usr/bin/env bash
# Shared helpers for the additive hooks only (skill-nudge, telemetry-capture).
# shell-safety.sh intentionally does NOT source this file — a bug here must
# only ever degrade an additive hook to a no-op, never silently disable the
# one blocking guard.

readonly AGENT_DEV_TELEMETRY_MAX_LINES=500

agent_dev_json_escape() {
  # Escapes $1 for embedding as a JSON string value (no surrounding quotes).
  local input="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -Rs . | sed -e 's/^"//' -e 's/"$//'
    return
  fi
  # bash-only fallback if jq is unavailable in the consuming repo
  local out="$input"
  local bs='\'
  out="${out//"$bs"/"$bs$bs"}"
  out="${out//\"/"$bs"\"}"
  out="${out//$'\n'/"$bs"n}"
  out="${out//$'\r'/"$bs"r}"
  out="${out//$'\t'/"$bs"t}"
  printf '%s' "$out"
}

agent_dev_telemetry_append() {
  # agent_dev_telemetry_append <event> <tool> <status>
  # Human-readable single line — matches monitors/monitors.json's raw-tail
  # consumption, no JSON-parsing contract to maintain.
  [ "${AGENT_DEV_TELEMETRY:-1}" = "0" ] && return 0
  local event="$1" tool="$2" status="$3"
  local dir="${CLAUDE_PROJECT_DIR:-.}/.claude"
  local log="$dir/telemetry.log"
  mkdir -p "$dir" 2>/dev/null || return 0
  printf '%s %s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$event" "$tool" "$status" >>"$log" 2>/dev/null || return 0

  local lines
  lines=$(wc -l <"$log" 2>/dev/null || echo 0)
  lines=${lines//[^0-9]/}
  if [ -n "$lines" ] && [ "$lines" -gt "$AGENT_DEV_TELEMETRY_MAX_LINES" ]; then
    local tmp lockdir
    tmp=$(mktemp "$dir/telemetry.log.XXXXXX" 2>/dev/null) || return 0
    lockdir="$dir/telemetry.log.lock"
    # Use mkdir for atomic lock (POSIX-safe, no dependencies).
    # Only one process wins; others skip rotation without blocking (exit 0).
    if mkdir "$lockdir" 2>/dev/null; then
      trap "rm -rf \"$lockdir\" \"$tmp\"" RETURN
      # Serialize rotation: tail the current log content, then atomically rename.
      # The mv operation is atomic so a concurrent append is never silently dropped.
      tail -n "$AGENT_DEV_TELEMETRY_MAX_LINES" "$log" >"$tmp" 2>/dev/null && \
        mv "$tmp" "$log" 2>/dev/null
    else
      # Another process holds the lock; skip rotation (no blocking).
      rm -f "$tmp" 2>/dev/null
    fi
  fi
  return 0
}

agent_dev_skill_exists() {
  # agent_dev_skill_exists <skill-name> — checks the plugin's own bundled
  # skills (shipped at $CLAUDE_PLUGIN_ROOT/skills/), not the consuming repo's.
  local name="$1"
  local dir="${CLAUDE_PLUGIN_ROOT:-.}/skills/$name"
  [ -f "$dir/SKILL.md" ]
}
