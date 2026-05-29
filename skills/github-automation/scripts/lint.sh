#!/usr/bin/env bash
# Best-effort linter for GitHub Actions workflows.
#
# Tier 1: actionlint  (the real thing — expression checks, shellcheck inside run:, schema)
# Tier 2: yamllint    (YAML structure only — won't catch Actions-specific issues)
# Tier 3: python -c yaml.safe_load + a handful of critical-rule grep checks
#
# Exits 0 on clean, non-zero on issues.
#
# Usage:
#   bash lint.sh .github/workflows/ci.yml
#   bash lint.sh .github/workflows/         # whole directory

set -u

target="${1:-.github/workflows}"
if [[ ! -e "$target" ]]; then
  echo "error: $target does not exist" >&2
  exit 2
fi

# Collect files
files=()
if [[ -d "$target" ]]; then
  shopt -s nullglob
  for f in "$target"/*.yml "$target"/*.yaml; do
    files+=("$f")
  done
  shopt -u nullglob
else
  files+=("$target")
fi

if [[ ${#files[@]} -eq 0 ]]; then
  echo "error: no .yml/.yaml files under $target" >&2
  exit 2
fi

# -------- Tier 1: actionlint --------
if command -v actionlint >/dev/null 2>&1; then
  echo "linter: actionlint"
  actionlint "${files[@]}"
  exit $?
fi

# -------- Tier 2: yamllint (YAML-only) --------
if command -v yamllint >/dev/null 2>&1; then
  echo "linter: yamllint (Actions-specific checks NOT performed — install actionlint for full coverage)"
  yamllint -d "{extends: relaxed, rules: {line-length: disable}}" "${files[@]}"
  yl_rc=$?
  # Even if YAML is valid, run the critical-rule grep checks below.
  echo
else
  echo "linter: built-in (install actionlint for proper checks)"
  yl_rc=0
fi

# -------- Tier 3: minimal YAML parse + critical-rule checks --------
parse_rc=0
have_pyyaml=0
if command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1; then
  py=$(command -v python3 || command -v python)
  if "$py" -c "import yaml" >/dev/null 2>&1; then
    have_pyyaml=1
  fi
fi

if [[ $have_pyyaml -eq 1 ]]; then
  for f in "${files[@]}"; do
    if ! "$py" - "$f" <<'PY' >/dev/null 2>&1
import sys, yaml
with open(sys.argv[1], encoding="utf-8") as fh:
    yaml.safe_load(fh)
PY
    then
      echo "  ERROR: YAML parse failed: $f" >&2
      parse_rc=1
    fi
  done
else
  echo "  (skipping YAML parse — install PyYAML for parse check: pip install pyyaml)"
fi

# Critical rules: things that are silent runtime bugs.
crit_rc=0
for f in "${files[@]}"; do
  # 1) Expression injection: ${{ github.event.*.title|body|message|head_ref|... }} directly in a run: line.
  if grep -nE 'run:.*\$\{\{\s*github\.(event\.(pull_request|issue|comment|review|head_commit)\.(title|body|message)|head_ref|event\.head_commit\.message)' "$f" >/dev/null; then
    echo "  WARN ($f): possible expression injection — untrusted github.event field inside run:. Use env: instead." >&2
    grep -nE 'run:.*\$\{\{\s*github\.(event\.(pull_request|issue|comment|review|head_commit)\.(title|body|message)|head_ref|event\.head_commit\.message)' "$f" >&2
    crit_rc=1
  fi

  # 2) uses: tag without SHA pinning for third-party actions (best-effort heuristic).
  #    Flags `uses: org/repo@v1` etc. where org is NOT actions/, github/, or starts with ./
  while IFS= read -r line; do
    # Extract the uses: target (no line-number prefix — plain grep, not -n)
    ref=$(echo "$line" | sed -nE 's/^[[:space:]]*-?[[:space:]]*uses:[[:space:]]+([^[:space:]]+).*$/\1/p')
    [[ -z "$ref" ]] && continue
    [[ "$ref" == ./* || "$ref" == docker://* ]] && continue
    [[ "$ref" != *@* ]] && continue
    rev="${ref##*@}"
    repo="${ref%@*}"
    org="${repo%%/*}"
    if [[ ${#rev} -eq 40 && "$rev" =~ ^[0-9a-f]+$ ]]; then
      continue
    fi
    if [[ "$org" != "actions" && "$org" != "github" ]]; then
      echo "  WARN ($f): third-party action not pinned to SHA: $ref" >&2
      crit_rc=1
    fi
  done < <(grep -E '^[[:space:]]*-?[[:space:]]*uses:' "$f")

  # 3) pull_request_target with a checkout of the PR head — extremely dangerous.
  if grep -q 'pull_request_target' "$f" && grep -qE 'ref:\s*\$\{\{\s*github\.event\.pull_request\.head' "$f"; then
    echo "  ERROR ($f): pull_request_target combined with checkout of PR head SHA — secret-exposing footgun. See security-hardening.md §4." >&2
    crit_rc=1
  fi

  # 4) No `permissions:` at all.
  if ! grep -qE '^\s*permissions\s*:' "$f"; then
    echo "  WARN ($f): no 'permissions:' block — relies on repo default. Add explicit permissions." >&2
    crit_rc=1
  fi
done

# Final exit code: any failure bubbles up.
rc=0
[[ $yl_rc -ne 0 ]] && rc=1
[[ $parse_rc -ne 0 ]] && rc=1
[[ $crit_rc -ne 0 ]] && rc=1

if [[ $rc -eq 0 ]]; then
  echo "lint OK (${#files[@]} file(s))"
fi
exit $rc
