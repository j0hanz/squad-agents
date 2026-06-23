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

EVALS_FILE="$PLUGIN_DIR/skills/${SKILL_NAME}/evals/evals.json"

EXTRA_FLAGS=()
if [ "$SKIP_PERMISSIONS" = "1" ]; then
    EXTRA_FLAGS+=(--dangerously-skip-permissions)
fi

if [ -f "$EVALS_FILE" ]; then
    echo "Found evals.json at $EVALS_FILE. Running evals loop."
    CASE_IDS=$(jq -r '.[] | .id' "$EVALS_FILE" | tr -d '\r')
    for case_id in $CASE_IDS; do
        case_id=$(echo "$case_id" | tr -d '\r')
        echo "=== Eval Case ID: $case_id ==="
        PROMPT=$(jq -r --argjson cid "$case_id" '.[] | select(.id == $cid) | .prompt' "$EVALS_FILE")
        LOG_FILE="$OUTPUT_DIR/claude-output-case-${case_id}.json"
        
        echo "Running claude -p with plugin-dir: $PLUGIN_DIR for case $case_id"
        timeout 300 claude -p "$PROMPT" \
            --plugin-dir "$PLUGIN_DIR" \
            --max-turns "$MAX_TURNS" \
            --output-format stream-json \
            --verbose \
            "${EXTRA_FLAGS[@]}" \
            > "$LOG_FILE" 2>&1 || true

        echo ""
        echo "=== Results for Case $case_id ==="

        ESCAPED_NAME=$(printf '%s' "$SKILL_NAME" | sed 's/[.[\*^$()+?{}|\\]/\\&/g')
        SKILL_PATTERN='"skill":"([^"]*:)?'"${ESCAPED_NAME}"'"'
        if grep -q '"name":"Skill"' "$LOG_FILE" && grep -qE "$SKILL_PATTERN" "$LOG_FILE"; then
            echo "✅ PASS: Skill '$SKILL_NAME' was triggered"
            echo "Running grader..."
            if node "$PLUGIN_DIR/tests/skill-triggering/grade-transcript.mjs" "$SKILL_NAME" "$LOG_FILE" "$case_id"; then
                echo "✅ PASS: Grading succeeded for case $case_id"
            else
                echo "❌ FAIL: Grading failed for case $case_id"
                exit 1
            fi
        else
            echo "❌ FAIL: Skill '$SKILL_NAME' was NOT triggered"
            exit 1
        fi
    done
    exit 0
else
    echo "No evals.json found. Falling back to existing static prompt test behavior."
    PROMPT=$(cat "$PROMPT_FILE" | tr -d '\r')
    LOG_FILE="$OUTPUT_DIR/claude-output.json"
    cd "$OUTPUT_DIR"

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
fi
