// Shared utilities for agent-dev hooks.
//
// Every hook in this plugin is *additive-only*: it may inject context (stdout)
// or perform a side effect, then exits 0. Hooks never block a tool, never open a
// permission gate, and never prompt the user. These helpers make that contract
// the path of least resistance — see AGENTS.md → "Hooks are additive only".

import { execFileSync } from 'node:child_process';
import { appendFileSync, readFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';

const MAX_STDIN_SIZE = 10 * 1024 * 1024; // 10MB

/** Read all of stdin and parse it as the hook event JSON. Never throws. */
export async function readStdin() {
  const chunks = [];
  let totalSize = 0;
  try {
    for await (const chunk of process.stdin) {
      totalSize += chunk.length;
      if (totalSize > MAX_STDIN_SIZE) {
        throw new Error(`stdin exceeds ${MAX_STDIN_SIZE} bytes`);
      }
      chunks.push(chunk);
    }
  } catch (err) {
    debug('readStdin failed', err.message);
    return { _parseError: err.message };
  }

  const raw = Buffer.concat(chunks).toString('utf8').trim();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (err) {
    return { _raw: raw, _parseError: err.message };
  }
}

/** Project root. CLAUDE_PROJECT_DIR is set for every hook; fall back to cwd. */
export function getProjectDir() {
  return process.env.CLAUDE_PROJECT_DIR || process.cwd();
}

/** Diagnostics gate. Set CLAUDE_HOOKS_DEBUG=1 to see hook internals on stderr. */
export function isDebug() {
  return process.env.CLAUDE_HOOKS_DEBUG === '1';
}

/** Write a diagnostic line to stderr (only when debugging). Never touches stdout. */
export function debug(...args) {
  if (isDebug()) process.stderr.write(`[hook] ${args.join(' ')}\n`);
}

/**
 * Telemetry honors the `telemetry_enabled` plugin config, surfaced as an env
 * var. Defaults on; set AGENT_DEV_TELEMETRY=0 to silence.
 */
export function telemetryEnabled() {
  return process.env.AGENT_DEV_TELEMETRY !== '0';
}

/** Append a JSON record as one line to a file under the project dir. Best-effort. */
export function appendJsonl(relPath, record) {
  try {
    const file = join(getProjectDir(), relPath);
    mkdirSync(dirname(file), { recursive: true });
    appendFileSync(file, `${JSON.stringify(record)}\n`, 'utf8');
  } catch (err) {
    debug('appendJsonl failed', String(err));
  }
}

/** Read the last `n` JSON lines from a JSONL file. Returns [] on any problem. */
export function readJsonlTail(relPath, n) {
  try {
    const file = join(getProjectDir(), relPath);
    const lines = readFileSync(file, 'utf8').split('\n').filter(Boolean);
    return lines
      .slice(-n)
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

/** Write a telemetry record (gated by config). Side effect only. */
export function writeTelemetry(record) {
  if (!telemetryEnabled()) return;
  appendJsonl('.claude/telemetry.log', { timestamp: new Date().toISOString(), ...record });
}

/**
 * Run a command synchronously and return trimmed stdout, or '' on any failure.
 * Used for read-only probes (git status, formatters) — never let a failed probe
 * break the workflow.
 */
export function sh(file, args, opts = {}) {
  try {
    return execFileSync(file, args, {
      cwd: getProjectDir(),
      encoding: 'utf8',
      timeout: opts.timeout ?? 8000,
      stdio: ['ignore', 'pipe', 'ignore'],
      windowsHide: true,
      ...opts,
    }).trim();
  } catch (err) {
    debug(`sh ${file} failed`, String(err?.message || err));
    return '';
  }
}

/** Events whose plain `additionalContext` is injected into Claude's context. */
const CONTEXT_EVENTS = new Set([
  'SessionStart',
  'UserPromptSubmit',
  'PostToolUse',
  'PostToolUseFailure',
]);

/**
 * Build the correct additive output object for an event so a handler can just
 * return a string. Returns null when the event can't inject context additively
 * (e.g. Stop, where injection requires blocking — which we never do).
 */
export function asContext(event, text) {
  if (!text || !CONTEXT_EVENTS.has(event)) return null;
  return { hookSpecificOutput: { hookEventName: event, additionalContext: text } };
}
