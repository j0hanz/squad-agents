import json

import pytest
from scripts.aggregate_benchmark import (
    calculate_stats,
    aggregate_results,
    generate_markdown,
    load_run_results,
)


def test_calculate_stats_empty():
    result = calculate_stats([])
    assert result == {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}


def test_calculate_stats_single():
    result = calculate_stats([0.8])
    assert result["mean"] == pytest.approx(0.8)
    assert result["stddev"] == 0.0
    assert result["min"] == pytest.approx(0.8)
    assert result["max"] == pytest.approx(0.8)


def test_calculate_stats_multiple():
    result = calculate_stats([0.5, 0.75, 1.0])
    assert result["mean"] == pytest.approx(0.75)
    assert result["min"] == pytest.approx(0.5)
    assert result["max"] == pytest.approx(1.0)
    assert result["stddev"] > 0


def test_aggregate_results_empty():
    result = aggregate_results({})
    assert "delta" in result
    delta = result["delta"]
    assert delta["pass_rate"] == "+0.00"
    assert delta["time_seconds"] == "+0.0"
    assert delta["tokens"] == "+0"


def test_aggregate_results_single_config():
    runs = [
        {"pass_rate": 1.0, "time_seconds": 5.0, "tokens": 100},
        {"pass_rate": 0.5, "time_seconds": 3.0, "tokens": 80},
    ]
    result = aggregate_results({"with_skill": runs})
    assert "with_skill" in result
    assert result["with_skill"]["pass_rate"]["mean"] == pytest.approx(0.75)
    assert "delta" in result


def test_aggregate_results_two_configs():
    with_runs = [{"pass_rate": 0.9, "time_seconds": 4.0, "tokens": 90}]
    without_runs = [{"pass_rate": 0.6, "time_seconds": 5.0, "tokens": 100}]
    result = aggregate_results({"with_skill": with_runs, "without_skill": without_runs})
    delta = result["delta"]
    assert delta["pass_rate"] == "+0.30"


def _make_grading(pass_rate: float, passed: int, failed: int, total: int) -> dict:
    return {
        "summary": {
            "pass_rate": pass_rate,
            "passed": passed,
            "failed": failed,
            "total": total,
        },
        "timing": {"total_duration_seconds": 2.5},
        "execution_metrics": {
            "total_tool_calls": 4,
            "output_chars": 200,
            "errors_encountered": 0,
        },
        "expectations": [],
        "user_notes_summary": {},
    }


def test_load_run_results_workspace_layout(tmp_path):
    eval_dir = tmp_path / "eval-1"
    for config in ("with_skill", "without_skill"):
        run_dir = eval_dir / config / "run-1"
        run_dir.mkdir(parents=True)
        grading = _make_grading(1.0 if config == "with_skill" else 0.5, 4, 0, 4)
        (run_dir / "grading.json").write_text(json.dumps(grading))

    results = load_run_results(tmp_path)
    assert set(results.keys()) == {"with_skill", "without_skill"}
    assert results["with_skill"][0]["pass_rate"] == 1.0
    assert results["without_skill"][0]["pass_rate"] == 0.5


def test_load_run_results_missing_grading_warns(tmp_path, capsys):
    run_dir = tmp_path / "eval-1" / "with_skill" / "run-1"
    run_dir.mkdir(parents=True)
    # No grading.json written

    load_run_results(tmp_path)
    captured = capsys.readouterr()
    assert "grading.json not found" in captured.out


def test_generate_markdown_has_summary():
    benchmark = {
        "metadata": {
            "skill_name": "test-skill",
            "executor_model": "claude-sonnet-4-6",
            "timestamp": "2026-01-01T00:00:00Z",
            "evals_run": [1, 2],
            "runs_per_configuration": 3,
        },
        "run_summary": {
            "with_skill": {
                "pass_rate": {"mean": 0.9, "stddev": 0.05, "min": 0.8, "max": 1.0},
                "time_seconds": {"mean": 4.0, "stddev": 0.5, "min": 3.0, "max": 5.0},
                "tokens": {"mean": 100, "stddev": 10, "min": 80, "max": 120},
            },
            "without_skill": {
                "pass_rate": {"mean": 0.6, "stddev": 0.1, "min": 0.5, "max": 0.7},
                "time_seconds": {"mean": 5.0, "stddev": 0.5, "min": 4.5, "max": 5.5},
                "tokens": {"mean": 110, "stddev": 10, "min": 100, "max": 120},
            },
            "delta": {"pass_rate": "+0.30", "time_seconds": "-1.0", "tokens": "-10"},
        },
        "notes": [],
    }
    md = generate_markdown(benchmark)
    assert "# Skill Benchmark: test-skill" in md
    assert "## Summary" in md
    assert "Pass Rate" in md
