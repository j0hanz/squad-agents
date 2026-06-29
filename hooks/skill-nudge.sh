#!/usr/bin/env bash
# SessionStart hook — additive only. Points toward this plugin's bundled
# skills, but only on a cooldown (not every single session) and only toward
# skills actually present, never hardcoded blind.
set -euo pipefail

cat >/dev/null 2>&1 || true # drain stdin; SessionStart payload unused

# Load project-local settings (frontmatter only if env var not already set)
AGENT_SDLC_SETTINGS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/claude-agent-sdlc.local.md"
if [[ -z "${AGENT_SDLC_SKILL_NUDGE:-}" ]]; then
  if [[ -f "$AGENT_SDLC_SETTINGS_FILE" ]]; then
    FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$AGENT_SDLC_SETTINGS_FILE" 2>/dev/null || true)
    if [[ -n "$FRONTMATTER" ]]; then
      NUDGE_VAL=$(echo "$FRONTMATTER" | grep '^skill_nudge:' | sed 's/skill_nudge: *//' 2>/dev/null || true)
      if [[ "$NUDGE_VAL" == "false" ]]; then
        export AGENT_SDLC_SKILL_NUDGE=0
      elif [[ "$NUDGE_VAL" == "true" ]]; then
        export AGENT_SDLC_SKILL_NUDGE=1
      fi
    fi
  fi
fi

agent_sdlc_json_escape() {
  # Escapes $1 for embedding as a JSON string value (no surrounding quotes).
  # Node is a guaranteed prerequisite for this plugin environment.
  node -e 'process.stdout.write(JSON.stringify(process.argv[1]).slice(1, -1))' "$1" 2>/dev/null
}

agent_sdlc_enum_skills() {
  # agent_sdlc_enum_skills — lists all skill directory names by globbing
  # $CLAUDE_PLUGIN_ROOT/skills/*/SKILL.md, sorted, one per line.
  # Returns empty if no skills found or glob fails.
  local root="${CLAUDE_PLUGIN_ROOT:-.}"
  local skill_files
  # ponytail: glob may produce zero matches or no skills/ dir at all
  skill_files=$(find "$root/skills" -maxdepth 2 -name "SKILL.md" 2>/dev/null | sort || true)
  if [ -z "$skill_files" ]; then
    return 0
  fi
  while IFS= read -r file; do
    local d="${file%/SKILL.md}"
    printf '%s\n' "${d##*/}"
  done <<< "$skill_files"
}

# Legacy env var and frontmatter flag force mode to 'off'
if [ "${AGENT_SDLC_SKILL_NUDGE:-1}" = "0" ]; then
  BOOTSTRAP_MODE="off"
else
  # Default to 'full' if not set
  BOOTSTRAP_MODE="${AGENT_SDLC_BOOTSTRAP_MODE:-full}"
fi

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
