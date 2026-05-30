from scripts.generate_report import generate_html


def _minimal_data(description: str = "test description") -> dict:
    return {
        "original_description": "original",
        "best_description": description,
        "best_score": "3/4",
        "iterations_run": 1,
        "holdout": 0.0,
        "train_size": 4,
        "test_size": 0,
        "history": [
            {
                "iteration": 1,
                "description": description,
                "train_passed": 3,
                "train_failed": 1,
                "train_total": 4,
                "train_results": [
                    {
                        "query": "fix bug",
                        "should_trigger": True,
                        "pass": True,
                        "triggers": 2,
                        "runs": 2,
                    },
                    {
                        "query": "add feature",
                        "should_trigger": True,
                        "pass": True,
                        "triggers": 2,
                        "runs": 2,
                    },
                    {
                        "query": "deploy app",
                        "should_trigger": False,
                        "pass": True,
                        "triggers": 0,
                        "runs": 2,
                    },
                    {
                        "query": "write tests",
                        "should_trigger": True,
                        "pass": False,
                        "triggers": 0,
                        "runs": 2,
                    },
                ],
                "test_results": None,
                "test_passed": None,
                "test_total": None,
            }
        ],
    }


def test_generate_html_returns_string():
    html = generate_html(_minimal_data())
    assert isinstance(html, str)
    assert len(html) > 100


def test_generate_html_contains_description():
    html = generate_html(_minimal_data("my-test-description"))
    assert "my-test-description" in html


def test_generate_html_escapes_description():
    html = generate_html(_minimal_data('<script>alert("xss")</script>'))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_generate_html_no_auto_refresh_by_default():
    html = generate_html(_minimal_data())
    assert 'http-equiv="refresh"' not in html


def test_generate_html_auto_refresh_when_requested():
    html = generate_html(_minimal_data(), auto_refresh=True)
    assert 'http-equiv="refresh"' in html


def test_generate_html_skill_name_in_title():
    html = generate_html(_minimal_data(), skill_name="my-skill")
    assert "my-skill" in html
