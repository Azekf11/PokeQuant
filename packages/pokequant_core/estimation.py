"""Estimation of pull rates with their uncertainty (protocol §4.2, amendment A4).

- A binary rate (x hits in n packs) has posterior Beta(w·x + a₀, w·(n - x) + a₀).
- A slot with k mutually exclusive outcomes has posterior
  Dirichlet(w·x₁ + a₀, …, w·x_k + a₀), which keeps Σp = 1.

``a₀`` is the prior pseudo-count: ½ for Jeffreys (main analysis), 1 for the
uniform prior (robustness test 8). ``w`` ∈ (0, 1] down-weights counts that were
reconstructed from a published rate and margin rather than tallied: w = 1 uses
them as if exact, w < 1 widens the posterior (robustness, ADR 0010).

The cases x = 0 and x = n need no special treatment: with a₀ > 0 both
posteriors are proper.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats

JEFFREYS = 0.5
UNIFORM = 1.0


def _check_prior_weight(prior: float, weight: float) -> None:
    if prior <= 0:
        raise ValueError(f"prior pseudo-count must be positive (got {prior})")
    if not 0 < weight <= 1:
        raise ValueError(f"weight must lie in (0, 1] (got {weight})")


def _check_counts(hits: float, packs: float) -> None:
    if packs <= 0 or not 0 <= hits <= packs:
        raise ValueError(f"need 0 <= hits <= packs and packs > 0 (got {hits}/{packs})")


@dataclass(frozen=True)
class BetaPosterior:
    a: float
    b: float

    @property
    def mean(self) -> float:
        return self.a / (self.a + self.b)

    def interval(self, level: float = 0.95) -> tuple[float, float]:
        """Equal-tailed credible interval."""
        tail = (1 - level) / 2
        low = float(stats.beta.ppf(tail, self.a, self.b))
        high = float(stats.beta.ppf(1 - tail, self.a, self.b))
        return low, high

    def sample(self, rng: np.random.Generator, size: int) -> NDArray[np.float64]:
        return rng.beta(self.a, self.b, size)


def beta_posterior(
    hits: float, packs: float, *, prior: float = JEFFREYS, weight: float = 1.0
) -> BetaPosterior:
    _check_counts(hits, packs)
    _check_prior_weight(prior, weight)
    return BetaPosterior(weight * hits + prior, weight * (packs - hits) + prior)


@dataclass(frozen=True)
class DirichletPosterior:
    outcomes: tuple[str, ...]
    alpha: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.outcomes) != len(self.alpha) or len(self.outcomes) < 2:
            raise ValueError("need at least two outcomes, one alpha each")
        if len(set(self.outcomes)) != len(self.outcomes):
            raise ValueError("outcome names must be unique")
        if any(a <= 0 for a in self.alpha):
            raise ValueError("every alpha must be positive")

    @property
    def mean(self) -> dict[str, float]:
        total = math.fsum(self.alpha)
        return {o: a / total for o, a in zip(self.outcomes, self.alpha, strict=True)}

    def marginal(self, outcome: str) -> BetaPosterior:
        """The marginal of one outcome is Beta(alpha_k, sum(alpha) - alpha_k)."""
        a = self.alpha[self.outcomes.index(outcome)]
        return BetaPosterior(a, math.fsum(self.alpha) - a)

    def sample(self, rng: np.random.Generator, size: int) -> NDArray[np.float64]:
        """Array of shape (size, k); columns follow ``outcomes``."""
        return rng.dirichlet(self.alpha, size)


def slot_posterior(
    rates: Mapping[str, tuple[float, float]],
    residual: str,
    *,
    prior: float = JEFFREYS,
    weight: float = 1.0,
) -> DirichletPosterior:
    """Dirichlet posterior for one slot from per-pack (hits, packs) of its rare outcomes.

    ``rates`` maps each outcome observed in the registry to (hits, packs);
    ``residual`` names the outcome that fills the slot otherwise (e.g. a
    reverse-holo card). Registry rows of one set have different denominators
    (ADR 0010): they are put on a common, conservative sample size, the
    smallest ``packs`` among the rows, keeping each observed rate. The
    residual count is that sample size minus the other pseudo-counts.
    """
    if not rates:
        raise ValueError("need at least one observed outcome")
    if residual in rates:
        raise ValueError(f"residual outcome {residual!r} is also an observed outcome")
    _check_prior_weight(prior, weight)
    for hits, packs in rates.values():
        _check_counts(hits, packs)
    n = min(packs for _, packs in rates.values())
    pseudo = {o: hits / packs * n for o, (hits, packs) in rates.items()}
    rest = n - math.fsum(pseudo.values())
    if rest <= 0:
        raise ValueError(f"observed rates sum to {1 - rest / n:.4f} >= 1: not one slot")
    outcomes = (*sorted(pseudo), residual)
    counts = [*(pseudo[o] for o in sorted(pseudo)), rest]
    return DirichletPosterior(outcomes, tuple(weight * x + prior for x in counts))


@dataclass(frozen=True)
class HomogeneityTest:
    """Pearson χ² test that several datasets share one rate."""

    chi2: float
    dof: int
    p_value: float
    min_expected: float  # χ² approximation doubtful below 5


def homogeneity_test(counts: Sequence[tuple[float, float]]) -> HomogeneityTest:
    """``counts``: one (hits, packs) pair per dataset, for one set and rarity."""
    if len(counts) < 2:
        raise ValueError("need at least two datasets")
    for hits, packs in counts:
        _check_counts(hits, packs)
    table = np.array([[hits, packs - hits] for hits, packs in counts], dtype=float)
    result = stats.chi2_contingency(table, correction=False)
    return HomogeneityTest(
        chi2=float(result.statistic),
        dof=int(result.dof),
        p_value=float(result.pvalue),
        min_expected=float(np.min(result.expected_freq)),
    )


@dataclass(frozen=True)
class PredictiveCheck:
    """Held-out check of observed hits against a beta-binomial posterior predictive."""

    expected: float
    low: int  # central 95 % predictive interval
    high: int
    p_value: float  # two-sided mid-p
    observed: int

    @property
    def inside(self) -> bool:
        return self.low <= self.observed <= self.high


def predictive_check(posterior: BetaPosterior, hits: int, packs: int) -> PredictiveCheck:
    """Compare ``hits`` in ``packs`` held-out packs with the posterior predictive of ``posterior``.

    The predictive distribution is BetaBinomial(packs, a, b). The two-sided
    mid-p value is 2 min(P(X < x) + P(X = x) / 2, P(X > x) + P(X = x) / 2),
    capped at 1.
    """
    _check_counts(hits, packs)
    dist = stats.betabinom(packs, posterior.a, posterior.b)
    point = float(dist.pmf(hits))
    below = float(dist.cdf(hits)) - point
    above = float(dist.sf(hits))
    p = min(1.0, 2 * min(below + point / 2, above + point / 2))
    low, high = (int(v) for v in dist.interval(0.95))
    return PredictiveCheck(float(dist.mean()), low, high, p, hits)


def holm(p_values: Sequence[float], alpha: float) -> list[bool]:
    """Holm-Bonferroni step-down: True where the hypothesis is rejected."""
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    rejected = [False] * len(p_values)
    for rank, i in enumerate(order):
        if p_values[i] > alpha / (len(p_values) - rank):
            break
        rejected[i] = True
    return rejected
