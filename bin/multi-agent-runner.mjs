#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export function initPlan(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Plan file does not exist: ${filePath}`);
  }
  const content = fs.readFileSync(filePath, 'utf-8');
  const lanes = [];
  const lines = content.split('\n');
  let idCounter = 1;

  for (const line of lines) {
    if (line.trim().startsWith('- [ ]')) {
      // 1. Strip the markdown list/checkbox prefix
      let titleText = line.trim().replace(/^-\s*\[\s*[xX ]\s*\]\s*/, '');
      
      // 2. Ignore/remove the "(depends on: ...)" suffix
      titleText = titleText.replace(/\(depends on:[^)]*\)/i, '').trim();

      // 3. Ignore the file list by looking at colons and backticks
      const firstColon = titleText.indexOf(':');
      const firstBacktick = titleText.indexOf('`');
      if (firstColon !== -1 && (firstBacktick === -1 || firstColon < firstBacktick)) {
        titleText = titleText.substring(0, firstColon);
      } else if (firstBacktick !== -1) {
        titleText = titleText.substring(0, firstBacktick);
      }
      const title = titleText.trim() || `Task ${idCounter}`;
      
      // Extract code blocks / files
      const filesTouched = [];
      const codeMatches = line.matchAll(/`([^`]+)`/g);
      for (const m of codeMatches) {
        filesTouched.push(m[1]);
      }

      // Extract dependencies
      const dependsOn = [];
      const depMatch = line.match(/\(depends on:\s*([^)]+)\)/i);
      if (depMatch) {
        const deps = depMatch[1].split(',').map(d => d.trim()).filter(Boolean);
        for (const dep of deps) {
          if (dep.toLowerCase() !== 'none') {
            const laneMatch = dep.match(/lane[- ]?(\d+)/i);
            const taskMatch = dep.match(/task[- ]?(\d+)/i);
            if (laneMatch) {
              dependsOn.push(`lane-${laneMatch[1]}`);
            } else if (taskMatch) {
              dependsOn.push(`lane-${taskMatch[1]}`);
            }
          }
        }
      }

      lanes.push({
        id: `lane-${idCounter++}`,
        title,
        filesTouched,
        dependsOn,
        status: 'PENDING',
        role: 'Writer',
        verdict: null,
        commit: null,
        reviews: {
          spec: { verdict: null, runs: 0 },
          quality: { verdict: null, runs: 0 }
        }
      });
    }
  }

  // Verify that the target lane exists in the parsed lanes list
  for (const lane of lanes) {
    lane.dependsOn = lane.dependsOn.filter(depId => {
      return lanes.some(l => l.id === depId);
    });
  }

  return {
    planPath: filePath,
    status: 'IN_PROGRESS',
    lanes,
    history: [{ timestamp: new Date().toISOString(), event: 'INIT', message: `Initialized with ${lanes.length} lanes` }]
  };
}

export function saveState(state) {
  const stateDir = path.resolve('.claude');
  if (!fs.existsSync(stateDir)) {
    fs.mkdirSync(stateDir, { recursive: true });
  }
  const statePath = path.join(stateDir, 'multi_agent_state.json');
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2), 'utf-8');
}

export function evaluateStep(state) {
  const actions = [];
  const runningLanes = state.lanes.filter(l => ['RUNNING', 'SPEC_REVIEW', 'QUALITY_REVIEW', 'MERGE_WAIT'].includes(l.status));

  for (const lane of state.lanes) {
    if (lane.status === 'PENDING') {
      const depsCompleted = lane.dependsOn.every(depId => {
        const depLane = state.lanes.find(l => l.id === depId);
        return depLane && depLane.status === 'COMPLETED';
      });

      // Check for file touch conflicts with currently running lanes
      const hasConflict = runningLanes.some(rl => 
        rl.filesTouched.some(f => lane.filesTouched.includes(f))
      );

      const dispatchedNewLanes = actions.filter(a => a.action === 'DISPATCH_IMPLEMENTER').length;
      if (depsCompleted && !hasConflict && (runningLanes.length + dispatchedNewLanes < 3)) {
        actions.push({
          laneId: lane.id,
          action: 'DISPATCH_IMPLEMENTER',
          prompt: `SCOPE:\n  Files IN scope: ${lane.filesTouched.join(', ')}\nOBJECTIVE:\n  ${lane.title}\nCONTEXT:\n  Last commit: HEAD\nOUTPUT:\n  VERDICT: DONE | BLOCKED | NEEDS_CONTEXT`
        });
      }
    } else if (lane.status === 'SPEC_REVIEW' && lane.reviews.spec.verdict === null) {
      actions.push({
        laneId: lane.id,
        action: 'DISPATCH_SPEC_REVIEWER',
        prompt: `SCOPE:\n  Files changed: ${lane.filesTouched.join(', ')}\nOBJECTIVE:\n  Verify ${lane.title} matches spec.`
      });
    } else if (lane.status === 'QUALITY_REVIEW' && lane.reviews.quality.verdict === null) {
      actions.push({
        laneId: lane.id,
        action: 'DISPATCH_QUALITY_REVIEWER',
        prompt: `SCOPE:\n  Files changed: ${lane.filesTouched.join(', ')}\nOBJECTIVE:\n  Review code quality.`
      });
    }
  }

  return actions;
}

export function updateState(state, update) {
  const lane = state.lanes.find(l => l.id === update.laneId);
  if (!lane) return state;

  if (update.phase === 'implementation') {
    lane.verdict = update.verdict;
    lane.commit = update.commit;
    if (update.files) lane.filesTouched = update.files;
    
    if (update.verdict === 'DONE' || update.verdict === 'DONE_WITH_CONCERNS') {
      lane.status = 'SPEC_REVIEW';
    } else {
      lane.status = 'BLOCKED';
    }
  } else if (update.phase === 'spec-review') {
    lane.reviews.spec.verdict = update.verdict;
    lane.reviews.spec.runs++;
    
    if (update.verdict === 'SPEC_PASS') {
      lane.status = 'QUALITY_REVIEW';
    } else {
      if (lane.reviews.spec.runs < 2) {
        lane.status = 'PENDING';
        lane.verdict = null;
        lane.reviews.spec.verdict = null; // reset for next run
      } else {
        lane.status = 'BLOCKED';
      }
    }
  } else if (update.phase === 'quality-review') {
    lane.reviews.quality.verdict = update.verdict;
    lane.reviews.quality.runs++;

    if (update.verdict === 'QUALITY_PASS' || update.verdict === 'MINOR') {
      lane.status = 'COMPLETED'; // Assume merge succeeds; conflicts handled in Task 3
    } else {
      if (lane.reviews.quality.runs < 2) {
        lane.status = 'PENDING';
        lane.verdict = null;
        lane.reviews.quality.verdict = null; // reset for next run
        lane.reviews.spec.verdict = null; // reset spec review so it doesn't get stuck in SPEC_REVIEW
      } else {
        lane.status = 'BLOCKED';
      }
    }
  }

  if (!state.history) {
    state.history = [];
  }
  state.history.push({
    timestamp: new Date().toISOString(),
    event: 'UPDATE',
    message: `Updated lane ${update.laneId} in phase ${update.phase} with verdict ${update.verdict}`
  });

  return state;
}

// CLI entrypoint handling
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [,, command, arg] = process.argv;
  if (command === 'init' && arg) {
    const state = initPlan(arg);
    saveState(state);
    console.log(`Initialized multi-agent state in .claude/multi_agent_state.json`);
  } else if (command === 'step') {
    const statePath = path.resolve('.claude/multi_agent_state.json');
    if (!fs.existsSync(statePath)) {
      console.error('Error: State file not found. Run init first.');
      process.exit(1);
    }
    let state = JSON.parse(fs.readFileSync(statePath, 'utf-8'));
    
    if (process.argv.includes('--update')) {
      const payloadIndex = process.argv.indexOf('--update') + 1;
      const payload = JSON.parse(process.argv[payloadIndex]);
      state = updateState(state, payload);
      saveState(state);
    }

    const actions = evaluateStep(state);
    console.log(JSON.stringify(actions, null, 2));
  }
}
