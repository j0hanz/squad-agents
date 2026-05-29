#!/usr/bin/env node
/**
 * discover.mjs — Repository discovery helper for implementation plans.
 *
 * Scans the repository for files matching glob patterns and/or symbol
 * names (functions, classes, components, exports, routes, tests, …)
 * and prints Markdown reference links ready to paste into a plan.
 *
 * Targets Node.js 24.x LTS. Uses only built-ins (node:fs.globSync,
 * node:util.parseArgs); no runtime dependencies.
 */

import { readFileSync, statSync, globSync } from "node:fs";
import { join, sep, posix } from "node:path";
import { parseArgs } from "node:util";
import { argv, cwd, exit, stdout, stderr, version } from "node:process";

// Read-only discovery; for an extra seat-belt run with:
//   node --permission --allow-fs-read=. scripts/discover.mjs ...

// Skip files larger than this when scanning for symbols. Discovery is a
// CLI workflow; bounding read size keeps memory predictable on large repos.
const MAX_FILE_BYTES = 2_000_000;

// Minimum supported Node major. Aligned with the project's Node 24 baseline.
const MIN_NODE_MAJOR = 24;

const VERSION = "1.0.0";

const IGNORED_DIRS = new Set([
  "node_modules",
  "dist",
  "build",
  "out",
  ".nuxt",
  ".turbo",
  ".cache",
  ".venv",
  "venv",
  "__pycache__",
  "coverage",
  ".pytest_cache",
  "target",
  "bin",
  "obj",
]);

const BINARY_EXT = new Set([
  "png",
  "jpg",
  "jpeg",
  "gif",
  "webp",
  "ico",
  "pdf",
  "zip",
  "tar",
  "gz",
  "exe",
  "dll",
  "so",
  "dylib",
  "wasm",
  "woff",
  "woff2",
  "ttf",
  "otf",
  "mp3",
  "mp4",
  "mov",
  "avi",
  "wav",
  "ogg",
  "bin",
]);

// Heuristic symbol declaration patterns for common languages.
// All patterns are stateful (`g`/`m`); callers must reset `lastIndex`.
const DECL_PATTERNS = [
  // JS/TS: function, class, const/let/var, type, interface, enum, default exports
  /\b(?:export\s+(?:default\s+)?(?:async\s+)?)?(?:function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)/g,
  /\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[:=]/g,
  // Python
  /^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)/gm,
  /^\s*class\s+([A-Za-z_]\w*)/gm,
  // Go
  /\bfunc\s+(?:\([^)]*\)\s+)?([A-Za-z_]\w*)/g,
  /\btype\s+([A-Za-z_]\w*)\s+(?:struct|interface)/g,
  // Rust
  /\bfn\s+([A-Za-z_]\w*)/g,
  /\b(?:struct|enum|trait|impl)\s+([A-Za-z_]\w*)/g,
  // Java/C#/Kotlin
  /\b(?:public|private|protected|internal|static|final|abstract)\s+[\w<>[\],\s]*?\s+([A-Za-z_]\w*)\s*\(/g,
];

const HELP = `discover.mjs — Repository discovery helper for implementation plans.

Usage:
  node scripts/discover.mjs [options]

Options:
  --root <dir>      Repo root to scan (default: cwd)
  --files <globs>   Comma-separated file globs (e.g. "src/**/*.{ts,tsx},**/*.md")
  --names <list>    Comma-separated symbol names or /regex/ patterns
  --ext  <list>     Comma-separated extensions filter (e.g. "ts,tsx,js")
  --max  <n>        Max matches per category (default: 200)
  --json            Emit JSON instead of Markdown
  --no-lines        Omit line numbers from symbol links
  -h, --help        Show this help
  --version         Print version info and exit

Examples:
  node scripts/discover.mjs --files "src/**/*.ts" --names "parseConfig,UserService"
  node scripts/discover.mjs --names "/^use[A-Z]/" --ext ts,tsx
  node scripts/discover.mjs --files "plan/**/*.md" --json

Notes:
  - Zero dependencies; uses only Node built-ins.
  - Brace expansion is supported in --files patterns (e.g. **/*.{ts,tsx}).
  - Skips node_modules, dist, build, out, .next, .venv, __pycache__, coverage,
    target, bin, obj, and all dot-directories (.git, .github, .vscode, …).
  - Symbol detection is heuristic across JS/TS, Python, Go, Rust, Java/Kotlin/C#.
    Treat results as candidates.
  - Read-only: safe under Node's permission model with --allow-fs-read=<root>.
`;

