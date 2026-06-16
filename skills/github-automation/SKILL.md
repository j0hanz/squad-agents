---
name: github-automation
description: "GitHub automation skill for writing, hardening, or debugging GitHub Actions workflows (PATH A) and building gh CLI scripts or batch API automation (PATH B). Trigger on: 'add CI', 'set up release', 'deploy to AWS/GCP/Azure', 'pin actions', 'harden workflow', 'matrix testing', 'composite action', 'reusable workflow', 'why isn't this triggering', 'close issues in bulk', 'sync labels', 'cross-repo bot', 'rate-limit-safe script', 'gh api', 'list PRs in a script'. Also trigger when user shares a .github/workflows/*.yml and asks to fix or improve it."
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

When in doubt: if the output is a YAML workflow file, use Path A. If the output is a shell/Python script calling `gh`, use Path B. For one-off CLI questions ("what command do I use?"), answer directly without creating a script file.

**Required output per path:**

- **Path A:** The workflow `.yml` file + lint result (which tier ran) + security auditor output summary. No YAML without lint passing.
- **Path B:** The complete script (no placeholders) + the recommended test invocation + auth prerequisites noted. One-off commands are answered inline — no script file.

**Routing for conceptual questions**: if the user asks a concept-only question (no authoring needed), use Path A but skip to the Answer shape section — give a docs-grounded explanation, no workflow file required.

---

## PATH A — ACTIONS: GitHub Actions Workflows

GitHub Actions is a YAML-on-top-of-event-handlers product with a lot of footguns: unpinned actions, over-broad `GITHUB_TOKEN` scopes, secret leaks through expression injection, `pull_request_target` misuse, cache poisoning, OIDC misconfig.

### When NOT to use Path A

- A _specific failing CI run_ the user wants triaged from logs → this path is not optimized for CI log triage; consider using the `diagnose` skill with the CI log as input.
- CodeQL or Dependabot configuration → this path can handle them but is not specialized; say so and proceed.

### Workflow

**Note on resolution:** use the absolute path of the directory containing this `SKILL.md` file as `<skill-dir>` (or `$CLAUDE_PLUGIN_ROOT/skills/github-automation` if available).

Follow these steps in order. Don't skip validation — runtime-only feedback is what makes Actions painful.

#### 1. Orient

Before writing anything:

```bash
ls -la .github/workflows/ 2>/dev/null || echo "no workflows yet"
```

If the user pointed at a specific file, read it first. If they're scaffolding from scratch, decide the filename — short, kebab-case, ends in `.yml` (e.g., `ci.yml`, `release.yml`, `deploy-prod.yml`).

#### 2. Classify intent

Pick one. The classification drives which reference to load:

| Intent                               | Load this reference                                                                                              |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Build/test on push or PR             | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § CI                                          |
| Release on tag / version bump        | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Release                                     |
| Deploy to cloud (AWS)                | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Deploy + `references/oidc-cloud.md` § AWS   |
| Deploy to cloud (GCP)                | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Deploy + `references/oidc-cloud.md` § GCP   |
| Deploy to cloud (Azure)              | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Deploy + `references/oidc-cloud.md` § Azure |
| Matrix / cross-version testing       | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Matrix                                      |
| Reusable workflow / composite action | **MANDATORY — READ ENTIRE FILE**: `references/workflow-recipes.md` § Reuse                                       |
| Harden existing workflow             | Apply the hardening checklist below, then **READ ENTIRE FILE**: `references/security-hardening.md`               |
| Diagnose a misbehaving workflow      | **MANDATORY — READ ENTIRE FILE**: `references/troubleshooting.md`                                                |
| Pure docs / conceptual question      | **MANDATORY — READ ENTIRE FILE**: `references/topic-map.md` → live `docs.github.com`                             |

You don't have to read the whole reference — jump to the section. **Do NOT load** references for intents you didn't select.

#### 3. Apply the recipe

Write the workflow file using the recipe as a starting point, then adapt to the user's stack.

**Three non-negotiables on every workflow you author:**

1. **NEVER use unpinned third-party actions.** Pin to a full SHA with the version tag as a trailing comment. First-party `actions/*` may use a major tag, but SHA pinning is the safer default.

   ```yaml
   - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
   ```

   **IMPORTANT:** Verify `gh auth status` before running pinning scripts. If not authenticated, explain this to the user as pinning requires API access.

   Use `<skill-dir>/scripts/pin_actions.py` to resolve tags → SHAs in bulk.

2. **NEVER write a workflow without `permissions:` at the top.** Default to least privilege at the workflow level, widen per-job only where needed:

   ```yaml
   permissions:
     contents: read
   ```

   For OIDC: add `id-token: write` only on the deploy job.

   **OIDC config values are not secrets.** IAM role ARN, GCP workload identity provider, Azure client/tenant IDs, region, and bucket name are non-sensitive. Store them as repo/environment **variables** (`vars.AWS_ROLE_ARN`, `vars.AWS_REGION`) so they are visible in workflow diffs and review. Storing them in `secrets.*` hides them unnecessarily and is a common mistake.

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

