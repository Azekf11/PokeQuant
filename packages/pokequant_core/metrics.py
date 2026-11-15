"""Risk metrics on simulated profits (protocol §7.0).

Π is a profit: losses are negative. VaR and CVaR are reported as *positive
losses*: VaR = -q_alpha(Π), CVaR = -mean of the ceil(alpha N) smallest values.
Each metric comes with a Monte Carlo standard error (batch means).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
QUANTILES = (0.05, 0.25, 0.75, 0.95)


def var(profit: FloatArray, alpha: float = 0.05) -> float:
    return -float(np.quantile(profit, alpha))


def cvar(profit: FloatArray, alpha: float = 0.05) -> float:
    k = math.ceil(alpha * len(profit))
    if k < 1:
        raise ValueError("sample too small for this alpha")
    return -float(np.mean(np.partition(profit, k - 1)[:k]))


def p_loss(profit: FloatArray) -> float:
    return float(np.mean(profit < 0))


def p_gain(profit: FloatArray) -> float:
    """P(Π > 0); in E2, P(K < a(c*)): opening was cheaper than buying."""
    return float(np.mean(profit > 0))


def _quantile(q: float) -> Callable[[FloatArray], float]:
    def metric(x: FloatArray) -> float:
        return float(np.quantile(x, q))

    return metric


METRICS: dict[str, Callable[[FloatArray], float]] = {
    "mean": lambda x: float(np.mean(x)),
    "median": lambda x: float(np.median(x)),
    "p_loss": p_loss,
    "p_gain": p_gain,
    **{f"q{int(q * 100):02d}": _quantile(q) for q in QUANTILES},
    "var05": var,
    "cvar05": cvar,
}


# +1: higher is better; -1: lower is better (ADR 0011, item 5).
DIRECTION: dict[str, int] = {
    **{name: 1 for name in METRICS},
    "p_loss": -1,
    "var05": -1,
    "cvar05": -1,
}


def constant_metrics(value: float) -> dict[str, float]:
    """Metrics of a deterministic profit (Strategy B)."""
    out = {name: value for name in METRICS}
    out.update(p_loss=float(value < 0), p_gain=float(value > 0), var05=-value, cvar05=-value)
    return out


def compare(a: FloatArray, b: FloatArray | float, direction: int) -> tuple[float, str]:
    """Share of epistemic draws in which A is strictly better than B, and the verdict."""
    a = np.asarray(a, dtype=np.float64)
    b_arr = np.broadcast_to(np.asarray(b, dtype=np.float64), a.shape)
    if np.array_equal(a, b_arr):
        return 0.0, "tie"
    share = float(np.mean(direction * (a - b_arr) > 0))
    worse = float(np.mean(direction * (a - b_arr) < 0))
    if share >= 0.90:
        return share, "decisive: A"
    if worse >= 0.90:
        return share, "decisive: B"
    return share, "undetermined"


def batch_se(x: FloatArray, metric: Callable[[FloatArray], float], batches: int = 20) -> float:
    """Monte Carlo standard error of ``metric`` by batch means (protocol §7.0)."""
    if len(x) < batches * 20:
        raise ValueError("too few runs for batch-means standard errors")
    values = [metric(b) for b in np.array_split(x, batches)]
    return float(np.std(values, ddof=1) / math.sqrt(batches))


@dataclass(frozen=True)
class Summary:
    value: dict[str, float]
    mc_se: dict[str, float]


def summarise(profit: FloatArray, batches: int = 20) -> Summary:
    """All metrics of one aleatory sample, with batch-means standard errors.

    Quantile-type metrics computed on batches are biased for small batches; the
    standard error is still the batch-means estimate of their spread.
    """
    return Summary(
        value={name: f(profit) for name, f in METRICS.items()},
        mc_se={name: batch_se(profit, f, batches) for name, f in METRICS.items()},
    )


def epistemic_interval(values: FloatArray, level: float = 0.95) -> tuple[float, float]:
    """Central interval of a metric across epistemic draws."""
    tail = (1 - level) / 2
    low, high = np.quantile(values, [tail, 1 - tail])
    return float(low), float(high)


def share_better(a: FloatArray, b: FloatArray) -> float:
    """Share of epistemic draws in which ``a`` exceeds ``b`` (decision rules, §7.0b)."""
    if a.shape != b.shape:
        raise ValueError("compare the same epistemic draws")
    return float(np.mean(a > b))


def verdict(share: float, threshold: float = 0.90) -> str:
    """'decisive' (≥ 0.90 either way) or 'undetermined' (protocol §7.0b)."""
    if share >= threshold:
        return "decisive: first"
    if share <= 1 - threshold:
        return "decisive: second"
    return "undetermined"
