# Discovery Guide: Verifying File Paths & Code Symbols

## Why Discovery Matters

Plans are executed by agents or developers unfamiliar with the repository. Every file path and code symbol must be **verified to exist** — otherwise an agent wastes time searching or fabricates paths.

## Running Discovery

From the repository root, use `discover.mjs`:

```bash
# Find TypeScript files matching a pattern
node <skill>/scripts/discover.mjs --files "src/**/*.ts,src/**/*.tsx" --ext ts,tsx

# Find specific function/class names
node <skill>/scripts/discover.mjs --names "parseConfig,UserService" --ext ts,tsx

# Regex pattern (e.g., all React hooks)
node <skill>/scripts/discover.mjs --names "/^use[A-Z]/" --ext ts,tsx

# Combined: files + symbols
node <skill>/scripts/discover.mjs \
  --files "src/auth/**/*.ts" \
  --names "SessionAccess,parseJWT,validateToken" \
  --ext ts,tsx
```

## Discovery Output Format

```
## Files

- [src/auth/session.ts](src/auth/session.ts)
- [src/auth/jwt.ts](src/auth/jwt.ts)

## Symbols

- [validateToken](src/auth/jwt.ts#L42)
- [SessionAccess](src/auth/session.ts#L18)
```

## Rules

1. **Run discovery before writing the plan** — don't guess paths
2. **Copy line anchors exactly** — never fabricate `#L999` if line 999 doesn't exist
3. **Paste only what you reference** — don't bloat plan with unrelated files
4. **If discovery returns no matches**: Simplify the pattern, or check if directory exists
5. **For new files**: Discovery can't find files that don't exist yet — document as assumptions

## When Discovery Fails

| Situation | Action |
|-----------|--------|
| Pattern returns 0 results | Simplify glob pattern or check directory exists |
| Symbol not found | Try `--names "/.*/"` to see all symbols, then narrow |
| Expected path doesn't exist | Mark `UNVERIFIED: [path]` in plan; note resolution plan |
| New files created during authoring | Re-run discovery before finalizing plan |
| Cross-repo discovery needed | Use `--assume-paths` flag; document assumptions |

## Multi-Repo & Cross-Repo Scenarios

**Discovery works within a single repository.** For multi-repo scenarios:

1. **Option A: Use `--assume-paths`** — Assume paths exist; note assumptions in plan
2. **Option B: Document assumptions** — Mark expected paths as `UNVERIFIED` with resolution plan
3. **Option C: Create per-repo plans** — One plan per service; link via dependencies

## Post-Write Validation

After saving the plan, re-verify all links:

```bash
node <skill>/scripts/discover.mjs \
  --files "src/auth/session.ts,src/auth/jwt.ts" \
  --names "validateToken,SessionAccess" \
  --ext ts,tsx
```

**Check**: 
- Every file link matches discovery output
- Every symbol link matches discovery output with correct line number
- If line numbers drifted, update from latest discovery

## Full Discovery Options

```bash
node skills/create-plan/scripts/discover.mjs --help
```
