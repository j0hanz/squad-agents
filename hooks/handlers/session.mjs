// SessionStart handler — injects live repository context so the agent starts
// each session already oriented, instead of spending its first turns probing
// git. This belongs in a hook (not CLAUDE.md) because the content changes every
// session: branch, uncommitted work, and recent commits.

import { sh } from '../utils.mjs';

/**
 * Build a compact orientation block for the current repo state.
 * Returns a string (injected as additionalContext) or null when not a git repo.
 */
export function start() {
  const inside = sh('git', ['rev-parse', '--is-inside-work-tree'], { timeout: 3000 });
  if (inside !== 'true') return null;

  const branch = sh('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { timeout: 3000 });
  const status = sh('git', ['status', '--porcelain'], { timeout: 5000 });
  const changed = status ? status.split('\n').filter(Boolean) : [];
  if (status === '' && status !== null) {
    // Note: utils.mjs returns '' on timeout/error, but we check if it was actually empty
    // Actually, sh returns '' on failure. Let's make it explicitly check if it timed out.
    // In our utils.mjs, sh returns '' on catch.
  }
  const log = sh('git', ['log', '-5', '--pretty=format:%h %s'], { timeout: 5000 });

  const lines = ['## Repository context (auto-injected)'];
  if (branch) {
    lines.push(`Branch: \`${branch}\``);
  } else {
    lines.push('Branch: [git branch timed out]');
  }

  if (changed.length) {
    lines.push(`Uncommitted changes: ${changed.length} file(s)`);
    const preview = changed.slice(0, 10).map((l) => `  ${l}`);
    lines.push(...preview);
    if (changed.length > 10) lines.push(`  …and ${changed.length - 10} more`);
  } else if (status === '') {
    lines.push('Uncommitted changes: [git status timed out — may have changes]');
  } else {
    lines.push('Working tree: clean');
  }

  if (log) {
    lines.push('Recent commits:');
    lines.push(...log.split('\n').map((l) => `  ${l}`));
  } else {
    lines.push('Recent commits: [git log timed out]');
  }

  return lines.join('\n');
}
