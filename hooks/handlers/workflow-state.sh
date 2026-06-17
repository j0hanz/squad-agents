#!/usr/bin/env bash
# hooks/handlers/workflow-state.sh — Intercept PreToolUse for complete_task.
# Block if verification_passed is not true in .claude/state/workflow.json.

# Source helpers
set -euo pipefail
source "$(dirname "$0")/../lib.sh"

INPUT=$(cat)
TOOL=$(jq -r '.tool_name // ""' <<< "$INPUT")

# Only intercept complete_task (case insensitive check or exact)
if [[ "$TOOL" != "complete_task" ]]; then
    emit_allow
    exit 0
fi

STATE_FILE="${PROJECT_DIR}/.claude/state/workflow.json"

# Default to false if file missing or invalid
PASSED="false"
if [[ -f "$STATE_FILE" ]]; then
    PASSED=$(jq -r '.verification_passed' "$STATE_FILE" 2>/dev/null)
fi

if [[ "$PASSED" != "true" ]]; then
    emit_block "Workflow Block: verification_passed is false or missing in .claude/state/workflow.json. Task completion is prohibited until verification passes."
else
    emit_allow
fi
