"""Sale-price benchmark and weekly price panel (ADR 0014, tag ``prereg-v3``).

Cardmarket's ``avg30`` is the venue's "average sale price over the last 30
days" (EUR). This module converts it to USD at the ECB reference rate,
computes the exact break-even booster price b* in each posterior draw for a
given price basis (Q1), and summarises price ratios with a bootstrap interval
of the median (Q2).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from pokequant_core.comparator import SetContext, build_context, drawable_pools, posterior_models
from pokequant_core.experiment import ExperimentConfig
from pokequant_core.ingest.http import CachedClient
from pokequant_core.schemas import CardPrinting, PriceObservation, PullRateObservation
from pokequant_core.simulate import slot_card_probabilities
from pokequant_core.valuation import PriceBasis, PriceVector, select_prices

ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    "?startPeriod={start}&endPeriod={end}&format=jsondata"
)
HIT_POOLS = (
    "double rare",
    "ace spec rare",
    "illustration rare",
    "ultra rare",
    "special illustration rare",
    "hyper rare",
)


@dataclass(frozen=True)
class FxRate:
    usd_per_eur: float
    rate_date: date
    url: str


def parse_ecb(payload: Mapping[str, Any], on_or_before: date) -> tuple[float, date]:
    """Last ECB observation dated on or before ``on_or_before`` (SDMX-JSON)."""
    dates = [
        date.fromisoformat(v["id"])
        for v in payload["structure"]["dimensions"]["observation"][0]["values"]
    ]
    series = next(iter(payload["dataSets"][0]["series"].values()))
    points = [
        (dates[int(k)], float(v[0]))
        for k, v in series["observations"].items()
        if v and v[0] is not None and dates[int(k)] <= on_or_before
    ]
    if not points:
        raise ValueError(f"no ECB rate on or before {on_or_before}")
    day, rate = max(points)
    return rate, day


def ecb_rate(client: CachedClient, snapshot: date, raw_dir: Path) -> FxRate:
    """ECB USD-per-EUR reference rate of the last published day <= snapshot."""
    start = snapshot - timedelta(days=10)
    url = ECB_URL.format(start=start.isoformat(), end=snapshot.isoformat())
    fetched = client.get_json(url, raw_dir / f"EXR-D.USD.EUR-{snapshot.isoformat()}.json")
    rate, day = parse_ecb(fetched.data, snapshot)
    return FxRate(rate, day, url)


def to_usd(
    observations: Iterable[PriceObservation], statistic: str, fx: FxRate
) -> list[PriceObservation]:
    """Cardmarket observations of ``statistic`` converted to USD (other fields kept)."""
    return [
        o.model_copy(update={"currency": "USD", "amount": round(o.amount * fx.usd_per_eur, 6)})
        for o in observations
        if o.venue == "cardmarket" and o.currency == "EUR" and o.statistic == statistic
    ]


def with_basis(
    cfg: ExperimentConfig, snapshot: date, venue: str, statistic: str
) -> ExperimentConfig:
    """The main configuration valued on another price basis (USD) at ``snapshot``."""
    pricing = cfg.pricing.model_copy(update={"venue": venue, "statistic": statistic})
    data = cfg.data.model_copy(update={"tcgdex": snapshot.isoformat(), "reference_date": snapshot})
    return cfg.model_copy(update={"pricing": pricing, "data": data})


def hit_coverage(ctx: SetContext, prices: PriceVector) -> float:
    pools = drawable_pools(ctx.posterior)
    hits = [p for name in HIT_POOLS for p in pools.get(name, [])]
    return sum(p in prices.prices for p in hits) / len(hits) if hits else 0.0


def break_even_draws(ctx: SetContext, seed: int, draws: int) -> np.ndarray:
    """Exact b* = sum_i P(i in a pack) l(i), shape (draws, scenarios)."""
    rows = []
    for model in posterior_models(ctx, seed, draws):
        cm = ctx.compile(model)
        rows.append(slot_card_probabilities(cm).sum(axis=0) @ ctx.value_matrix(cm))
    return np.asarray(rows)


@dataclass(frozen=True)
class BreakEven:
    set_id: str
    basis: str
    scenario: str
    mean: float
    low: float
    high: float
    coverage: float


def break_even(
    cfg: ExperimentConfig,
    set_id: str,
    printings: Sequence[CardPrinting],
    rates: Sequence[PullRateObservation],
    observations: Sequence[PriceObservation],
    basis_name: str,
    scenarios: Sequence[str],
) -> list[BreakEven]:
    """Posterior mean and 95 % interval of b* for one set and price basis."""
    ctx = build_context(cfg, set_id, printings, rates, observations)
    p = cfg.pricing
    vector = select_prices(
        observations,
        PriceBasis(
            p.venue, p.currency, p.price_type, p.statistic, p.condition, cfg.data.reference_date
        ),
    )
    coverage = hit_coverage(ctx, vector)
    values = break_even_draws(ctx, cfg.simulation.seed, cfg.simulation.epistemic_draws)
    out = []
    for name in scenarios:
        col = values[:, ctx.scenarios.index(name)]
        out.append(
            BreakEven(
                set_id,
                basis_name,
                name,
                float(col.mean()),
                float(np.quantile(col, 0.025)),
                float(np.quantile(col, 0.975)),
                coverage,
            )
        )
    return out


@dataclass(frozen=True)
class RatioSummary:
    n: int
    median: float
    q1: float
    q3: float
    low: float
    high: float


def ratio_summary(ratios: Sequence[float], resamples: int, seed: int) -> RatioSummary:
    """Median, quartiles and a percentile-bootstrap 95 % interval of the median."""
    x = np.asarray(ratios, dtype=np.float64)
    if x.size == 0:
        raise ValueError("no ratio to summarise")
    rng = np.random.Generator(np.random.PCG64(seed))
    boot = np.median(x[rng.integers(0, x.size, size=(resamples, x.size))], axis=1)
    return RatioSummary(
        int(x.size),
        float(np.median(x)),
        float(np.quantile(x, 0.25)),
        float(np.quantile(x, 0.75)),
        float(np.quantile(boot, 0.025)),
        float(np.quantile(boot, 0.975)),
    )


def paired_ratios(num: PriceVector, den: PriceVector, ids: Iterable[str]) -> list[float]:
    """num/den for the printings priced in both vectors."""
    return [num.prices[i] / den.prices[i] for i in ids if i in num.prices and i in den.prices]
