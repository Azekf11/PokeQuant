"""Robustness variants (ADR 0012): price median, pool weights, bounds, exclusion, relabelling."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest
from test_booster import printings, rates
from test_comparator import CFG, T, context, observations

from pokequant_core.comparator import Column, build_context, jobs, run_job
from pokequant_core.robustness import (
    bound_model,
    check_conclusions,
    relabel,
    run_specs,
    short_print_weights,
    variants,
)
from pokequant_core.schemas import PriceObservation
from pokequant_core.simulate import compile_model, slot_card_probabilities
from pokequant_core.valuation import PriceBasisError, statistics_median, value_cards


def _obs(pid: str, stat: str, ptype: str, amount: float) -> PriceObservation:
    return PriceObservation.model_validate(
        {
            "printing_id": pid,
            "condition": "unspecified",
            "currency": "USD",
            "amount": amount,
            "price_type": ptype,
            "statistic": stat,
            "venue": "tcgplayer",
            "observed_at": T,
            "fetched_at": T,
            "source": "test",
            "source_url": "https://example.org",
        }
    )


def test_statistics_median_is_an_indicative_estimate() -> None:
    pid = "en:zz:20:holo"
    obs = [
        _obs(pid, "low", "listing", 40.0),
        _obs(pid, "mid", "listing", 55.0),
        _obs(pid, "high", "listing", 200.0),
        _obs(pid, "market", "provider_market", 50.0),
        _obs("en:zz:21:holo", "market", "provider_market", 30.0),  # only one statistic
    ]
    v = statistics_median(obs, "tcgplayer", "USD", "unspecified", T.date(),
                          ("low", "mid", "high", "market"))  # fmt: skip
    assert v.prices == {pid: 52.5, "en:zz:21:holo": 30.0}
    assert v.basis.price_type == "estimate"
    central = CFG.scenario("central")
    pools = {"special illustration rare": [pid], "hyper rare": ["en:zz:21:holo"]}
    with pytest.raises(PriceBasisError, match="not a transaction value"):
        value_cards(v, pools, central, "pool_median")
    assert value_cards(v, pools, central, "pool_median", allow_estimate=True).price[pid] == 52.5


def test_multiplicity_weights_printings_within_their_pool() -> None:
    ctx = context()
    model = ctx.posterior.mean_model()
    pool = ctx.posterior.pools["double rare"]
    short = pool[0]
    weights = {p: (76 if p == short else 121) for p in pool}
    plain = slot_card_probabilities(compile_model(model))
    cm = compile_model(model, multiplicity=weights)
    weighted = slot_card_probabilities(cm)
    i, j = cm.index(short), cm.index(pool[1])
    assert weighted[:, i].sum() / weighted[:, j].sum() == pytest.approx(76 / 121)
    total = [cm.index(p) for p in pool]
    assert weighted[:, total].sum() == pytest.approx(plain[:, total].sum())  # rarity rate kept
    with pytest.raises(ValueError, match="bad multiplicity"):
        compile_model(model, multiplicity={"en:zz:999:holo": 2})
    assert short_print_weights(printings(), "zz") == {}


def test_bound_models_bracket_the_posterior_mean() -> None:
    post = context().posterior
    mean = post.mean_model()
    low, high = bound_model(post, "low"), bound_model(post, "high")
    for s_mean, s_low, s_high in zip(mean.slots, low.slots, high.slots, strict=True):
        assert math.fsum(s_low.outcomes.values()) == pytest.approx(1.0)
        spec = next(x for x in post.layout.slots if x.slot_id == s_mean.slot_id)
        for rarity in spec.hits:
            if rarity in s_mean.outcomes:
                assert s_low.outcomes[rarity] < s_mean.outcomes[rarity] < s_high.outcomes[rarity]


def test_top_share_exclusion_removes_the_most_valuable_cards() -> None:
    base = context()
    ctx = build_context(CFG, "zz", printings(), rates(), observations(), exclude_top=0.05)
    assert len(ctx.excluded) == math.ceil(0.05 * len(base.observed))
    central = base.values[base.scenarios.index("central")]
    top = sorted(base.observed, key=lambda c: -central.price[c])[: len(ctx.excluded)]
    assert ctx.excluded == frozenset(top)
    assert not ctx.excluded & ctx.observed
    for cv in ctx.values:
        assert all(cv.liquidation[p] == 0.0 for p in ctx.excluded)


def test_value_columns_share_the_simulated_openings() -> None:
    """A column identical to central gives the same metrics: common random numbers."""
    twin = Column(CFG.scenario("central").model_copy(update={"name": "twin"}), "central")
    ctx = build_context(CFG, "zz", printings(), rates(), observations(), columns=(twin,))
    assert ctx.scenarios[-1] == "twin"
    res = dataclasses.asdict(run_job(ctx, jobs(CFG)[1], 1, seed=5, draws=2, runs=400))
    assert res["a_metrics"]["twin"] == res["a_metrics"]["central"]
    swapped = relabel(res, {"central": "twin"})
    assert swapped["scenarios"] == ["gross", "central", "adverse"]
    assert swapped["a_metrics"]["central"] == res["a_metrics"]["twin"]
    assert "twin" not in swapped["extra"]["break_even_booster_price"]


def test_conclusions_and_variant_catalogue() -> None:
    ctx = context()
    res = [
        dataclasses.asdict(run_job(ctx, j, i, seed=5, draws=3, runs=400))
        for i, j in enumerate(jobs(CFG))
    ]
    c = check_conclusions(res, 4.49)
    assert set(c) == {"C1", "C2", "C3", "break_even"}
    assert set(c["break_even"]["zz"]) == {"central", "gross"}
    single = check_conclusions(
        [dataclasses.asdict(run_job(ctx, jobs(CFG)[1], 1, seed=5, draws=1, runs=400,
                                    models=[bound_model(ctx.posterior, "low")]))],
        4.49,
        single_model=True,
    )  # fmt: skip
    assert isinstance(single["C1"]["holds"], bool)
    names = {s.name for s in run_specs(CFG)}
    assert {v.run for v in variants()} <= names
    columns = next(s for s in run_specs(CFG) if s.name == "values").columns
    r3 = next(c for c in columns if c.scenario.name == "R3|x1.5").scenario
    assert r3.shipping_per_sale == pytest.approx(1.5 * CFG.scenario("central").shipping_per_sale)
    assert r3.liquidity_haircut == CFG.scenario("central").liquidity_haircut
    assert np.isclose(
        next(c for c in columns if c.scenario.name == "R10|h=0.27").scenario.liquidity_haircut,
        0.27,
    )
