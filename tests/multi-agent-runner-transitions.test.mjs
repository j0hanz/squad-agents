import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evaluateStep, updateState } from '../bin/multi-agent-runner.mjs';

test('finds ready pending tasks with met dependencies', () => {
  const state = {
    lanes: [
      { id: 'lane-1', status: 'PENDING', dependsOn: [], filesTouched: ['f1.js'] },
      { id: 'lane-2', status: 'PENDING', dependsOn: ['lane-1'], filesTouched: ['f2.js'] },
    ],
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
        reviews: { spec: { verdict: null, runs: 0 }, quality: { verdict: null, runs: 0 } },
      },
    ],
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
    files: ['f1.js'],
  });

  assert.strictEqual(state.lanes[0].status, 'SPEC_REVIEW');
});

test('reviews are dispatched even when at concurrency cap', () => {
  const state = {
    lanes: [
      { id: 'lane-1', status: 'RUNNING', dependsOn: [], filesTouched: ['f1.js'] },
      { id: 'lane-2', status: 'RUNNING', dependsOn: [], filesTouched: ['f2.js'] },
      {
        id: 'lane-3',
        status: 'SPEC_REVIEW',
        dependsOn: [],
        filesTouched: ['f3.js'],
        reviews: { spec: { verdict: null, runs: 0 }, quality: { verdict: null, runs: 0 } },
      },
      { id: 'lane-4', status: 'PENDING', dependsOn: [], filesTouched: ['f4.js'] },
    ],
  };

  const nextActions = evaluateStep(state);
  // There are 3 running/active lanes (lane-1, lane-2, lane-3).
  // lane-4 (PENDING) should NOT be dispatched because we are at the concurrency cap of 3.
  // But lane-3 (SPEC_REVIEW) should still have a DISPATCH_SPEC_REVIEWER action dispatched.

  const implementerActions = nextActions.filter((a) => a.action === 'DISPATCH_IMPLEMENTER');
  assert.strictEqual(
    implementerActions.length,
    0,
    'Should not dispatch new pending lane at concurrency cap',
  );

  const specActions = nextActions.filter((a) => a.action === 'DISPATCH_SPEC_REVIEWER');
  assert.strictEqual(
    specActions.length,
    1,
    'Should dispatch spec review action at concurrency cap',
  );
  assert.strictEqual(specActions[0].laneId, 'lane-3');
});

test('failed reviews reset to PENDING and get re-dispatched', () => {
  let state = {
    lanes: [
      {
        id: 'lane-1',
        status: 'SPEC_REVIEW',
        dependsOn: [],
        filesTouched: ['f1.js'],
        verdict: 'DONE',
        reviews: { spec: { verdict: null, runs: 0 }, quality: { verdict: null, runs: 0 } },
      },
    ],
  };

  // 1. Run spec review, fail it on first run
  state = updateState(state, {
    laneId: 'lane-1',
    phase: 'spec-review',
    verdict: 'SPEC_FAIL',
  });

  // Under the fix, status must go to PENDING, verdict must clear, spec verdict must clear
  assert.strictEqual(state.lanes[0].status, 'PENDING');
  assert.strictEqual(state.lanes[0].verdict, null);
  assert.strictEqual(state.lanes[0].reviews.spec.verdict, null);
  assert.strictEqual(state.lanes[0].reviews.spec.runs, 1);

  // 2. Next step should evaluate and dispatch implementer again
  let actions = evaluateStep(state);
  assert.strictEqual(actions.length, 1);
  assert.strictEqual(actions[0].action, 'DISPATCH_IMPLEMENTER');

  // 3. Move to RUNNING, complete implementation callback
  state.lanes[0].status = 'RUNNING';
  state = updateState(state, {
    laneId: 'lane-1',
    phase: 'implementation',
    verdict: 'DONE',
    commit: 'c2',
    files: ['f1.js'],
  });

  assert.strictEqual(state.lanes[0].status, 'SPEC_REVIEW');

  // 4. In SPEC_REVIEW, next step should dispatch spec reviewer again
  actions = evaluateStep(state);
  assert.strictEqual(actions.length, 1);
  assert.strictEqual(actions[0].action, 'DISPATCH_SPEC_REVIEWER');

  // 5. Spec review passes now
  state = updateState(state, {
    laneId: 'lane-1',
    phase: 'spec-review',
    verdict: 'SPEC_PASS',
  });
  assert.strictEqual(state.lanes[0].status, 'QUALITY_REVIEW');
  assert.strictEqual(state.lanes[0].reviews.spec.runs, 2);

  // 6. Quality review fails on first run
  state = updateState(state, {
    laneId: 'lane-1',
    phase: 'quality-review',
    verdict: 'QUALITY_FAIL',
  });

  // Under the fix, status must go to PENDING, verdict must clear, quality verdict must clear, spec verdict must clear
  assert.strictEqual(state.lanes[0].status, 'PENDING');
  assert.strictEqual(state.lanes[0].verdict, null);
  assert.strictEqual(state.lanes[0].reviews.quality.verdict, null);
  assert.strictEqual(state.lanes[0].reviews.spec.verdict, null);
  assert.strictEqual(state.lanes[0].reviews.quality.runs, 1);

  // 7. Next step should evaluate and dispatch implementer again
  actions = evaluateStep(state);
  assert.strictEqual(actions.length, 1);
  assert.strictEqual(actions[0].action, 'DISPATCH_IMPLEMENTER');
});

test('prevents concurrent dispatch of conflicting pending lanes', () => {
  const state = {
    lanes: [
      { id: 'lane-1', status: 'PENDING', dependsOn: [], filesTouched: ['f1.js'] },
      { id: 'lane-2', status: 'PENDING', dependsOn: [], filesTouched: ['f1.js'] },
    ],
  };

  const nextActions = evaluateStep(state);
  // Both lanes have no dependencies, but they overlap on 'f1.js'.
  // Only the first one should be dispatched, and the second one should be deferred in this step.
  assert.strictEqual(nextActions.length, 1);
  assert.strictEqual(nextActions[0].laneId, 'lane-1');
  assert.strictEqual(nextActions[0].action, 'DISPATCH_IMPLEMENTER');
});
