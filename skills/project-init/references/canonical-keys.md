# Claim Schema & Canonical Keys

This is the OUTPUT-SCHEMA contract for Phase 1 discovery lanes. Each lane returns a **JSON array of claims**. Claims whose key is outside this closed vocabulary, or whose evidence fails verification, are dropped by `init.py generate` (and listed in the dropped report). Nothing else reaches `AGENTS.md`.

## Claim object

```json
{
  "key": "cmd.build",
  "value": "pnpm build",
  "evidence": { "path": "package.json", "match": "\"build\":" },
  "confidence": 0.8
}
```

- **key** — must be a fixed key or a key under an allowed prefix (below). Anything else is dropped.
- **value** — the fact, one physical line. Sanitized on write (newlines/control chars stripped), capped at 320 chars. `conv.*` values may pack several atomic facts (see "`conv.*` atomic facts" below); every other key is always a single fact.
- **evidence.path** — repo-relative path that PROVES the claim. Must resolve to a readable text file inside the repo root (symlinks resolved). Out-of-repo paths are rejected.
- **evidence.match** — a literal substring that must appear in the cited file. **Required** for `pm`, `cmd.*`, and `file.*` (command/version keys) — a claim of a runnable command with no `match` is dropped as unverifiable. Optional for `dep.*` and `conv.*`.
- **confidence** — 0–1; tiebreaker only. Evidence tier (lockfile > manifest/config > other > prose) wins first.

## Closed vocabulary

The command buckets (`cmd.*`, `file.*`) are a **closed task set** — an unknown task is dropped (logged), so two lanes can't fragment the toolchain into `cmd.test` + `cmd.tests`. The repo-specific buckets (`dep.*`, `conv.*`) keep an **open suffix** but are **count-capped**. To widen the command set, edit `CMD_KEYS` / `FILE_KEYS` / `CMD_ALIASES` in `scripts/init.py`.

| Key           | Section              | Notes                                                                                                             |
| :------------ | :------------------- | :---------------------------------------------------------------------------------------------------------------- |
| `purpose`     | header               | one sentence; what the repo does (usually passed via `--purpose`, not a claim)                                    |
| `stack`       | header               | languages/frameworks in one line, e.g. `TypeScript + Node` (L2 lane)                                              |
| `pm`          | Package Manager      | the package manager name (e.g. `pnpm`) — **match required**                                                       |
| `cmd.<task>`  | Package Manager      | task ∈ `{install, build, dev, start, run, test, lint, format, typecheck, validate, release}` — **match required** |
| `file.<task>` | File-Scoped Commands | task ∈ `{lint, test, typecheck, format}`, file-targeted (e.g. `eslint path/to/file.js`) — **match required**      |
| `dep.<name>`  | Dependency Locations | where deps live, e.g. `dep.node_modules` → `node_modules/` — **open suffix, max 6**                               |
| `conv.<name>` | Key Conventions      | a real, verifiable convention; may pack several atomic facts (see below) — **open suffix, max 7 keys**            |

### `conv.*` atomic facts

A `conv.*` value may hold more than one atomic fact, joined by the literal token `||`. The renderer splits each `conv.*` value on that token and emits one bullet per fact. Embed backticks around real identifiers/paths directly in the fact text — the renderer does **not** add them for `conv.*` (unlike `pm`/`cmd.*`/`dep.*`, where the renderer backticks the whole value itself, so don't double up there).

A claim like:

```json
"value": "Throw `FsError` carrying a `Problem` (`src/core/errors.ts`) || Never throw raw `Error`"
```

renders as:

- Throw `FsError` carrying a `Problem` (`src/core/errors.ts`)
- Never throw raw `Error`

Each piece still counts toward the 320-char value cap as one string — keep a topic's whole packed value under that, not 320 chars per fact.

**Aliases** (normalized automatically): `tests`/`unit`→`test`, `tsc`/`tc`/`types`→`typecheck`, `fmt`→`format`, `serve`→`start`, `watch`→`dev`, `compile`→`build`, `check`→`validate`, `setup`→`install`.

`purpose`, `pm`, `cmd.build`, `cmd.test` are protected from budget trimming (never silently dropped if a winner exists). A repo legitimately lacking a build/test command simply omits it — absence is not a lint failure.

## Evidence tier (derived from the cited path, not agent-declared)

| Tier | Cited file        | Example                                                                      |
| :--- | :---------------- | :--------------------------------------------------------------------------- |
| 4    | lockfile          | `pnpm-lock.yaml`, `go.sum`, `Cargo.lock`                                     |
| 3    | manifest / config | `package.json`, `pyproject.toml`, `tsconfig.json`, `.github/workflows/*.yml` |
| 2    | other source file | a `Makefile` command, a script                                               |
| 1    | prose / docs      | `README.md`, `*.rst`                                                         |

When two lanes claim the same key, the higher tier wins (then higher confidence). This is how `pnpm` (citing the lockfile) beats `npm` (citing a README sentence) automatically.

## Lane guidance

- Keep claims minimal and high-signal — the file budget is `<100` lines. Prefer 3–7 `conv.*` topics, not 20; pack 1-3 atomic facts per topic with `||`, not one giant run-on sentence.
- Never invent a command. If you can't cite it with a literal `match`, don't claim it.
- Commands are TEXT. Do not run them; you have no Bash.
