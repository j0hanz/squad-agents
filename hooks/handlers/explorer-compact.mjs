import fs from 'fs/promises';
import path from 'path';
import { getPluginDataDir } from '../utils.mjs';

export async function compactFlush(input) {
  const sessionId = input?.session_id || 'unknown';
  const logDir = getPluginDataDir();
  const breadcrumbLog = path.join(logDir, 'explorer-breadcrumbs.log');
  const sessionFile = path.join(logDir, `explorer-session-${sessionId}.json`);

  let content;
  try {
    content = await fs.readFile(breadcrumbLog, 'utf8');
  } catch (e) {
    if (e.code === 'ENOENT') return null;
    throw e;
  }
  if (!content) return null;

  const patterns = new Set();
  for (const line of content.split('\n')) {
    if (!line) continue;
    // Log format: "2026-05-29T10:00:00Z [ToolName] pattern"
    // Match everything after the closing ] of the tool name.
    const match = line.match(/\] (.+)$/);
    if (match) patterns.add(match[1]);
  }

  const searched = Array.from(patterns).slice(0, 20);
  const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

  await fs.writeFile(sessionFile, JSON.stringify({ searched, timestamp: ts }));
  return null;
}

export async function compactRestore(input) {
  const sessionId = input?.session_id || 'unknown';
  const logDir = getPluginDataDir();
  const sessionFile = path.join(logDir, `explorer-session-${sessionId}.json`);

  try {
    const data = JSON.parse(await fs.readFile(sessionFile, 'utf8'));
    if (!data.searched || !data.searched.length) return null;
    const searched = data.searched.join(' · ');
    const ts = data.timestamp || '';
    return `Already explored this session (before compaction):\n  Searched patterns: ${searched}\n  Session snapshot: ${ts}`;
  } catch (e) {
    return null;
  }
}
