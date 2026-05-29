---
description: Get a guided tour of the agent-dev plugin.
---

# Welcome — Plugin Walkthrough

Welcome to the **agent-dev** plugin! This tool is designed to help you build, test, and maintain high-quality Claude Code agents and skills.

## 🚀 Key Workflows

### 1. Planning a Feature

Use `/plan [description]` to run the sequential planning pipeline:

- **Brainstorm:** Explore intent and design.
- **Spec:** Define technical requirements.
- **Plan:** Create a step-by-step implementation plan.

### 2. Developing Components

Use `/new [skill|agent|hook] [name]` to scaffold new components.

### 3. Evaluating Behavior

The plugin follows an **eval-first** philosophy:

- `/eval create [name]` — Author a new test suite.
- `/eval run [name]` — Run behavioral simulations.

### 4. Health Checks

Use `/check all` to ensure your plugin structure, agents, and hooks are correct.

### 5. Delivery

Use `/deliver` to validate your work and commit it with proper attribution.

## 🤖 Specialized Agents

- **Coder:** Autonomous code execution and refactoring.
- **Explorer:** Research-focused, read-only exploration of code and docs.

## 📚 Getting Started

Try running `/check all` now to see the health status of this workspace!
