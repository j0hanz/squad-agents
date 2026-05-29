import fs from 'fs/promises';
import path from 'path';
import { getProjectDir, getPluginDataDir, createPreToolUse } from '../utils.mjs';

export async function breadcrumb(input) {
  const tool = input?.tool_name || 'unknown';
  const pattern = input?.tool_input?.pattern || input?.tool_input?.query || '?';
  const logDir = getPluginDataDir();
  await fs.mkdir(logDir, { recursive: true });
  const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  await fs.appendFile(
    path.join(logDir, 'explorer-breadcrumbs.log'),
    `${ts} [${tool}] ${pattern}\n`,
  );
  return null;
}

export async function breadcrumbBatch(input) {
  const calls = input?.tool_calls;
  if (!Array.isArray(calls) || calls.length === 0) return null;

  const SEARCH_TOOLS = new Set(['Grep', 'Glob']);
  const relevant = calls.filter((c) => SEARCH_TOOLS.has(c?.tool_name));
  if (!relevant.length) return null;

  const logDir = getPluginDataDir();
  await fs.mkdir(logDir, { recursive: true });
  const ts = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  const lines = relevant.map((c) => {
    const pattern = c.tool_input?.pattern || c.tool_input?.query || c.tool_input?.path || '?';
    return `${ts} [${c.tool_name}] ${pattern}`;
  });
  await fs.appendFile(path.join(logDir, 'explorer-breadcrumbs.log'), `${lines.join('\n')}\n`);
  return null;
}

export async function readIntercept(input) {
  const toolInput = input?.tool_input || {};
  const filePathRaw = toolInput.file_path;
  if (!filePathRaw || toolInput.offset !== undefined || toolInput.limit !== undefined) return null;

  const proj = getProjectDir();
  const filePath = path.isAbsolute(filePathRaw) ? filePathRaw : path.join(proj, filePathRaw);

  let lines;
  try {
    const content = await fs.readFile(filePath, 'utf8');
    lines = content.split('\n').length;
  } catch (e) {
    return null;
  }

  if (lines <= 300) return null;

  const updatedInput = { ...toolInput, limit: 150 };
  return createPreToolUse(
    updatedInput,
    `File has ~${lines} lines. Loaded first 150. Use offset/limit to read further sections.`,
  );
}

export async function searchEnrich(input) {
  const tool = input?.tool_name;
  if (tool !== 'Grep') return null;

  const toolInput = input?.tool_input || {};
  if (toolInput.glob) return null;

  const proj = getProjectDir();
  let manifestCount = 0;
  let langType = '';

  const checkExists = async (f) => {
    try {
      return (await fs.stat(path.join(proj, f))).isFile();
    } catch (e) {
      return false;
    }
  };

  if (await checkExists('package.json')) {
    manifestCount++;
    langType = 'ts';
  }
  if (await checkExists('go.mod')) {
    manifestCount++;
    langType = 'go';
  }
  if (await checkExists('Cargo.toml')) {
    manifestCount++;
    langType = 'rust';
  }
  if ((await checkExists('pyproject.toml')) || (await checkExists('requirements.txt'))) {
    manifestCount++;
    langType = 'py';
  }

  if (manifestCount !== 1) langType = '';

  const exclGlob = '!{node_modules,dist,build,.git,__pycache__,.next,vendor,target,bin,obj}/**';

  const updatedInput = { ...toolInput, glob: exclGlob };
  if (!toolInput.type && langType) {
    updatedInput.type = langType;
  }

  return createPreToolUse(updatedInput);
}
