---
name: github-automation
description: >-
  GitHub automation — two paths. PATH A (ACTIONS): Writing, editing, linting, hardening, or
  debugging GitHub Actions workflows (.github/workflows/*.yml), reusable workflows,
  composite/JS/Docker actions, OIDC cloud deploys, SHA pinning, GITHUB_TOKEN scopes, matrices,
  caching, concurrency, environments, or migrating from Jenkins/CircleCI/GitLab/Travis. Triggers
  on "add CI", "set up release", "pin these actions", "fix this YAML", "deploy to AWS from
  GitHub". PATH B (CLI): Building `gh` CLI scripts, headless automation, cross-repo bots, `gh
  api` batch operations, pagination, rate-limit-safe workflows, or production-grade gh scripting.
disable-model-invocation: true
allowed-tools: Bash(python *) Bash(python3 *)
---

# GitHub Automation

## Routing

Read this first — pick one path and follow only that section.

| Signal                                                                                                                                                                   | Path                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| Writing, editing, linting, or hardening `.github/workflows/*.yml`; YAML workflow authoring; "add CI", "set up release", "pin these actions", "why isn't this triggering" | **PATH A — ACTIONS** |
| Building a `gh` script, batch API operations, headless automation, cross-repo bot, `gh api` usage, rate-limit-safe looping                                               | **PATH B — CLI**     |

When in doubt: if the output is a YAML workflow file, use Path A. If the output is a shell/Python script calling `gh`, use Path B.

---

## PATH A — ACTIONS: GitHub Actions Workflows

GitHub Actions is a YAML-on-top-of-event-handlers product with a lot of footguns: unpinned actions, over-broad `GITHUB_TOKEN` scopes, secret leaks through expression injection, `pull_request_target` misuse, cache poisoning, OIDC misconfig.

### When NOT to use Path A

- A _specific failing CI run_ the user wants triaged from logs → defer to `gh-fix-ci` if present.
- CodeQL config → `codeql`. Dependabot config → `dependabot`.

If those sibling skills are not present, this path can still answer, but say so.

### Workflow

Follow these steps in order. Don't skip validation — runtime-only feedback is what makes Actions painful.

#### 1. Orient

Before writing anything:

```bash
ls -la .github/workflows/ 2>/dev/null || echo "no workflows yet"
```

If the user pointed at a specific file, read it first. If they're scaffolding from scratch, decide the filename — short, kebab-case, ends in `.yml` (e.g., `ci.yml`, `release.yml`, `deploy-prod.yml`).

#### 2. Classify intent

Pick one. The classification drives which reference to load:

| Intent                               | Load this reference                                                                                                      |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| Build/test on push or PR             | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § CI                                                  |
| Release on tag / version bump        | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Release                                             |
| Deploy to cloud (AWS)                | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Deploy + `references/oidc-cloud.md` § AWS           |
| Deploy to cloud (GCP)                | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Deploy + `references/oidc-cloud.md` § GCP           |
| Deploy to cloud (Azure)              | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Deploy + `references/oidc-cloud.md` § Azure         |
| Matrix / cross-version testing       | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Matrix                                              |
| Reusable workflow / composite action | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Reuse                                               |
| Harden existing workflow             | **MANDATORY — READ ENTIRE FILE**: `references/security-hardening.md`                                                     |
| Diagnose a misbehaving workflow      | **MANDATORY — READ ENTIRE FILE**: `references/troubleshooting.md`                                                        |
| Pure docs / conceptual question      | **MANDATORY — READ ENTIRE FILE**: `references/topic-map.md` → live `docs.github.com`                                     |

You don't have to read the whole reference — jump to the section. **Do NOT load** references for intents you didn't select.

#### 3. Apply the recipe

Write the workflow file using the recipe as a starting point, then adapt to the user's stack.

**Three non-negotiables on every workflow you author:**

1. **NEVER use unpinned third-party actions.** Pin to a full SHA with the version tag as a trailing comment. First-party `actions/*` may use a major tag, but SHA pinning is the safer default.

   ```yaml
   - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
   ```

   **IMPORTANT:** Verify `gh auth status` before running pinning scripts. If not authenticated, explain this to the user as pinning requires API access.

   Use `scripts/pin_actions.py` to resolve tags → SHAs in bulk.

2. **NEVER write a workflow without `permissions:` at the top.** Default to least privilege at the workflow level, widen per-job only where needed:

   ```yaml
   permissions:
     contents: read
   ```

   For OIDC: add `id-token: write` only on the deploy job.

3. **NEVER interpolate untrusted input into `run:` blocks.** Pipe through `env:` so the shell sees a real variable:

   ```yaml
   - env:
       PR_TITLE: ${{ github.event.pull_request.title }}
     run: echo "$PR_TITLE"
   ```

#### 4. Validate before claiming done

```bash
python <skill-dir>/scripts/lint.py .github/workflows/<file>.yml
```

`lint.py` is the cross-platform linter. It prefers `actionlint` when installed, otherwise performs built-in Python-based checks for expression injection, SHA pinning, and permissions.

**Do not report the task complete until lint passes. ALWAYS report which linter tier was used (e.g., "actionlint" or "built-in Python checks").**

**After lint passes — spawn the `workflow-security-auditor` subagent** (`agents/workflow-security-auditor.md`) for semantic security review that rule-based linting cannot catch:

```
Agent(
  description: "Security audit of [workflow filename]",
  prompt: |
    workflow_path: [absolute path to the .github/workflows/*.yml file]
    project_root: [repository root, for resolving composite action paths]
)
```

The agent evaluates 7 semantic dimensions: OIDC trust scope, `pull_request_target` safety, secret scope tightness, token scope minimality, runner trust level, artifact/cache poisoning surface, and dispatch input trust. Check the output:
- `summary.critical > 0` or `summary.high > 0` → **resolve before reporting complete**
- `summary.medium` or `summary.low` → disclose findings to the user; they do not block completion
- `clean: true` → workflow is semantically secure; proceed

#### 5. Verify the trigger fires

- `push`/`pull_request` workflow → push a branch and watch it
- `workflow_dispatch` → `gh workflow run <file>.yml`
- `schedule` → note that the first run can be delayed up to ~15 min, and crons must be UTC

### Scripts (Path A)

#### `scripts/pin_actions.py`

Resolves every `uses: org/repo@<ref>` in a workflow to a full commit SHA, rewrites in place, appends the original tag as a comment. Requires `gh` authenticated or `git` installed. Idempotent.

```bash
python <skill-dir>/scripts/pin_actions.py .github/workflows/ci.yml
python <skill-dir>/scripts/pin_actions.py .github/workflows/   # whole directory
```

#### `scripts/lint.py` (Preferred over `lint.sh`)

```bash
python <skill-dir>/scripts/lint.py .github/workflows/ci.yml
python <skill-dir>/scripts/lint.py .github/workflows/   # whole directory
```

Cross-platform linter. Tries: `actionlint` → `yamllint` → built-in Python check.

### Answer shape (Path A)

For _authoring_ tasks, the output is the file plus a short summary mentioning: what you wrote, hardening choices (permissions, pinning, OIDC vs. secret), the lint result, and how to verify.

For _conceptual_ questions, fall back to docs-grounded answers: direct answer, link the narrowest `docs.github.com` page, only include YAML when asked. Mark inferences explicitly: `According to docs, ...` vs. `Inference: ...`.

### Common mistakes to avoid (Path A)

These are in addition to the three non-negotiables above (permissions, SHA-pinning, no untrusted interpolation) — don't restate those:

- **NEVER** pin to `@main` or `@master`.
- **NEVER** suggest long-lived `AWS_ACCESS_KEY_ID` / `GCP_SA_KEY` secrets when OIDC is the documented path.
- **NEVER** use `pull_request_target` for builds — it runs with secrets on PR head code from forks.
- **NEVER** confuse reusable workflows (`uses: org/repo/.github/workflows/x.yml@ref`) with composite actions (`uses: ./path/to/action`).
- **NEVER** reach for matrix when a couple of explicit jobs would be clearer.

### Bundled references (Path A)

- **`references/workflow-recipes.md`** — minimal templates for CI, release, deploy, matrix, reusable workflows, composite actions.
- **`references/security-hardening.md`** — permissions/SHA pinning/OIDC patterns.
- **`references/oidc-cloud.md`** — OIDC blocks for AWS, GCP, Azure.
- **`references/troubleshooting.md`** — common workflow failure patterns and fixes.
- **`references/topic-map.md`** — canonical `docs.github.com` URLs by topic.

---

## PATH B — CLI: GitHub CLI Automation

This path is for building and hardening GitHub CLI automation used in CI/CD, headless scripts, bots, or cross-repo workflows.

### Expert Anti-Patterns (NEVER do these)

- **NEVER** wrap a manual workflow in `gh` automation. If the user only needs a one-off command, do not convert it into a headless script.
- **NEVER** use `GITHUB_TOKEN` for cross-repo or organization-level automation. That token is repo-scoped and is silently invalid outside the current repo.
- **NEVER** assume `gh api --paginate` is safe for mutations. If the list changes while you mutate it, snapshot IDs first and iterate over the snapshot.
- **NEVER** hide failures with `|| true` unless you already filtered for a known idempotent duplicate condition.
- **NEVER** use `--template` for machine-readable automation output. Templates are brittle and break when GitHub changes field ordering or output formatting.

### When to prefer `gh api`

For production automation, choose `gh api` over wrapper commands. It gives you structured JSON output, a single auth surface, built-in `--paginate`, `--jq`, and HTTP method support. Use wrapper commands like `gh pr create` only for simple manual CLI steps, not headless scripts.

### Headless script rules

Always make automation scripts non-interactive:

- set `GH_PROMPT_DISABLED=1` in CI or batch scripts
- verify auth with `gh auth status` before mutating state
- use `GH_TOKEN` / `GITHUB_TOKEN` only for the intended repo scope
- avoid `gh auth login` in unattended environments

```bash
export GH_PROMPT_DISABLED=1
export GH_TOKEN="${{ secrets.GH_TOKEN }}"
gh auth status
gh api /repos/:owner/:repo/issues --json number,title,state
```

### Safe auth and token selection

- prefer GitHub App tokens or OIDC over long-lived PATs in automation
- use `GITHUB_TOKEN` only when the action is confined to the current repo
- for cross-repo automation, inject a separate fine-grained token into the environment

If the automation needs organization-level or multi-repo access:
`MANDATORY — READ ENTIRE FILE: references/headless-auth-patterns.md`
**Do NOT load** this reference if the automation only targets the current repo context.

For PR triage and failing Actions log extraction, use `scripts/inspect_pr_checks.py`:
`MANDATORY: run python <skill-dir>/scripts/inspect_pr_checks.py --help` before using it.

### Machine-readable output patterns

- `--json` returns JSON fields directly
- `--jq` extracts just the values you need
- `--template` is brittle; prefer `--json` + `jq`

```bash
gh api repos/:owner/:repo/issues --json number,title,state --jq '.[].number'
```

### Pagination and batch safety

- use `gh api --paginate` instead of manual `Link` header handling
- use `--limit N` when you only need the first N results
- snapshot IDs before mutating if the list may change during processing
- add batching and jitter for write-heavy loops to avoid secondary rate limits

If automating more than a few dozen items:
`MANDATORY — READ ENTIRE FILE: references/api-pagination-and-limits.md`
**Do NOT load** this reference if automating fewer than 20 items.

Example safe batch pattern:

```bash
gh api repos/:owner/:repo/issues --paginate --jq '.[].number' > issue_ids.txt
cat issue_ids.txt | while read issue; do
  gh api -X PATCH repos/:owner/:repo/issues/$issue -f state=closed
  sleep 1
done
```

### Idempotent automation patterns

- prefer a read-then-create flow instead of swallowing failures from `POST`
- use `PATCH` for updates to existing resources when the API supports it

```bash
exists=$(gh api repos/:owner/:repo/labels/needs-triage --jq '.name' 2>/dev/null || true)
if [ -z "$exists" ]; then
  gh api -X POST repos/:owner/:repo/labels \
    -f name="needs-triage" -f color="ff0000"
fi
```

### Recommended script checklist

- [ ] `GH_PROMPT_DISABLED=1` is set for all script runs
- [ ] auth is validated before the first API call
- [ ] output is consumed with `--json` or `--jq`
- [ ] batch mutations are rate-limit-safe
- [ ] cross-repo access uses an explicit token, not the default repo token
- [ ] creation commands are idempotent or tolerate already-existing resources

### Bundled references (Path B)

- **`references/headless-auth-patterns.md`** — GH_TOKEN, GitHub App tokens, OIDC for cross-repo/org automation.
- **`references/api-pagination-and-limits.md`** — safe pagination and rate-limit strategies for large batch operations.
