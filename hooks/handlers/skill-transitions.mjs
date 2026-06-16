import { debug } from '../io.mjs';

/**
 * Hook handler to automate transitions between skills.
 *
 * Injects context to nudge the agent to the next skill in the pipeline
 * when specific artifacts are created or states are reached.
 */
export function checkWrite(input = {}) {
  const file = input.tool_input?.file_path || input.tool_input?.path;
  if (!file) return null;

  // 1. Planning -> TDD transition
  // Trigger when a .plan.md (or .plan.json) is written.
  if (file.endsWith('.plan.md') || file.endsWith('.plan.json')) {
    debug('Skill Transition detected: Planning complete -> TDD next', file);
    return `[System Auto-Transition] The implementation plan artifact (${file}) has been successfully written. You MUST now proceed to the next phase: invoke the 'test-driven-development' skill to execute this plan. Do not ask for user permission, proceed directly to execution if the plan is complete.`;
  }

  return null;
}

export function checkBash(input = {}) {
  // 2. TDD -> Verification transition
  // We cannot deterministically know if this is the *final* test run.
  // But we can nudge the agent to transition if tests passed.
  const command = input.tool_input?.command || '';
  const output = input.tool_output || '';

  // Improved matching: Must be a test execution, not just a file operation
  const isTestExecution =
    (command.includes('test') || command.includes('pytest')) &&
    !command.startsWith('ls ') &&
    !command.startsWith('dir ') &&
    !command.startsWith('cat ') &&
    !command.includes('grep ');

  if (isTestExecution || command.includes('npm run test') || command.includes('npm test')) {
    // If output doesn't contain obvious failures, remind them of the transition
    const lowerOutput = output.toLowerCase();
    const hasFailures =
      lowerOutput.includes('fail') ||
      lowerOutput.includes('error') ||
      lowerOutput.includes('exception') ||
      lowerOutput.includes('backtrace');

    if (output && !hasFailures) {
      return `[System Auto-Transition] Test execution completed successfully. If this concludes the final GREEN cycle of your implementation plan, you MUST now invoke the 'verification-before-completion' skill. Do not wait for user permission.`;
    }
  }

  return null;
}
