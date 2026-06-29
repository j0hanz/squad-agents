#!/usr/bin/env bash
# Run all skill-triggering tests.
# Usage: ./run-all.sh [max-turns]
#
# Iterates over every .txt file in prompts/, derives the skill name
# from the filename stem, and runs claude -p to test triggering.

set -e

MAX_TURNS="${1:-3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROMPTS_DIR="$SCRIPT_DIR/prompts"

if [ ! -d "$PROMPTS_DIR" ]; then
    echo "ERROR: prompts directory not found: $PROMPTS_DIR"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    echo "ERROR: 'claude' not found on PATH. Install Claude Code CLI and try again."
    exit 1
fi

PASSED=0
FAILED=0
RESULTS=()

echo "=== Running All Skill Triggering Tests ==="
echo ""

shopt -s nullglob
prompt_files=("$PROMPTS_DIR"/*.txt)
shopt -u nullglob

if [ ${#prompt_files[@]} -eq 0 ]; then
    echo "ERROR: no .txt prompt files found in $PROMPTS_DIR"
    exit 1
fi

TIMESTAMP=$(date +%s)
EXTRA_FLAGS=()
if [ "$SKIP_PERMISSIONS" = "1" ]; then
    EXTRA_FLAGS+=(--dangerously-skip-permissions)
fi

for prompt_file in "${prompt_files[@]}"; do
    skill_name="$(basename "$prompt_file" .txt)"
    echo "Testing: $skill_name"

    # Fixture variants (e.g. *-pressure.txt) test an existing skill under
    # adversarial framing; they expect the base skill name to trigger.
    expected_skill="${skill_name%-pressure}"
    
    OUTPUT_DIR="/tmp/agent-sdlc-tests/${TIMESTAMP}/skill-triggering/${skill_name}"
    mkdir -p "$OUTPUT_DIR"
    
    PROMPT=$(cat "$prompt_file" | tr -d '\r')
    LOG_FILE="$OUTPUT_DIR/claude-output.json"
    
    echo "Running claude -p with plugin-dir: $PLUGIN_DIR"
    (
        cd "$OUTPUT_DIR"
        timeout 300 claude -p "$PROMPT" \
            --plugin-dir "$PLUGIN_DIR" \
            --max-turns "$MAX_TURNS" \
            --output-format stream-json \
            "${EXTRA_FLAGS[@]}" \
            > "$LOG_FILE" 2>&1 || true
    )
    
    echo ""
    echo "=== Results ==="
    
    ESCAPED_NAME=$(printf '%s' "$expected_skill" | sed 's/[.[\*^$()+?{}|\\]/\\&/g')
    SKILL_PATTERN='"skill":"([^"]*:)?'"${ESCAPED_NAME}"'"'
    if grep -q '"name":"Skill"' "$LOG_FILE" && grep -qE "$SKILL_PATTERN" "$LOG_FILE"; then
        echo "✅ PASS: Skill '$expected_skill' was triggered"
        PASSED=$((PASSED + 1))
        RESULTS+=("✅ $skill_name")
    else
        echo "❌ FAIL: Skill '$expected_skill' was NOT triggered"
        FAILED=$((FAILED + 1))
        RESULTS+=("❌ $skill_name")
    fi
    
    echo ""
    echo "Skills triggered in this run:"
    grep -oE '"skill":"[^"]*"' "$LOG_FILE" 2>/dev/null | sort -u || echo "  (none)"
    echo ""
    echo "Full log: $LOG_FILE"
    echo ""
    echo "---"
    echo ""
done

echo "=== Summary ==="
for result in "${RESULTS[@]}"; do
    echo "  $result"
done
echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
