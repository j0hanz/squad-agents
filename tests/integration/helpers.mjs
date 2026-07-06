import { mkdtempSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

/**
 * Create a minimal project directory and return its path.
 * Caller is responsible for cleanup via cleanupProject().
 */
export function createTmpProject(files = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'squad-agents-project-'));
  for (const [name, content] of Object.entries(files)) {
    writeFileSync(join(dir, name), content, 'utf-8');
  }
  return dir;
}

export function cleanupProject(dir) {
  if (dir && existsSync(dir)) {
    try {
      rmSync(dir, { recursive: true, force: true });
    } catch (err) {
      console.warn(`[cleanup] Failed to remove directory ${dir}: ${err.message}`);
    }
  }
}
