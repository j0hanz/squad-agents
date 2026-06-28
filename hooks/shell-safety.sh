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
#
# A denylisted command can also be hidden inside $(...) / `...` / <(...) /
# >(...) of an otherwise-harmless outer command (e.g. `echo $(rm -rf ~)`),
# which the ;/&/|/&&/|| segment splitter alone never looks inside. Because
# $(...) is extremely common for harmless purposes this guard does not reject
# substitution outright — instead it extracts the
# *contents* of each substitution and scans them with the exact same
# denylist checks as top-level segments, recursively closing the gap without
# blocking ordinary `VAR=$(date)`-style usage.
set -euo pipefail

OVERRIDE_VAR="AGENT_SDLC_SKIP_SHELL_SAFETY"
if [ "${!OVERRIDE_VAR:-0}" = "1" ]; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"[agent-sdlc:shell-safety] WARNING: shell guard bypassed via AGENT_SDLC_SKIP_SHELL_SAFETY env var"}}'
  exit 0
fi

# Load local settings override if exists
AGENT_SDLC_SETTINGS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/claude-agent-sdlc.local.md"
if [ -f "$AGENT_SDLC_SETTINGS_FILE" ]; then
  FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$AGENT_SDLC_SETTINGS_FILE" 2>/dev/null || true)
  if [ -n "$FRONTMATTER" ]; then
    SKIP_SAFETY=$(echo "$FRONTMATTER" | grep '^skip_shell_safety:' | sed 's/skip_shell_safety: *//' 2>/dev/null || true)
    if [ "$SKIP_SAFETY" = "true" ]; then
      printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"[agent-sdlc:shell-safety] WARNING: shell guard bypassed via skip_shell_safety in local config"}}'
      exit 0
    fi
  fi
fi

input=$(cat)

extract_command() {
  # extract_command <json> — pulls .tool_input.command out of the PreToolUse
  # payload. Prefers jq; falls back to a Node.js one-liner since Node is a
  # guaranteed prerequisite for this plugin environment.
  local json="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq -r '.tool_input.command // empty' 2>/dev/null
    return
  fi
  node -e 'try { console.log(JSON.parse(process.argv[1]).tool_input.command); } catch (e) {}' "$json" 2>/dev/null
}

command=$(extract_command "$input") || command=""

if [ -z "$command" ]; then
  exit 0
fi

deny() {
  printf '[agent-sdlc:shell-safety] Blocked: %s. Set %s=1 to override.\n' "$1" "$OVERRIDE_VAR" >&2
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
# ~user (tilde-username form, another user's home dir) is included; bare ~
# still matches since the username class allows zero characters.
# Known accepted gaps (inherited, not new): doesn't resolve a prior `cd /`
# making a relative target root-equivalent, doesn't follow symlinks, and
# doesn't catch variable indirection (`T=/; rm -rf "$T"`) — closing those
# would require shelling out for path resolution, which this guard avoids.
ROOT_TARGET_PATTERN='(^|[[:space:]])["'"'"']?(\$HOME/?|~[A-Za-z0-9_-]*/?|/\*|/)["'"'"']?([[:space:]]|$)'

# Best-effort, non-nested extraction of $(...) / `...` / <(...) / >(...)
# contents from the full command — each becomes its own candidate to scan
# below, alongside the top-level segments, so a denylisted command hidden
# inside a substitution of an unrelated outer command is still caught. Not
# a full shell parser: deliberately simple, leftmost-match extraction: for a
# nested case like `$(echo $(rm -rf ~))`, the innermost construct is found
# and stripped first, then the (now unnested) remainder is found on the next
# iteration — see the loop's removal step.
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
scan_target="$command"
if [ -n "$substitution_contents" ]; then
  scan_target="$command"$'\n'"$substitution_contents"
fi

# Split on ; && || | & and literal newlines into segments — best-effort, not
# a full shell parser. %s, not %b: $command/$scan_target is already plain
# decoded text by this point (jq, or the fallback above, both produce real
# newline bytes from a JSON \n), not an escape-sequence string to
# re-interpret — %b would wrongly eat a literal \n/\t inside e.g. a Windows
# path (C:\new\file.txt) as if it were an escape sequence, corrupting it.
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
    elif $has_recursive && [[ "$trimmed" =~ $ROOT_TARGET_PATTERN ]]; then
      # Not gated on $has_force: an unforced `rm -r` against a root-like
      # target is just as destructive on any file that's already
      # deletable; the interactive per-file prompt isn't a real safety net
      # in a non-interactive hook context.
      deny "recursive delete (non-forced) of a root-level path ('$trimmed')"
    fi
  fi

  # git push --force / -f / --force-with-lease (combined, separated, or
  # long-form) explicitly targeting main or master. Word-order independent:
  # flags are scanned across all words and the branch patterns search the
  # whole segment, not a fixed position relative to --force.
  #
  # Force-pushing to a named branch OTHER than main/master (e.g. a shared
  # release branch) is a deliberate, accepted gap, not an oversight: an
  # earlier design considered denying any force-push with no explicit
  # branchspec (treating "implicit current branch" as inherently risky),
  # but that inverts the risk profile — it blocks the common, safe, everyday
  # workflow (bare `git push --force` to your own tracked feature branch)
  # while still exempting the actually-risky case of naming another shared
  # branch. Closing this gap for real requires asking git which branch is
  # checked out / tracked, which this hook deliberately avoids (see file
  # header: no subprocess dependency).
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
