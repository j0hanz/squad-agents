import { execSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

/**
 * Run `claude -p <prompt>` in an isolated temp directory.
 * Returns { stdout, stderr, exitCode }.
 */
export function runClaude(prompt, { timeout = 120_000, allowedTools = [], cwd } = {}) {
  const dir = cwd ?? mkdtempSync(join(tmpdir(), 'agent-dev-integration-'));
  const toolFlag = allowedTools.length ? `--allowedTools "${allowedTools.join(',')}"` : '';
  const cmd = `claude -p ${JSON.stringify(prompt)} --output-format json ${toolFlag}`;
  try {
    const stdout = execSync(cmd, {
      cwd: dir,
      timeout,
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    return { stdout, stderr: '', exitCode: 0, dir };
  } catch (err) {
    return { stdout: err.stdout ?? '', stderr: err.stderr ?? '', exitCode: err.status ?? 1, dir };
  }
}

/**
 * Assert that `text` contains `pattern` (string or RegExp).
 * Throws with a clear message if it doesn't.
 */
export function assertContains(text, pattern, label = '') {
  const ok = pattern instanceof RegExp ? pattern.test(text) : text.includes(pattern);
  if (!ok) {
    throw new Error(
      `assertContains failed${label ? ` [${label}]` : ''}:\n  pattern: ${pattern}\n  text (first 500): ${text.slice(0, 500)}`,
    );
  }
}

/**
 * Assert that `text` does NOT contain `pattern`.
 */
export function assertNotContains(text, pattern, label = '') {
  const found = pattern instanceof RegExp ? pattern.test(text) : text.includes(pattern);
  if (found) {
    throw new Error(
      `assertNotContains failed${label ? ` [${label}]` : ''}:\n  pattern: ${pattern}\n  text (first 500): ${text.slice(0, 500)}`,
    );
  }
}

/**
 * Create a minimal project directory and return its path.
 * Caller is responsible for cleanup via cleanupProject().
 */
export function createTmpProject(files = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'agent-dev-project-'));
  for (const [name, content] of Object.entries(files)) {
    writeFileSync(join(dir, name), content, 'utf-8');
  }
  return dir;
}

export function cleanupProject(dir) {
  if (dir && existsSync(dir)) {
    rmSync(dir, { recursive: true, force: true });
  }
}
