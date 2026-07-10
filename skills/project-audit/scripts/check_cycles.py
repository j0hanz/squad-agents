"""Joins lanes' free-text import claims into an inter-lane graph and finds cycles.

This is the one deterministic step in project-audit's "ask, don't compute"
pipeline: free-text import answers from parallel lane agents need a reliable
join, which judgment alone can't guarantee (see design brief Risks section).
Intra-lane edges are dropped on purpose -- a cycle within one directory isn't
the "circular dependency between modules" finding this audit cares about.

Does NOT attempt full alias/re-export resolution -- normalization only
strips superficial formatting (quotes, semicolons, a leading "./"). An import
expressed in a form normalization can't reconcile with the target lane's
directory prefix will simply not resolve to an edge; this is an accepted,
disclosed limitation, not a bug.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def normalize_import(raw: str) -> str:
    s = raw.strip()
    s = s.rstrip(";")
    s = s.strip().strip("'\"")
    s = s.replace(
        "\\", "/"
    )  # Windows backslash separators -> forward slash before resolution
    if s.startswith("./"):
        s = s[2:]
    return s.strip()


def resolve_lane(import_path: str, lane_dirs: dict[str, str]) -> str | None:
    for lane, prefix in lane_dirs.items():
        prefix = prefix.strip("/")
        if import_path == prefix or import_path.startswith(prefix + "/"):
            return lane
    return None


def build_lane_graph(
    lane_imports: dict[str, list[str]], lane_dirs: dict[str, str]
) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {lane: set() for lane in lane_imports}
    for lane, raw_imports in lane_imports.items():
        for raw in raw_imports:
            target_lane = resolve_lane(normalize_import(raw), lane_dirs)
            if target_lane and target_lane != lane:
                graph[lane].add(target_lane)
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's strongly-connected-components, iterative (no recursion limit).

    Returns each SCC of size > 1 as a cycle, plus any single-node self-loop.
    """
    index_counter = [0]
    stack: list[str] = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    result: list[list[str]] = []

    for start in graph:
        if start in index:
            continue
        work_stack = [(start, iter(graph.get(start, ())))]
        index[start] = index_counter[0]
        lowlink[start] = index_counter[0]
        index_counter[0] += 1
        stack.append(start)
        on_stack[start] = True

        while work_stack:
            node, neighbors = work_stack[-1]
            advanced = False
            for neighbor in neighbors:
                if neighbor not in index:
                    index[neighbor] = index_counter[0]
                    lowlink[neighbor] = index_counter[0]
                    index_counter[0] += 1
                    stack.append(neighbor)
                    on_stack[neighbor] = True
                    work_stack.append((neighbor, iter(graph.get(neighbor, ()))))
                    advanced = True
                    break
                elif on_stack.get(neighbor):
                    lowlink[node] = min(lowlink[node], index[neighbor])
            if advanced:
                continue

            work_stack.pop()
            if work_stack:
                parent = work_stack[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])

            if lowlink[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack[member] = False
                    component.append(member)
                    if member == node:
                        break
                is_self_loop = len(component) == 1 and component[0] in graph.get(
                    component[0], ()
                )
                if len(component) > 1 or is_self_loop:
                    result.append(component)

    return result


def _extract_lane_refs(text: str, lane_names: set[str]) -> list[str]:
    """Pull cross-lane references from free text: backtick-quoted or
    bold-quoted identifiers that match a known lane directory name.

    Matches kebab-case lane names only (``[a-z][a-z0-9-]+``) — the GROUP step
    bands directories into kebab-case lanes, so names with underscores, dots,
    or uppercase are intentionally not matched here.
    """
    refs: list[str] = []
    for m in re.findall(r"`([a-z][a-z0-9-]+)`", text):
        if m in lane_names:
            refs.append(m)
    for m in re.findall(r"\*\*([a-z][a-z0-9-]+):?\*\*", text):
        if m in lane_names:
            refs.append(m)
    return refs


def _scan_root(root: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Scan mode: each immediate subdirectory of <root> is a lane; cross-refs
    are read from its SKILL.md. A fallback when lane agents' Q2 import lists
    aren't piped on stdin."""
    lane_names = {
        p.name
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith((".", "__"))
    }
    lane_dirs = {name: name for name in lane_names}
    lane_imports: dict[str, list[str]] = {}
    for name in lane_names:
        skill_md = root / name / "SKILL.md"
        if skill_md.is_file():
            lane_imports[name] = _extract_lane_refs(
                skill_md.read_text(encoding="utf-8", errors="replace"), lane_names
            )
        else:
            lane_imports[name] = []
    return lane_imports, lane_dirs


def _read_lane_json(stream) -> tuple[dict[str, list[str]], dict[str, str]]:
    """stdin mode: the documented Step-3 API. JSON maps each lane to its dir
    prefix and raw Q2 import list: {"<lane>": {"dir": "<prefix>", "imports":
    ["'./x'", ...]}, ...}. Feeds build_lane_graph directly."""
    try:
        data = json.load(stream)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict) or not data:
        print(
            "error: stdin JSON must be a non-empty object mapping lanes to "
            "{'dir': <prefix>, 'imports': [<raw>, ...]}",
            file=sys.stderr,
        )
        sys.exit(2)
    lane_imports: dict[str, list[str]] = {}
    lane_dirs: dict[str, str] = {}
    for lane, spec in data.items():
        if not isinstance(spec, dict):
            print(
                f"error: lane {lane!r} must map to an object with 'dir' and 'imports'",
                file=sys.stderr,
            )
            sys.exit(2)
        lane_dirs[lane] = str(spec.get("dir", lane))
        raw_imports = spec.get("imports", [])
        if not isinstance(raw_imports, list):
            print(f"error: lane {lane!r} 'imports' must be a list", file=sys.stderr)
            sys.exit(2)
        lane_imports[lane] = [str(x) for x in raw_imports]
    return lane_imports, lane_dirs


def _report(
    root_label: str,
    lane_imports: dict[str, list[str]],
    graph: dict[str, set[str]],
    cycles: list[list[str]],
) -> None:
    print(f"root: {root_label}")
    print(f"lanes: {len(lane_imports)}")
    print(f"edges: {sum(len(v) for v in graph.values())}")
    if not cycles:
        print("cycles: none")
        return
    print(f"cycles: {len(cycles)}")
    for i, cyc in enumerate(cycles, 1):
        print(f"  cycle {i}: {' -> '.join(cyc)}")


def _self_check() -> None:
    # one assert exercising normalize_import -> resolve_lane ->
    # build_lane_graph -> find_cycles; fails if the entrypoint's core breaks.
    g = build_lane_graph(
        {"a": ["'./b/x'"], "b": ["'./a/y'"]},
        {"a": "a", "b": "b"},
    )
    assert find_cycles(g), "self-check: expected a cycle"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Join lane cross-references into an inter-lane graph and report "
            "cycles. Two input modes: (1) pipe JSON on stdin mapping each lane "
            "to its dir prefix and raw Q2 imports "
            '({"<lane>": {"dir": "<prefix>", "imports": ["\'./x\'", ...]}, ...}) '
            "— the documented project-audit Step-3 API; (2) give a <root> whose "
            "immediate subdirectories are lanes, reading cross-refs from each "
            "lane's SKILL.md (a fallback when lane Q2 lists aren't piped)."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        help="root directory whose immediate subdirs are lanes (scan mode; "
        "omitted when lane JSON is piped on stdin)",
    )
    args = parser.parse_args()

    _self_check()

    if not sys.stdin.isatty():
        lane_imports, lane_dirs = _read_lane_json(sys.stdin)
        root_label = "(stdin)"
    elif args.root is not None:
        root = Path(args.root)
        if not root.is_dir():
            print(f"error: {root!s} is not a directory", file=sys.stderr)
            sys.exit(2)
        lane_imports, lane_dirs = _scan_root(root)
        root_label = str(root)
    else:
        parser.error("provide a root directory, or pipe lane JSON on stdin")

    graph = build_lane_graph(lane_imports, lane_dirs)
    cycles = find_cycles(graph)
    _report(root_label, lane_imports, graph, cycles)


if __name__ == "__main__":
    main()
