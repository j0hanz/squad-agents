#!/usr/bin/env bash
# SessionStart hook nudges towards bundled skills.
# Applies cooldown and dynamically lists available skills.
set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

cat >/dev/null 2>&1 || true # Drain unused stdin.

# Load project-local settings.
SQUAD_AGENTS_SETTINGS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/squad-agents.local.md"
if [[ -z "${SQUAD_AGENTS_SKILL_NUDGE:-}" ]]; then
  if [[ -f "$SQUAD_AGENTS_SETTINGS_FILE" ]]; then
    FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$SQUAD_AGENTS_SETTINGS_FILE" 2>/dev/null || true)
    if [[ -n "$FRONTMATTER" ]]; then
      NUDGE_VAL=$(printf '%s\n' "$FRONTMATTER" | grep '^skill_nudge:' | sed 's/skill_nudge: *//' | sed 's/[[:space:]]*$//' | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/" 2>/dev/null || true)
      if [[ "$NUDGE_VAL" == "false" ]]; then
        export SQUAD_AGENTS_SKILL_NUDGE=0
      elif [[ "$NUDGE_VAL" == "true" ]]; then
        export SQUAD_AGENTS_SKILL_NUDGE=1
      fi
    fi
  fi
fi

squad_agents_json_escape() {
  # Escapes \ and " — the only two characters that need escaping in these
  # messages (no newlines, no control chars, no angle brackets to escape).
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

squad_agents_enum_skills() {
  # Lists available skill directory names.
  local root="${CLAUDE_PLUGIN_ROOT:-.}"
  while IFS= read -r -d '' file; do
    local d="${file%/SKILL.md}"
    printf '%s\n' "${d##*/}"
  done < <(find "$root/skills" -maxdepth 2 -name "SKILL.md" -print0 2>/dev/null | sort -z || true)
}

# Exit early if nudge is disabled.
if [ "${SQUAD_AGENTS_SKILL_NUDGE:-1}" = "0" ]; then
  exit 0
fi
BOOTSTRAP_MODE="${SQUAD_AGENTS_BOOTSTRAP_MODE:-cooldown}"

# Fetch skill list once — shared by both cooldown and full modes.
available=$(squad_agents_enum_skills)
[ -z "$available" ] && exit 0

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude"
STATE_FILE="$STATE_DIR/skill-nudge-state"
COOLDOWN_SECONDS=86400 # 24h cooldown.

# Mode: cooldown (default — once per 24h).
if [ "$BOOTSTRAP_MODE" = "cooldown" ]; then
  now=$(date +%s)
  if [ -f "$STATE_FILE" ]; then
    last=$(cat "$STATE_FILE" 2>/dev/null || printf '0\n')
    last=${last//[^0-9]/}
    [ -z "$last" ] && last=0
    if [ $((now - last)) -lt "$COOLDOWN_SECONDS" ]; then
      exit 0
    fi
  fi
  mkdir -p "$STATE_DIR" 2>/dev/null || true
  printf '%s' "$now" >"$STATE_FILE" 2>/dev/null || true

  list=$(printf '%s\n' "$available" | paste -sd ',' - | sed 's/,/, /g')
  message="[squad-agents:skill-nudge] This plugin includes skills for structured workflows: ${list}. They auto-trigger on matching tasks, or invoke directly with /skill-name."
  escaped=$(squad_agents_json_escape "$message")
  printf '%s\n' "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"${escaped}\"}}"
  exit 0
fi

# Mode: full (opt-in via SQUAD_AGENTS_BOOTSTRAP_MODE=full — fires every session).
list=$(printf '%s\n' "$available" | paste -sd ',' -)
gates="Gate 0 Repository Onboarding, Gate 1 Task Definition, Gate 2 Scope & System, Gate 3 Execution Strategy, Gate 4 Quality & Delivery"
message="<EXTREMELY_IMPORTANT>[squad-agents:skill-nudge] Before responding, check using-squad-agents-skills for routing: ${gates}. Bundled skills available this session: ${list}.</EXTREMELY_IMPORTANT>"
escaped=$(squad_agents_json_escape "$message")
printf '%s\n' "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"${escaped}\"}}"
exit 0