// ─── Environment ────────────────────────────────────────────────────────────

function assertNodeVersion() {
  const m = /^v(\d+)\./.exec(version);
  const major = m ? Number.parseInt(m[1], 10) : 0;
  if (major < MIN_NODE_MAJOR) {
    stderr.write(
      `discover.mjs: requires Node.js >= ${MIN_NODE_MAJOR} (current ${version}).\n`,
    );
    exit(2);
  }
}

// ─── CLI parsing ────────────────────────────────────────────────────────────

// Split a comma-separated CLI value, ignoring commas inside `{…}` so that
// brace expressions like `**/*.{ts,tsx}` survive intact.
function splitList(s) {
  const input = s ?? "";
  if (input.length === 0) return [];
  const out = [];
  let depth = 0;
  let buf = "";
  for (const ch of input) {
    if (ch === "{") depth++;
    else if (ch === "}") depth = Math.max(0, depth - 1);

    if (ch === "," && depth === 0) {
      if (buf.trim()) out.push(buf.trim());
      buf = "";
    } else {
      buf += ch;
    }
  }
  if (buf.trim()) out.push(buf.trim());
  return out;
}

function parseCliArgs(rawArgs) {
  const { values } = parseArgs({
    args: rawArgs,
    options: {
      root: { type: "string" },
      files: { type: "string" },
      names: { type: "string" },
      ext: { type: "string" },
      max: { type: "string" },
      json: { type: "boolean", default: false },
      "no-lines": { type: "boolean", default: false },
      help: { type: "boolean", short: "h", default: false },
      version: { type: "boolean", default: false },
    },
    strict: true,
    allowPositionals: false,
  });
  const max = Number.parseInt(values.max ?? "", 10);
  return {
    root: values.root ?? cwd(),
    files: splitList(values.files),
    names: splitList(values.names),
    ext: splitList(values.ext).map((e) => e.replace(/^\./, "").toLowerCase()),
    max: Number.isFinite(max) && max > 0 ? max : 200,
    json: values.json === true,
    lines: values["no-lines"] !== true,
    help: values.help === true,
    version: values.version === true,
  };
}

function compileNamePattern(token) {
  const m = /^\/(.+)\/([gimsuy]*)$/.exec(token);
  if (m) {
    // Strip stateful flags (g, y); reusing such regexes with .test() in
    // loops produces alternating results due to lastIndex carry-over.
    const flags = (m[2] || "").replace(/[gy]/g, "");
    return new RegExp(m[1], flags);
  }
  // Plain name: word-boundary, exact match.
  const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`\\b${escaped}\\b`);
}

// ─── Path / file filtering ──────────────────────────────────────────────────

// Exclude predicate for fs.globSync. Returning true prunes the entry (and,
// for directories, prunes traversal into them).
function shouldExcludeEntry(p) {
  const rel = typeof p === "string" ? p : (p?.name ?? "");
  return rel
    .split(/[\\/]/)
    .some(
      (part) =>
        part &&
        part !== "." &&
        (IGNORED_DIRS.has(part) || part.startsWith(".")),
    );
}

function toPosix(p) {
  return p.split(sep).join(posix.sep);
}

function getExt(path) {
  const i = path.lastIndexOf(".");
  return i === -1 ? "" : path.slice(i + 1).toLowerCase();
}

function isValidTargetFile(
  rel,
  absPath,
  extFilter,
  maxBytes = Number.POSITIVE_INFINITY,
) {
  if (BINARY_EXT.has(getExt(rel))) return false;
  if (extFilter.size > 0 && !extFilter.has(getExt(rel))) return false;
  try {
    const st = statSync(absPath);
    return st.isFile() && st.size <= maxBytes;
  } catch {
    return false;
  }
}

/**
 * Walk repo files matching one or more glob patterns, applying the
 * shared exclusion + extension + size filter. Yields posix-relative
 * and absolute path pairs, deduplicated across patterns.
 */
function* walkFiles({ root, patterns, extFilter, maxBytes }) {
  const seen = new Set();
  for (const pattern of patterns) {
    for (const rawPath of globSync(pattern, {
      cwd: root,
      exclude: shouldExcludeEntry,
    })) {
      const rel = toPosix(rawPath);
      if (seen.has(rel)) continue;
      const abs = join(root, rawPath);
      if (!isValidTargetFile(rel, abs, extFilter, maxBytes)) continue;
      seen.add(rel);
      yield { rel, abs };
    }
  }
}

