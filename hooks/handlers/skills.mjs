// SessionStart handler — injects the plugin's skill routing guide so the agent
// knows which skills exist and how to choose between them from its first turn,
// instead of discovering them ad hoc mid-task. The guide is read live from
// using-agent-dev/SKILL.md, so edits to the map propagate automatically — the
// advantage of a hook over copying the table into CLAUDE.md. Additive only:
// it injects context and never blocks or prompts.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { debug } from '../utils.mjs';

// Plugin root, resolved relative to this module (handlers live at <root>/hooks/
// handlers/), so it works regardless of the process working directory.
const PLUGIN_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const GUIDE = join(PLUGIN_ROOT, 'skills', 'skills-routing-guide.md');
const MAX_CHARS = 10000; // hard ceiling: the platform caps injected context at 10k chars

// Honors the `skills_announce` plugin config (surfaced as an env var).
function enabled() {
  return process.env.AGENT_DEV_SKILLS_ANNOUNCE !== '0';
}

/** Strip a leading YAML frontmatter block (--- … ---) from a markdown string. */
function stripFrontmatter(md) {
  const lines = md.split('\n');
  if (lines[0]?.trim() !== '---') return md;
  let i = 1;
  while (i < lines.length && lines[i].trim() !== '---') i++;
  return lines.slice(i + 1).join('\n');
}

/** SessionStart: surface the skill routing guide as additive context. */
export function announce() {
  if (!enabled()) return null;

  let body;
  try {
    body = stripFrontmatter(readFileSync(GUIDE, 'utf8')).trim();
  } catch (err) {
    debug('skills.announce: cannot read routing guide', String(err));
    return null;
  }
  if (!body) return null;

  const header =
    'The agent-dev plugin ships the skills mapped below. When a task matches ' +
    'one, invoke it with the Skill tool rather than improvising; for overlaps ' +
    'and sequencing, this routing guide is authoritative.';

  return `${header}\n\n${body}`.slice(0, MAX_CHARS);
}