`lint.py` is the cross-platform linter. It prefers `actionlint` when installed, otherwise performs built-in Python-based checks for expression injection, SHA pinning, and permissions. Always invoke via the `<skill-dir>` absolute path (see the Scripts section for how to resolve it) — relative paths break when the working directory is not the project root.

**Do not report the task complete until lint passes. ALWAYS report which linter tier was used (e.g., "actionlint" or "built-in Python checks").**

**After lint passes — spawn the `workflow-security-auditor` subagent** (`agents/workflow-security-auditor.md`) for semantic security review that rule-based linting cannot catch. (Note: `disable-model-invocation: true` in this skill's frontmatter only prevents skill preloading into subagents — it does NOT block `Agent()` calls. Spawning the security auditor via `Agent()` works normally.)

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

### Hardening checklist (use when intent = "harden existing workflow")

Work through these in order. Each issue must be addressed before running lint:

- [ ] **SHA-pin all third-party actions** — replace `@v4`/`@main` with `@<40-char-sha> # vX.Y.Z`. Run `scripts/pin_actions.py` to do it in bulk.
- [ ] **Add `permissions:` block** — if absent, add `permissions: contents: read` at the workflow level. Widen per-job only where necessary (e.g., `id-token: write` only on a deploy job).
- [ ] **Fix expression injection** — find every `${{ github.event.pull_request.title }}`, `${{ github.head_ref }}`, `${{ github.event.*.body }}` etc. that appears inside a `run:` block and move it to an `env:` key. The shell must never see the raw expression value.
- [ ] **Audit `pull_request_target`** — if present, verify it does NOT check out or execute PR head code. If it does, change the trigger to `pull_request` (for the test job) + `workflow_run` (for the results/notification job).
- [ ] **Scope secrets** — check every `secrets.*` reference. Is each secret only accessed by the step that genuinely needs it? Move secrets to job-level `env:` rather than step-level when possible.
- [ ] **No long-lived cloud credentials** — if the workflow calls AWS/GCP/Azure, confirm it uses OIDC (`id-token: write` + the cloud provider's OIDC action), not a stored access key or service account JSON.
- [ ] **Check `runs-on`** — self-hosted runners on public repos with fork-PR triggers are dangerous. Flag this for the user if present.

After addressing all items, run lint and the security-auditor subagent as described in step 4.

### Scripts (Path A)

> **Resolving `<skill-dir>`:** Every script command uses `<skill-dir>` as a placeholder for the absolute path to this skill's directory. In Claude Code, resolve it as `$CLAUDE_PLUGIN_ROOT/skills/github-automation`. Example on a typical install: `~/.claude/skills/github-automation` or the path shown by your plugin loader. Do not use a relative path — scripts must be invoked from any working directory.

#### `scripts/pin_actions.py`

Resolves every `uses: org/repo@<ref>` in a workflow to a full commit SHA, rewrites in place, appends the original tag as a comment. Requires `gh` authenticated or `git` installed. Idempotent.

```bash
python <skill-dir>/scripts/pin_actions.py .github/workflows/ci.yml
python <skill-dir>/scripts/pin_actions.py .github/workflows/
```

#### `scripts/lint.py`

```bash
python <skill-dir>/scripts/lint.py .github/workflows/ci.yml
python <skill-dir>/scripts/lint.py .github/workflows/
```

Cross-platform linter. Tries: `actionlint` → `yamllint` → built-in Python check. Always use absolute paths to avoid path-resolution issues in subagent contexts.

### Answer shape (Path A)

For _authoring_ tasks, the output is the file plus a short summary mentioning: what you wrote, hardening choices (permissions, pinning, OIDC vs. secret), the lint result, and how to verify.

For _conceptual_ questions, fall back to docs-grounded answers: direct answer, link the narrowest `docs.github.com` page, only include YAML when asked. Mark inferences explicitly: `According to docs, ...` vs. `Inference: ...`.

### Common mistakes to avoid (Path A)

These are in addition to the three non-negotiables above (permissions, SHA-pinning, no untrusted interpolation) — don't restate those:

- **NEVER** pin to `@main` or `@master`.
- **NEVER** suggest long-lived `AWS_ACCESS_KEY_ID` / `GCP_SA_KEY` secrets when OIDC is the documented path.
- **NEVER** use `pull_request_target` for builds — it runs with secrets on PR head code from forks. The safe pattern for "run tests in PR context, then post results with write access" is `pull_request` for the build + `workflow_run` for the follow-up step.
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

### One-off commands vs. headless scripts

If the user asks "what command do I use to…" or "how do I quickly…", give the `gh` command directly. Do NOT create a script file, add `GH_PROMPT_DISABLED`, or add auth checks. Reserve script creation for tasks that need to run in CI or repeat across many resources.

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

### Auth token selection for cross-repo automation

When the automation touches more than one repo or org-level resources:

- Use `GH_ORG_TOKEN` (a fine-grained PAT with the required scopes across all targets), not `GITHUB_TOKEN`
- Export it as `GH_TOKEN` so the CLI picks it up: `export GH_TOKEN="$GH_ORG_TOKEN"`
- Store it in GitHub Secrets as a named secret (e.g., `GH_ORG_TOKEN`), not as `GITHUB_TOKEN` which gets the automatic repo-scoped token

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
