import os
import sys
from typing import List, Dict, Any
from utils.extractor import extract_imports_with_positions, detect_lang
from utils.walk import walk_dir, DEFAULT_EXCLUDE


def run_bleed_detection(
    target_dir: str, infra_packages: List[str]
) -> List[Dict[str, Any]]:
    files = walk_dir(target_dir, DEFAULT_EXCLUDE)
    violations = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            continue

        lang = detect_lang(file_path)
        lines = content.splitlines()

        for match in extract_imports_with_positions(content, lang):
            imp = match["specifier"]
            index = match["index"]

            normalized = imp[5:] if imp.startswith("node:") else imp

            is_violation = False
            if normalized in infra_packages:
                is_violation = True
            else:
                for pkg in infra_packages:
                    if normalized.startswith(f"{pkg}/"):
                        is_violation = True
                        break

            if is_violation:
                line_no = content.count("\n", 0, index) + 1
                code = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                violations.append(
                    {"file": file_path, "violation": imp, "line": line_no, "code": code}
                )

    return violations


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect infrastructure bleeds into domain code."
    )
    parser.add_argument(
        "dir", nargs="?", default="src/domain", help="Directory to analyze"
    )
    parser.add_argument(
        "infra",
        nargs="?",
        default="express,typeorm,prisma,fs,path,react,mongoose",
        help="Comma-separated infra packages",
    )

    args = parser.parse_args()
    infra_packages = args.infra.split(",")

    print(
        f"Checking {args.dir} for infrastructure bleeds ({', '.join(infra_packages)})..."
    )
    abs_dir = os.path.abspath(args.dir)

    try:
        violations = run_bleed_detection(abs_dir, infra_packages)

        print("\n--- Infrastructure Leaks (Seam Test Failures) ---")
        if not violations:
            print("None found. Domain looks pure.")
        else:
            # Simple table formatting
            print(f"{'File':<50} {'Leak':<20} {'Line':<5}")
            print("-" * 77)
            for v in violations:
                rel_file = os.path.relpath(v["file"], os.getcwd())
                print(f"{rel_file:<50} {v['violation']:<20} {v['line']:<5}")

    except FileNotFoundError:
        print(f"Directory not found: {args.dir}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
