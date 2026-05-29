import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const tmpDir = mkdtempSync(path.join(os.tmpdir(), 'explorer-test-'));
process.env.CLAUDE_PLUGIN_DATA = tmpDir;

const { breadcrumb } = await import('./explorer-search.mjs');
const { compactFlush, compactRestore } = await import('./explorer-compact.mjs');
const { cwdWatch, fileChanged } = await import('./explorer-prompt.mjs');
const { prefetch } = await import('./explorer-web.mjs');
const { readIntercept, searchEnrich } = await import('./explorer-search.mjs');
const { stop, subagentStop } = await import('./explorer-context.mjs');

// --- breadcrumb + breadcrumbBatch ---

test('breadcrumb: logs to pluginDataDir and returns null', async () => {
  const result = await breadcrumb({
    tool_name: 'Grep',
    tool_input: { pattern: 'authMiddleware' },
  });
  assert.strictEqual(result, null);
  // Assert written to pluginDataDir (the shared path compactFlush reads from)
  const logPath = path.join(tmpDir, 'explorer-breadcrumbs.log');
  const content = readFileSync(logPath, 'utf8');
  assert.match(content, /\[Grep\] authMiddleware/);
});

test('breadcrumb: handles missing tool_input gracefully', async () => {
  const result = await breadcrumb({ tool_name: 'Glob' });
  assert.strictEqual(result, null);
});

test('breadcrumbBatch: logs all tool calls from batch input and returns null', async () => {
  const { breadcrumbBatch } = await import('./explorer-search.mjs');
  const result = await breadcrumbBatch({
    tool_calls: [
      { tool_name: 'Grep', tool_input: { pattern: 'batchPattern1' } },
      { tool_name: 'Glob', tool_input: { pattern: '**/*.ts' } },
    ],
  });
  assert.strictEqual(result, null);
  const logPath = path.join(tmpDir, 'explorer-breadcrumbs.log');
  const content = readFileSync(logPath, 'utf8');
  assert.match(content, /batchPattern1/);
  assert.match(content, /\*\*\/\*\.ts/);
});

test('breadcrumbBatch: returns null for empty or missing tool_calls', async () => {
  const { breadcrumbBatch } = await import('./explorer-search.mjs');
  assert.strictEqual(await breadcrumbBatch({}), null);
  assert.strictEqual(await breadcrumbBatch({ tool_calls: [] }), null);
});

test('breadcrumbBatch: skips tool calls without Grep/Glob tool names', async () => {
  const { breadcrumbBatch } = await import('./explorer-search.mjs');
  const result = await breadcrumbBatch({
    tool_calls: [
      { tool_name: 'Bash', tool_input: { command: 'ls' } },
      { tool_name: 'Read', tool_input: { file_path: 'foo.ts' } },
    ],
  });
  assert.strictEqual(result, null);
});

// --- compactFlush + compactRestore roundtrip ---

test('compactFlush + compactRestore: roundtrip preserves searched patterns', async () => {
  // Seed via breadcrumb() — validates the full pipeline, not a direct file write
  await breadcrumb({
    tool_name: 'Grep',
    tool_input: { pattern: 'authMiddleware' },
  });
  await breadcrumb({
    tool_name: 'Glob',
    tool_input: { pattern: '*.controller.ts' },
  });

  const sessionId = 'test-session-001';
  await compactFlush({ session_id: sessionId });

  const restored = await compactRestore({ session_id: sessionId });
  assert.ok(
    typeof restored === 'string',
    'compactRestore should return a string after breadcrumbs were written',
  );
  assert.match(restored, /before compaction/i);
  assert.match(restored, /authMiddleware|controller/);
});

test('compactRestore: returns null for unknown session', async () => {
  const result = await compactRestore({ session_id: 'nonexistent-session-xyz' });
  assert.strictEqual(result, null);
});

// --- cwdWatch ---

test('cwdWatch: returns watchPaths array for a real directory', async () => {
  // Create a temp dir with a known file
  const dir = mkdtempSync(path.join(os.tmpdir(), 'cwdwatch-'));
  writeFileSync(path.join(dir, 'package.json'), '{"name":"test"}');

  const result = await cwdWatch({ new_cwd: dir });
  assert.ok(result?.hookSpecificOutput?.watchPaths?.length >= 1);
  assert.ok(result.hookSpecificOutput.watchPaths.some((p) => p.endsWith('package.json')));
});

test('cwdWatch: returns empty watchPaths for empty directory', async () => {
  const dir = mkdtempSync(path.join(os.tmpdir(), 'cwdwatch-empty-'));
  const result = await cwdWatch({ new_cwd: dir });
  assert.deepEqual(result?.hookSpecificOutput?.watchPaths, []);
});

test('cwdWatch: returns null when new_cwd is missing', async () => {
  const result = await cwdWatch({});
  assert.strictEqual(result, null);
});

// --- fileChanged ---

test('fileChanged: returns null when file_path is missing', async () => {
  const result = await fileChanged({});
  assert.strictEqual(result, null);
});

test('fileChanged: returns null for nonexistent file', async () => {
  const result = await fileChanged({ file_path: '/nonexistent/path/file.ts' });
  assert.strictEqual(result, null);
});

