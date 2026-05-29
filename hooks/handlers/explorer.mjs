// Re-export facade — preserves all existing hook references (runner.mjs explorer <action>).
// Logic lives in focused sub-modules; import from those directly for unit tests.
export { context, stop, subagentStop, sessionEnd, subagentStart } from './explorer-context.mjs';
export { breadcrumb, searchEnrich, readIntercept, breadcrumbBatch } from './explorer-search.mjs';
export { compactFlush, compactRestore } from './explorer-compact.mjs';
export { prefetch } from './explorer-web.mjs';
export { cwdWatch, fileChanged, promptPreload } from './explorer-prompt.mjs';
