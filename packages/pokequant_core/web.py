"""Aggregates published by the static web demo (ADR 0013).

Only derived statistics are published (ADR 0009): the break-even grid below
sums over every card of a set, and :func:`card_level_leaks` checks that an
export names no printing.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import numpy as np

from pokequant_core.comparator import SetContext, posterior_models
from pokequant_core.simulate import slot_card_probabilities

# Keep factor k = (1 - haircut)(1 - seller fee rates), fixed cost F per card sold (USD).
KEEP = np.round(np.arange(0.30, 1.0001, 0.025), 3)
FIXED = np.round(np.arange(0.0, 6.0001, 0.10), 2)
FORBIDDEN_KEYS = frozenset({"price", "prices", "target", "printing_id", "acquisition"})


def break_even_grid(
    ctx: SetContext, seed: int, draws: int, scenario: str = "central"
) -> dict[str, Any]:
    """b*(k, F) = expected sum over one pack of max(0, k p(c) - F), per posterior draw.

    p(c) is the price of ``scenario`` (observed, or imputed by its missing rule).
    With k and F of a cost scenario, a cell equals that scenario's break-even
    booster price. Returns the grid axes and the mean and 95 % interval over draws.
    """
    values = ctx.values[ctx.scenarios.index(scenario)]
    mean_cm = ctx.compile(ctx.posterior.mean_model())
    price = np.array([values.price[p] for p in mean_cm.printing_ids])
    payoff = np.maximum(0.0, KEEP[:, None, None] * price[None, None, :] - FIXED[None, :, None])
    cells = []
    for model in posterior_models(ctx, seed, draws):
        cm = ctx.compile(model)
        if cm.printing_ids != mean_cm.printing_ids:
            raise RuntimeError("posterior draws changed the printing set")
        cells.append(payoff @ slot_card_probabilities(cm).sum(axis=0))
    stack = np.stack(cells)  # draws x keep x fixed
    low, high = np.quantile(stack, [0.025, 0.975], axis=0)
    return {
        "keep": KEEP.tolist(),
        "fixed": FIXED.tolist(),
        "mean": np.round(stack.mean(axis=0), 4).tolist(),
        "low": np.round(low, 4).tolist(),
        "high": np.round(high, 4).tolist(),
    }


def _keys(node: Any) -> Iterable[str]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield str(k)
            yield from _keys(v)
    elif isinstance(node, list):
        for v in node:
            yield from _keys(v)


def card_level_leaks(payload: Any, printing_ids: Iterable[str]) -> list[str]:
    """Printing identifiers or card-level keys found in an export (empty if clean)."""
    text = json.dumps(payload)
    found = sorted(p for p in set(printing_ids) if f'"{p}"' in text)
    found += sorted({k for k in _keys(payload) if k in FORBIDDEN_KEYS})
    return found
