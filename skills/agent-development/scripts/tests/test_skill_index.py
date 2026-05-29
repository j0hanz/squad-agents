from pathlib import Path
from lib.skill_index import scan_skills, score_skill, recommend_skills

FIXTURES = Path(__file__).parent / "fixtures" / "sample-skills"


def test_scan_finds_three_skills():
    skills = scan_skills([FIXTURES])
    names = {s.name for s in skills}
    assert names == {"code-reviewer", "gh-cli", "disabled-skill"}


def test_disabled_excluded_by_default():
    skills = scan_skills([FIXTURES], include_disabled=False)
    names = {s.name for s in skills}
    assert "disabled-skill" not in names
    assert "code-reviewer" in names


def test_score_high_overlap():
    skills = scan_skills([FIXTURES])
    cr = next(s for s in skills if s.name == "code-reviewer")
    score = score_skill(cr, agent_task="please review this PR and audit the diff")
    assert score > 0.3  # at least one strong keyword match


def test_score_low_overlap():
    skills = scan_skills([FIXTURES])
    cr = next(s for s in skills if s.name == "code-reviewer")
    score = score_skill(cr, agent_task="generate a database schema for users")
    assert score < 0.15


def test_recommend_returns_ranked_list():
    result = recommend_skills(
        agent_task="review my PR and run gh api to fetch labels",
        skill_dirs=[FIXTURES],
        top_k=2,
    )
    assert len(result["candidates"]) == 2
    # gh-cli and code-reviewer should both rank above disabled-skill
    names = [c["skill"] for c in result["candidates"]]
    assert "disabled-skill" not in names


def test_recommend_includes_caveats():
    result = recommend_skills(agent_task="x", skill_dirs=[FIXTURES])
    assert any("pin exact" in c.lower() for c in result["caveats"])
