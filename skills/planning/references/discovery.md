# Discovery Guide

`discover.py` resolves file paths and code symbols to verified markdown links ready to paste into plan tasks.

## Usage

```bash
# Find files matching a pattern
python <skill-dir>/scripts/discover.py --files "src/**/*.ts,src/**/*.tsx"

# Find specific symbols
python <skill-dir>/scripts/discover.py --names "parseConfig,UserService" --ext ts,tsx

# Regex symbol pattern (e.g., all React hooks)
python <skill-dir>/scripts/discover.py --names "/^use[A-Z]/" --ext ts,tsx

# Combined: files + symbols
python <skill-dir>/scripts/discover.py \
  --files "src/auth/**/*.ts" \
  --names "signToken,validateToken"
```

## Output (paste directly into plan tasks)

```markdown
- [src/auth/jwt.ts](src/auth/jwt.ts)
- [signToken](src/auth/jwt.ts#L24) — `src/auth/jwt.ts:24`
- [validateToken](src/auth/jwt.ts#L41) — `src/auth/jwt.ts:41`
```

Copy the link blocks directly into `Files:` and `Symbols:` fields. Never fabricate `#L` anchors.

## Rules

1. Run discovery before writing task fields — never guess paths
2. Copy line anchors exactly as reported
3. For new files (not yet created): mark as `[UNVERIFIED: path/to/new-file.ts](UNVERIFIED)` and note which task creates it
4. For cross-repo paths: use `--assume-paths` modifier and document assumptions

## When discovery returns no matches

| Situation                    | Action                                            |
| ---------------------------- | ------------------------------------------------- |
| Pattern returns 0 results    | Simplify glob; check the directory exists         |
| Symbol not found             | Try broader pattern; verify the symbol name       |
| New file created during plan | Mark UNVERIFIED; resolve after creating task runs |
| Cross-repo path needed       | Document as assumption; use `--assume-paths`      |

## Full options

```bash
python <skill-dir>/scripts/discover.py --help
```

Options: `--root`, `--files`, `--names`, `--ext`, `--max`, `--json`, `--no-lines`
