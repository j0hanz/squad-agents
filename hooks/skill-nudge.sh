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

# Legacy env var and frontmatter flag force mode to 'off'
if [ "${AGENT_SDLC_SKILL_NUDGE:-1}" = "0" ]; then
  AGENT_SDLC_BOOTSTRAP_MODE="off"
fi

# Default to 'full' if not set
BOOTSTRAP_MODE="${AGENT_SDLC_BOOTSTRAP_MODE:-full}"

# Mode: off — exit immediately with no output
if [ "$BOOTSTRAP_MODE" = "off" ]; then
  exit 0
fi

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude"
STATE_FILE="$STATE_DIR/skill-nudge-state"
COOLDOWN_SECONDS=86400 # 24h — avoid nudging every single session

# Mode: cooldown — use 24h cooldown gate (original behavior)
if [ "$BOOTSTRAP_MODE" = "cooldown" ]; then
  now=$(date +%s)
  if [ -f "$STATE_FILE" ]; then
    last=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
    last=${last//[^0-9]/}
    [ -z "$last" ] && last=0
    if [ $((now - last)) -lt "$COOLDOWN_SECONDS" ]; then
      exit 0
    fi
  fi
  # Update state file timestamp
  mkdir -p "$STATE_DIR" 2>/dev/null || true
  printf '%s' "$now" >"$STATE_FILE" 2>/dev/null || true

  # Run original cooldown-gated message with dynamic skill list
  available=$(agent_sdlc_enum_skills)
  [ -z "$available" ] && exit 0
  list=$(echo "$available" | paste -sd ',' - | sed 's/,/, /g')
  message="[agent-sdlc:skill-nudge] This plugin includes skills for structured workflows: ${list}. They auto-trigger on matching tasks, or invoke directly with /skill-name."
  escaped=$(agent_sdlc_json_escape "$message")
  printf '%s\n' "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"${escaped}\"}}"
  exit 0
fi

# Mode: full — unconditional injection with gate routing context
if [ "$BOOTSTRAP_MODE" = "full" ]; then
  # Enumerate available skills dynamically
  available=$(agent_sdlc_enum_skills)
  [ -z "$available" ] && exit 0
  list=$(echo "$available" | paste -sd ',' -)

  # Gate names (hardcoded, changes only with gate structure)
  gates="Gate 0 Repository Onboarding, Gate 1 Task Definition, Gate 2 Scope & System, Gate 3 Execution Strategy, Gate 4 Quality & Delivery"

  # Template with both gate names and dynamic skill list
  message="<EXTREMELY_IMPORTANT>[agent-sdlc:skill-nudge] Before responding, check using-agent-sdlc-skills for routing: ${gates}. Bundled skills available this session: ${list}.</EXTREMELY_IMPORTANT>"
  escaped=$(agent_sdlc_json_escape "$message")
  printf '%s\n' "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"${escaped}\"}}"
  exit 0
fi

# Unknown mode — degrade to no-op
exit 0
