#!/usr/bin/env bash
# PreToolUse(Bash) guard — blocks a short, explicit list of catastrophic command
# patterns. Self-contained (no lib.sh dependency): a bug in the shared helper
# library used by the additive handlers must never silently disable this guard.
#
# Best-effort only — not a general security control. Matches are structural
# (command word + flag set on each ;/&&/||/| segment), not raw substring
# search, so a denylist word appearing inside a quoted string or commit message
# does not trigger a block. Narrow by design: favors under-blocking over
# over-blocking, since a false-positive block breaks a downstream user's
# unrelated workflow in a repo this plugin's author doesn't control.
set -euo pipefail

OVERRIDE_VAR="AGENT_DEV_SKIP_SHELL_SAFETY"
if [ "${!OVERRIDE_VAR:-0}" = "1" ]; then
  exit 0
fi

input=$(cat)

extract_command() {
  # extract_command <json> — pulls .tool_input.command out of the PreToolUse
  # payload. Prefers jq; falls back to a bash-only regex extractor so a
  # missing jq degrades to best-effort parsing instead of disabling the
  # guard outright (an empty result here exits 0 further down, same as if
  # the command were genuinely absent).
  local json="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq -r '.tool_input.command // empty' 2>/dev/null
    return
  fi
  if [[ "$json" =~ \"command\"[[:space:]]*:[[:space:]]*\"((\\.|[^\"\\])*)\" ]]; then
    local raw="${BASH_REMATCH[1]}"
    raw="${raw//\\\"/\"}"
    raw="${raw//\\n/$'\n'}"
    raw="${raw//\\t/$'\t'}"
    raw="${raw//\\\\/\\}"
    printf '%s' "$raw"
  fi
}

command=$(extract_command "$input") || command=""

if [ -z "$command" ]; then
  exit 0
fi

json_escape() {
  # json_escape <string> — minimal escaping for embedding inside a JSON
  # string literal we build by hand (no jq dependency on this path).
  local s="$1"
  local bs='\'
  s="${s//"$bs"/"$bs$bs"}"
  s="${s//\"/"$bs"\"}"
  s="${s//$'\n'/"$bs"n}"
  s="${s//$'\r'/"$bs"r}"
  s="${s//$'\t'/"$bs"t}"
  printf '%s' "$s"
}

deny() {
  local reason
  reason="$(json_escape "$1")"
  printf '%s\n' "{\"hookSpecificOutput\": {\"permissionDecision\": \"deny\"}, \"systemMessage\": \"[agent-dev:shell-safety] Blocked: ${reason}. Set ${OVERRIDE_VAR}=1 to override.\"}" >&2
  exit 2
}

has_char() {
  # has_char <flags> <char> — true if <char> appears anywhere in <flags>
  case "$1" in
  *"$2"*) return 0 ;;
  *) return 1 ;;
  esac
}

collect_short_flags() {
  # collect_short_flags <word...> — concatenates the letters of every
  # short-flag-style token (e.g. "-rf" "-x" -> "rfx"), so callers can check
  # for a flag regardless of whether it was combined or passed separately.
  local w out=""
  for w in "$@"; do
    case "$w" in
    -[A-Za-z]*) out+="${w#-}" ;;
    esac
  done
  printf '%s' "$out"
}

has_long_flag() {
  # has_long_flag <name> <word...> — true if --<name> or --<name>=value
  # appears among the words.
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

# Matches a root-level deletion target, optionally wrapped in matching
# quotes (e.g. "/" or '~'), with or without a trailing slash on ~ / $HOME.
ROOT_TARGET_PATTERN='(^|[[:space:]])["'"'"']?(\$HOME/?|~/?|/\*|/)["'"'"']?([[:space:]]|$)'

# Split on ; && || | into segments — best-effort, not a full shell parser.
IFS=$'\n' read -r -d '' -a segments < <(printf '%s\0' "$command" | tr ';|' '\n' | sed -E 's/&&/\n/g') || true

for segment in "${segments[@]}"; do
  # trim leading/trailing whitespace
  trimmed="$(printf '%s' "$segment" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [ -z "$trimmed" ] && continue

  # rm -rf / rm -fr (combined, separated, or long-form) against a root-like
  # target: /, /*, ~, $HOME — quoted or not.
  if [[ "$trimmed" =~ ^rm([[:space:]]|$) ]]; then
    read -ra words <<<"$trimmed"
    shortflags="$(collect_short_flags "${words[@]:1}")"
    has_recursive=false
    has_force=false
    { has_char "$shortflags" r || has_char "$shortflags" R || has_long_flag recursive "${words[@]:1}"; } && has_recursive=true
    { has_char "$shortflags" f || has_long_flag force "${words[@]:1}"; } && has_force=true
    if $has_recursive && $has_force && [[ "$trimmed" =~ $ROOT_TARGET_PATTERN ]]; then
      deny "recursive force-delete of a root-level path ('$trimmed')"
    fi
  fi

  # git push --force / -f / --force-with-lease (combined, separated, or
  # long-form) explicitly targeting main or master.
  if [[ "$trimmed" =~ ^git[[:space:]]+push([[:space:]]|$) ]]; then
    read -ra words <<<"$trimmed"
    shortflags="$(collect_short_flags "${words[@]:2}")"
    has_force=false
    { has_char "$shortflags" f || has_long_flag force "${words[@]:2}" || has_long_flag force-with-lease "${words[@]:2}"; } && has_force=true
    if $has_force && [[ "$trimmed" =~ (^|[[:space:]])([a-zA-Z0-9._-]*/)?:(main|master)([[:space:]]|$) ]] || [[ "$trimmed" =~ (^|[[:space:]])([a-zA-Z0-9._/-]*/)?(main|master)([[:space:]]|$) ]]; then
      deny "force-push targeting main/master ('$trimmed')"
    fi
  fi

  # git clean with -f/--force, -d, and -x all present (combined or
  # separated) — repo-wide untracked+ignored wipe.
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
