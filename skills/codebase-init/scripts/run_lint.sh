#!/usr/bin/env bash
set -euo pipefail

: "${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT not set}"
: "${CLAUDE_PROJECT_DIR:?CLAUDE_PROJECT_DIR not set}"

py=$(command -v python3 || command -v python) || { echo "error: python3/python not found" >&2; exit 1; }
"$py" "${CLAUDE_PLUGIN_ROOT}/skills/codebase-init/scripts/run.py" lint-agents-md "${CLAUDE_PROJECT_DIR}/AGENTS.md"
