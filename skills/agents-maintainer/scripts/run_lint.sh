#!/bin/bash
python "${CLAUDE_PLUGIN_ROOT}/skills/agents-maintainer/scripts/run.py" lint-agents-md "${CLAUDE_PROJECT_DIR}/AGENTS.md"
