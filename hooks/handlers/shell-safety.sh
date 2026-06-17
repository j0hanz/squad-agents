#!/usr/bin/env bash
# PreToolUse(Bash): warn when a risky shell pattern is detected.
# Additive only — returns additionalContext, never blocks.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "PreToolUse"' "$INPUT" "PreToolUse")
COMMAND=$(safe_jq '.tool_input.command // empty' "$INPUT")

STARTED=$(date +%s%3N)

warn=""
if [[ -n "$COMMAND" ]]; then
  checks=(
    'rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*|--recursive\s+--force|--force\s+--recursive|-r\s+-f|-f\s+-r):force-remove pattern'
    'git\s+push\b.*(\s-f\b|--force\b|--force-with-lease\b):force-push pattern'
    'DROP\s+TABLE:SQL DROP TABLE'
    'TRUNCATE\s+TABLE:SQL TRUNCATE TABLE'
    'git\s+reset\s+--hard:hard reset pattern'
    'git\s+checkout\s+--:checkout -- discard changes'
    'rm\s+-[a-z]*r[a-z]*f[a-z]*.*>\s*/dev/null:silenced force-remove pattern'
  )
  for entry in "${checks[@]}"; do
    pattern="${entry%%:*}"
    label="${entry##*:}"
    if echo "$COMMAND" | grep -qiE "$pattern"; then
      warn="Shell safety: detected a ${label} — confirm intent before this runs."
      break
    fi
  done
fi

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

if [[ -n "$warn" ]]; then
  emit_context "$EVENT" "$warn"
fi

write_telemetry "shell-safety" "check" "$EVENT" "$DURATION" "success"
exit 0
