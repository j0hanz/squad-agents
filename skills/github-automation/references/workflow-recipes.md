# Workflow Recipes

Minimal, current templates. Copy the structure; swap the language/tool steps.

All recipes assume the **three non-negotiables** from SKILL.md:

- Pin third-party actions to SHA
- `permissions:` set explicitly, least privilege
- Untrusted input goes through `env:`, never directly into `run:`

For terseness, recipes below show `@v4` style — the model should run `scripts/pin_actions.py` (or pin manually) before finalizing.

---

## CI

The 90% case: build + test on push and PR.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4 # swap for setup-python, setup-go, etc.
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm test
```

**Decisions to call out when authoring:**

- `concurrency` cancels superseded runs on the same branch (saves minutes), but **never** cancels on `main` — that's how you accidentally skip a deploy.
- `cache: 'npm'` in `setup-node` is the supported path. Don't reach for `actions/cache` directly unless you need a custom key.
- For monorepos, add `paths:` filters under `pull_request:` so the job only fires on relevant changes.

### Path filter variant

```yaml
on:
  pull_request:
    paths:
      - "packages/api/**"
      - ".github/workflows/api-ci.yml"
```

### Skip-CI for docs-only changes

Use `paths-ignore` rather than `if:` on every step — it short-circuits the whole run.

---

## Release

Triggered by a tag, builds artifacts, publishes a GitHub Release.

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

permissions:
  contents: write # to create the release
  id-token: write # for attestations / OIDC publish

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - run: npm ci
      - run: npm run build
      - run: npm pack

      - uses: actions/attest-build-provenance@v1
        with:
          subject-path: "*.tgz"

      - uses: softprops/action-gh-release@v2 # pin to SHA in real use
        with:
          files: "*.tgz"
          generate_release_notes: true
```

For npm publish, add an OIDC-based publish step (npm supports trusted publishers as of 2024+). For PyPI, use `pypa/gh-action-pypi-publish` with `id-token: write`. Both avoid storing publish tokens entirely.

---

## Deploy

Use OIDC for cloud credentials. See `oidc-cloud.md` for the cloud-side trust policy. The workflow side:

```yaml
name: Deploy

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write # required for OIDC

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production # gates this with environment protection rules
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gha-deployer
          aws-region: us-east-1

      - run: aws s3 sync ./dist s3://my-bucket --delete
```

**Decisions:**

- `environment: production` enables required reviewers / wait timers / branch protection from the GitHub UI. Always use environments for prod.
- `id-token: write` goes at the **job** level, not the workflow level. Other jobs (build, test) shouldn't get the OIDC token.
- Region, role ARN, and bucket name should be repo or environment **variables** (`vars.AWS_REGION`), not secrets. They're not sensitive and putting them in vars makes them visible during review.

---

## Matrix

Test across versions/OSes. Keep the matrix dimension small — it multiplies fast.

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node: ["20", "22"]
        include:
          - os: ubuntu-latest
            node: "20"
            coverage: true # extra flag on one cell
        exclude:
          - os: macos-latest
            node: "20" # don't bother running this combo
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: npm ci
      - run: npm test
      - if: matrix.coverage
        run: npm run coverage
```

**Decisions:**

- `fail-fast: false` so one failing cell doesn't cancel the rest — usually what you want for cross-platform.
- `include` adds cells; `exclude` removes them.
- When the matrix gets to >12 cells, reconsider — maybe split into two workflows or test fewer combos on PR + full matrix on main.

### Conditional matrix expansion

Generate the matrix dynamically from a job output (useful for "test changed packages"):

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.changed.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
      - id: changed
        run: echo "packages=$(./scripts/detect-changed.sh)" >> "$GITHUB_OUTPUT"

  test:
    needs: detect
    if: needs.detect.outputs.packages != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: ${{ fromJSON(needs.detect.outputs.packages) }}
    steps:
      - run: cd packages/${{ matrix.package }} && npm test
```

---

## Reusable workflows

Call a workflow from another workflow. Use when you have shared CI logic across repos or across many workflows in one repo.

**Caller:**

```yaml
jobs:
  call-build:
    uses: my-org/shared-workflows/.github/workflows/node-build.yml@v1 # pin to SHA in real use
    with:
      node-version: "20"
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**Called (in `.github/workflows/node-build.yml`):**

```yaml
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        required: true
    secrets:
      NPM_TOKEN:
        required: true

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci
```

**Reusable workflow vs. composite action — when to pick which:**

- **Reusable workflow** (`uses:` at job level): runs as its own job(s), has its own runner, can use matrix, can set permissions. Better for "I want a whole job's worth of logic shared."
- **Composite action** (`uses:` at step level): inlines into the calling job, shares the runner. Better for a sequence of steps you want to invoke as one.

If you find yourself nesting reusable workflows >2 levels deep, that's a smell — flatten.

---

## Composite action

Bundle a sequence of steps as a single `uses:`. Lives in `.github/actions/<name>/action.yml`.

```yaml
# .github/actions/setup-project/action.yml
name: Setup project
description: Checkout, install Node, restore caches, install deps
inputs:
  node-version:
    description: Node version
    required: false
    default: "20"
runs:
  using: composite
  steps:
    - uses: actions/checkout@v4

    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: "npm"

    - shell: bash
      run: npm ci
```

Caller:

```yaml
steps:
  - uses: ./.github/actions/setup-project
    with:
      node-version: "22"
```

**Notes:**

- Every `run:` in a composite **must** specify `shell:` — there's no default.
- Composite actions can't use `secrets:` directly. Pass them via inputs, but mask carefully.
- Local composite actions (`./.github/actions/...`) require `actions/checkout` before they can be referenced.

---

## Scheduled workflow

```yaml
on:
  schedule:
    - cron: "0 6 * * *" # 06:00 UTC daily
  workflow_dispatch: # always include this so humans can trigger manually
```

**Gotchas:**

- Crons are in UTC, full stop. No timezone option.
- Schedules on default branch only.
- GitHub may delay scheduled runs by up to ~15 min during high load. If you need second-precision, use an external cron.
- Schedules are disabled automatically after 60 days of repository inactivity.
