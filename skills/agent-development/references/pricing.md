# Pricing Reference & Methodology

This file documents the heuristic methods used by `scripts/cost.py` and the per-model
rate table in `scripts/lib/pricing.py`.

**Pricing snapshot date:** 2026-05-18
**Source:** https://www.anthropic.com/pricing

---

## Per-Model Rate Table

| Model                        | Input $/MTok | Output $/MTok |
|------------------------------|-------------:|--------------:|
| claude-haiku-4-5-20251001    |         0.80 |          4.00 |
| claude-sonnet-4-6            |         3.00 |         15.00 |
| claude-opus-4-7              |        15.00 |         75.00 |

For unknown model IDs, `pricing.py` uses Sonnet-tier rates as a conservative
fallback and sets `is_fallback_pricing: true` in the output.

---

## Token-Estimation Heuristics

### System Prompt

`tokens ~= len(text) // 4`

Industry rule-of-thumb for English prose with cl100k-compatible BPE tokenizers.
Real token counts range from ~3.5 to ~4.5 chars/token; 4 is a safe midpoint for
agent system prompts which are prose-heavy.

### Tool Schemas

`150 tokens per tool (flat budget)`

A typical schema (one-sentence description + 2-3 named properties with descriptions)
is approximately 120-180 tokens. The 150-token flat budget errs slightly high to
avoid bill surprises.

### Skill Bodies

Skill bodies are **not counted** because they load dynamically at runtime and their
content is unknown at static analysis time. `cost.py` surfaces this as a caveat.
For a more accurate estimate: measure each skill's SKILL.md body and add
`len(body) // 4` to your input token total manually.

---

## How to Refresh

When Anthropic updates pricing:

1. Check current rates at https://www.anthropic.com/pricing
2. Update the `_TABLE` dict in `scripts/lib/pricing.py`
3. Update `PRICING_DATE` in `scripts/lib/pricing.py` to today's date
4. Update the table in this file and the snapshot date above
5. Commit: `chore(agent-dev): refresh pricing snapshot YYYY-MM-DD`

The `--help` output of `cost.py` references this file; users who ask "where do these
numbers come from?" are pointed here.

---

## Cost Smell Thresholds

| Threshold           |   Value | Rationale |
|---------------------|--------:|-----------|
| Input token warning | > 10,000 | Signals over-specified prompt or too many tools |
| Suite cost warning  |  > $5.00 | Reasonable pause-and-reconsider threshold for 3-run eval |

Both are constants in `scripts/cost.py` and can be changed there if needed.
