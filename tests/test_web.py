"""Web export (ADR 0013): the break-even grid and the card-level leak check."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from test_comparator import CFG, context

from pokequant_core.comparator import jobs, posterior_models, run_job
from pokequant_core.simulate import slot_card_probabilities
from pokequant_core.valuation import liquidation_value
from pokequant_core.web import FIXED, KEEP, break_even_grid, card_level_leaks


def _cell(grid: dict[str, list[list[float]]], k: float, f: float, field: str = "mean") -> float:
    i = int(np.argmin(np.abs(np.asarray(KEEP) - k)))
    j = int(np.argmin(np.abs(np.asarray(FIXED) - f)))
    assert KEEP[i] == pytest.approx(k) and FIXED[j] == pytest.approx(f)
    return grid[field][i][j]


def test_grid_reproduces_the_break_even_price_of_the_run() -> None:
    ctx = context()
    grid = break_even_grid(ctx, seed=5, draws=4)
    res = dataclasses.asdict(run_job(ctx, jobs(CFG)[0], 0, seed=5, draws=4, runs=400))
    gross = res["extra"]["break_even_booster_price"]["gross"]
    assert _cell(grid, 1.0, 0.0) == pytest.approx(float(np.mean(gross)), abs=1e-4)
    mean = np.asarray(grid["mean"])
    assert np.all(np.diff(mean, axis=0) >= -1e-12)  # more kept, more value
    assert np.all(np.diff(mean, axis=1) <= 1e-12)  # higher fixed cost, less value
    assert np.all(np.asarray(grid["low"]) <= mean + 1e-9)
    assert np.all(mean <= np.asarray(grid["high"]) + 1e-9)


def test_grid_cell_equals_the_valuation_of_a_cost_scenario() -> None:
    """On a grid point, a cell is the mean over draws of E[sum of l(c)] under that scenario."""
    ctx = context()
    scenario = CFG.scenario("central").model_copy(
        update={
            "liquidity_haircut": 0.2,
            "marketplace_fee_rate": 0.0,
            "payment_fee_rate": 0.0,
            "selling_fixed_fee": 0.5,
            "shipping_per_sale": 1.0,
        }
    )
    prices = ctx.values[ctx.scenarios.index("central")].price
    expected = []
    for model in posterior_models(ctx, 5, 3):
        cm = ctx.compile(model)
        ell = np.array([liquidation_value(prices[p], scenario) for p in cm.printing_ids])
        expected.append(float(slot_card_probabilities(cm).sum(axis=0) @ ell))
    grid = break_even_grid(ctx, seed=5, draws=3)
    assert _cell(grid, 0.8, 1.5) == pytest.approx(float(np.mean(expected)), abs=1e-4)


def test_card_level_leaks_are_detected() -> None:
    ids = ["en:zz:1:holo", "en:zz:2:normal"]
    assert card_level_leaks({"rows": [{"set": "zz", "mean": 1.0}]}, ids) == []
    assert card_level_leaks({"rows": [{"card": "en:zz:1:holo"}]}, ids) == ["en:zz:1:holo"]
    assert card_level_leaks({"e2": [{"target": "x"}]}, ids) == ["target"]
