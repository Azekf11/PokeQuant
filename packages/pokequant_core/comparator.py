"""Strategy comparator: E1 budget and E2 target, A (opening) vs B (buying).

Protocol §6-7 and ADR 0011. Every comparison is run on the same posterior draws
and the same simulated openings for all cost scenarios (common random
numbers); scenarios differ only by the value columns.

Random streams: for set i, ``SeedSequence(seed, spawn_key=(i, 0))`` draws the
pull-rate posterior; job j of set i uses ``spawn_key=(i, 1, j)`` for its
aleatory draws and ``(i, 2, j)`` for its run at the posterior-mean model. The
results therefore do not depend on the order in which jobs run.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from pokequant_core.booster import LAYOUTS, SIR, SetPosterior, build_set_posterior
from pokequant_core.experiment import ExperimentConfig
from pokequant_core.metrics import METRICS, constant_metrics, summarise
from pokequant_core.model import BoosterModel, p_hit
from pokequant_core.schemas import CardPrinting, PriceObservation, PullRateObservation
from pokequant_core.simulate import (
    CompiledModel,
    compile_model,
    simulate_e1,
    simulate_e2,
    slot_card_probabilities,
)
from pokequant_core.valuation import CardValues, MissingRule, PriceBasis, select_prices, value_cards

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class SetContext:
    """Everything one set needs: posterior, values per scenario, observed prices."""

    set_id: str
    index: int  # position of the set in the config (seeding)
    posterior: SetPosterior
    scenarios: tuple[str, ...]
    values: tuple[CardValues, ...]  # one per scenario, same order
    observed: frozenset[str]  # pool printings with an observed price
    booster_cost: FloatArray  # one per scenario

    def value_matrix(self, cm: CompiledModel) -> FloatArray:
        """l(c) for every compiled printing, one column per scenario."""
        return np.array(
            [[cv.liquidation[p] for cv in self.values] for p in cm.printing_ids], dtype=np.float64
        )

    def acquisition(self, printing_id: str) -> FloatArray:
        return np.array([cv.acquisition[printing_id] for cv in self.values])


def missing_rule(cfg: ExperimentConfig, scenario: str) -> MissingRule:
    """Adverse uses its own rule; every other scenario the central one (ADR 0011, item 1)."""
    rules = cfg.pricing.missing_price
    return rules.adverse if scenario == "adverse" else rules.central


def build_context(
    cfg: ExperimentConfig,
    set_id: str,
    printings: Sequence[CardPrinting],
    rates: Sequence[PullRateObservation],
    observations: Sequence[PriceObservation],
    *,
    layout: str | None = None,
    prior: float | None = None,
    weight: float | None = None,
) -> SetContext:
    posterior = build_set_posterior(
        set_id,
        [p for p in printings if p.set_id == set_id],
        [r for r in rates if r.set_id == set_id],
        LAYOUTS[layout or cfg.product.layout],
        prior=cfg.estimation.prior if prior is None else prior,
        weight=cfg.estimation.weight if weight is None else weight,
    )
    pricing = cfg.pricing
    basis = PriceBasis(
        pricing.venue,
        pricing.currency,
        pricing.price_type,
        pricing.statistic,
        pricing.condition,
        cfg.data.reference_date,
    )
    prices = select_prices(observations, basis)
    pools = drawable_pools(posterior)
    values = tuple(
        value_cards(prices, pools, s, missing_rule(cfg, s.name)) for s in cfg.cost_scenarios
    )
    observed = frozenset(p for ids in pools.values() for p in ids if p in prices.prices)
    return SetContext(
        set_id=set_id,
        index=cfg.sets.index(set_id),
        posterior=posterior,
        scenarios=tuple(s.name for s in cfg.cost_scenarios),
        values=values,
        observed=observed,
        booster_cost=np.array([s.booster_cost for s in cfg.cost_scenarios]),
    )


def drawable_pools(posterior: SetPosterior) -> dict[str, list[str]]:
    """Pools of the printings a pack can contain under the posterior's layout."""
    names = {s.residual for s in posterior.layout.slots}
    names |= {r for s in posterior.layout.slots for r in s.hits}
    return {k: v for k, v in posterior.pools.items() if k in names}


# --- Strategy B -------------------------------------------------------------


def greedy_basket(cv: CardValues, candidates: frozenset[str], budget: float) -> list[str]:
    """Most expensive observed printings first, each at most once, within the budget."""
    basket, left = [], budget
    for p in sorted(candidates, key=lambda c: (-cv.acquisition[c], c)):
        if cv.acquisition[p] <= left:
            basket.append(p)
            left -= cv.acquisition[p]
    return basket


def basket_profit(cv: CardValues, basket: Sequence[str]) -> float:
    return float(sum(cv.liquidation[p] - cv.acquisition[p] for p in basket))


def choose_target(ctx: SetContext, kind: str) -> str:
    """``top_price`` or ``top_sir`` among observed pool printings (ADR 0011, item 3)."""
    cv = ctx.values[ctx.scenarios.index("central")]
    if kind == "top_price":
        pool = ctx.observed
    elif kind == "top_sir":
        pool = frozenset(ctx.posterior.pools.get(SIR, ())) & ctx.observed
    else:
        raise ValueError(f"unknown target rule {kind!r}")
    if not pool:
        raise ValueError(f"no observed printing for target rule {kind!r} in {ctx.set_id}")
    return min(pool, key=lambda c: (-cv.acquisition[c], c))


# --- Jobs -------------------------------------------------------------------


