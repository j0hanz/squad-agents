import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.json_utils import load_json
from scripts.utils import parse_skill_md

_TRIGGER_TOOLS = frozenset({"Skill", "Read"})


def find_project_root(start_path: Path | None = None) -> Path:
    """Find the project root by searching for .claude directory."""
    current = start_path or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


async def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        await asyncio.to_thread(project_commands_dir.mkdir, parents=True, exist_ok=True)
        indented_desc = "\n  ".join(skill_description.splitlines())
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        await asyncio.to_thread(
            command_file.write_text, command_content, encoding="utf-8"
        )

        cmd = [
            "claude",
            "-p",
            query,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=project_root,
            env=env,
        )

        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                process.terminate()
                await process.wait()
            except ProcessLookupError:
                pass
            return False

        triggered = False
        pending_tool_name: str | None = None
        accumulated_json = ""

        for raw_line in stdout.decode(errors="replace").splitlines():
            line = raw_line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "stream_event":
                se = event.get("event", {})
                se_type = se.get("type", "")

                if se_type == "content_block_start":
                    cb = se.get("content_block", {})
                    if cb.get("type") == "tool_use":
                        tool_name = cb.get("name", "")
                        if tool_name in _TRIGGER_TOOLS:
                            pending_tool_name = tool_name
                            accumulated_json = ""

                elif se_type == "content_block_delta" and pending_tool_name:
                    delta = se.get("delta", {})
                    if delta.get("type") == "input_json_delta":
                        accumulated_json += delta.get("partial_json", "")
                        if clean_name in accumulated_json:
                            triggered = True

                elif se_type in ("content_block_stop", "message_stop"):
                    if pending_tool_name and clean_name in accumulated_json:
                        triggered = True
                    pending_tool_name = None
                    accumulated_json = ""

            elif event.get("type") == "assistant":
                message = event.get("message", {})
                for content_item in message.get("content", []):
                    if content_item.get("type") != "tool_use":
                        continue
                    tool_name = content_item.get("name", "")
                    tool_input = content_item.get("input", {})
                    if tool_name == "Skill" and clean_name in str(
                        tool_input.get("skill", "")
                    ):
                        triggered = True
                    elif tool_name == "Read" and clean_name in str(
                        tool_input.get("file_path", "")
                    ):
                        triggered = True

        return triggered
    finally:
        await asyncio.to_thread(command_file.unlink, missing_ok=True)


async def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    semaphore = asyncio.Semaphore(num_workers)

    async def sem_run_single(item):
        async with semaphore:
            return await run_single_query(
                item["query"],
                skill_name,
                description,
                timeout,
                str(project_root),
                model,
            )

    tasks = []
    for item in eval_set:
        for _ in range(runs_per_query):
            tasks.append(sem_run_single(item))

    results_data = await asyncio.gather(*tasks, return_exceptions=True)

    query_triggers = {}
    idx = 0
    for item in eval_set:
        query = item["query"]
        query_triggers[query] = []
        for _ in range(runs_per_query):
            res = results_data[idx]
            idx += 1
            if isinstance(res, Exception):
                query_triggers[query].append(False)
            else:
                query_triggers[query].append(res)

    results = []
    for item in eval_set:
        query = item["query"]
        triggers = query_triggers[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        did_pass = (
            (trigger_rate >= trigger_threshold)
            if should_trigger
            else (trigger_rate < trigger_threshold)
        )
        results.append(
            {
                "query": query,
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers),
                "pass": did_pass,
            }
        )

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run trigger evaluation for a skill description"
    )
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument(
        "--description", default=None, help="Override description to test"
    )
    parser.add_argument(
        "--num-workers", type=int, default=10, help="Number of parallel workers"
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout per query in seconds"
    )
    parser.add_argument(
        "--runs-per-query", type=int, default=3, help="Number of runs per query"
    )
    parser.add_argument(
        "--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold"
    )
    parser.add_argument("--model", default=None, help="Model to use")
    parser.add_argument(
        "--verbose", action="store_true", help="Print progress to stderr"
    )
    args = parser.parse_args()

    eval_set = load_json(Path(args.eval_set))
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    output = asyncio.run(
        run_eval(
            eval_set=eval_set,
            skill_name=name,
            description=description,
            num_workers=args.num_workers,
            timeout=args.timeout,
            project_root=project_root,
            runs_per_query=args.runs_per_query,
            trigger_threshold=args.trigger_threshold,
            model=args.model,
        )
    )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
