import { mkdtempSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

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
  const dir = mkdtempSync(join(tmpdir(), 'agent-sdlc-project-'));
  for (const [name, content] of Object.entries(files)) {
    writeFileSync(join(dir, name), content, 'utf-8');
  }
  return dir;
}

export function cleanupProject(dir) {
  if (dir && existsSync(dir)) {
    const maxRetries = 10;
    for (let i = 0; i < maxRetries; i++) {
      try {
        rmSync(dir, { recursive: true, force: true });
        return;
      } catch (err) {
        if (i === maxRetries - 1) {
          console.warn(`[cleanup] Failed to remove directory ${dir}: ${err.message}`);
          return;
        }
        // Sleep 200ms before retrying
        try {
          Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 200);
        } catch {}
      }
    }
  }
}
