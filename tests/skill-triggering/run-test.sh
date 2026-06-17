#!/usr/bin/env bash
# Test skill triggering with naive prompts.
# Usage: ./run-test.sh <skill-name> <prompt-file> [max-turns]
#
# Runs claude -p with --output-format stream-json and checks whether
# the Skill tool was invoked with the expected skill name.

set -e

SKILL_NAME="$1"
PROMPT_FILE="$2"
MAX_TURNS="${3:-3}"

if [ -z "$SKILL_NAME" ] || [ -z "$PROMPT_FILE" ]; then
    echo "Usage: $0 <skill-name> <prompt-file> [max-turns]"
    echo "Example: $0 brainstorming ./prompts/brainstorming.txt"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    echo "ERROR: 'claude' not found on PATH. Install Claude Code CLI and try again."
    exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompt file not found: $PROMPT_FILE"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

TIMESTAMP=$(date +%s)
OUTPUT_DIR="/tmp/agent-dev-tests/${TIMESTAMP}/skill-triggering/${SKILL_NAME}"
mkdir -p "$OUTPUT_DIR"

PROMPT=$(cat "$PROMPT_FILE")

echo "=== Skill Triggering Test ==="
echo "Skill:       $SKILL_NAME"
echo "Prompt file: $PROMPT_FILE"
echo "Max turns:   $MAX_TURNS"
echo "Output dir:  $OUTPUT_DIR"
echo ""

cp "$PROMPT_FILE" "$OUTPUT_DIR/prompt.txt"

LOG_FILE="$OUTPUT_DIR/claude-output.json"
cd "$OUTPUT_DIR"

EXTRA_FLAGS=()
if [ "$SKIP_PERMISSIONS" = "1" ]; then
    EXTRA_FLAGS+=(--dangerously-skip-permissions)
fi

echo "Running claude -p with plugin-dir: $PLUGIN_DIR"
timeout 300 claude -p "$PROMPT" \
    --plugin-dir "$PLUGIN_DIR" \
    --max-turns "$MAX_TURNS" \
    --output-format stream-json \
    "${EXTRA_FLAGS[@]}" \
    > "$LOG_FILE" 2>&1 || true

echo ""
echo "=== Results ==="

ESCAPED_NAME=$(printf '%s' "$SKILL_NAME" | sed 's/[.[\*^$()+?{}|\\]/\\&/g')
SKILL_PATTERN='"skill":"([^"]*:)?'"${ESCAPED_NAME}"'"'
if grep -q '"name":"Skill"' "$LOG_FILE" && grep -qE "$SKILL_PATTERN" "$LOG_FILE"; then
    echo "✅ PASS: Skill '$SKILL_NAME' was triggered"
    TRIGGERED=true
else
    echo "❌ FAIL: Skill '$SKILL_NAME' was NOT triggered"
    TRIGGERED=false
fi

echo ""
echo "Skills triggered in this run:"
grep -oE '"skill":"[^"]*"' "$LOG_FILE" 2>/dev/null | sort -u || echo "  (none)"

echo ""
echo "Full log: $LOG_FILE"

if [ "$TRIGGERED" = "true" ]; then
    exit 0
else
    exit 1
fi
