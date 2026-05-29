"""
Per-model pricing table (USD per million tokens).
Single source of truth — update PRICING_DATE when refreshing rates.
See references/pricing.md for methodology and refresh instructions.
"""

from __future__ import annotations
from typing import Tuple

# Snapshot date — update this when you refresh the table below.
PRICING_DATE = "2026-05-18"
PRICING_URL = "https://www.anthropic.com/pricing"

# (input_$/MTok, output_$/MTok)
_TABLE: dict = {
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-haiku-4-5": (0.80, 4.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-7": (15.00, 75.00),
}

_FALLBACK = "claude-sonnet-4-6"


def get_pricing(model: str) -> Tuple[float, float, bool]:
    """
    Return (input_$/MTok, output_$/MTok, is_fallback).
    is_fallback=True means the model was unrecognised; Sonnet rates were used.
    """
    if model in _TABLE:
        return (*_TABLE[model], False)

    model_l = model.lower()
    if "haiku" in model_l:
        return (*_TABLE["claude-haiku-4-5-20251001"], False)
    if "opus" in model_l:
        return (*_TABLE["claude-opus-4-7"], False)
    if "sonnet" in model_l:
        return (*_TABLE["claude-sonnet-4-6"], False)

    return (*_TABLE[_FALLBACK], True)


def cost_usd(input_tokens: int, output_tokens: int, model: str) -> Tuple[float, bool]:
    """Return (total_cost_usd, is_fallback)."""
    inp_rate, out_rate, is_fallback = get_pricing(model)
    cost = (input_tokens / 1_000_000 * inp_rate) + (
        output_tokens / 1_000_000 * out_rate
    )
    return cost, is_fallback
