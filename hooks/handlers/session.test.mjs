import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, mkdirSync, existsSync, readFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const tmpDir = mkdtempSync(path.join(os.tmpdir(), 'session-test-'));
process.env.CLAUDE_PROJECT_DIR = tmpDir;

// Mock session-config.json
const configDir = path.resolve('hooks/config');
mkdirSync(configDir, { recursive: true });
const configPath = path.join(configDir, 'session-config.json');
const originalConfig = existsSync(configPath) ? readFileSync(configPath, 'utf-8') : null;

const mockConfig = {
  envCandidates: ['.env.test'],
  artifactCandidates: ['test-artifact.json'],
  serviceMarkers: [{ file: 'Procfile', label: 'Procfile' }],
};
writeFileSync(configPath, JSON.stringify(mockConfig));

const { context, env } = await import('./session.mjs');

test('session: context returns basic repo info', async () => {
  const result = await context();
  assert.ok(result?.hookSpecificOutput?.additionalContext);
  assert.match(result.hookSpecificOutput.additionalContext, /Repo:/);
});

test('session: env detects existing files from config', async () => {
  // Create mock files in the tmp project dir
  writeFileSync(path.join(tmpDir, '.env.test'), 'FOO=bar');
  writeFileSync(path.join(tmpDir, 'test-artifact.json'), '{}');
  writeFileSync(path.join(tmpDir, 'Procfile'), 'web: node server.js');

  const result = await env();
  assert.ok(result?.hookSpecificOutput?.additionalContext);
  assert.match(result.hookSpecificOutput.additionalContext, /\.env\.test/);
  assert.match(result.hookSpecificOutput.additionalContext, /test-artifact\.json/);
  assert.match(result.hookSpecificOutput.additionalContext, /Procfile/);
});

test('session: end writes summary to .claude/status.md', async () => {
  const { end } = await import('./session.mjs');
  const claudeDir = path.join(tmpDir, '.claude');
  mkdirSync(claudeDir, { recursive: true });

  const result = await end();
  assert.strictEqual(result, null);

  const statusPath = path.join(tmpDir, '.claude', 'status.md');
  assert.ok(existsSync(statusPath), '.claude/status.md should exist after session.end()');
  const content = readFileSync(statusPath, 'utf8');
  assert.match(content, /session ended/i);
});

test('session: contextRefresh returns session context', async () => {
  process.env.CLAUDE_PROJECT_DIR = tmpDir;
  const { contextRefresh } = await import('./session.mjs');
  const result = await contextRefresh();
  assert.ok(result?.hookSpecificOutput?.additionalContext);
  assert.match(result.hookSpecificOutput.additionalContext, /Repo:|Session|Branch/);
});

// Cleanup config after tests
test.after(() => {
  if (originalConfig) {
    writeFileSync(configPath, originalConfig);
  }
});

test('session: env returns null when no files match', async () => {
  // Use a different tmp dir without files
  const emptyDir = mkdtempSync(path.join(os.tmpdir(), 'session-test-empty-'));
  process.env.CLAUDE_PROJECT_DIR = emptyDir;

  const result = await env();
  assert.strictEqual(result, null);
});
