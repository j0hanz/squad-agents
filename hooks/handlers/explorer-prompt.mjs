import fs from 'fs/promises';
import { readdirSync } from 'fs';
import { spawnSync } from 'child_process';
import path from 'path';
import { getProjectDir } from '../utils.mjs';

export async function cwdWatch(input) {
  const newCwd = input?.new_cwd;
  if (!newCwd) return null;
  const candidates = [
    'package.json',
    'go.mod',
    'Cargo.toml',
    'pyproject.toml',
    'ARCHITECTURE.md',
    'CONTEXT.md',
    'CLAUDE.md',
    'AGENTS.md',
  ];
  const paths = [];
  for (const f of candidates) {
    const p = path.join(newCwd, f);
    try {
      const stats = await fs.stat(p);
      if (stats.isFile()) paths.push(p);
    } catch (e) {
      if (e.code !== 'ENOENT') throw e;
    }
  }
  return { hookSpecificOutput: { watchPaths: paths } };
}

export async function fileChanged(input) {
  const file = input?.file_path;
  const event = input?.event || 'change';
  if (!file) return null;

  try {
    const stats = await fs.stat(file);
    if (!stats.isFile()) return null;
  } catch (e) {
    if (e.code === 'ENOENT') return null;
    throw e;
  }

  const name = path.basename(file);
  const content = await fs.readFile(file, 'utf8');
  const head = content.split('\n').slice(0, 40).join('\n');
  return `[FileChanged] ${name} (${event}). Current state (first 40 lines):\n${head}`;
}

const STOP_WORDS = new Set([
  'the',
  'is',
  'how',
  'does',
  'what',
  'where',
  'a',
  'an',
  'in',
  'of',
  'to',
  'for',
  'and',
  'or',
  'with',
  'that',
  'this',
  'are',
  'was',
  'be',
  'do',
  'it',
  'at',
  'by',
  'on',
  'as',
  'from',
  'i',
  'you',
  'we',
  'can',
  'will',
  'would',
  'could',
  'should',
  'not',
  'but',
  'if',
  'then',
  'when',
  'have',
  'has',
  'had',
  'get',
  'use',
  'its',
  'which',
  'who',
  'their',
  'they',
  'there',
  'my',
  'me',
  'our',
  'your',
  'he',
  'she',
  'him',
  'her',
  'all',
  'any',
  'each',
  'more',
  'also',
  'about',
  'into',
  'up',
  'out',
  'just',
  'like',
  'so',
  'no',
  'yes',
  'via',
  'per',
  'vs',
  'etc',
  'work',
  'works',
  'used',
]);

const EXCLUDE_DIRS = new Set([
  'node_modules',
  '.git',
  '__pycache__',
  'dist',
  'build',
  'target',
  '.venv',
  '.next',
  'vendor',
  'bin',
  'obj',
]);

function findRg() {
  for (const cmd of ['rg', 'ripgrep']) {
    try {
      const r = spawnSync(cmd, ['--version'], { stdio: 'pipe' });
      if (r.status === 0) return cmd;
    } catch (e) {}
  }
  return null;
}

function contentSearchRg(terms, proj, rgCmd) {
  const found = new Set();
  for (const term of terms) {
    const r = spawnSync(
      rgCmd,
      [
        '--files-with-matches',
        '--max-count',
        '1',
        '--ignore-case',
        '--glob',
        '!node_modules/**',
        '--glob',
        '!dist/**',
        '--glob',
        '!.git/**',
        '--glob',
        '!__pycache__/**',
        '--glob',
        '!build/**',
        term,
        '.',
      ],
      { cwd: proj, stdio: 'pipe', encoding: 'utf8' },
    );
    (r.stdout || '')
      .split('\n')
      .filter(Boolean)
      .slice(0, 5)
      .forEach((f) => found.add(f));
  }
  return found;
}

function collectPaths(dir, maxDepth = 3) {
  const results = [];
  function walk(current, depth) {
    if (depth > maxDepth) return;
    let entries;
    try {
      entries = readdirSync(current, { withFileTypes: true });
    } catch (e) {
      return;
    }
    for (const entry of entries) {
      if (EXCLUDE_DIRS.has(entry.name)) continue;
      if (entry.isFile()) {
        results.push(path.relative(dir, path.join(current, entry.name)));
      } else if (entry.isDirectory()) {
        walk(path.join(current, entry.name), depth + 1);
      }
    }
  }
  walk(dir, 0);
  return results;
}

function nameSearch(terms, proj) {
  const allPaths = collectPaths(proj, 3);
  const found = new Set();
  for (const term of terms) {
    for (const p of allPaths) {
      if (p.toLowerCase().includes(term)) found.add(p);
    }
  }
  return found;
}

export async function promptPreload(input) {
  const prompt = input?.prompt;
  if (!prompt) return null;

  const terms = Array.from(new Set(prompt.toLowerCase().match(/[a-z]+/g) || []))
    .filter((w) => w.length > 2 && !STOP_WORDS.has(w))
    .slice(0, 8);

  if (!terms.length) return null;

  const proj = getProjectDir();
  let found;

  const rgCmd = findRg();
  if (rgCmd) {
    // Prefer rg for content search (more accurate)
    found = contentSearchRg(terms, proj, rgCmd);
  } else {
    // Fallback: filename/path search (cross-platform, no rg dependency)
    found = nameSearch(terms, proj);
  }

  const uniqueFiles = Array.from(found).slice(0, 10).join(' · ');
  if (!uniqueFiles) return null;

  return {
    hookSpecificOutput: {
      additionalContext: `Relevant files (pre-searched): ${uniqueFiles}`,
    },
  };
}
