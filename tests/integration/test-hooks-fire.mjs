/**
 * Integration test: hooks write telemetry when the plugin is active.
 *
 * SLOW: requires claude CLI + ANTHROPIC_API_KEY. Run manually.
 * Run: node tests/integration/test-hooks-fire.mjs
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { execSync } from 'node:child_process';
import process from 'node:process';
import { cleanupProject } from './helpers.mjs';

// Skip all tests if claude CLI is not available
let claudeAvailable = false;
try {
  execSync('claude --version', { stdio: 'ignore' });
  claudeAvailable = true;
} catch {
  // claude CLI not available; tests will be skipped
}

const skipIfNoClaude = claudeAvailable ? test : test.skip;

skipIfNoClaude('session hook writes telemetry log', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'hook-test-'));
  const claudeDir = join(dir, '.claude');
  mkdirSync(claudeDir, { recursive: true });

  try {
    // Run the session.start hook directly (does not need API key)
    const pluginRoot = process.cwd();
    execSync(`node "${join(pluginRoot, 'hooks/runner.mjs')}" session start`, {
      cwd: dir,
      env: { ...process.env, CLAUDE_PROJECT_DIR: dir },
      stdio: 'ignore',
    });

    const logPath = join(claudeDir, 'telemetry.log');
    assert.ok(existsSync(logPath), 'telemetry.log should exist after session hook runs');

    const lines = readFileSync(logPath, 'utf-8').trim().split('\n');
    assert.ok(lines.length > 0, 'telemetry.log should have at least one entry');

    const entry = JSON.parse(lines[lines.length - 1]);
    assert.strictEqual(entry.domain, 'session');
    assert.strictEqual(entry.action, 'start');
    assert.strictEqual(entry.status, 'success');
    assert.ok(typeof entry.duration === 'number');
  } finally {
    cleanupProject(dir);
  }
});

skipIfNoClaude('format hook runs without error on a JS file', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'format-test-'));
  const jsFile = join(dir, 'test.js');
  writeFileSync(jsFile, 'const x=1;const y=2;\n', 'utf-8');

  try {
    const pluginRoot = process.cwd();
    const input = JSON.stringify({ tool_name: 'Write', tool_input: { file_path: jsFile } });
    // format.run should exit 0 even if prettier is not installed (it is installed here)
    execSync(
      `echo ${JSON.stringify(input)} | node "${join(pluginRoot, 'hooks/runner.mjs')}" format run`,
      {
        cwd: dir,
        env: { ...process.env, CLAUDE_PROJECT_DIR: dir },
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
      },
    );
    // No assertion on content — just must not throw (exit non-zero)
    assert.ok(true, 'format hook ran without error');
  } catch (err) {
    assert.fail(`format hook exited non-zero: ${err.stderr}`);
  } finally {
    cleanupProject(dir);
  }
});
