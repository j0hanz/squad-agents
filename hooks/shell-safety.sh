#!/usr/bin/env bash
# PreToolUse(Bash) guard blocks catastrophic command patterns.
# Self-contained to ensure reliability.
# Best-effort, structural matching prevents false positives.
# Extracts and scans substitution contents like $(...) and `...`.
set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

OVERRIDE_VAR="SQUAD_AGENTS_SKIP_SHELL_SAFETY"
if [ "${!OVERRIDE_VAR:-0}" = "1" ]; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"[squad-agents:shell-safety] WARNING: shell guard bypassed via SQUAD_AGENTS_SKIP_SHELL_SAFETY env var"}}'
  exit 0
fi

# Load local settings.
SQUAD_AGENTS_SETTINGS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/squad-agents.local.md"
if [[ -f "$SQUAD_AGENTS_SETTINGS_FILE" ]]; then
  FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$SQUAD_AGENTS_SETTINGS_FILE" 2>/dev/null || true)
  if [[ -n "$FRONTMATTER" ]]; then
    SKIP_SAFETY=$(printf '%s\n' "$FRONTMATTER" | grep '^skip_shell_safety:' | sed 's/skip_shell_safety: *//' | sed 's/[[:space:]]*$//' | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/" 2>/dev/null || true)
    if [[ "$SKIP_SAFETY" == "true" ]]; then
      printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"[squad-agents:shell-safety] WARNING: shell guard bypassed via skip_shell_safety in local config"}}'
      exit 0
    fi
  fi
fi

input=$(cat)

extract_command() {
  # Extracts .tool_input.command from the PreToolUse JSON payload.
  node -e 'try { console.log(JSON.parse(process.argv[1]).tool_input.command); } catch (e) {}' "$1" 2>/dev/null
}

command=$(extract_command "$input") || command=""

if [ -z "$command" ]; then
  exit 0
fi

deny() {
  printf '[squad-agents:shell-safety] Blocked: %s. Set %s=1 to override.\n' "$1" "$OVERRIDE_VAR" >&2
  exit 2
}

has_char() {
  # Returns true if <char> is in <flags>.
  case "$1" in
  *"$2"*) return 0 ;;
  *) return 1 ;;
  esac
}

collect_short_flags() {
  # Concatenates short flags (e.g., "-rf" "-x" -> "rfx").
  local w out=""
  for w in "$@"; do
    case "$w" in
    -[A-Za-z]*) out+="${w#-}" ;;
    esac
  done
  printf '%s' "$out"
}

has_long_flag() {
  # Returns true if --<name> or --<name>=value exists.
  local name="$1"
  shift
  local w
  for w in "$@"; do
    case "$w" in
    --"$name" | --"$name"=*) return 0 ;;
    esac
  done
  return 1
}

# Matches root-level deletion targets (/, /*, ~, $HOME).
# Does not resolve relative paths, symlinks, or variables.
ROOT_TARGET_PATTERN='(^|[[:space:]])["'"'"']?(\$HOME/?|~[A-Za-z0-9_-]*/?|/\*|/)["'"'"']?([[:space:]]|$)'

# Extracts contents of substitutions: $(...), `...`, <(...), >(...).
# Uses leftmost-match extraction to handle nesting iteratively.
extract_substitution_contents() {
  local rest="$1" out=""
  local -a patterns=('\$\(([^()]*)\)' '`([^`]*)`' '<\(([^()]*)\)' '>\(([^()]*)\)')
  local pattern matched=1
  while [ "$matched" = 1 ]; do
    matched=0
    for pattern in "${patterns[@]}"; do
      if [[ "$rest" =~ $pattern ]]; then
        out+="${BASH_REMATCH[1]}"$'\n'
        rest="${rest/"${BASH_REMATCH[0]}"/}"
        matched=1
      fi
    done
  done
  printf '%s' "$out"
}

substitution_contents="$(extract_substitution_contents "$command")"
scan_target="$command"$'\n'"$substitution_contents"

# Splits command into segments by ;, &&, ||, |, &, and newlines.
IFS=$'\n' read -r -d '' -a segments < <(printf '%s' "$scan_target" | awk '
  {
    str = $0
    pos = 1
    len = length(str)

    while (pos <= len) {
      match_pos = match(substr(str, pos), /\|\||&&|[&|;]/)
      if (match_pos == 0) {
        segment = substr(str, pos)
        if (segment != "") print segment
        break
      }

      segment = substr(str, pos, match_pos - 1)
      if (segment != "") print segment

      pos = pos + match_pos + RLENGTH - 1
    }
  }
') || true

for segment in "${segments[@]}"; do
  # Trim whitespace.
  trimmed="$(printf '%s' "$segment" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [ -z "$trimmed" ] && continue

  # Catch recursive force-deletes against root-like targets.
  if [[ "$trimmed" =~ ^rm([[:space:]]|$) ]]; then
    read -ra words <<<"$trimmed"
    shortflags="$(collect_short_flags "${words[@]:1}")"
    has_recursive=false
    has_force=false
    { has_char "$shortflags" r || has_char "$shortflags" R || has_long_flag recursive "${words[@]:1}"; } && has_recursive=true
    { has_char "$shortflags" f || has_long_flag force "${words[@]:1}"; } && has_force=true
    if $has_recursive && $has_force && [[ "$trimmed" =~ $ROOT_TARGET_PATTERN ]]; then
      deny "recursive force-delete of a root-level path ('$trimmed')"
    elif $has_recursive && [[ "$trimmed" =~ $ROOT_TARGET_PATTERN ]]; then
      # Catch non-forced recursive deletes against root-like targets.
      deny "recursive delete (non-forced) of a root-level path ('$trimmed')"
    fi
  fi

  # Catch force-pushes explicitly targeting main or master branches.
  # Force-pushing to other branches or without a branchspec is allowed.
  if [[ "$trimmed" =~ ^git[[:space:]]+push([[:space:]]|$) ]]; then
    read -ra words <<<"$trimmed"
    shortflags="$(collect_short_flags "${words[@]:2}")"
    has_force=false
    { has_char "$shortflags" f || has_long_flag force "${words[@]:2}" || has_long_flag force-with-lease "${words[@]:2}"; } && has_force=true
    if $has_force && {
      [[ "$trimmed" =~ (^|[[:space:]])([a-zA-Z0-9._-]*/)?:(main|master)([[:space:]]|$) ]] ||
        [[ "$trimmed" =~ (^|[[:space:]])([a-zA-Z0-9._/-]*/)?(main|master)([[:space:]]|$) ]] ||
        [[ "$trimmed" =~ (^|[[:space:]]|=)(main|master):[A-Za-z0-9]*([[:space:]]|$) ]]
    }; then
      deny "force-push targeting main/master ('$trimmed')"
    fi
  fi

  # Catch git clean -fdx (repo-wide wipe).
  if [[ "$trimmed" =~ ^git[[:space:]]+clean([[:space:]]|$) ]]; then
    read -ra words <<<"$trimmed"
    shortflags="$(collect_short_flags "${words[@]:2}")"
    has_force=false
    { has_char "$shortflags" f || has_long_flag force "${words[@]:2}"; } && has_force=true
    if $has_force && has_char "$shortflags" d && has_char "$shortflags" x; then
      deny "git clean -fdx wipes untracked and ignored files repo-wide ('$trimmed')"
    fi
  fi
done

exit 0
