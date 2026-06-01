// PostToolUse(Edit|Write) handler — auto-formats the file the agent just wrote
// so generated code matches repo style without the agent spending a turn on it.
// Runs the project's existing formatters (Prettier for JS/JSON/MD, Ruff for
// Python). Pure side effect: it never blocks (the write already happened) and
// stays silent unless debugging.

import { sh, debug, getProjectDir } from '../utils.mjs';
import { existsSync } from 'node:fs';
import { extname, join } from 'node:path';

// Extensions Prettier handles in this repo's config.
const PRETTIER = new Set(['.js', '.mjs', '.cjs', '.json', '.md', '.yml', '.yaml']);
const RUFF = new Set(['.py']);

// Prettier's JS entry point. We run it through `node` rather than the .bin
// shim because Node 22+ refuses to exec .cmd/.bat shims via execFile, and
// invoking the .cjs directly needs no shell and works on every platform.
function prettierEntry() {
  const entry = join(getProjectDir(), 'node_modules', 'prettier', 'bin', 'prettier.cjs');
  return existsSync(entry) ? entry : null;
}

/** PostToolUse: format the written file in place. Returns null (side effect). */
export function onWrite(input = {}) {
  // Claude native tools use file_path; filesystem-mcp create/edit use path
  const file = input.tool_input?.file_path ?? input.tool_input?.path;
  if (!file || !existsSync(file)) return null;

  const ext = extname(file).toLowerCase();

  if (PRETTIER.has(ext)) {
    const entry = prettierEntry();
    if (entry) {
      // 20s timeout handles most files; very large files (10MB+) may timeout gracefully
      // and be skipped. Side effect: formatting fails silently, write succeeds.
      sh(process.execPath, [entry, '--write', file], { timeout: 20000 });
      debug('prettier formatted', file);
    }
  } else if (RUFF.has(ext)) {
    // Ruff ships a native binary — execFile runs it directly, no shell needed.
    // Two passes: format (20s) then check --fix (20s). Total max ~40s for large files.
    sh('ruff', ['format', file], { timeout: 20000 });
    sh('ruff', ['check', '--fix', '--quiet', file], { timeout: 20000 });
    debug('ruff formatted', file);
  }

  return null;
}
