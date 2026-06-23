import os
import sys
from typing import List, Optional, Tuple, Dict, Any
from utils.extractor import extract_imports, detect_lang
from utils.graph import find_cycles
from utils.walk import walk_dir, DEFAULT_EXCLUDE


def import_candidates(from_file: str, imp: str, lang: str) -> List[str]:
    from_dir = os.path.dirname(from_file)

    if lang == "py":
        # Leading dots are package levels: one dot = current package (same dir),
        # each extra dot = one parent up.
        dots = 0
        while dots < len(imp) and imp[dots] == ".":
            dots += 1

        if dots == 0:
            # Absolute import or not relative in the expected way
            # But locality check only cares about relative imports (starting with '.')
            return []

        rest = imp[dots:].split(".")
        rest = [r for r in rest if r]

        base = from_dir
        for _ in range(1, dots):
            base = os.path.dirname(base)

        resolved = os.path.join(base, *rest)
        # ponytail: bare "from . import x" (rest=[]) only resolves via __init__.py;
        # PEP 420 namespace packages without __init__.py won't match. Fix if that
        # pattern shows up: capture the imported names and try them as submodules.
        return [f"{resolved}.py", os.path.join(resolved, "__init__.py")]

    # js / go
    resolved = os.path.abspath(os.path.join(from_dir, imp))
    candidates = []

    basename = os.path.basename(imp)
    if "." in basename:
        # Import already carries an extension
        candidates.append(resolved)
        # TS allows a '.js' specifier to resolve to the '.ts' source.
        no_ext, _ = os.path.splitext(resolved)
        candidates.extend([f"{no_ext}.ts", f"{no_ext}.tsx"])

    candidates.extend(
        [
            f"{resolved}.ts",
            f"{resolved}.tsx",
            f"{resolved}.js",
            f"{resolved}.jsx",
            f"{resolved}.mjs",
            f"{resolved}.cjs",
            f"{resolved}.go",
            os.path.join(resolved, "index.ts"),
            os.path.join(resolved, "index.tsx"),
            os.path.join(resolved, "index.js"),
            os.path.join(resolved, "index.jsx"),
            os.path.join(resolved, "index.mjs"),
        ]
    )
    return candidates


def run_locality_check(
    target_dir: str, exclude: Optional[List[str]] = None
) -> Tuple[List[List[str]], List[Dict[str, Any]]]:
    if exclude is None:
        exclude = DEFAULT_EXCLUDE

    files = walk_dir(target_dir, exclude)
    graph = {}

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            continue

        lang = detect_lang(file_path)
        imports = extract_imports(content, lang)
        graph[file_path] = []

        for imp in imports:
            # Only care about relative imports for locality
            if not imp.startswith("."):
                continue

            for candidate in import_candidates(file_path, imp, lang):
                if os.path.exists(candidate):
                    graph[file_path].append(candidate)
                    break

    cycles = find_cycles(graph)

    # Calculate Fan-out
    fan_out = []
    for file, deps in graph.items():
        fan_out.append({"file": file, "count": len(deps)})

    fan_out.sort(key=lambda x: x["count"], reverse=True)

    return cycles, fan_out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Check locality and circular dependencies."
    )
    parser.add_argument("dir", nargs="?", default="src", help="Directory to analyze")

    args = parser.parse_args()

    print(f"Checking locality in {args.dir}...")
    abs_dir = os.path.abspath(args.dir)

    try:
        cycles, fan_out = run_locality_check(abs_dir)

        print("\n--- Circular Dependencies ---")
        if not cycles:
            print("None found.")
        else:
            for i, cycle in enumerate(cycles):
                print(f"\nCycle {i + 1}:")
                for node in cycle:
                    print(f"  - {os.path.relpath(node, os.getcwd())}")

        print("\n--- Top 5 Fan-out (Highest Imports) ---")
        for item in fan_out[:5]:
            print(
                f"  - {os.path.relpath(item['file'], os.getcwd())} ({item['count']} imports)"
            )

    except FileNotFoundError:
        print(f"Directory not found: {args.dir}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
