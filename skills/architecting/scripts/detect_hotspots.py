"""Architectural hotspot detection script.

Computes architectural debt hotspots by combining code churn, file sizes, fan-out,
and package boundary violations.
"""

import argparse
import logging
import os
import subprocess
import sys
import traceback
from collections import Counter
from pathlib import Path
from typing import Any

from check_locality import run_locality_check
from detect_bleed import run_bleed_detection
from git_coupling import run_git_coupling

# Hotspot score weights: fan-out and bleeds count more than raw churn/size.
WEIGHTS = {
    "fan_out": 2,
    "bleed": 3,
    "churn_score_cap": 5,
    "size_lines_per_point": 100,
    "size_score_cap": 5,
    "high_risk_threshold": 15,
    "medium_risk_threshold": 7,
}

# Set up logging to write to sys.stderr dynamically so that testing capture works correctly.
logger = logging.getLogger(__name__)


class StderrHandler(logging.Handler):
    def emit(self, record):
        try:
            sys.stderr.write(self.format(record) + "\n")
        except Exception:
            pass


logger.addHandler(StderrHandler())


def run_hotspot_detection(
    dir_path: str, infra_pkgs: list[str] | None = None, since: str = "6 months ago"
) -> list[dict[str, Any]]:
    """Detect architectural hotspots in the given directory.

    Calculates scores for files based on fan-out, package bleed, git churn, and size,
    and returns a sorted list of files with their scores and risk levels.

    Args:
        dir_path: Path to the directory to analyze.
        infra_pkgs: List of infrastructure packages to check for bleed violations.
        since: Git window range for measuring coupling and churn (e.g., '6 months ago').

    Returns:
        A list of dictionaries containing analysis results for each file,
        sorted in descending order of hotspot score.
    """
    if infra_pkgs is None:
        infra_pkgs = []

    abs_dir = os.path.abspath(dir_path)

    # Run individual analyses
    cycles, fan_out = run_locality_check(abs_dir)
    violations = run_bleed_detection(abs_dir, infra_pkgs) if infra_pkgs else []
    coupling_results = run_git_coupling(
        abs_dir, since=since, min_count=1, top_n=1000000
    )
    if "error" in coupling_results:
        logger.warning(
            "git churn data unavailable (%s); churn score will be 0 for all files.",
            coupling_results["error"],
        )
    file_churn = coupling_results["fileChurn"]

    # Find repo root to resolve git paths
    repo_root = abs_dir
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=abs_dir, encoding="utf-8"
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    def to_abs(git_rel_path: str) -> str:
        """Convert a git relative path to an absolute path."""
        return os.path.abspath(os.path.join(repo_root, git_rel_path))

    # Build lookup maps
    fan_out_map = {f["file"]: f["count"] for f in fan_out}
    bleed_map = Counter(v["file"] for v in violations)

    churn_map = {to_abs(f["file"]): f["commits"] for f in file_churn}
    max_churn = max((f["commits"] for f in file_churn), default=1)

    # Union of all files
    all_files = fan_out_map.keys() | bleed_map.keys() | churn_map.keys()

    results = []
    for file_path in all_files:
        if not os.path.exists(file_path):
            continue

        lines = 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
        except (UnicodeDecodeError, OSError):
            pass

        fo = fan_out_map.get(file_path, 0)
        bl = bleed_map.get(file_path, 0)
        raw_churn = churn_map.get(file_path, 0)
        churn_score = (
            round((raw_churn / max_churn) * WEIGHTS["churn_score_cap"])
            if max_churn > 0
            else 0
        )
        size_score = min(
            lines // WEIGHTS["size_lines_per_point"], WEIGHTS["size_score_cap"]
        )

        score = (
            fo * WEIGHTS["fan_out"] + bl * WEIGHTS["bleed"] + churn_score + size_score
        )
        risk = (
            "HIGH"
            if score >= WEIGHTS["high_risk_threshold"]
            else "MEDIUM"
            if score >= WEIGHTS["medium_risk_threshold"]
            else "LOW"
        )

        results.append(
            {
                "file": os.path.relpath(file_path, os.getcwd()),
                "score": score,
                "fanOut": fo,
                "bleedCount": bl,
                "churn": raw_churn,
                "lines": lines,
                "risk": risk,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect architectural hotspots.")
    parser.add_argument("dir", nargs="?", default="src", help="Directory to analyze")
    parser.add_argument(
        "infra",
        nargs="?",
        default="express,typeorm,prisma,fs,path,react,mongoose,sqlalchemy,django,flask",
        help="Comma-separated infra packages",
    )
    parser.add_argument("--since", default="6 months ago", help="Git --since window")

    args = parser.parse_args()
    infra_pkgs = [p.strip() for p in args.infra.split(",") if p.strip()]

    print(f"\nDetecting architectural hotspots in {args.dir}...")
    print(f"Infrastructure packages: {', '.join(infra_pkgs)}")
    print(f"Git window: since {args.since}\n")

    try:
        if not Path(args.dir).is_dir():
            raise FileNotFoundError(f"Directory not found: {args.dir}")

        results = run_hotspot_detection(args.dir, infra_pkgs, since=args.since)

        if not results:
            print("No files found.")
            sys.exit(0)

        print("--- Architectural Debt Hotspots (ranked) ---\n")
        header = f"{'Risk':<10} {'Score':<6} {'File':<50} {'Fan-out':<8} {'Bleeds':<6} {'Churn':<6} {'Lines'}"
        print(header)
        print("-" * len(header))

        for r in results[:15]:
            print(
                f"{r['risk']:<10} {r['score']:<6} {r['file']:<50} {r['fanOut']:<8} {r['bleedCount']:<6} {r['churn']:<6} {r['lines']}"
            )

        high = [r for r in results if r["risk"] == "HIGH"]
        if high:
            print(
                f"\n⚠  {len(high)} HIGH-risk file(s) found. These are your top refactoring targets."
            )

    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