@dataclass(frozen=True)
class Job:
    estimand: str  # "E1" or "E2"
    label: str  # "n=10", "top_price", ...
    n_packs: int = 0  # E1
    target_rule: str = ""  # E2


def jobs(cfg: ExperimentConfig) -> list[Job]:
    out = [Job("E1", f"n={n}", n_packs=n) for n in cfg.estimands.E1.budgets_in_packs]
    out += [Job("E2", k, target_rule=k) for t in cfg.estimands.E2.targets for k in t]
    return out


def _stream(seed: int, *key: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed, spawn_key=key)))


def posterior_models(ctx: SetContext, seed: int, draws: int) -> list[BoosterModel]:
    return ctx.posterior.sample_models(_stream(seed, ctx.index, 0), draws)


@dataclass
class JobResult:
    set_id: str
    job: Job
    scenarios: tuple[str, ...]
    a_metrics: dict[str, dict[str, list[float]]]  # scenario -> metric -> per draw
    a_se: dict[str, dict[str, list[float]]]  # MC standard errors, per draw
    b_metrics: dict[str, dict[str, float]]  # scenario -> metric (deterministic)
    mean_model: dict[str, dict[str, dict[str, float]]]  # scenario -> {"value", "se"}
    extra: dict[str, Any]


def _simulate(
    job: Job,
    ctx: SetContext,
    cm: CompiledModel,
    values: FloatArray,
    rng: np.random.Generator,
    runs: int,
    target: str,
    n_max: int,
) -> FloatArray:
    """Profit Π of Strategy A, shape (runs, n_scenarios)."""
    if job.estimand == "E1":
        return simulate_e1(
            cm, values, rng, n_packs=job.n_packs, booster_cost=ctx.booster_cost, runs=runs
        )
    a = ctx.acquisition(target)
    cost, _ = simulate_e2(
        cm,
        values,
        rng,
        target=target,
        booster_cost=ctx.booster_cost,
        target_price=a,
        n_max=n_max,
        runs=runs,
    )
    return a - cost


def run_job(
    ctx: SetContext,
    job: Job,
    job_index: int,
    *,
    seed: int,
    draws: int,
    runs: int,
    models: Sequence[BoosterModel] | None = None,
) -> JobResult:
    models = list(models) if models is not None else posterior_models(ctx, seed, draws)
    mean_cm = compile_model(ctx.posterior.mean_model())
    values = ctx.value_matrix(mean_cm)
    extra: dict[str, Any] = {}
    target, n_max = "", 0
    if job.estimand == "E2":
        target = choose_target(ctx, job.target_rule)
        p_mean = p_hit(ctx.posterior.mean_model(), target)
        n_max = math.ceil(3 / p_mean)
        extra.update(target=target, p_hit_mean_model=p_mean, n_max=n_max)
        extra["acquisition"] = dict(
            zip(ctx.scenarios, ctx.acquisition(target).tolist(), strict=True)
        )
        b_profit = dict.fromkeys(ctx.scenarios, 0.0)
    else:
        baskets = {}
        b_profit = {}
        for name, cv, b in zip(ctx.scenarios, ctx.values, ctx.booster_cost, strict=True):
            basket = greedy_basket(cv, ctx.observed, job.n_packs * float(b))
            baskets[name] = len(basket)
            b_profit[name] = basket_profit(cv, basket)
        extra["basket_size"] = baskets
    a_metrics: dict[str, dict[str, list[float]]] = {
        s: {m: [] for m in METRICS} for s in ctx.scenarios
    }
    a_se: dict[str, dict[str, list[float]]] = {s: {m: [] for m in METRICS} for s in ctx.scenarios}
    break_even: list[list[float]] = []
    p_hits: list[float] = []
    aleatory = np.random.SeedSequence(seed, spawn_key=(ctx.index, 1, job_index)).spawn(len(models))
    for model, ss in zip(models, aleatory, strict=True):
        cm = compile_model(model)
        if cm.printing_ids != mean_cm.printing_ids:
            raise RuntimeError("posterior draws changed the printing set")
        profit = _simulate(job, ctx, cm, values, np.random.Generator(np.random.PCG64(ss)), runs,
                           target, n_max)  # fmt: skip
        for k, s in enumerate(ctx.scenarios):
            summary = summarise(profit[:, k])
            for m in METRICS:
                a_metrics[s][m].append(summary.value[m])
                a_se[s][m].append(summary.mc_se[m])
        break_even.append((slot_card_probabilities(cm).sum(axis=0) @ values).tolist())
        if target:
            p_hits.append(p_hit(model, target))
    extra["break_even_booster_price"] = {
        s: [row[k] for row in break_even] for k, s in enumerate(ctx.scenarios)
    }
    if p_hits:
        extra["p_hit"] = p_hits
    profit = _simulate(job, ctx, mean_cm, values, _stream(seed, ctx.index, 2, job_index), runs,
                       target, n_max)  # fmt: skip
    mean_model = {}
    for k, s in enumerate(ctx.scenarios):
        summary = summarise(profit[:, k])
        mean_model[s] = {"value": summary.value, "se": summary.mc_se}
    return JobResult(
        set_id=ctx.set_id,
        job=job,
        scenarios=ctx.scenarios,
        a_metrics=a_metrics,
        a_se=a_se,
        b_metrics={s: constant_metrics(b_profit[s]) for s in ctx.scenarios},
        mean_model=mean_model,
        extra=extra,
    )


def as_arrays(result: JobResult, scenario: str) -> Mapping[str, FloatArray]:
    return {m: np.asarray(v) for m, v in result.a_metrics[scenario].items()}
