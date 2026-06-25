#!/usr/bin/env bash
# SessionStart hook — additive only. Points toward this plugin's bundled
# skills, but only on a cooldown (not every single session) and only toward
# skills actually present, never hardcoded blind. lib.sh sourcing failure
# degrades to a silent no-op, never an error.
set -euo pipefail

cat >/dev/null 2>&1 || true # drain stdin; SessionStart payload unused

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/lib.sh" 2>/dev/null || exit 0

[ "${AGENT_DEV_SKILL_NUDGE:-1}" = "0" ] && exit 0

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude"
STATE_FILE="$STATE_DIR/skill-nudge-state"
LOCK_DIR="$STATE_DIR/skill-nudge-lock"
COOLDOWN_SECONDS=86400 # 24h — avoid nudging every single session

now=$(date +%s)

# Atomic check-and-set via lock directory to prevent race condition where
# two simultaneous SessionStart invocations both pass cooldown check.
# mkdir is atomic and fails if lock already exists.
mkdir -p "$STATE_DIR" 2>/dev/null || true
if mkdir "$LOCK_DIR" 2>/dev/null; then
  trap "rmdir \"$LOCK_DIR\" 2>/dev/null || true" EXIT

  if [ -f "$STATE_FILE" ]; then
    last=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
    last=${last//[^0-9]/}
    [ -z "$last" ] && last=0
    if [ $((now - last)) -lt "$COOLDOWN_SECONDS" ]; then
      exit 0
    fi
  fi

  # Inside the lock, safe to update STATE_FILE
  printf '%s' "$now" >"$STATE_FILE" 2>/dev/null || true
else
  # Lock failed: another process is inside the check-and-set window.
  # Exit cleanly to avoid duplicate nudge.
  exit 0
fi

candidates=("parallel-brainstorming" "test-driven-development" "diagnose")
available=()
for name in "${candidates[@]}"; do
  if agent_dev_skill_exists "$name"; then
    available+=("$name")
  fi
done

[ "${#available[@]}" -eq 0 ] && exit 0

list=$(printf '%s, ' "${available[@]}")
list="${list%, }"
message="[agent-dev:skill-nudge] This plugin includes skills for structured workflows: ${list}. They auto-trigger on matching tasks, or invoke directly with /skill-name."
escaped=$(agent_dev_json_escape "$message")

printf '%s\n' "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"${escaped}\"}}"
exit 0
