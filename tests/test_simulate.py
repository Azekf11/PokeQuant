from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from scipy import stats
from test_booster import printings, rates

from pokequant_core.booster import LAYOUTS, build_set_posterior
from pokequant_core.metrics import cvar, epistemic_interval, p_loss, share_better, summarise, var
from pokequant_core.metrics import verdict as decide
from pokequant_core.model import BoosterModel, Slot, p_card_in_slot, p_hit
from pokequant_core.runner import generators, run_nested, write_manifest
from pokequant_core.simulate import (
    compile_model,
    open_packs,
    pack_values,
    simulate_e1,
    simulate_e2,
    split_on_target,
    values_vector,
)


def toy(p: float = 0.3) -> BoosterModel:
    """One slot, two cards: 'x' with probability p, 'y' otherwise."""
    return BoosterModel(
        product_id="toy",
        set_id="toy",
        version="t",
        cards_by_rarity={"hit": ["x"], "miss": ["y"]},
        slots=[Slot(slot_id="s", outcomes={"hit": p, "miss": 1 - p})],
    )


def rich() -> BoosterModel:
    return build_set_posterior("zz", printings(), rates(), LAYOUTS["tcgplayer"]).mean_model()


def test_toy_case_matches_exact_mean_and_variance() -> None:
    cm = compile_model(toy(0.3))
    values = values_vector(cm, {"x": 10.0, "y": 0.0})
    v = pack_values(cm, values, np.random.default_rng(1), 400_000)
    se = math.sqrt(21.0 / len(v))
    assert abs(v.mean() - 3.0) < 4 * se  # E = 0.3 * 10
    assert v.var() == pytest.approx(21.0, rel=0.02)  # Var = 0.3 * 0.7 * 100


def test_simulated_card_frequencies_match_theory() -> None:
    model = rich()
    cm = compile_model(model, distinct_groups=())
    n = 200_000
    cards = open_packs(cm, np.random.default_rng(2), n)
    for col, slot in enumerate(model.slots):
        if slot.slot_id not in {"rev2", "rare"}:
            continue
        observed = np.bincount(cards[:, col], minlength=len(cm.printing_ids))
        expected = np.array([p_card_in_slot(model, slot, p) for p in cm.printing_ids]) * n
        keep = expected > 0
        assert observed[~keep].sum() == 0
        chi2 = stats.chisquare(observed[keep], expected[keep])
        assert chi2.pvalue > 1e-4


def test_hit_counts_follow_the_binomial() -> None:
    model = rich()
    cm = compile_model(model)
    target = model.cards_by_rarity["special illustration rare"][0]
    p = p_hit(model, target)
    n_packs, runs = 100, 20_000
    packs = open_packs(cm, np.random.default_rng(3), n_packs * runs).reshape(runs, n_packs, -1)
    hits = (packs == cm.index(target)).any(axis=2).sum(axis=1)
    assert hits.mean() == pytest.approx(n_packs * p, rel=0.05)
    assert hits.var() == pytest.approx(n_packs * p * (1 - p), rel=0.1)


def test_commons_and_uncommons_are_distinct_within_a_pack() -> None:
    cm = compile_model(rich())
    cards = open_packs(cm, np.random.default_rng(4), 50_000)
    for group in cm.distinct_groups:
        sub = np.sort(cards[:, list(group)], axis=1)
        assert not np.any(sub[:, 1:] == sub[:, :-1])


def test_monte_carlo_error_decays_like_inverse_square_root() -> None:
    cm = compile_model(toy(0.3))
    values = values_vector(cm, {"x": 10.0, "y": 0.0})
    rng = np.random.default_rng(5)
    sizes = [1_000, 10_000, 100_000]
    errors = [
        np.sqrt(np.mean([(pack_values(cm, values, rng, n).mean() - 3.0) ** 2 for _ in range(60)]))
        for n in sizes
    ]
    slope = np.polyfit(np.log10(sizes), np.log10(errors), 1)[0]
    assert slope == pytest.approx(-0.5, abs=0.1)


def test_e1_profit_is_value_minus_cost() -> None:
    cm = compile_model(toy(1.0))
    values = values_vector(cm, {"x": 2.0, "y": 0.0})
    profit = simulate_e1(cm, values, np.random.default_rng(6), n_packs=10, booster_cost=4.5, runs=5)
    assert np.allclose(profit, 10 * 2.0 - 10 * 4.5)