// ─── Symbol detection ───────────────────────────────────────────────────────

/** Return every captured declaration name on a single line. */
function findDeclaredNamesOnLine(line) {
  const names = [];
  for (const dp of DECL_PATTERNS) {
    dp.lastIndex = 0;
    let m;
    while ((m = dp.exec(line)) !== null) {
      if (m[1]) names.push(m[1]);
    }
  }
  return names;
}

function findSymbols(content, namePatterns, filePath) {
  const hits = [];
  const lines = content.split(/\r?\n/);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const linePatterns = namePatterns.filter((p) => p.test(line));
    if (linePatterns.length === 0) continue;

    const declNames = findDeclaredNamesOnLine(line);
    if (declNames.length === 0) continue;

    for (const pat of linePatterns) {
      if (declNames.some((n) => pat.test(n))) {
        hits.push({
          file: filePath,
          line: i + 1,
          match: line.trim().slice(0, 200),
        });
      }
    }
  }
  return hits;
}

function extractName(line) {
  return findDeclaredNamesOnLine(line)[0] ?? null;
}

// ─── Collection ─────────────────────────────────────────────────────────────

function collectMatchedFiles(opts) {
  if (opts.files.length === 0) return [];
  const out = [];
  const extFilter = new Set(opts.ext);
  for (const { rel } of walkFiles({
    root: opts.root,
    patterns: opts.files,
    extFilter,
    maxBytes: Number.POSITIVE_INFINITY,
  })) {
    if (out.length >= opts.max) break;
    out.push(rel);
  }
  return out;
}

function collectMatchedSymbols(opts, namePatterns) {
  if (namePatterns.length === 0) return [];
  const out = [];
  const extFilter = new Set(opts.ext);
  for (const { rel, abs } of walkFiles({
    root: opts.root,
    patterns: ["**/*"],
    extFilter,
    maxBytes: MAX_FILE_BYTES,
  })) {
    if (out.length >= opts.max) break;

    let content;
    try {
      content = readFileSync(abs, "utf8");
    } catch {
      continue;
    }
    for (const h of findSymbols(content, namePatterns, rel)) {
      if (out.length >= opts.max) break;
      out.push(h);
    }
  }
  return out;
}

// ─── Rendering ──────────────────────────────────────────────────────────────

function renderMarkdown(matchedFiles, matchedSymbols, withLines) {
  const out = [];
  if (matchedFiles.length > 0) {
    for (const f of matchedFiles) out.push(`- [${f}](${f})`);
    out.push("");
  }
  if (matchedSymbols.length > 0) {
    for (const s of matchedSymbols) {
      const name = extractName(s.match) || s.match.slice(0, 60);
      const anchor = withLines ? `${s.file}#L${s.line}` : s.file;
      out.push(`- [${name}](${anchor}) — \`${s.file}:${s.line}\``);
    }
    out.push("");
  }
  if (out.length === 0) out.push("No matches.");
  return out.join("\n");
}

// ─── Entry point ────────────────────────────────────────────────────────────

function main() {
  const opts = parseCliArgs(argv.slice(2));
  if (opts.help) {
    stdout.write(HELP);
    return 0;
  }
  if (opts.version) {
    stdout.write(`discover.mjs ${VERSION} (node ${version})\n`);
    return 0;
  }
  if (opts.files.length === 0 && opts.names.length === 0) {
    stderr.write(
      "Provide at least one of --files or --names. Use --help for usage.\n",
    );
    return 2;
  }

  const namePatterns = opts.names.map(compileNamePattern);
  const matchedFiles = collectMatchedFiles(opts);
  const matchedSymbols = collectMatchedSymbols(opts, namePatterns);

  matchedFiles.sort();
  matchedSymbols.sort((a, b) =>
    a.file === b.file ? a.line - b.line : a.file.localeCompare(b.file),
  );

  if (opts.json) {
    stdout.write(
      `${JSON.stringify(
        { files: matchedFiles, symbols: matchedSymbols },
        null,
        2,
      )  }\n`,
    );
    return 0;
  }

  stdout.write(renderMarkdown(matchedFiles, matchedSymbols, opts.lines));
  return 0;
}

try {
  assertNodeVersion();
  exit(main());
} catch (err) {
  const msg = err instanceof Error ? err.message : String(err);
  stderr.write(`discover.mjs: ${msg}\n`);
  exit(1);
}
