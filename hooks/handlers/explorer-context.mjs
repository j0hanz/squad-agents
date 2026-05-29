import fs from 'fs';
import path from 'path';
import { getProjectDir, getPluginDataDir, createSessionStart } from '../utils.mjs';

const EXCLUDE = new Set([
  'node_modules',
  '.git',
  '__pycache__',
  'dist',
  'build',
  'target',
  '.venv',
  '.next',
  'vendor',
]);

function findFilesAtDepth(dir, names, maxDepth) {
  const results = [];
  function walk(current, depth) {
    if (depth > maxDepth) return;
    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch (e) {
      return;
    }
    for (const entry of entries) {
      if (EXCLUDE.has(entry.name)) continue;
      if (entry.isFile() && names.includes(entry.name)) {
        results.push(path.join(current, entry.name));
      } else if (entry.isDirectory() && depth < maxDepth) {
        walk(path.join(current, entry.name), depth + 1);
      }
    }
  }
  walk(dir, 0);
  return results;
}

function findDirsNamed(dir, names, maxDepth) {
  const results = [];
  function walk(current, depth) {
    if (depth > maxDepth) return;
    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch (e) {
      return;
    }
    for (const entry of entries) {
      if (!entry.isDirectory() || EXCLUDE.has(entry.name)) continue;
      if (names.includes(entry.name))
        results.push(path.relative(dir, path.join(current, entry.name)));
      if (depth < maxDepth) walk(path.join(current, entry.name), depth + 1);
    }
  }
  walk(dir, 0);
  return results;
}

function readHead(filePath, lineCount = 30, maxChars = 400) {
  try {
    return fs
      .readFileSync(filePath, 'utf8')
      .split('\n')
      .slice(0, lineCount)
      .join(' ')
      .slice(0, maxChars);
  } catch (e) {
    return '';
  }
}

export async function context() {
  const proj = getProjectDir();

  const topDirs = (() => {
    try {
      return (
        fs
          .readdirSync(proj, { withFileTypes: true })
          .filter((e) => e.isDirectory() && !e.name.startsWith('.') && !EXCLUDE.has(e.name))
          .map((e) => e.name)
          .sort()
          .join('  ') || 'none'
      );
    } catch (e) {
      return 'none';
    }
  })();

  const manifestNames = [
    'package.json',
    'Cargo.toml',
    'go.mod',
    'pyproject.toml',
    'pom.xml',
    'Gemfile',
    'requirements.txt',
  ];
  const manifests =
    findFilesAtDepth(proj, manifestNames, 2)
      .map((f) => path.basename(f))
      .sort()
      .slice(0, 10)
      .join('  ') || 'none found';

  const entryNames = [
    'main.js',
    'main.ts',
    'main.mjs',
    'main.py',
    'main.go',
    'main.rs',
    'index.js',
    'index.ts',
    'index.py',
  ];
  const entryPoints =
    findFilesAtDepth(proj, entryNames, 3)
      .map((f) => path.relative(proj, f))
      .slice(0, 10)
      .join('  ') || 'none';

  const cmdDirs = findDirsNamed(proj, ['cmd', 'app'], 2).join('  ');

  const instructionNames = ['CLAUDE.md', 'AGENTS.md', 'GEMINI.md'];
  const instructionFiles =
    findFilesAtDepth(proj, instructionNames, 4)
      .map((f) => path.relative(proj, f))
      .join('  ') || 'none';

  let archDocs = '';
  for (const candidate of ['ARCHITECTURE.md', 'CONTEXT.md', 'docs/adr', 'docs/decisions', 'ADR']) {
    const p = path.join(proj, candidate);
    try {
      const stats = fs.statSync(p);
      if (stats.isFile()) {
        archDocs += `  [${candidate}]: ${readHead(p)}\n`;
      } else if (stats.isDirectory()) {
        const mdFiles = fs.readdirSync(p).filter((f) => f.endsWith('.md'));
        for (const name of mdFiles) {
          archDocs += `  [${candidate}/${name}]: ${readHead(path.join(p, name), 30, 300)}\n`;
        }
      }
    } catch (e) {
      if (e.code !== 'ENOENT') throw e;
    }
  }

  let output = `Top-level dirs: ${topDirs}\n`;
  output += `Project manifests: ${manifests}\n`;
  output += `Entry points: ${entryPoints}${cmdDirs ? `  cmd/app dirs: ${cmdDirs}` : ''}\n`;
  output += `Nested instruction files: ${instructionFiles}\n`;
  if (archDocs) output += `Architecture docs:\n${archDocs}`;

  return createSessionStart(output);
}

export async function stop() {
  return { systemMessage: 'Explorer: investigation complete.' };
}

export async function subagentStop(input) {
  const transcript = input?.agent_transcript_path;
  const type = input?.agent_type || 'unknown';
  if (!transcript) return null;

  try {
    const stats = fs.statSync(transcript);
    if (!stats.isFile()) return null;
  } catch (e) {
    if (e.code === 'ENOENT') return null;
    throw e;
  }

  const tail = fs.readFileSync(transcript, 'utf8').split('\n').slice(-20).join('\n');
  return `[Subagent: ${type}] Final context (last 20 lines of transcript):\n${tail}`;
}

export async function sessionEnd() {
  return { systemMessage: 'Explorer: session complete.' };
}

export async function subagentStart(input) {
  const type = input?.agent_type || 'unknown';
  const logDir = getPluginDataDir();
  const logPath = path.join(logDir, 'explorer-breadcrumbs.log');

  let content;
  try {
    content = fs.readFileSync(logPath, 'utf8');
  } catch (e) {
    if (e.code === 'ENOENT') return null;
    throw e;
  }
  if (!content.trim()) return null;

  const patterns = new Set();
  for (const line of content.split('\n')) {
    const match = line.match(/\] (.+)$/);
    if (match) patterns.add(match[1]);
  }
  if (!patterns.size) return null;

  const summary = Array.from(patterns).slice(0, 10).join(' · ');
  return `[Subagent: ${type}] Session has already explored: ${summary}`;
}