def test_target_split_excludes_the_target_and_keeps_distributions() -> None:
    model = rich()
    cm = compile_model(model)
    target = model.cards_by_rarity["hyper rare"][0]
    split = split_on_target(cm, target)
    assert split.p_hit == pytest.approx(p_hit(model, target))
    cards = open_packs(split.without, np.random.default_rng(7), 100_000)
    assert not np.any(cards == split.target)
    with pytest.raises(ValueError, match="exactly one slot"):
        split_on_target(cm, model.cards_by_rarity["common"][0])


def test_e2_is_exact_with_constant_values() -> None:
    """Every printing worth 1: the cards sold are 10 per pack minus the target."""
    model = rich()
    cm = compile_model(model)
    target = model.cards_by_rarity["special illustration rare"][0]
    values = np.ones(len(cm.printing_ids))
    cost, opened = simulate_e2(
        cm, values, np.random.default_rng(8), target=target, booster_cost=4.0,
        target_price=50.0, n_max=150, runs=40_000,
    )  # fmt: skip
    hit = opened < 150
    assert np.allclose(cost[hit], opened[hit] * 4.0 - (10 * opened[hit] - 1))
    p = p_hit(model, target)
    assert np.mean(~hit) == pytest.approx((1 - p) ** 150, abs=0.01)  # P(no hit in n_max)
    expected_opened = (1 - (1 - p) ** 150) / p  # E[min(K, n_max)]
    assert opened.mean() == pytest.approx(expected_opened, rel=0.02)


def test_risk_metrics_on_a_known_sample() -> None:
    x = np.arange(1, 101, dtype=float) - 50.5  # -49.5 ... 49.5
    assert cvar(x, 0.05) == pytest.approx(-np.mean(x[:5]))
    assert var(x, 0.05) == pytest.approx(-np.quantile(x, 0.05))
    assert p_loss(x) == 0.5
    s = summarise(np.random.default_rng(9).normal(0, 1, 20_000))
    assert s.value["mean"] == pytest.approx(0, abs=0.05)
    assert s.mc_se["mean"] == pytest.approx(1 / math.sqrt(20_000), rel=0.5)
    assert s.value["cvar05"] > s.value["var05"] > 0
    assert epistemic_interval(np.arange(1001.0)) == pytest.approx((25.0, 975.0))
    assert decide(share_better(np.ones(10), np.zeros(10))) == "decisive: first"
    assert decide(0.5) == "undetermined"


def test_nested_runs_are_reproducible(tmp_path: Path) -> None:
    post = build_set_posterior("zz", printings(), rates(), LAYOUTS["tcgplayer"])
    model = post.mean_model()
    prices = {p: float(i % 7) for i, p in enumerate(sorted(compile_model(model).printing_ids))}

    def experiment(m: BoosterModel, rng: np.random.Generator) -> np.ndarray:
        cm = compile_model(m)
        return simulate_e1(cm, values_vector(cm, prices), rng, n_packs=3, booster_cost=4.49,
                           runs=1_000)  # fmt: skip

    kwargs = {"seed": 11, "epistemic_draws": 4, "data_snapshot_ids": ["test"],
              "parameters": {"n_packs": 3}, "run_id": "t"}  # fmt: skip
    a = run_nested(post, experiment, **kwargs)  # type: ignore[arg-type]
    b = run_nested(post, experiment, **kwargs)  # type: ignore[arg-type]
    assert write_manifest(a, tmp_path / "a.json") == write_manifest(b, tmp_path / "b.json")
    assert len(set(a.metric("mean"))) == 4  # draws differ from each other
    assert [g.random() for g in generators(1, 2)] == [g.random() for g in generators(1, 2)]


def test_aggregate_and_card_by_card_paths_agree() -> None:
    model = rich()
    cm = compile_model(model, distinct_groups=())
    values = np.random.default_rng(10).gamma(0.5, 4.0, len(cm.printing_ids))
    exact = simulate_e1(cm, values, np.random.default_rng(11), n_packs=10, booster_cost=0.0,
                        runs=40_000, exact_packs=True)  # fmt: skip
    fast = simulate_e1(cm, values, np.random.default_rng(12), n_packs=10, booster_cost=0.0,
                       runs=40_000)  # fmt: skip
    se = math.sqrt(exact.var() / len(exact) + fast.var() / len(fast))
    assert abs(exact.mean() - fast.mean()) < 4 * se
    assert fast.std() == pytest.approx(exact.std(), rel=0.03)
    assert stats.ks_2samp(exact, fast).pvalue > 1e-3
