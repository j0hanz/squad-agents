import os
import subprocess
import sys
import traceback
from typing import List, Optional, Dict, Any
from check_locality import run_locality_check
from detect_bleed import run_bleed_detection
from git_coupling import run_git_coupling

# Hotspot score weights: fan-out and bleeds count more than raw churn/size.
FAN_OUT_WEIGHT = 2
BLEED_WEIGHT = 3
CHURN_SCORE_CAP = 5
SIZE_LINES_PER_POINT = 100
SIZE_SCORE_CAP = 5
HIGH_RISK_THRESHOLD = 15
MEDIUM_RISK_THRESHOLD = 7


def run_hotspot_detection(
    dir_path: str, infra_pkgs: Optional[List[str]] = None, since: str = "6 months ago"
) -> List[Dict[str, Any]]:
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
        print(
            f"Warning: git churn data unavailable ({coupling_results['error']}); "
            "churn score will be 0 for all files.",
            file=sys.stderr,
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
        return os.path.abspath(os.path.join(repo_root, git_rel_path))

    # Build lookup maps
    fan_out_map = {f["file"]: f["count"] for f in fan_out}
    bleed_map = {}
    for v in violations:
        bleed_map[v["file"]] = bleed_map.get(v["file"], 0) + 1

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
                lines = len(f.readlines())
        except (UnicodeDecodeError, PermissionError, OSError):
            pass

        fo = fan_out_map.get(file_path, 0)
        bl = bleed_map.get(file_path, 0)
        raw_churn = churn_map.get(file_path, 0)
        churn_score = round((raw_churn / max_churn) * CHURN_SCORE_CAP)
        size_score = min(lines // SIZE_LINES_PER_POINT, SIZE_SCORE_CAP)

        score = fo * FAN_OUT_WEIGHT + bl * BLEED_WEIGHT + churn_score + size_score
        risk = (
            "HIGH"
            if score >= HIGH_RISK_THRESHOLD
            else "MEDIUM"
            if score >= MEDIUM_RISK_THRESHOLD
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
    import argparse

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

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
