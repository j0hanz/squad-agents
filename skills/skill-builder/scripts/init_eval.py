#!/usr/bin/env python3
"""
Automate the setup of evaluation workspaces.
Creates directory structure and eval_metadata.json for a test case.
"""

import argparse
import json
from pathlib import Path


def init_eval(
    skill_name: str,
    iteration: int,
    eval_id: int,
    prompt: str,
    eval_name: str = "",
    runs: int = 3,
) -> None:
    """Initialize an evaluation workspace."""
    # Sanitize skill_name to prevent path traversal (strip ../ and path separators)
    safe_name = Path(skill_name).name
    base_dir = (
        Path(f"{safe_name}-workspace") / f"iteration-{iteration}" / f"eval-{eval_id}"
    )

    # Define configurations
    configs = ["with_skill", "without_skill"]

    for config in configs:
        config_dir = base_dir / config
        # Create run directories
        for i in range(1, runs + 1):
            run_dir = config_dir / f"run-{i}"
            (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
            print(f"Created: {run_dir}/outputs")

    # Create eval_metadata.json
    metadata = {
        "eval_id": eval_id,
        "eval_name": eval_name or f"eval-{eval_id}",
        "prompt": prompt,
        "assertions": [],
    }

    metadata_path = base_dir / "eval_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Generated: {metadata_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize an evaluation workspace")
    parser.add_argument("--skill-name", required=True, help="Name of the skill")
    parser.add_argument("--iteration", type=int, default=1, help="Iteration number")
    parser.add_argument("--eval-id", type=int, required=True, help="Evaluation ID")
    parser.add_argument("--prompt", required=True, help="The test prompt")
    parser.add_argument("--name", help="Descriptive name for the evaluation")
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of run directories to create per configuration",
    )

    args = parser.parse_args()
    init_eval(
        args.skill_name, args.iteration, args.eval_id, args.prompt, args.name, args.runs
    )


if __name__ == "__main__":
    main()