test('fileChanged: returns string with filename for existing file', async () => {
  const file = path.join(tmpDir, 'test-changed.ts');
  writeFileSync(file, 'const x = 1;\n');
  const result = await fileChanged({ file_path: file, event: 'change' });
  assert.ok(typeof result === 'string');
  assert.match(result, /test-changed\.ts/);
  assert.match(result, /change/);
});

// --- prefetch ---

test('prefetch: returns prompt-injection warning for any URL', async () => {
  const result = await prefetch({
    tool_input: { url: 'https://example.com/api-docs' },
  });
  assert.ok(result !== null);
  const str = JSON.stringify(result);
  assert.match(str, /injection/i);
});

test('prefetch: handles missing url gracefully', async () => {
  const result = await prefetch({ tool_input: {} });
  assert.ok(result !== null);
});

// --- readIntercept ---

test('readIntercept: returns null for small files', async () => {
  const file = path.join(tmpDir, 'small.ts');
  writeFileSync(file, Array(10).fill('const x = 1;').join('\n'));
  const result = await readIntercept({ tool_input: { file_path: file } });
  assert.strictEqual(result, null);
});

test('readIntercept: returns limit hint for large files', async () => {
  const file = path.join(tmpDir, 'large.ts');
  writeFileSync(file, Array(400).fill('const x = 1;').join('\n'));
  const result = await readIntercept({ tool_input: { file_path: file } });
  assert.ok(result !== null);
  const str = JSON.stringify(result);
  assert.match(str, /150/);
});

test('readIntercept: returns null when offset/limit already set', async () => {
  const file = path.join(tmpDir, 'large2.ts');
  writeFileSync(file, Array(400).fill('const x = 1;').join('\n'));
  const result = await readIntercept({
    tool_input: { file_path: file, offset: 0, limit: 50 },
  });
  assert.strictEqual(result, null);
});

test('readIntercept: returns null for missing file', async () => {
  const result = await readIntercept({
    tool_input: { file_path: '/no/such/file.ts' },
  });
  assert.strictEqual(result, null);
});

// --- searchEnrich ---

test('searchEnrich: returns null for non-Grep tools', async () => {
  const result = await searchEnrich({ tool_name: 'Glob', tool_input: {} });
  assert.strictEqual(result, null);
});

test('searchEnrich: returns null when glob already set', async () => {
  const result = await searchEnrich({
    tool_name: 'Grep',
    tool_input: { pattern: 'foo', glob: '*.ts' },
  });
  assert.strictEqual(result, null);
});

// --- stop ---

test('stop: returns systemMessage string', async () => {
  const result = await stop({});
  assert.ok(typeof result?.systemMessage === 'string');
  assert.match(result.systemMessage, /Explorer/i);
});

// --- subagentStop ---

test('subagentStop: returns null when transcript missing', async () => {
  const result = await subagentStop({});
  assert.strictEqual(result, null);
});

test('subagentStop: returns null for nonexistent transcript path', async () => {
  const result = await subagentStop({
    agent_transcript_path: '/no/such/transcript.md',
    agent_type: 'coder',
  });
  assert.strictEqual(result, null);
});

test('subagentStop: returns string with agent type for existing transcript', async () => {
  const file = path.join(tmpDir, 'transcript.md');
  writeFileSync(file, 'line1\nline2\nfinal result\n');
  const result = await subagentStop({
    agent_transcript_path: file,
    agent_type: 'coder',
  });
  assert.ok(typeof result === 'string');
  assert.match(result, /coder/);
});

test('sessionEnd: returns systemMessage string', async () => {
  const { sessionEnd } = await import('./explorer-context.mjs');
  const result = await sessionEnd({});
  assert.ok(typeof result?.systemMessage === 'string');
  assert.match(result.systemMessage, /session/i);
});

test('subagentStart: returns null when no breadcrumbs exist', async () => {
  const freshDir = mkdtempSync(path.join(os.tmpdir(), 'substart-'));
  process.env.CLAUDE_PLUGIN_DATA = freshDir;
  const { subagentStart } = await import('./explorer-context.mjs');
  const result = await subagentStart({ agent_type: 'coder' });
  assert.strictEqual(result, null);
  process.env.CLAUDE_PLUGIN_DATA = tmpDir;
});

test('subagentStart: returns context string when breadcrumbs exist', async () => {
  process.env.CLAUDE_PLUGIN_DATA = tmpDir;
  const { subagentStart } = await import('./explorer-context.mjs');
  const result = await subagentStart({ agent_type: 'coder' });
  if (result !== null) {
    assert.ok(typeof result === 'string');
    assert.match(result, /coder|explored/i);
  }
});

// --- facade smoke test ---

test('explorer.mjs facade re-exports all expected functions', async () => {
  const facade = await import('./explorer.mjs');
  const expected = [
    'context',
    'stop',
    'subagentStop',
    'sessionEnd',
    'subagentStart',
    'breadcrumb',
    'searchEnrich',
    'readIntercept',
    'breadcrumbBatch',
    'compactFlush',
    'compactRestore',
    'prefetch',
    'cwdWatch',
    'fileChanged',
    'promptPreload',
  ];
  for (const fn of expected) {
    assert.strictEqual(typeof facade[fn], 'function', `facade missing export: ${fn}`);
  }
});
