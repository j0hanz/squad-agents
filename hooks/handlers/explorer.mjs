// Explorer handler — gives the agent a short-term memory of what it has already
// searched and read, so it stops re-running the same Grep/Glob/Read and wasting
// turns. PreToolUse records a breadcrumb (side effect, async); SessionStart
// replays recent breadcrumbs as context; SessionEnd flushes/rotates the trail.

import { appendJsonl, readJsonlTail, getProjectDir } from '../utils.mjs';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const TRAIL = '.claude/explorer-breadcrumbs.log';
const MAX_TRAIL = 200; // cap so the log can't grow unbounded

/** Summarize a search/read tool call into a one-line breadcrumb target. */
function describe(tool, input = {}) {
  switch (tool) {
    case 'Grep':
      return input.pattern ? `grep /${input.pattern}/${input.path ? ` in ${input.path}` : ''}` : '';
    case 'Glob':
      return input.pattern ? `glob ${input.pattern}` : '';
    case 'Read':
      return input.file_path ? `read ${input.file_path}` : '';
    case 'WebFetch':
      return input.url ? `fetch ${input.url}` : '';
    // filesystem-mcp tools
    case 'mcp__filesystem__read':
      if (input.paths?.length) return `fs:read ${input.paths.length} files`;
      return input.path ? `fs:read ${input.path}` : '';
    case 'mcp__filesystem__search_text':
      return input.searchPattern
        ? `fs:grep /${input.searchPattern}/${input.path ? ` in ${input.path}` : ''}`
        : '';
    case 'mcp__filesystem__find_files':
      return input.pattern
        ? `fs:find ${input.pattern}${input.path ? ` in ${input.path}` : ''}`
        : '';
    case 'mcp__filesystem__list':
      return input.path ? `fs:list ${input.path}` : '';
    default:
      return '';
  }
}

/** PreToolUse: record what the agent explored. Pure side effect — no output. */
export function breadcrumb(input = {}) {
  const note = describe(input.tool_name, input.tool_input);
  if (!note) return null;
  appendJsonl(TRAIL, { ts: new Date().toISOString(), note });
  return null;
}

/** SessionStart: surface the recent exploration trail so context survives resume. */
export function replay() {
  const recent = readJsonlTail(TRAIL, 12);
  if (!recent.length) return null;
  // De-duplicate while preserving recency (most recent win) and session-relative order.
  // Each breadcrumb has ts (ISO timestamp) for temporal context; group by session.
  const seen = new Set();
  const notes = [];
  for (let i = recent.length - 1; i >= 0; i--) {
    const entry = recent[i];
    const n = entry.note;
    if (n && !seen.has(n)) {
      seen.add(n);
      // Include timestamp if available for session-relative ordering across resume.
      const time = entry.ts ? new Date(entry.ts).toLocaleTimeString() : '';
      notes.unshift(`  ${n}${time ? ` [${time}]` : ''}`);
    }
  }
  if (!notes.length) return null;
  return ['## Recently explored (this project)', ...notes.slice(-10)].join('\n');
}

/** SessionEnd: rotate the trail so it stays bounded. Pure side effect. */
export function flush() {
  try {
    const file = join(getProjectDir(), TRAIL);
    const lines = readFileSync(file, 'utf8').split('\n').filter(Boolean);
    if (lines.length > MAX_TRAIL) {
      writeFileSync(file, `${lines.slice(-MAX_TRAIL).join('\n')}\n`, 'utf8');
    }
  } catch {
    // No trail yet, or unreadable — nothing to flush.
  }
  return null;
}
