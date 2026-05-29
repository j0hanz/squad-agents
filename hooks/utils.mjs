import os from 'os';
import { execSync } from 'child_process';
import fs from 'fs';

export const getProjectDir = () => process.env.CLAUDE_PROJECT_DIR || process.cwd();
export const getPluginDataDir = () => process.env.CLAUDE_PLUGIN_DATA || os.tmpdir();

export function runCmd(cmd, cwd = getProjectDir(), timeout = 5000) {
  try {
    return execSync(cmd, { cwd, stdio: 'pipe', encoding: 'utf-8', timeout }).trim();
  } catch (e) {
    return '';
  }
}

export function isFile(filePath) {
  try {
    return fs.statSync(filePath).isFile();
  } catch (e) {
    return false;
  }
}

export function isDir(dirPath) {
  try {
    return fs.statSync(dirPath).isDirectory();
  } catch (e) {
    return false;
  }
}

export function createPreToolUse(updatedInput, additionalContext = undefined) {
  const output = { hookEventName: 'PreToolUse', updatedInput };
  if (additionalContext) output.additionalContext = additionalContext;
  return { hookSpecificOutput: output };
}

export function createSessionStart(additionalContext) {
  return {
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext,
    },
  };
}

export function createPostToolUse(additionalContext) {
  return {
    hookSpecificOutput: {
      hookEventName: 'PostToolUse',
      additionalContext,
    },
  };
}

export function createPostToolUseFailure(additionalContext) {
  return {
    hookSpecificOutput: {
      hookEventName: 'PostToolUseFailure',
      additionalContext,
    },
  };
}
