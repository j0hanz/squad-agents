/**
 * Integration test: hook handlers behave correctly when invoked directly,
 * the way hooks.json invokes them (stdin JSON in, stdout JSON / exit code
 * out). Exercises hooks/*.sh directly — no `claude` CLI needed.
 *
 * Run: node tests/integration/test-hooks-fire.mjs
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync, mkdirSync, mkdtempSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import process from 'node:process';
import { cleanupProject } from './helpers.mjs';

const pluginRoot = process.cwd();
const hooksDir = join(pluginRoot, 'hooks');

let bashCmd = 'bash';
if (process.platform === 'win32') {
  const gitBashPaths = [
    'C:\\Program Files\\Git\\bin\\bash.exe',
    'C:\\Program Files\\Git\\usr\\bin\\bash.exe',
    'C:\\Program Files (x86)\\Git\\bin\\bash.exe',
    'C:\\Program Files (x86)\\Git\\usr\\bin\\bash.exe',
  ];
  for (const p of gitBashPaths) {
    if (existsSync(p)) {
      bashCmd = p;
      break;
    }
  }
}

function runHandler(name, input, env = {}) {
  try {
    const stdout = execFileSync(bashCmd, [join(hooksDir, name)], {
      input: JSON.stringify(input),
      encoding: 'utf-8',
      env: { ...process.env, ...env },
    });
    return { stdout, exitCode: 0 };
  } catch (err) {
    return { stdout: err.stdout ?? '', stderr: err.stderr ?? '', exitCode: err.status ?? 1 };
  }
}

test('shell-safety.sh blocks rm -rf / with exit code 2', () => {
  const { exitCode, stderr } = runHandler('shell-safety.sh', {
    tool_input: { command: 'rm -rf /' },
  });
  // PreToolUse on exit 2 ignores stdout entirely and feeds stderr to Claude
  // as plain text — there is no documented path where stderr is parsed as
  // JSON, so the deny message is plain text, not a hookSpecificOutput blob.
  assert.strictEqual(exitCode, 2);
  assert.ok(
    stderr.includes('Blocked:') && stderr.includes('root-level path'),
    'stderr should contain the plain-text deny reason',
  );
});

test('shell-safety.sh allows an rm -rf on a subpath', () => {
  const { exitCode } = runHandler('shell-safety.sh', {
    tool_input: { command: 'rm -rf /home/user/project/node_modules' },
  });
  assert.strictEqual(exitCode, 0);
});

test('shell-safety.sh allows the denylist word inside a quoted string', () => {
  const { exitCode } = runHandler('shell-safety.sh', {
    tool_input: { command: "git commit -m 'do not rm -rf / ever'" },
  });
  assert.strictEqual(exitCode, 0);
});

test('shell-safety.sh blocks rm -r (no -f) on a root-level path', () => {
  const { exitCode, stderr } = runHandler('shell-safety.sh', {
    tool_input: { command: 'rm -r /' },
  });
  assert.strictEqual(exitCode, 2);
  assert.ok(stderr.includes('non-forced'), 'stderr should explain the non-forced variant');
});

test('shell-safety.sh allows rm -r (no -f) on a subpath', () => {
  const { exitCode } = runHandler('shell-safety.sh', {
    tool_input: { command: 'rm -r ./build' },
  });
  assert.strictEqual(exitCode, 0);
});

test('shell-safety.sh allows a bare git push --force (no branchspec) — deliberate, not an oversight', () => {
  const { exitCode } = runHandler('shell-safety.sh', {
    tool_input: { command: 'git push --force' },
  });
  assert.strictEqual(exitCode, 0);
});

test('shell-safety.sh blocks git push --force regardless of flag/branch token order', () => {
  const { exitCode } = runHandler('shell-safety.sh', {
    tool_input: { command: 'git push origin --force master' },
  });
  assert.strictEqual(exitCode, 2);
});

test('shell-safety.sh blocks --force-with-lease=main:<sha> refspec form', () => {
  const { exitCode } = runHandler('shell-safety.sh', {
    tool_input: { command: 'git push --force-with-lease=main:abc123' },
  });
  assert.strictEqual(exitCode, 2);
});

test('shell-safety.sh allows force-push to a named non-default branch — documented accepted gap', () => {
  const { exitCode } = runHandler('shell-safety.sh', {
    tool_input: { command: 'git push --force origin my-wip-branch' },
  });
  assert.strictEqual(exitCode, 0);
});

test('shell-safety.sh respects the AGENT_SDLC_SKIP_SHELL_SAFETY override', () => {
  const { exitCode } = runHandler(
    'shell-safety.sh',
    { tool_input: { command: 'rm -rf /' } },
    { AGENT_SDLC_SKIP_SHELL_SAFETY: '1' },
  );
  assert.strictEqual(exitCode, 0);
});

test('shell-safety.sh respects skip_shell_safety in settings file (various formats)', () => {
  const formats = [
    'skip_shell_safety: true',
    'skip_shell_safety: "true"',
    "skip_shell_safety: 'true'",
    'skip_shell_safety: true   ',
  ];

  for (const format of formats) {
    const dir = mkdtempSync(join(tmpdir(), 'agent-sdlc-safety-settings-'));
    try {
      mkdirSync(join(dir, '.claude'), { recursive: true });
      writeFileSync(
        join(dir, '.claude', 'claude-agent-sdlc.local.md'),
        `---
${format}
---
`,
      );

      const { exitCode } = runHandler(
        'shell-safety.sh',
        { tool_input: { command: 'rm -rf /' } },
        { CLAUDE_PROJECT_DIR: dir, CLAUDE_PLUGIN_ROOT: pluginRoot },
      );
      assert.strictEqual(exitCode, 0, `Failed for format: ${format}`);
    } finally {
      cleanupProject(dir);
    }
  }
});

test('skill-nudge.sh respects skill_nudge in settings file (various formats)', () => {
  const formats = [
    'skill_nudge: false',
    'skill_nudge: "false"',
    "skill_nudge: 'false'",
    'skill_nudge: false   ',
  ];

  for (const format of formats) {
    const dir = mkdtempSync(join(tmpdir(), 'agent-sdlc-nudge-settings-'));
    try {
      mkdirSync(join(dir, '.claude'), { recursive: true });
      writeFileSync(
        join(dir, '.claude', 'claude-agent-sdlc.local.md'),
        `---
${format}
---
`,
      );

      const { stdout, exitCode } = runHandler(
        'skill-nudge.sh',
        {},
        {
          CLAUDE_PROJECT_DIR: dir,
          CLAUDE_PLUGIN_ROOT: pluginRoot,
          AGENT_SDLC_BOOTSTRAP_MODE: 'full',
        },
      );
      assert.strictEqual(exitCode, 0);
      assert.strictEqual(stdout.trim(), '', `Failed for format: ${format}`);
    } finally {
      cleanupProject(dir);
    }
  }
});

test('skill-nudge.sh emits additionalContext on first fire, then stays quiet (cooldown)', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agent-sdlc-nudge-'));
  try {
    const first = runHandler(
      'skill-nudge.sh',
      {},
      {
        CLAUDE_PROJECT_DIR: dir,
        CLAUDE_PLUGIN_ROOT: pluginRoot,
        AGENT_SDLC_BOOTSTRAP_MODE: 'cooldown',
      },
    );
    assert.strictEqual(first.exitCode, 0);
    const parsed = JSON.parse(first.stdout);
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('brainstorming'));

    const second = runHandler(
      'skill-nudge.sh',
      {},
      {
        CLAUDE_PROJECT_DIR: dir,
        CLAUDE_PLUGIN_ROOT: pluginRoot,
        AGENT_SDLC_BOOTSTRAP_MODE: 'cooldown',
      },
    );
    assert.strictEqual(second.exitCode, 0);
    assert.strictEqual(second.stdout.trim(), '');
  } finally {
    cleanupProject(dir);
  }
});

test('skill-nudge.sh default mode (no BOOTSTRAP_MODE env) is cooldown', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agent-sdlc-nudge-default-'));
  try {
    const first = runHandler(
      'skill-nudge.sh',
      {},
      {
        CLAUDE_PROJECT_DIR: dir,
        CLAUDE_PLUGIN_ROOT: pluginRoot,
      },
    );
    assert.strictEqual(first.exitCode, 0);
    assert.notStrictEqual(first.stdout.trim(), '', 'default should emit on first fire');

    const second = runHandler(
      'skill-nudge.sh',
      {},
      {
        CLAUDE_PROJECT_DIR: dir,
        CLAUDE_PLUGIN_ROOT: pluginRoot,
      },
    );
    assert.strictEqual(second.exitCode, 0);
    assert.strictEqual(second.stdout.trim(), '', 'default should cooldown on second fire');
  } finally {
    cleanupProject(dir);
  }
});

test('skill-nudge.sh respects AGENT_SDLC_SKILL_NUDGE=0', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agent-sdlc-nudge-'));
  try {
    const { stdout, exitCode } = runHandler(
      'skill-nudge.sh',
      {},
      { CLAUDE_PROJECT_DIR: dir, CLAUDE_PLUGIN_ROOT: pluginRoot, AGENT_SDLC_SKILL_NUDGE: '0' },
    );
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
  } finally {
    cleanupProject(dir);
  }
});

test('all hooks.json handler commands reference an existing handler file', () => {
  const hooksConfig = JSON.parse(readFileSync(join(pluginRoot, 'hooks', 'hooks.json'), 'utf-8'));
  const referenced = [];
  for (const matchers of Object.values(hooksConfig.hooks ?? {})) {
    for (const matcher of matchers) {
      for (const hook of matcher.hooks ?? []) {
        const match = hook.command?.match(/hooks\/([\w-]+\.sh)/);
        if (match) referenced.push(match[1]);
      }
    }
  }
  assert.ok(referenced.length > 0, 'hooks.json should reference at least one handler');
  for (const name of referenced) {
    assert.ok(existsSync(join(hooksDir, name)), `${name} should exist in hooks/`);
  }
});
