#!/usr/bin/env python3
"""Behavioral test harness for agents using Claude Code's hook protocol.

Usage:
  python scripts/simulate.py <agent.md> <cases.yaml> [options]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

import shutil
from simulator import (
    evaluate_assertions,
    parse_tool_calls_jsonl,
    aggregate_runs,
    RunResult,
)


def _safety_check(args) -> tuple[bool, str]:
    if os.environ.get("CLAUDE_CODE_REMOTE") == "true":
        return (False, "refusing to simulate in remote web environment")
    if args.worktree or args.sandbox:
        return True, ""
    cwd = Path.cwd().resolve()
    tmp_prefix = Path(tempfile.gettempdir()).resolve()
    try:
        cwd.relative_to(tmp_prefix)
        return True, ""
    except ValueError:
        return (
            False,
            "safety precondition not met: pass --worktree or --sandbox, or run inside tmpdir",
        )


def _write_observer(simulate_dir: Path) -> Path:
    simulate_dir.mkdir(parents=True, exist_ok=True)
    obs = simulate_dir / "observer.py"
    src = Path(__file__).parent / "lib" / "observer.py"
    shutil.copy2(src, obs)
    return obs


def _write_hooks_config(simulate_dir: Path, observer: Path) -> Path:
    cfg = {
        "hooks": {
            ev: [
                {
                    "matcher": ".*" if ev in {"PreToolUse", "PostToolUse"} else "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{sys.executable} {observer}",
                            "timeout": 5,
                        }
                    ],
                }
            ]
            for ev in ("PreToolUse", "PostToolUse", "Stop")
        }
    }
    out = simulate_dir / "hooks-config.json"
    out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return out


def _load_cases(path: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_case(
    case: dict, agent_file: Path, hooks_config: Path, runs: int, simulate_dir: Path
) -> list[RunResult]:
    prompt = case.get("prompt")
    expect = case.get("expect", {})
    results = []

    for i in range(runs):
        run_id = f"{case.get('id', 'case')}-run-{i}"
        run_dir = simulate_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["SIMULATE_RUN_ID"] = run_id
        env["SIMULATE_OUT_DIR"] = str(simulate_dir / "runs")
        env["CLAUDE_CONFIG_DIR"] = str(run_dir / ".claude-config")  # Isolated config

        # We need to inject the hooks config. Since we can't easily modify the global
        # config for a single run without affecting others, we use an env var that
        # Claude Code's hook loader respects for dev overrides.
        env["CLAUDE_HOOKS_CONFIG"] = str(hooks_config)

        start_time = time.time()

        cmd = ["claude", "-p", prompt, "--output-format", "json"]
        if agent_file:
            # How to specify the agent? Usually by pointing to its instructions or using it.
            # If it's a subagent file, we might need a specific CLI flag if available.
            # For now, we assume the prompt includes "Use [agent]" if needed.
            pass

        try:
            res = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=300
            )
            duration_s = time.time() - start_time

            # Parse output
            try:
                out_data = json.loads(res.stdout)
                final_response = out_data.get("completion", "")
                tokens_in = out_data.get("usage", {}).get("input_tokens", 0)
                tokens_out = out_data.get("usage", {}).get("output_tokens", 0)
            except Exception:
                final_response = res.stdout
                tokens_in = tokens_out = 0

            # Parse tool calls from observer log
            log_file = run_dir / "tool-calls.jsonl"
            calls = []
            if log_file.exists():
                calls = parse_tool_calls_jsonl(log_file.read_text())

            # Evaluate
            eval_res = evaluate_assertions(calls, final_response, expect, duration_s)

            results.append(
                RunResult(
                    passed=eval_res.passed,
                    duration_ms=int(duration_s * 1000),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                )
            )

        except subprocess.TimeoutExpired:
            results.append(RunResult(False, 300000, 0, 0))
        except Exception as e:
            print(f"Run {run_id} failed: {e}")
            results.append(RunResult(False, 0, 0, 0))

    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("agent_file")
    p.add_argument("cases_file")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--worktree", action="store_true")
    p.add_argument("--sandbox", action="store_true")
    p.add_argument("--simulate-dir", default=".simulate")
    p.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Validate config and write observer files without running claude",
    )
    p.add_argument(
        "--report",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = p.parse_args()

    ok, reason = _safety_check(args)
    if not ok:
        print(f"error: {reason}")
        sys.exit(2)

    agent_path = Path(args.agent_file)
    cases_path = Path(args.cases_file)
    cases_data = _load_cases(cases_path)

    simulate_dir = Path(args.simulate_dir)
    observer = _write_observer(simulate_dir)
    hooks_cfg = _write_hooks_config(simulate_dir, observer)

    if args.dry_run:
        if args.report == "json":
            payload = {
                "dry_run": True,
                "suite": cases_data.get("suite", "default"),
                "safety_checks_passed": True,
                "agent": str(agent_path),
                "cases": len(cases_data.get("cases", [])),
                "simulate_dir": str(simulate_dir),
                "observer": str(observer),
                "hooks_config": str(hooks_cfg),
            }
            print(json.dumps(payload))
        else:
            suite_name = cases_data.get("suite", "default")
            cases = cases_data.get("cases", [])
            print(f"[dry-run] Suite: {suite_name}")
            print(f"[dry-run] Agent: {agent_path}")
            print(f"[dry-run] Cases ({len(cases)}):")
            for c in cases:
                print(
                    f"  - {c.get('name', c.get('id', 'unnamed'))}: {c.get('prompt', '')[:60]}"
                )
            print(f"[dry-run] Observer written to: {observer}")
            print(f"[dry-run] Hooks config written to: {hooks_cfg}")
        sys.exit(0)

    suite_results = {}

    print(f"Running simulation suite: {cases_data.get('suite', 'default')}")

    for case in cases_data.get("cases", []):
        print(f"  Case: {case.get('id', 'unknown')}...", end="", flush=True)
        results = run_case(case, agent_path, hooks_cfg, args.runs, simulate_dir)
        summary = aggregate_runs(results)
        suite_results[case.get("id")] = summary
        print(f" {summary['pass_rate'] * 100:.0f}% pass")

    # Final report
    if args.report == "json":
        print(json.dumps(suite_results))
    else:
        print("\n## Simulation Report\n")
        for case_id, summary in suite_results.items():
            status = (
                "✅"
                if summary["pass_rate"] == 1.0
                else "⚠️"
                if summary["pass_rate"] > 0
                else "❌"
            )
            print(
                f"- {status} **{case_id}**: {summary['pass_rate'] * 100:.0f}% pass "
                f"(n={summary['n']}), {summary['median_latency_ms']}ms median"
            )

    if all(s["pass_rate"] == 1.0 for s in suite_results.values()):
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
