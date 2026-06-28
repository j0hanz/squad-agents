#!/usr/bin/env bash
# Shared helpers for the additive hooks only (skill-nudge).
# shell-safety.sh intentionally does NOT source this file — a bug here must
# only ever degrade an additive hook to a no-op, never silently disable the
# one blocking guard.

# Load project-local settings
AGENT_SDLC_SETTINGS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/claude-agent-sdlc.local.md"
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


agent_sdlc_json_escape() {
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

agent_sdlc_skill_exists() {
  # agent_sdlc_skill_exists <skill-name> — checks the plugin's own bundled
  # skills (shipped at $CLAUDE_PLUGIN_ROOT/skills/), not the consuming repo's.
  local name="$1"
  local dir="${CLAUDE_PLUGIN_ROOT:-.}/skills/$name"
  [ -f "$dir/SKILL.md" ]
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
    dirname "$file" | xargs basename
  done <<< "$skill_files"
}
