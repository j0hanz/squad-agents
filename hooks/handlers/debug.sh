#!/usr/bin/env bash
# Stop: scan uncommitted diff for debug artifacts (console.log, debugger, .only, etc.).
# Blocks stop if found so the agent cleans them up first.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "Stop"' "$INPUT" "Stop")
STOP_HOOK_ACTIVE=$(safe_jq '.stop_hook_active // false' "$INPUT" "false")

STARTED=$(date +%s%3N)

if [[ "$STOP_HOOK_ACTIVE" == "true" ]]; then
  write_telemetry "debug" "scan" "$EVENT" "0" "success"
  exit 0
fi

DIFF=$(git -C "$PROJECT_DIR" diff --unified=0 --no-color 2>/dev/null || true)

if [[ -z "$DIFF" ]]; then
  write_telemetry "debug" "scan" "$EVENT" "0" "success"
  exit 0
fi

# Each entry: <ERE pattern>|<label>
probes=(
  '\bconsole\.(log|debug|trace)\s*\(|console.log'
  '\bdebugger\s*;?|debugger statement'
  '\b(describe|it|test)\.only\s*\(|test .only (focused test)'
  '\b(fdescribe|fit)\s*\(|focused test (fdescribe/fit)'
  '\b(pdb\.set_trace|breakpoint)\s*\(|python breakpoint'
  '//\s*@ts-nocheck|ts-nocheck suppression'
)

current_file=""
findings=()

while IFS= read -r line; do
  if [[ "$line" == "+++ b/"* ]]; then
    current_file="${line:6}"
    continue
  fi
  # Only inspect added lines (not the +++ header itself)
  if [[ "$line" != "+"* ]] || [[ "$line" == "+++"* ]]; then
    continue
  fi
  added="${line:1}"
  for probe_entry in "${probes[@]}"; do
    pattern="${probe_entry%%|*}"
    label="${probe_entry##*|}"
    if echo "$added" | grep -qE "$pattern"; then
      excerpt="${added:0:120}"
      findings+=("  - ${current_file}: ${label} (\"${excerpt}\")")
      break
    fi
  done
done <<< "$DIFF"

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

if (( ${#findings[@]} > 0 )); then
  count=${#findings[@]}
  list=$(printf '%s\n' "${findings[@]}")
  msg="Warning: ${count} debug artifact(s) in uncommitted changes:
${list}
Clean these up before completing the task."
  # Use block decision so the agent actually addresses these before stopping.
  jq -n --arg r "$msg" '{decision:"block",reason:$r}'
fi

write_telemetry "debug" "scan" "$EVENT" "$DURATION" "success"
exit 0
