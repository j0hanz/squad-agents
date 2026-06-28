import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evaluateStep, updateState } from '../bin/multi-agent-runner.mjs';

test('finds ready pending tasks with met dependencies', () => {
  const state = {
    lanes: [
      { id: 'lane-1', status: 'PENDING', dependsOn: [], filesTouched: ['f1.js'] },
      { id: 'lane-2', status: 'PENDING', dependsOn: ['lane-1'], filesTouched: ['f2.js'] }
    ]
  };

  const nextActions = evaluateStep(state);
  assert.strictEqual(nextActions.length, 1);
  assert.strictEqual(nextActions[0].laneId, 'lane-1');
  assert.strictEqual(nextActions[0].action, 'DISPATCH_IMPLEMENTER');
});

test('applies updates and advances state machine', () => {
  let state = {
    lanes: [
      {
        id: 'lane-1',
        status: 'PENDING',
        dependsOn: [],
        filesTouched: ['f1.js'],
        reviews: { spec: { verdict: null, runs: 0 }, quality: { verdict: null, runs: 0 } }
      }
    ]
  };

  // 1. Move to RUNNING
  const actions = evaluateStep(state);
  assert.strictEqual(actions[0].action, 'DISPATCH_IMPLEMENTER');
  state.lanes[0].status = 'RUNNING';

  // 2. Complete implementation callback
  state = updateState(state, {
    laneId: 'lane-1',
    phase: 'implementation',
    verdict: 'DONE',
    commit: 'c1',
    files: ['f1.js']
  });

  assert.strictEqual(state.lanes[0].status, 'SPEC_REVIEW');
});
