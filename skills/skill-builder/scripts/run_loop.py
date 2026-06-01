import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_report import generate_html
from scripts.improve_description import improve_description
from scripts.json_utils import load_json
from scripts.run_eval import find_project_root, run_eval
from scripts.utils import parse_skill_md


def split_eval_set(
    eval_set: list[dict], holdout: float, seed: int = 42
) -> tuple[list[dict], list[dict]]:
    random.seed(seed)
    trigger = [e for e in eval_set if e["should_trigger"]]
    no_trigger = [e for e in eval_set if not e["should_trigger"]]
    random.shuffle(trigger)
    random.shuffle(no_trigger)

    n_trigger_test = (
        max(1, int(len(trigger) * holdout)) if trigger and holdout > 0 else 0
    )
    n_no_trigger_test = (
        max(1, int(len(no_trigger) * holdout)) if no_trigger and holdout > 0 else 0
    )

    test_set = trigger[:n_trigger_test] + no_trigger[:n_no_trigger_test]
    train_set = trigger[n_trigger_test:] + no_trigger[n_no_trigger_test:]
    return train_set, test_set


async def _run_iteration(
    iteration: int,
    current_description: str,
    train_set: list[dict],
    test_set: list[dict],
    skill_name: str,
    num_workers: int,
    timeout: int,
    runs_per_query: int,
    trigger_threshold: float,
    model: str,
) -> tuple[dict, dict | None]:
    all_queries = train_set + test_set
    project_root = find_project_root()

    all_results = await run_eval(
        eval_set=all_queries,
        skill_name=skill_name,
        description=current_description,
        num_workers=num_workers,
        timeout=timeout,
        project_root=project_root,
        runs_per_query=runs_per_query,
        trigger_threshold=trigger_threshold,
        model=model,
    )

    train_queries_set = {q["query"] for q in train_set}
    train_result_list = [
        r for r in all_results["results"] if r["query"] in train_queries_set
    ]
    test_result_list = [
        r for r in all_results["results"] if r["query"] not in train_queries_set
    ]

    train_passed = sum(1 for r in train_result_list if r["pass"])
    train_total = len(train_result_list)
    train_results = {
        "results": train_result_list,
        "summary": {
            "passed": train_passed,
            "failed": train_total - train_passed,
            "total": train_total,
        },
    }

    test_results = None
    if test_set:
        test_passed = sum(1 for r in test_result_list if r["pass"])
        test_total = len(test_result_list)
        test_results = {
            "results": test_result_list,
            "summary": {
                "passed": test_passed,
                "failed": test_total - test_passed,
                "total": test_total,
            },
        }

    return train_results, test_results


async def run_loop_async(
    eval_set: list[dict],
    skill_path: Path,
    description_override: str | None,
    num_workers: int,
    timeout: int,
    max_iterations: int,
    runs_per_query: int,
    trigger_threshold: float,
    holdout: float,
    model: str,
    verbose: bool,
    live_report_path: Path | None = None,
    log_dir: Path | None = None,
) -> dict:
    name, original_description, content = parse_skill_md(skill_path)
    current_description = description_override or original_description
    train_set, test_set = (
        split_eval_set(eval_set, holdout) if holdout > 0 else (eval_set, [])
    )
    history = []

    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"Iteration {iteration}/{max_iterations}...")

        train_results, test_results = await _run_iteration(
            iteration,
            current_description,
            train_set,
            test_set,
            name,
            num_workers,
            timeout,
            runs_per_query,
            trigger_threshold,
            model,
        )

        history.append(
            {
                "iteration": iteration,
                "description": current_description,
                "train_passed": train_results["summary"]["passed"],
                "train_total": train_results["summary"]["total"],
                "train_results": train_results["results"],
                "test_passed": test_results["summary"]["passed"]
                if test_results
                else None,
                "test_total": test_results["summary"]["total"]
                if test_results
                else None,
                "test_results": test_results["results"] if test_results else None,
            }
        )

        if live_report_path:
            current_best = max(
                (
                    h.get("test_passed", 0) or 0
                    if test_set
                    else h.get("train_passed", 0) or 0
                    for h in history
                ),
                default=0,
            )
            report_html = generate_html(
                {
                    "original_description": original_description,
                    "best_description": current_description,
                    "best_score": current_best,
                    "iterations_run": len(history),
                    "history": history,
                    "train_size": len(train_set),
                    "test_size": len(test_set),
                },
                auto_refresh=True,
                skill_name=name,
            )
            await asyncio.to_thread(
                live_report_path.write_text, report_html, encoding="utf-8"
            )

        if train_results["summary"]["failed"] == 0 or iteration == max_iterations:
            break

        current_description = await asyncio.to_thread(
            improve_description,
            name,
            content,
            current_description,
            train_results,
            [
                {k: v for k, v in h.items() if not k.startswith("test_")}
                for h in history
            ],
            model,
            test_results,
            log_dir,
            iteration,
        )

    best = max(
        history,
        key=lambda h: (h["test_passed"] if test_set else h["train_passed"]) or 0,
    )
    best_score = (best["test_passed"] if test_set else best["train_passed"]) or 0
    return {
        "original_description": original_description,
        "best_description": best["description"],
        "best_score": best_score,
        "iterations_run": len(history),
        "train_size": len(train_set),
        "test_size": len(test_set),
        "history": history,
    }


def main():
    parser = argparse.ArgumentParser(description="Run eval + improve loop")
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--description", default=None)
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--holdout", type=float, default=0.2)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--live-report", help="Path to write live HTML report")
    parser.add_argument("--log-dir", help="Directory for detailed iteration logs")
    args = parser.parse_args()

    eval_set = load_json(Path(args.eval_set))
    live_report_path = Path(args.live_report) if args.live_report else None
    log_dir = Path(args.log_dir) if args.log_dir else None

    output = asyncio.run(
        run_loop_async(
            eval_set=eval_set,
            skill_path=Path(args.skill_path),
            description_override=args.description,
            num_workers=args.num_workers,
            timeout=args.timeout,
            max_iterations=args.max_iterations,
            runs_per_query=args.runs_per_query,
            trigger_threshold=args.trigger_threshold,
            holdout=args.holdout,
            model=args.model,
            verbose=args.verbose,
            live_report_path=live_report_path,
            log_dir=log_dir,
        )
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
