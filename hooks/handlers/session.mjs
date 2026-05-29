import fs from 'fs/promises';
import { readFileSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { getProjectDir, runCmd, createSessionStart } from '../utils.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const configPath = path.join(__dirname, '..', 'config', 'session-config.json');

let config = {
  envCandidates: [],
  artifactCandidates: [],
  serviceMarkers: [],
};

try {
  config = JSON.parse(readFileSync(configPath, 'utf-8'));
} catch (e) {
  // Fallback to empty config if not found
}

export async function context() {
  const proj = getProjectDir();

  let repo = runCmd('git rev-parse --show-toplevel', proj);
  repo = repo ? path.basename(repo) : 'unknown';

  const branch = runCmd('git rev-parse --abbrev-ref HEAD', proj) || 'unknown';
  const lastCommit = runCmd('git log -1 --format="%h %s"', proj) || 'none';

  let envName = 'unknown';
  const checkEnv = async (name) => {
    try {
      return (await fs.stat(path.join(proj, name))).isFile();
    } catch (e) {
      return false;
    }
  };

  for (const env of config.envCandidates) {
    if (await checkEnv(env)) {
      envName = env.replace('.env.', '') || 'default';
      break;
    }
  }
  if (envName === 'unknown' && process.env.APP_ENV) {
    envName = process.env.APP_ENV;
  }

  const output = `## Session Context\n\n**Repo:** ${repo}\n**Branch:** ${branch}\n**Last commit:** ${lastCommit}\n**Environment:** ${envName}`;

  return createSessionStart(output);
}

export async function env() {
  const projectDir = getProjectDir();
  const sections = [];

  const statusFile = path.join(projectDir, '.claude', 'status.md');
  try {
    const content = await fs.readFile(statusFile, 'utf8');
    if (content.trim()) sections.push(`## Last Session Status\n\n${content.trim()}`);
  } catch (e) {
    if (e.code !== 'ENOENT') throw e;
  }

  const envFiles = [];
  for (const f of config.envCandidates) {
    try {
      if ((await fs.stat(path.join(projectDir, f))).isFile()) envFiles.push(f);
    } catch (e) {}
  }
  if (envFiles.length) {
    sections.push(`## Active Environment Files\n\n${envFiles.join(', ')}`);
  }

  const artifacts = [];
  for (const f of config.artifactCandidates) {
    try {
      if ((await fs.stat(path.join(projectDir, f))).isFile()) artifacts.push(f);
    } catch (e) {}
  }
  if (artifacts.length) {
    sections.push(
      `## Test Failure Artifacts Found\n\n${artifacts.map((a) => `  - ${a}`).join('\n')}`,
    );
  }

  const detectedServices = [];
  for (const { file, label } of config.serviceMarkers) {
    try {
      if ((await fs.stat(path.join(projectDir, file))).isFile()) detectedServices.push(label);
    } catch (e) {}
  }
  if (detectedServices.length) {
    sections.push(
      `## Service Config Files\n\n${detectedServices.join(', ')} found — local services may be running`,
    );
  }

  if (sections.length) {
    return createSessionStart(sections.join('\n\n'));
  }
  return null;
}

export async function start() {
  const [ctxResult, envResult] = await Promise.all([context(), env()]);

  const parts = [];
  if (ctxResult?.hookSpecificOutput?.additionalContext)
    parts.push(ctxResult.hookSpecificOutput.additionalContext);
  if (envResult?.hookSpecificOutput?.additionalContext)
    parts.push(envResult.hookSpecificOutput.additionalContext);
  // Pointer only — full skill map loads on demand via agent-dev:using-agent-dev
  parts.push(
    '## Skills\nInvoke `agent-dev:using-agent-dev` to see all available process and domain skills.',
  );

  if (!parts.length) return null;
  return createSessionStart(parts.join('\n\n---\n\n'));
}

export async function end() {
  const proj = getProjectDir();
  const claudeDir = path.join(proj, '.claude');
  const statusPath = path.join(claudeDir, 'status.md');
  const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  try {
    await fs.mkdir(claudeDir, { recursive: true });
    await fs.writeFile(statusPath, `Session ended: ${ts}\n`);
  } catch (e) {
    // Non-fatal — status write failure should not error the hook
  }
  return null;
}

export async function contextRefresh() {
  return context();
}
