"""Scan workspace skills and recommend matches for an agent task."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .frontmatter import parse_frontmatter


_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "use",
        "uses",
        "using",
        "when",
        "if",
        "is",
        "are",
        "this",
        "that",
        "skill",
        "agent",
        "you",
        "your",
        "my",
        "it",
        "be",
        "should",
        "would",
        "could",
        "any",
        "some",
        "all",
    }
)


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())
    return {t for t in tokens if t not in _STOPWORDS}


@dataclass(frozen=True)
class SkillEntry:
    name: str
    description: str
    source_path: Path
    disable_model_invocation: bool


def scan_skills(
    skill_dirs: Iterable[Path],
    include_disabled: bool = True,
) -> list[SkillEntry]:
    """Walk skill_dirs and return all SKILL.md frontmatter as SkillEntry list."""
    out: list[SkillEntry] = []
    seen_names: set[str] = set()
    for d in skill_dirs:
        d = Path(d)
        if not d.exists():
            continue
        for skill_md in d.glob("*/SKILL.md"):
            fm, _body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            name = fm.get("name") or skill_md.parent.name
            if name in seen_names:
                continue
            seen_names.add(name)
            disabled = bool(fm.get("disable-model-invocation", False))
            description = fm.get("description") or ""
            if isinstance(description, list):
                description = " ".join(description)
            out.append(
                SkillEntry(
                    name=name,
                    description=str(description),
                    source_path=skill_md,
                    disable_model_invocation=disabled,
                )
            )
    if not include_disabled:
        out = [s for s in out if not s.disable_model_invocation]
    return out


def score_skill(skill: SkillEntry, agent_task: str) -> float:
    """Score a skill against an agent task. Returns 0.0–1.0 (roughly)."""
    skill_tokens = _tokenize(skill.description) | _tokenize(skill.name)
    task_tokens = _tokenize(agent_task)
    if not skill_tokens or not task_tokens:
        return 0.0
    intersection = skill_tokens & task_tokens
    # Jaccard-ish, biased toward task-side coverage
    if not intersection:
        return 0.0
    score = len(intersection) / (len(task_tokens) ** 0.5 + len(skill_tokens) ** 0.5)
    return min(score, 1.0)


def recommend_skills(
    agent_task: str,
    skill_dirs: Iterable[Path],
    top_k: int = 5,
    include_disabled: bool = True,
) -> dict:
    """Return a ranked dict of candidate skills."""
    skills = scan_skills(skill_dirs, include_disabled=include_disabled)
    scored = [(score_skill(s, agent_task), s) for s in skills]
    scored.sort(key=lambda x: -x[0])
    candidates = []
    for score, s in scored[:top_k]:
        if score <= 0.0:
            continue
        candidates.append(
            {
                "skill": s.name,
                "score": round(score, 3),
                "reason": _explain_match(s, agent_task),
                "recommended_pin": "exact-version-from-skill-source",
                "source": str(s.source_path),
            }
        )
    return {
        "agent_task_preview": agent_task[:120],
        "candidates": candidates,
        "caveats": [
            "Always pin exact versions in production. Never use 'latest' for skills.",
            "Audit any third-party skill before pinning — verify allowlist intersection.",
        ],
    }


def _explain_match(skill: SkillEntry, agent_task: str) -> str:
    skill_tokens = _tokenize(skill.description) | _tokenize(skill.name)
    task_tokens = _tokenize(agent_task)
    overlap = sorted(skill_tokens & task_tokens)[:5]
    if not overlap:
        return "weak match"
    return f"overlap on: {', '.join(overlap)}"
