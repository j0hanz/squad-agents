#!/usr/bin/env bash
set -euo pipefail

# validate.sh — dispatch to the right linter based on agent kind.

if [ $# -lt 1 ]; then
  echo "Usage: $0 <agent.md>" >&2
  exit 2
fi

AGENT_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Convert to absolute path
if [[ "$AGENT_FILE" != /* ]]; then
  AGENT_FILE="$(pwd)/$AGENT_FILE"
fi

# Convert to native path for Python if on Windows (with cygpath)
if command -v cygpath &> /dev/null; then
  AGENT_FILE_NATIVE=$(cygpath -w "$AGENT_FILE")
else
  AGENT_FILE_NATIVE="$AGENT_FILE"
fi

# Detect kind
KIND=$(cd "${SCRIPT_DIR}" && python3 << EOF
import sys
sys.path.insert(0, '.')
from lib.frontmatter import parse_frontmatter
from lib.agent_parser import detect_agent_kind
with open(r'${AGENT_FILE_NATIVE}') as f:
    fm, _ = parse_frontmatter(f.read())
print(detect_agent_kind(fm))
EOF
)

case "$KIND" in
  managed)
    # Run the original validation steps (frontmatter checks, etc.)
    # This is the managed-agent validation logic from validate-agent.sh

    echo "🔍 Validating agent file: $AGENT_FILE"

    if [ ! -f "$AGENT_FILE" ]; then
      echo "❌ File not found: $AGENT_FILE"
      exit 1
    fi
    echo "✅ File exists"

    # Check frontmatter start/end
    FIRST_LINE=$(head -n 1 "$AGENT_FILE" || true)
    if [ "$FIRST_LINE" != "---" ]; then
      echo "❌ File must start with YAML frontmatter (---)"
      exit 1
    fi
    if ! tail -n +2 "$AGENT_FILE" | grep -q '^---$'; then
      echo "❌ Frontmatter not closed (missing second ---)"
      exit 1
    fi
    echo "✅ Frontmatter present and closed"

    # Extract frontmatter
    FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$AGENT_FILE" || true)
    SYSTEM_PROMPT=$(awk '/^---$/{i++; next} i>=2{print}' "$AGENT_FILE" | sed '/./,$!d' || true)

    error_count=0
    warning_count=0

    # Helper to extract field
    field() {
      echo "$FRONTMATTER" | grep -E "^$1:" | sed -E "s/^$1: *//"
    }

    # name
    NAME=$(field name | sed 's/^"//;s/"$//')
    if [ -z "$NAME" ]; then
      echo "❌ Missing required field: name"
      error_count=$((error_count+1))
    else
      echo "✅ name: $NAME"
      if ! [[ "$NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$ ]]; then
        echo "❌ name must start/end with alphanumeric and contain only letters, numbers, hyphens"
        error_count=$((error_count+1))
      fi
      if [ ${#NAME} -lt 3 ]; then
        echo "❌ name too short (minimum 3 characters)"
        error_count=$((error_count+1))
      fi
      if [ ${#NAME} -gt 50 ]; then
        echo "❌ name too long (maximum 50 characters)"
        error_count=$((error_count+1))
      fi
      if [[ "$NAME" =~ ^(helper|assistant|agent|tool)$ ]]; then
        echo "⚠️  name is too generic: $NAME"
        warning_count=$((warning_count+1))
      fi
    fi

    # description
    DESCRIPTION=$(field description)
    if [ -z "$DESCRIPTION" ]; then
      echo "❌ Missing required field: description"
      error_count=$((error_count+1))
    else
      desc_length=${#DESCRIPTION}
      echo "✅ description: ${desc_length} characters"
      if [ $desc_length -lt 10 ]; then
        echo "⚠️  description too short (minimum 10 characters recommended)"
        warning_count=$((warning_count+1))
      fi
      if ! echo "$DESCRIPTION" | grep -q '<example>'; then
        echo "⚠️  description should include <example> blocks for triggering"
        warning_count=$((warning_count+1))
      fi
      if ! echo "$DESCRIPTION" | grep -qi 'use this agent when'; then
        echo "⚠️  description should include a 'Use this agent when' trigger phrase"
        warning_count=$((warning_count+1))
      fi
    fi

    # model
    MODEL=$(field model)
    if [ -z "$MODEL" ]; then
      echo "❌ Missing required field: model"
      error_count=$((error_count+1))
    else
      echo "✅ model: $MODEL"
    fi

    # color (optional but encouraged)
    COLOR=$(field color)
    if [ -z "$COLOR" ]; then
      echo "⚠️  color not specified (recommended for UI)"
      warning_count=$((warning_count+1))
    else
      echo "✅ color: $COLOR"
    fi

    # tools (optional)
    if echo "$FRONTMATTER" | grep -q "^tools:"; then
      echo "✅ tools: specified"
    else
      echo "💡 tools: not specified (agent may have wide tool access)"
      warning_count=$((warning_count+1))
    fi

    # system prompt
    if [ -z "$SYSTEM_PROMPT" ]; then
      echo "❌ System prompt is empty"
      error_count=$((error_count+1))
    else
      prompt_length=${#SYSTEM_PROMPT}
      echo "✅ System prompt: $prompt_length characters"
      if [ $prompt_length -lt 20 ]; then
        echo "❌ System prompt too short (minimum 20 characters)"
        error_count=$((error_count+1))
      fi
      if ! echo "$SYSTEM_PROMPT" | grep -q -E "You are|You will|Your"; then
        echo "⚠️  System prompt should address the agent in second person (You are...)"
        warning_count=$((warning_count+1))
      fi
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ $error_count -eq 0 ] && [ $warning_count -eq 0 ]; then
      echo "✅ All checks passed!"
      exit 0
    elif [ $error_count -eq 0 ]; then
      echo "⚠️  Validation passed with $warning_count warning(s)"
      exit 0
    else
      echo "❌ Validation failed with $error_count error(s) and $warning_count warning(s)"
      exit 1
    fi
    ;;
  cc_subagent)
    python3 "${SCRIPT_DIR}/compile.py" "${AGENT_FILE}" --json >/dev/null
    ;;
  *)
    echo "warning: could not detect agent kind for ${AGENT_FILE}" >&2
    # fall through to managed-style checks for safety
    exit 1
    ;;
esac
