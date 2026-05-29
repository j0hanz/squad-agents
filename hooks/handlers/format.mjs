import { spawnSync } from 'child_process';
import { existsSync } from 'fs';
import path from 'path';
import { createPostToolUse } from '../utils.mjs';

export async function run(input) {
  const filePath = input?.tool_input?.file_path;
  if (!filePath) return null;

  const ext = path.extname(filePath);

  function execute(cmd, args) {
    return spawnSync(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] });
  }

  // Format silently if a local formatter is available
  if (ext === '.js' || ext === '.ts' || ext === '.mjs') {
    const prettierBin = path.join(process.cwd(), 'node_modules', '.bin', 'prettier');
    if (existsSync(prettierBin)) {
      execute(prettierBin, ['--write', filePath]);
    }
  } else if (ext === '.py') {
    execute('ruff', ['format', filePath]);
  }

  // Fast syntax check (skip per-file tsc — single-file tsc ignores tsconfig and produces false errors)
  let result;
  if (ext === '.js' || ext === '.mjs') {
    result = execute('node', ['-c', filePath]);
  } else if (ext === '.py') {
    result = execute('python', ['-m', 'py_compile', filePath]);
  }

  if (result && result.status !== 0) {
    const errorMessage = result.stderr?.toString() || '';
    return createPostToolUse(
      `[Syntax Check] File saved with a syntax error:\n${errorMessage.trim()}`,
    );
  }

  return null;
}
