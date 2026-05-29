#!/usr/bin/env bash
# Backward-compat shim. Forwards to validate.sh.
exec "$(dirname "${BASH_SOURCE[0]}")/validate.sh" "$@"
