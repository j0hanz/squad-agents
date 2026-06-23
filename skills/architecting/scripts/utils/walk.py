import os
from typing import List, Set, Optional

DEFAULT_EXCLUDE = [
    "node_modules",
    ".test.",
    ".spec.",
    ".git",
    ".svn",
    ".hg",
    ".pytest_cache",
    ".tox",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "dist",
    "build",
    "coverage",
    ".coverage",
    ".next",
    ".nuxt",
    ".cache",
    ".parcel",
    ".npm",
    ".yarn",
    "target",
    ".gradle",
    ".m2",
    ".pytest",
    ".mypy_cache",
    ".ruff_cache",
    ".vscode",
    ".idea",
    ".DS_Store",
]


def walk_dir(
    root_dir: str,
    exclude: Optional[List[str]] = None,
    visited: Optional[Set[str]] = None,
) -> List[str]:
    """
    Recursively walk a directory, returning paths of TypeScript/JavaScript, Python, and Go files.
    """
    if exclude is None:
        exclude = []
    if visited is None:
        visited = set()

    files = []
    try:
        # Guard against symlink cycles
        real_path = os.path.realpath(root_dir)
        if real_path in visited:
            return files
        visited.add(real_path)

        for entry in os.scandir(root_dir):
            if any(pat in entry.name for pat in exclude):
                continue

            if entry.is_dir(follow_symlinks=True):
                files.extend(walk_dir(entry.path, exclude, visited))
            elif entry.is_file():
                if any(
                    entry.name.endswith(ext)
                    for ext in [".ts", ".tsx", ".js", ".mjs", ".py", ".go"]
                ):
                    files.append(os.path.abspath(entry.path))
    except (PermissionError, OSError):
        # Skip directories we can't read/traverse
        pass

    return files


if __name__ == "__main__":
    import sys
    import json

    test_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    print(json.dumps(walk_dir(test_dir, exclude=["node_modules", ".git"]), indent=2))
