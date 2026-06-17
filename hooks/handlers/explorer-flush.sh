#!/usr/bin/env bash
# SessionEnd: rotate the explorer breadcrumbs trail so it stays bounded.
# Pure side effect — no stdout output.
set -euo pipefail
source "${BASH_SOURCE[0]%/*}/../lib.sh"

INPUT=$(cat)
EVENT=$(safe_jq '.hook_event_name // "SessionEnd"' "$INPUT" "SessionEnd")

STARTED=$(date +%s%3N)

TRAIL=".claude/explorer-breadcrumbs.log"
MAX_TRAIL=200

trim_jsonl "$TRAIL" "$MAX_TRAIL"

ENDED=$(date +%s%3N)
DURATION=$(( ENDED - STARTED ))

write_telemetry "explorer" "flush" "$EVENT" "$DURATION" "success"
exit 0
