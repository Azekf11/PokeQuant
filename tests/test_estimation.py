from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from pokequant_core.estimation import (
    JEFFREYS,
    UNIFORM,
    DirichletPosterior,
    beta_posterior,
    homogeneity_test,
    slot_posterior,
)

PULL_RATES = Path(__file__).resolve().parents[1] / "data/raw/pokelife/2026-11-13/pull-rates.csv"
SELECTED = {"stellar-crown", "surging-sparks", "destined-rivals"}


def test_jeffreys_parameters_and_uniform_prior() -> None:
    post = beta_posterior(3, 10)
    assert (post.a, post.b) == (3.5, 7.5)
    assert beta_posterior(3, 10, prior=UNIFORM).a == 4.0


@pytest.mark.parametrize(("hits", "packs"), [(0, 50), (50, 50)])
def test_boundary_cases_give_proper_posteriors(hits: int, packs: int) -> None:
    post = beta_posterior(hits, packs)
    low, high = post.interval()
    assert 0.0 < low < post.mean < high < 1.0


def test_down_weighting_widens_the_interval_but_keeps_the_rate() -> None:
    full, half = beta_posterior(120, 10_000), beta_posterior(120, 10_000, weight=0.5)
    assert math.isclose(full.mean, half.mean, rel_tol=1e-2)
    width = [b - a for a, b in (full.interval(), half.interval())]
    assert width[1] > width[0] * 1.35  # ≈ √2 wider


@pytest.mark.parametrize(
    "kwargs", [{"hits": 11, "packs": 10}, {"hits": 1, "packs": 0}, {"hits": -1, "packs": 5}]
)
def test_invalid_counts_are_rejected(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        beta_posterior(**kwargs)


@pytest.mark.parametrize("kwargs", [{"prior": 0.0}, {"weight": 0.0}, {"weight": 1.5}])
def test_invalid_prior_or_weight_is_rejected(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        beta_posterior(1, 10, **kwargs)


def test_registry_intervals_are_jeffreys_on_the_published_counts() -> None:
    """The registry states its ci95 is a Jeffreys interval: check it for the selected sets."""
    with PULL_RATES.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["set_id"] in SELECTED]
    assert len(rows) == 17
    for r in rows:
        low, high = beta_posterior(int(r["hits"]), int(r["packs"]), prior=JEFFREYS).interval()
        assert low == pytest.approx(float(r["ci95_lower"]), abs=1e-5)
        assert high == pytest.approx(float(r["ci95_upper"]), abs=1e-5)


def test_slot_posterior_uses_the_smallest_denominator() -> None:
    post = slot_posterior({"ir": (80, 1000), "sir": (24, 2000)}, residual="reverse")
    assert post.outcomes == ("ir", "sir", "reverse")
    # n = 1000: ir 80, sir 12, reverse 908, plus ½ each
    assert post.alpha == pytest.approx((80.5, 12.5, 908.5))
    assert post.mean["sir"] == pytest.approx(12.5 / 1001.5)
    assert post.marginal("ir").mean == pytest.approx(post.mean["ir"])


def test_slot_posterior_rejects_rates_that_cannot_share_a_slot() -> None:
    with pytest.raises(ValueError, match="not one slot"):
        slot_posterior({"a": (600, 1000), "b": (500, 1000)}, residual="rest")
    with pytest.raises(ValueError, match="residual"):
        slot_posterior({"a": (1, 10)}, residual="a")


def test_dirichlet_samples_are_distributions() -> None:
    post = DirichletPosterior(("a", "b", "c"), (2.0, 3.0, 5.0))
    draws = post.sample(np.random.default_rng(1), 2_000)
    assert draws.shape == (2_000, 3)
    assert np.allclose(draws.sum(axis=1), 1.0)
    assert np.allclose(draws.mean(axis=0), [0.2, 0.3, 0.5], atol=0.02)


@pytest.mark.parametrize(
    ("outcomes", "alpha"), [(("a",), (1.0,)), (("a", "a"), (1.0, 1.0)), (("a", "b"), (1.0, 0.0))]
)
def test_invalid_dirichlet_is_rejected(outcomes: tuple[str, ...], alpha: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        DirichletPosterior(outcomes, alpha)


def test_homogeneity_test_detects_different_rates() -> None:
    same = homogeneity_test([(100, 1000), (105, 1000)])
    different = homogeneity_test([(100, 1000), (180, 1000)])
    assert same.dof == 1 and same.p_value > 0.5
    assert different.p_value < 1e-6
    assert same.min_expected > 5
    with pytest.raises(ValueError):
        homogeneity_test([(1, 10)])


@given(
    packs=st.integers(1, 100_000),
    share=st.floats(0, 1),
    weight=st.floats(0.05, 1),
    prior=st.sampled_from([JEFFREYS, UNIFORM]),
)
def test_beta_posterior_mean_lies_between_prior_and_data(
    packs: int, share: float, weight: float, prior: float
) -> None:
    hits = round(share * packs)
    post = beta_posterior(hits, packs, prior=prior, weight=weight)
    low, high = sorted((0.5, hits / packs))
    assert low - 1e-12 <= post.mean <= high + 1e-12


@given(
    counts=st.lists(st.integers(0, 300), min_size=1, max_size=4),
    packs=st.integers(1_300, 5_000),
)
def test_slot_posterior_mean_is_a_distribution(counts: list[int], packs: int) -> None:
    post = slot_posterior({f"r{i}": (x, packs) for i, x in enumerate(counts)}, "rest")
    assert math.isclose(math.fsum(post.mean.values()), 1.0)
    assert all(v > 0 for v in post.mean.values())


def test_predictive_check_centres_on_the_posterior_rate() -> None:
    from pokequant_core.estimation import predictive_check

    post = beta_posterior(100, 1000)
    near = predictive_check(post, 50, 500)
    assert near.expected == pytest.approx(500 * 100.5 / 1001)
    assert near.inside and near.p_value > 0.5
    far = predictive_check(post, 120, 500)
    assert not far.inside and far.p_value < 1e-6
    assert predictive_check(post, 0, 500).p_value < predictive_check(post, 30, 500).p_value


@given(st.lists(st.floats(0.0, 1.0), min_size=1, max_size=30))
def test_holm_rejects_no_more_than_bonferroni_step_down_allows(ps: list[float]) -> None:
    from pokequant_core.estimation import holm

    rejected = holm(ps, 0.05)
    assert all(p <= 0.05 for p, r in zip(ps, rejected, strict=True) if r)
    bonferroni = [p <= 0.05 / len(ps) for p in ps]
    assert all(r for r, b in zip(rejected, bonferroni, strict=True) if b)
