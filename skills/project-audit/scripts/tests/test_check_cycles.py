from check_cycles import (
    normalize_import,
    resolve_lane,
    build_lane_graph,
    find_cycles,
    _extract_lane_refs,
    main,
)
import json

import pytest


def test_normalize_import_strips_quotes_and_semicolon():
    assert normalize_import("'./billing/invoice';") == "billing/invoice"
    assert normalize_import('"billing/invoice"') == "billing/invoice"


def test_normalize_import_strips_leading_dot_slash():
    assert normalize_import("./orders/order") == "orders/order"


def test_normalize_import_converts_backslash_separators():
    # Windows path form must normalize the same as forward slashes, else an
    # import like '..\billing\invoice' silently fails to resolve to a lane.
    assert normalize_import("..\\billing\\invoice") == "../billing/invoice"
    assert normalize_import(".\\orders\\order") == "orders/order"


def test_resolve_lane_matches_prefix():
    lane_dirs = {"billing": "billing", "orders": "orders"}
    assert resolve_lane("billing/invoice", lane_dirs) == "billing"
    assert resolve_lane("orders/order", lane_dirs) == "orders"


def test_resolve_lane_no_match_returns_none():
    lane_dirs = {"billing": "billing"}
    assert resolve_lane("shared/utils", lane_dirs) is None


def test_resolve_lane_does_not_match_partial_directory_name():
    # "billingx" should not match the "billing" prefix
    lane_dirs = {"billing": "billing"}
    assert resolve_lane("billingx/thing", lane_dirs) is None


def test_build_lane_graph_drops_intra_lane_edges():
    lane_dirs = {"billing": "billing"}
    lane_imports = {"billing": ["'./billing/helpers'"]}
    graph = build_lane_graph(lane_imports, lane_dirs)
    assert graph["billing"] == set()


def test_build_lane_graph_builds_inter_lane_edge():
    lane_dirs = {"billing": "billing", "orders": "orders"}
    lane_imports = {
        "billing": ["'./orders/order'"],
        "orders": [],
    }
    graph = build_lane_graph(lane_imports, lane_dirs)
    assert graph["billing"] == {"orders"}
    assert graph["orders"] == set()


def test_build_lane_graph_ignores_unresolved_imports():
    lane_dirs = {"billing": "billing"}
    lane_imports = {"billing": ["express"]}
    graph = build_lane_graph(lane_imports, lane_dirs)
    assert graph["billing"] == set()


def test_find_cycles_detects_two_lane_cycle():
    graph = {"billing": {"orders"}, "orders": {"billing"}}
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert set(cycles[0]) == {"billing", "orders"}


def test_find_cycles_detects_transitive_three_lane_cycle():
    graph = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert set(cycles[0]) == {"a", "b", "c"}


def test_find_cycles_returns_empty_for_acyclic_graph():
    graph = {"a": {"b"}, "b": {"c"}, "c": set()}
    assert find_cycles(graph) == []


def test_find_cycles_detects_self_loop():
    graph = {"a": {"a"}}
    cycles = find_cycles(graph)
    assert len(cycles) == 1
    assert cycles[0] == ["a"]


# ── _extract_lane_refs (scan-mode text extraction) ──────────────────────────


def test_extract_lane_refs_backtick_and_bold():
    lane_names = {"billing", "orders"}
    text = "depends on `billing` and **orders:** plus **billing** and `nope`"
    assert _extract_lane_refs(text, lane_names) == ["billing", "orders", "billing"]


def test_extract_lane_refs_only_matches_known_lanes():
    # "shared" is backtick-quoted but not a lane -> ignored.
    lane_names = {"billing"}
    assert _extract_lane_refs("uses `billing` and `shared`", lane_names) == ["billing"]


def test_extract_lane_refs_skips_non_kebab_names():
    # Underscored/dotted/uppercase names don't match the kebab-case regex.
    lane_names = {"billing", "src_core"}
    text = "refs `billing` and `src_core` and `Api`"
    assert _extract_lane_refs(text, lane_names) == ["billing"]


# ── main (the CLI entrypoint SKILL.md invokes) ────────────────────────────────


def test_main_reads_lane_json_from_stdin_and_reports_cycle(
    capsys, monkeypatch, tmp_path
):
    payload = {
        "billing": {"dir": "billing", "imports": ["'./orders/order'"]},
        "orders": {"dir": "orders", "imports": ["'./billing/invoice'"]},
    }
    monkeypatch.setattr("sys.stdin", _FakeStdin(payload))
    monkeypatch.setattr("sys.argv", ["check_cycles.py"])
    main()
    out = capsys.readouterr().out
    assert "root: (stdin)" in out
    assert "lanes: 2" in out
    assert "cycles: 1" in out
    assert "billing" in out and "orders" in out


def test_main_stdin_acyclic_reports_none(capsys, monkeypatch):
    payload = {
        "a": {"dir": "a", "imports": ["'./b'"]},
        "b": {"dir": "b", "imports": []},
    }
    monkeypatch.setattr("sys.stdin", _FakeStdin(payload))
    monkeypatch.setattr("sys.argv", ["check_cycles.py"])
    main()
    assert "cycles: none" in capsys.readouterr().out


def test_main_stdin_defaults_dir_to_lane_name(capsys, monkeypatch):
    # "dir" omitted -> falls back to the lane name.
    payload = {"billing": {"imports": ["'./billing/x'"]}}  # intra-lane, no edge
    monkeypatch.setattr("sys.stdin", _FakeStdin(payload))
    monkeypatch.setattr("sys.argv", ["check_cycles.py"])
    main()
    out = capsys.readouterr().out
    assert "edges: 0" in out
    assert "cycles: none" in out


def test_main_scan_mode_reads_skill_md_per_subdir(capsys, tmp_path, monkeypatch):
    (tmp_path / "billing").mkdir()
    (tmp_path / "orders").mkdir()
    (tmp_path / "billing" / "SKILL.md").write_text("reaches into `orders` for data")
    (tmp_path / "orders" / "SKILL.md").write_text("depends on `billing`")
    monkeypatch.setattr("sys.stdin", _ClosedStdin())
    monkeypatch.setattr("sys.argv", ["check_cycles.py", str(tmp_path)])
    main()
    out = capsys.readouterr().out
    assert f"root: {tmp_path}" in out
    assert "lanes: 2" in out
    assert "cycles: 1" in out


def test_main_no_input_errors(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", _ClosedStdin())
    monkeypatch.setattr("sys.argv", ["check_cycles.py"])
    with pytest.raises(SystemExit):
        main()


def test_main_rejects_malformed_stdin_json(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", _FakeStdinRaw("{not json"))
    monkeypatch.setattr("sys.argv", ["check_cycles.py"])
    with pytest.raises(SystemExit):
        main()


class _FakeStdin:
    """Minimal stdin stand-in: isatty() False, readable JSON via json.load."""

    def __init__(self, payload):
        self._buf = json.dumps(payload)

    def isatty(self):
        return False

    def read(self):
        return self._buf

    def readline(self):
        return self._buf

    def __iter__(self):
        return iter(self._buf.splitlines())


class _FakeStdinRaw(_FakeStdin):
    def __init__(self, raw):
        self._buf = raw


class _ClosedStdin:
    """stdin stand-in for scan mode: isatty() True so stdin mode is skipped."""

    def isatty(self):
        return True
