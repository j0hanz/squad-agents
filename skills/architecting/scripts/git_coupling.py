import subprocess
import os
import sys
from typing import Dict, Any
from collections import Counter


def run_git_coupling(
    target_dir: str, min_count: int = 3, top_n: int = 20, since: str = "6 months ago"
) -> Dict[str, Any]:
    abs_dir = os.path.abspath(target_dir)

    try:
        # Run git log command
        cmd = [
            "git",
            "log",
            "--name-only",
            "--format=format:COMMIT",
            f"--since={since}",
            "--",
            abs_dir,
        ]
        output = subprocess.check_output(
            cmd, cwd=abs_dir, encoding="utf-8", errors="replace"
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            "pairs": [],
            "fileChurn": [],
            "error": "Not a git repository or git not available.",
        }

    # Parse commits into groups of files
    commits = []
    current_commit = []
    for line in output.splitlines():
        trimmed = line.strip()
        if trimmed == "COMMIT":
            if current_commit:
                commits.append(current_commit)
            current_commit = []
        elif trimmed:
            current_commit.append(trimmed)
    if current_commit:
        commits.append(current_commit)

    # Count co-occurrences
    pair_counts = Counter()
    file_counts = Counter()

    for files in commits:
        unique_files = sorted(set(files))
        file_counts.update(unique_files)

        if len(unique_files) < 2:
            continue

        for i in range(len(unique_files)):
            for j in range(i + 1, len(unique_files)):
                key = (unique_files[i], unique_files[j])
                pair_counts[key] += 1

    # Format results
    pairs = []
    for (fileA, fileB), count in pair_counts.items():
        if count >= min_count:
            pairs.append({"fileA": fileA, "fileB": fileB, "count": count})

    pairs.sort(key=lambda x: x["count"], reverse=True)
    pairs = pairs[:top_n]

    file_churn = []
    for file, count in file_counts.items():
        file_churn.append({"file": file, "commits": count})

    file_churn.sort(key=lambda x: x["commits"], reverse=True)
    file_churn = file_churn[:top_n]

    return {"pairs": pairs, "fileChurn": file_churn}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze git co-change coupling.")
    parser.add_argument("dir", nargs="?", default=".", help="Directory to analyze")
    parser.add_argument(
        "--min-count", type=int, default=3, help="Minimum co-change count"
    )
    parser.add_argument("--since", default="6 months ago", help="Git --since window")
    parser.add_argument("--top-n", type=int, default=20, help="Max results to return")

    args = parser.parse_args()

    results = run_git_coupling(
        args.dir, min_count=args.min_count, since=args.since, top_n=args.top_n
    )

    if "error" in results:
        print(f"Error: {results['error']}", file=sys.stderr)
        sys.exit(1)

    print("\n--- Co-Change Pairs (files that always change together) ---")
    if not results["pairs"]:
        print(f"None found with co-change count >= {args.min_count}.")
    else:
        # Simple table header
        print(f"{'File A':<40} {'File B':<40} {'Co-changes':<10}")
        print("-" * 92)
        for p in results["pairs"]:
            print(f"{p['fileA']:<40} {p['fileB']:<40} {p['count']:<10}")

        print(
            "\nHigh co-change count = hidden coupling. These files likely share a responsibility"
        )
        print(
            "that no import graph can reveal. Consider whether they belong in the same module."
        )

    print("\n--- Top File Churn (commits touching this file) ---")
    for item in results["fileChurn"][:10]:
        print(f"  {str(item['commits']).rjust(4)} commits  {item['file']}")
