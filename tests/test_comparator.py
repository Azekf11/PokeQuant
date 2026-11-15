"""Strategy comparator, comparison tables and hypothesis verdicts (ADR 0011)."""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
from test_booster import printings, rates

from pokequant_core.analysis import comparison_rows, hypotheses
from pokequant_core.comparator import (
    SetContext,
    basket_profit,
    build_context,
    choose_target,
    greedy_basket,
    jobs,
    posterior_models,
    run_job,
)
from pokequant_core.experiment import load_experiment
from pokequant_core.metrics import compare, constant_metrics
from pokequant_core.schemas import PriceObservation
from pokequant_core.simulate import compile_model, simulate_e1, simulate_e2

ROOT = Path(__file__).resolve().parents[1]
CFG = load_experiment(ROOT / "research/experiments/main.yaml").model_copy(update={"sets": ["zz"]})
T = datetime(2026, 11, 14, 22, 0, tzinfo=UTC)
PRICE = {  # rarity -> market price of each card (USD)
    "common": 0.1,
    "uncommon": 0.15,
    "rare": 0.25,
    "double rare": 1.5,
    "ultra rare": 4.0,
    "illustration rare": 8.0,
    "special illustration rare": 60.0,
    "hyper rare": 30.0,
}


def observations(skip: tuple[str, ...] = ()) -> list[PriceObservation]:
    out = []
    for p in printings():
        if p.printing_id in skip:
            continue
        amount = PRICE[p.rarity] * (1.2 if p.variant == "reverse" else 1.0) + int(p.number) / 100
        out.append(
            PriceObservation(
                printing_id=p.printing_id,
                condition="unspecified",
                currency="USD",
                amount=amount,
                price_type="provider_market",
                statistic="market",
                venue="tcgplayer",
                observed_at=T,
                fetched_at=T + timedelta(minutes=5),
                source="test",
                source_url="https://example.org",
            )
        )
    return out


def context(skip: tuple[str, ...] = ()) -> SetContext:
    return build_context(CFG, "zz", printings(), rates(), observations(skip))


def test_greedy_basket_buys_the_most_expensive_cards_that_fit() -> None:
    ctx = context()
    cv = ctx.values[ctx.scenarios.index("central")]
    basket = greedy_basket(cv, ctx.observed, 45.0)
    prices = [cv.acquisition[p] for p in basket]
    assert prices == sorted(prices, reverse=True) and sum(prices) <= 45.0
    assert len(basket) == len(set(basket))
    left = 45.0 - sum(prices)
    assert all(cv.acquisition[p] > left for p in ctx.observed - set(basket))
    assert basket_profit(cv, basket) < 0  # round trip costs fees and shipping


def test_targets_are_chosen_among_observed_prices() -> None:
    sir = "en:zz:20:holo"  # the only SIR (card numbers follow SPEC order)
    ctx = context()
    assert choose_target(ctx, "top_price") == sir
    assert choose_target(ctx, "top_sir") == sir
    with pytest.raises(ValueError, match="unknown target rule"):
        choose_target(ctx, "cheapest")
    hyper = "en:zz:21:holo"
    assert ctx.acquisition(hyper)[0] < ctx.acquisition(sir)[0]


def test_missing_price_rules_follow_the_scenario() -> None:
    missing = "en:zz:18:holo"  # an Illustration Rare; its pool has one other card
    ctx = context(skip=(missing,))
    by = dict(zip(ctx.scenarios, ctx.values, strict=True))
    assert by["central"].price[missing] == by["central"].price["en:zz:19:holo"]  # pool median
    assert by["gross"].price[missing] == by["central"].price[missing]
    assert by["adverse"].price[missing] == 0.0
    assert missing not in ctx.observed
    with pytest.raises(ValueError, match="no observed price"):
        context(skip=("en:zz:21:holo",))  # the only hyper rare: nothing to impute from


def test_scenario_columns_match_separate_runs() -> None:
    """Common random numbers: a value matrix equals the columns run one by one."""
    ctx = context()
    cm = compile_model(ctx.posterior.mean_model())
    v = ctx.value_matrix(cm)

    def rng() -> np.random.Generator:
        return np.random.default_rng(3)

    together = simulate_e1(cm, v, rng(), n_packs=5, booster_cost=ctx.booster_cost, runs=500)
    for k in range(v.shape[1]):
        alone = simulate_e1(cm, v[:, k], rng(), n_packs=5, booster_cost=ctx.booster_cost[k],
                            runs=500)  # fmt: skip
        assert alone.shape == (500,)
    assert together.shape == (500, v.shape[1])
    target = choose_target(ctx, "top_sir")
    a = ctx.acquisition(target)
    cost, opened = simulate_e2(cm, v, rng(), target=target, booster_cost=ctx.booster_cost,
                               target_price=a, n_max=50, runs=500)  # fmt: skip
    assert cost.shape == (500, v.shape[1]) and opened.shape == (500,)
    # Gross scenario values every card at its market price: higher pack value than central.
    g, c = ctx.scenarios.index("gross"), ctx.scenarios.index("central")
    assert np.all(
        together[:, g] + 5 * ctx.booster_cost[g] >= together[:, c] + 5 * ctx.booster_cost[c]
    )


def test_run_job_is_reproducible_and_complete(tmp_path: Path) -> None:
    ctx = context()
    all_jobs = jobs(CFG)
    assert [j.label for j in all_jobs] == ["n=1", "n=10", "n=36", "n=100", "top_price", "top_sir"]
    a = run_job(ctx, all_jobs[1], 1, seed=7, draws=3, runs=400)
    b = run_job(ctx, all_jobs[1], 1, seed=7, draws=3, runs=400)
    assert json.dumps(dataclasses.asdict(a), sort_keys=True) == json.dumps(
        dataclasses.asdict(b), sort_keys=True
    )
    models = posterior_models(ctx, 7, 3)
    assert len({m.slots[-1].outcomes["rare"] for m in models}) == 3  # distinct draws
    e2 = run_job(ctx, all_jobs[5], 5, seed=7, draws=3, runs=400)
    assert e2.extra["n_max"] >= 1 and len(e2.extra["p_hit"]) == 3
    assert all(v == 0.0 for v in (e2.b_metrics[s]["mean"] for s in ctx.scenarios))
    rows = comparison_rows(dataclasses.asdict(a))
    assert {r["verdict"] for r in rows} <= {"decisive: A", "decisive: B", "undetermined", "tie"}
    verdicts = hypotheses([dataclasses.asdict(a), dataclasses.asdict(e2)])
    assert set(verdicts) == {"H1", "H2", "H3", "H4"}


def test_compare_and_constant_metrics() -> None:
    assert compare(np.array([1.0, 2.0, 3.0]), 0.0, 1) == (1.0, "decisive: A")
    assert compare(np.array([1.0, 2.0, 3.0]), 0.0, -1) == (0.0, "decisive: B")
    assert compare(np.zeros(5), 0.0, 1) == (0.0, "tie")
    assert compare(np.array([-1.0, 1.0]), 0.0, 1)[1] == "undetermined"
    m = constant_metrics(-2.0)
    assert m["mean"] == m["q05"] == -2.0 and m["p_loss"] == 1.0 and m["cvar05"] == 2.0
