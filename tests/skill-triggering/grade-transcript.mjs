import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

export function parseTranscript(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Transcript file not found at ${filePath}`);
  }
  const fileContent = fs.readFileSync(filePath, 'utf8');
  return fileContent.split('\n')
    .filter(line => line.trim())
    .map(line => {
      try {
        const obj = JSON.parse(line);
        if (obj.type === 'assistant' && obj.message && Array.isArray(obj.message.content)) {
          return obj.message.content.map(block => {
            if (block.type === 'text') return block.text;
            if (block.type === 'tool_use') {
              const input = JSON.stringify(block.input) || '';
              return `[tool_use: ${block.name} (${input.length > 100 ? input.slice(0, 100) + '...' : input})]`;
            }
            return '';
          }).join('\n');
        }
        if (obj.type === 'tool_call' || (obj.type === 'system' && obj.subtype === 'tool_call')) {
          const name = obj.name || obj.tool_name || '';
          const input = JSON.stringify(obj.input || obj.tool_input || '') || '';
          return `[tool_use: ${name} (${input.length > 100 ? input.slice(0, 100) + '...' : input})]`;
        }
      } catch (e) {
        // Skip malformed lines
      }
      return '';
    })
    .filter(Boolean)
    .join('\n')
    .trim();
}

export function buildJudgePrompt(summary, expectations) {
  const checklist = expectations.map(exp => `- ${exp}`).join('\n');
  return `You are grading whether an AI agent's transcript satisfies a checklist. Respond with ONLY this JSON shape, no prose: {"results":[{"expectation":"<copy each expectation verbatim>","pass":true|false,"reason":"<one sentence>"}]}

Transcript:
${summary}

Checklist:
${checklist}`;
}

function exitWithError(skill, caseId, message) {
  console.log(JSON.stringify({ skill, caseId, verdict: 'ERROR', error: message }, null, 2));
  process.exit(1);
}

function main() {
  const args = process.argv.slice(2);
  if (args.length < 3) {
    console.error('Usage: node grade-transcript.mjs <skill> <transcript-path> <case-id>');
    process.exit(1);
  }
  const [skill, transcriptPath, caseIdStr] = args;
  const caseId = parseInt(caseIdStr, 10);

  const evalsPath = path.join('skills', skill, 'evals', 'evals.json');
  if (!fs.existsSync(evalsPath)) {
    exitWithError(skill, caseId, `evals.json not found for skill ${skill}`);
  }

  let evalsData;
  try {
    evalsData = JSON.parse(fs.readFileSync(evalsPath, 'utf8'));
  } catch (e) {
    exitWithError(skill, caseId, `Failed to parse evals.json: ${e.message}`);
  }

  const caseData = Array.isArray(evalsData) ? evalsData.find(c => c.id === caseId) : null;
  if (!caseData) {
    exitWithError(skill, caseId, `Case ID ${caseId} not found in evals.json`);
  }

  const expectations = caseData.expectations || caseData.assertions;
  if (!Array.isArray(expectations) || expectations.length === 0) {
    exitWithError(skill, caseId, `No expectations found for case ID ${caseId}`);
  }

  let summary;
  try {
    summary = parseTranscript(transcriptPath);
  } catch (e) {
    exitWithError(skill, caseId, e.message);
  }
  if (!summary) {
    exitWithError(skill, caseId, 'Transcript summary is empty');
  }

  const judgePrompt = buildJudgePrompt(summary, expectations);
  const tempPromptPath = path.join(path.dirname(transcriptPath), `judge-prompt-${Date.now()}.txt`);
  
  let stdoutStr;
  try {
    fs.writeFileSync(tempPromptPath, judgePrompt, 'utf8');
    const flags = ['-p', tempPromptPath, '--output-format', 'json', '--max-turns', '1', '--verbose'];
    if (process.env.SKIP_PERMISSIONS === '1') {
      flags.push('--dangerously-skip-permissions');
    }
    const proc = spawnSync('claude', flags, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] });
    if (proc.error) throw proc.error;
    if (proc.status !== 0) throw new Error(`Claude CLI exited with code ${proc.status}`);
    stdoutStr = proc.stdout;
  } catch (e) {
    exitWithError(skill, caseId, `Claude CLI execution failed: ${e.message}`);
  } finally {
    try {
      if (fs.existsSync(tempPromptPath)) fs.unlinkSync(tempPromptPath);
    } catch (e) {
      // ignore unlink error
    }
  }

  let resultEnvelope;
  try {
    resultEnvelope = JSON.parse(stdoutStr);
  } catch (e) {
    exitWithError(skill, caseId, `Failed to parse Claude CLI output: ${e.message}`);
  }

  const resultText = resultEnvelope.result;
  let gradeResult;
  try {
    gradeResult = JSON.parse(resultText);
  } catch (e) {
    exitWithError(skill, caseId, `Failed to parse grade results JSON: ${e.message}`);
  }

  if (!gradeResult || !Array.isArray(gradeResult.results)) {
    exitWithError(skill, caseId, 'Grade result JSON does not match expected schema');
  }

  const pass = gradeResult.results.every(r => r.pass === true);
  console.log(JSON.stringify({
    skill,
    caseId,
    verdict: pass ? 'PASS' : 'FAIL',
    results: gradeResult.results
  }, null, 2));

  process.exit(pass ? 0 : 1);
}

main();
