"""Module to detect infrastructure package leaks/bleeds into domain code."""

import argparse
import sys
from pathlib import Path
from typing import TypedDict
from utils.extractor import extract_imports_with_positions, detect_lang
from utils.walk import walk_dir, DEFAULT_EXCLUDE


class Violation(TypedDict):
    """Schema representing a domain bleed violation."""

    file: str
    violation: str
    line: int
    code: str


def run_bleed_detection(target_dir: str, infra_packages: list[str]) -> list[Violation]:
    """Scan files in target_dir to detect imports of any infra_packages.

    Args:
        target_dir: The path to the directory to scan.
        infra_packages: A list of package names that are considered infra.

    Returns:
        A list of Violation dictionaries detailing the detected leaks.
    """
    files = walk_dir(target_dir, DEFAULT_EXCLUDE)
    violations: list[Violation] = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                content = file_handle.read()
        except (UnicodeDecodeError, PermissionError):
            continue

        lang = detect_lang(file_path)
        lines = content.splitlines()

        for match in extract_imports_with_positions(content, lang):
            import_specifier = match["specifier"]
            index = match["index"]

            normalized = (
                import_specifier[5:]
                if import_specifier.startswith("node:")
                else import_specifier
            )

            is_violation = any(
                normalized == package
                or normalized.startswith(f"{package}/")
                or normalized.startswith(f"{package}.")
                for package in infra_packages
            )

            if is_violation:
                line_no = content.count("\n", 0, index) + 1
                code = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                violations.append(
                    {
                        "file": file_path,
                        "violation": import_specifier,
                        "line": line_no,
                        "code": code,
                    }
                )

    return violations


if __name__ == "__main__":
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

    try:
        target_path = Path(args.dir).resolve()
        if not target_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {args.dir}")

        violations = run_bleed_detection(str(target_path), infra_packages)

        print("\n--- Infrastructure Leaks (Seam Test Failures) ---")
        if not violations:
            print("None found. Domain looks pure.")
        else:
            # Simple table formatting
            print(f"{'File':<50} {'Leak':<20} {'Line':<5}")
            print("-" * 77)
            for violation in violations:
                file_path = Path(violation["file"])
                try:
                    rel_file = file_path.relative_to(Path.cwd(), walk_up=True)
                except ValueError:
                    rel_file = file_path
                print(
                    f"{str(rel_file):<50} {violation['violation']:<20} {violation['line']:<5}"
                )

    except FileNotFoundError:
        print(f"Directory not found: {args.dir}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
