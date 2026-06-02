#!/usr/bin/env bash
# Run all skill-triggering tests.
# Usage: ./run-all.sh
#
# Iterates over every .txt file in prompts/, derives the skill name
# from the filename stem, and calls run-test.sh for each.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="$SCRIPT_DIR/prompts"

if [ ! -d "$PROMPTS_DIR" ]; then
    echo "ERROR: prompts directory not found: $PROMPTS_DIR"
    exit 1
fi

PASSED=0
FAILED=0
RESULTS=()

echo "=== Running All Skill Triggering Tests ==="
echo ""

for prompt_file in "$PROMPTS_DIR"/*.txt; do
    skill_name="$(basename "$prompt_file" .txt)"

    echo "Testing: $skill_name"

    if "$SCRIPT_DIR/run-test.sh" "$skill_name" "$prompt_file" 3; then
        PASSED=$((PASSED + 1))
        RESULTS+=("✅ $skill_name")
    else
        FAILED=$((FAILED + 1))
        RESULTS+=("❌ $skill_name")
    fi

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
