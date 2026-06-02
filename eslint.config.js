import js from '@eslint/js';
import prettier from 'eslint-config-prettier';
import globals from 'globals';

export default [
  {
    ignores: [
      'node_modules/**',
      '.simulate/**',
      '.venv/**',
      '.ruff_cache/**',
      '__pycache__/**',
      'skills/skill-builder/assets/**',
    ],
  },

  js.configs.recommended,

  // All Node.js scripts — hooks, skills, bin, tests
  {
    files: [
      'hooks/**/*.mjs',
      'skills/**/*.mjs',
      'skills/**/*.js',
      'bin/**/*.mjs',
      'tests/**/*.mjs',
    ],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: globals.node,
    },
    rules: {
      // Fail-silent catch blocks are idiomatic in hook and script code
      'no-empty': ['error', { allowEmptyCatch: true }],
      // Catch params are routinely unused: catch (e) {} — don't require _e
      'no-unused-vars': [
        'error',
        {
          vars: 'all',
          args: 'after-used',
          argsIgnorePattern: '^_',
          caughtErrors: 'none',
          ignoreRestSiblings: true,
        },
      ],
      'no-var': 'error',
      'prefer-const': 'error',
      eqeqeq: ['error', 'always', { null: 'ignore' }],
      'object-shorthand': 'error',
      'prefer-template': 'error',
    },
  },

  // Hooks only: warn on console.log — debug.mjs scans for these as debug artifacts
  {
    files: ['hooks/**/*.mjs'],
    rules: {
      'no-console': 'warn',
    },
  },

  // Must be last — disables rules that conflict with prettier formatting
  prettier,
];
