"""
Per-model pricing table (USD per million tokens).
Single source of truth — update PRICING_DATE when refreshing rates.
See references/pricing.md for methodology and refresh instructions.
"""

from __future__ import annotations
from typing import Tuple, Dict


# Snapshot date — update this when you refresh the table below.
PRICING_DATE: str = "2026-05-18"
PRICING_URL: str = "https://www.anthropic.com/pricing"

# (input_$/MTok, output_$/MTok)
_TABLE: Dict[str, Tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-haiku-4-5": (0.80, 4.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-7": (15.00, 75.00),
}

_FALLBACK: str = "claude-sonnet-4-6"


def get_pricing(model: str) -> Tuple[float, float, bool]:
    """
    Return (input_$/MTok, output_$/MTok, is_fallback).

    Args:
        model: The model name string.

    Returns:
        A tuple of (input_rate, output_rate, is_fallback).
        is_fallback=True means the model was unrecognised; Sonnet rates were used.
    """
    if model in _TABLE:
        rates = _TABLE[model]
        return (rates[0], rates[1], False)

    model_l = model.lower()
    if "haiku" in model_l:
        rates = _TABLE["claude-haiku-4-5-20251001"]
        return (rates[0], rates[1], False)
    if "opus" in model_l:
        rates = _TABLE["claude-opus-4-7"]
        return (rates[0], rates[1], False)
    if "sonnet" in model_l:
        rates = _TABLE["claude-sonnet-4-6"]
        return (rates[0], rates[1], False)

    rates = _TABLE[_FALLBACK]
    return (rates[0], rates[1], True)


def cost_usd(input_tokens: int, output_tokens: int, model: str) -> Tuple[float, bool]:
    """
    Calculate the total cost in USD for a given number of tokens and model.

    Args:
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        model: The model name used.

    Returns:
        A tuple of (total_cost_usd, is_fallback).
    """
    inp_rate, out_rate, is_fallback = get_pricing(model)
    cost = (input_tokens / 1_000_000 * inp_rate) + (
        output_tokens / 1_000_000 * out_rate
    )
    return cost, is_fallback
