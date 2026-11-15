"""Robustness tests R1-R13 (protocol §7.2, ADR 0012).

A *run* is one computation: a set context (posterior, value columns) and a
number of aleatory runs. A *variant* is what the report shows: the results of
one run, with some main scenarios replaced by value columns of that run. Value
variants (R1, R2, R3, R10) share the run ``values``, so they are valued on the
very same simulated openings as the baseline (common random numbers).

Output of ``pokequant robustness <config>``, under
``results/<main run_id>/robustness/``: one folder per run with its
``results.json``, and a ``manifest.json`` listing runs and variants.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any, Literal

import numpy as np

from pokequant_core import __version__
from pokequant_core.analysis import comparison_rows, hypotheses
from pokequant_core.booster import DOUBLE_RARE, SetPosterior, build_pools
from pokequant_core.comparator import Column, SetContext, build_context, jobs, run_job
from pokequant_core.experiment import ExperimentConfig, load_experiment
from pokequant_core.experiment_run import processed_dir
from pokequant_core.ingest.store import read_records
from pokequant_core.metrics import DIRECTION, compare, epistemic_interval
from pokequant_core.model import BoosterModel
from pokequant_core.schemas import CardPrinting, PriceObservation, PullRateObservation

Result = dict[str, Any]
MAIN_SCENARIOS = ("gross", "central", "adverse")
R11_PRINTING = "en:sv07:067:holo"  # Dachsbun ex, Stellar Crown
R11_WEIGHTS = (76, 121)  # per-card pull rates 0.76 % vs 1.21 % (TCGplayer article)
CONCLUSION_METRICS = ("mean", "median", "cvar05")


@dataclass(frozen=True)
class RunSpec:
    name: str
    layout: str | None = None
    prior: float | None = None
    weight: float | None = None
    exclude_top: float = 0.0
    short_print: bool = False
    bound: Literal["", "low", "high"] = ""
    runs: int | None = None
    estimands: tuple[str, ...] = ("E1", "E2")
    sets: tuple[str, ...] | None = None
    columns: tuple[Column, ...] = ()


@dataclass(frozen=True)
class Variant:
    id: str  # robustness test ID of the config, or "baseline"
    label: str
    run: str
    replaces: Mapping[str, str] = field(default_factory=dict)  # main scenario -> column

    @property
    def single_model(self) -> bool:
        return self.run.startswith("R4")


def _scaled(cfg: ExperimentConfig, name: str, base: str, **update: float) -> Column:
    s = cfg.scenario(base).model_copy(update={"name": name, **update})
    return Column(s, base)


def run_specs(cfg: ExperimentConfig) -> list[RunSpec]:
    central = cfg.scenario("central")
    costs = (
        "marketplace_fee_rate",
        "payment_fee_rate",
        "selling_fixed_fee",
        "shipping_per_sale",
        "buyer_shipping",
    )
    columns = (
        *(
            Column(cfg.scenario(s).model_copy(update={"name": f"R1|{s}"}), s, "statistics_median")
            for s in MAIN_SCENARIOS
        ),
        _scaled(cfg, "R2|h=0.30", "central", liquidity_haircut=0.30),
        _scaled(cfg, "R2|h=0.50", "central", liquidity_haircut=0.50),
        *(
            _scaled(cfg, f"R3|x{k}", "central", **{c: getattr(central, c) * k for c in costs})
            for k in (0.5, 1.5)
        ),
        _scaled(cfg, "R10|h=0.27", "central", liquidity_haircut=0.27),
    )
    return [
        RunSpec("values", columns=columns),
        RunSpec("R4-low", bound="low"),
        RunSpec("R4-high", bound="high"),
        RunSpec("R5", exclude_top=0.01, estimands=("E1",)),
        *(RunSpec(f"R7-m{m}", runs=m) for m in (1_000, 10_000, 100_000)),
        RunSpec("R8", prior=1.0),
        RunSpec("R9b", weight=0.5),
        RunSpec("R11", short_print=True, sets=("sv07",)),
        RunSpec("R12", layout="hyper-in-rare-slot"),
    ]


def variants() -> list[Variant]:
    return [
        Variant("baseline", "main specification", "values"),
        Variant(
            "R1",
            "median of TCGplayer statistics (indicative)",
            "values",
            {s: f"R1|{s}" for s in MAIN_SCENARIOS},
        ),
        Variant("R2", "haircut 0.30", "values", {"central": "R2|h=0.30"}),
        Variant("R2", "haircut 0.50", "values", {"central": "R2|h=0.50"}),
        Variant("R3", "selling and shipping costs x0.5", "values", {"central": "R3|x0.5"}),
        Variant("R3", "selling and shipping costs x1.5", "values", {"central": "R3|x1.5"}),
        Variant("R4", "pull rates at lower 95 % bounds", "R4-low"),
        Variant("R4", "pull rates at upper 95 % bounds", "R4-high"),
        Variant("R5", "top 1 % printings excluded (E1)", "R5"),
        *(Variant("R7", f"{m:,} runs per draw", f"R7-m{m}") for m in (1_000, 10_000, 100_000)),
        Variant("R8", "uniform prior", "R8"),
        Variant("R9b", "half sample size (w = 0.5)", "R9b"),
        Variant(
            "R10",
            "haircut 0.27 (Heck et al. 2026, transferred)",
            "values",
            {"central": "R10|h=0.27"},
        ),
        Variant("R11", "Dachsbun ex short print (sv07)", "R11"),
        Variant("R12", "Hyper Rare in the rare slot", "R12"),
    ]


# --- Models -------------------------------------------------------------------


def bound_model(posterior: SetPosterior, which: Literal["low", "high"]) -> BoosterModel:
    """Every hit rarity at a bound of its marginal 95 % interval; the residual takes the rest."""
    probs: dict[str, list[float]] = {}
    for spec in posterior.layout.slots:
        post = posterior.posteriors.get(spec.slot_id)
        if post is None:
            continue
        values = {}
        for o in post.outcomes:
            if o != spec.residual:
                low, high = post.marginal(o).interval(0.95)
                values[o] = low if which == "low" else high
        values[spec.residual] = 1.0 - math.fsum(values.values())
        if values[spec.residual] <= 0:
            raise ValueError(f"{posterior.set_id} {spec.slot_id}: bounds leave no residual")
        probs[spec.slot_id] = [values[o] for o in post.outcomes]
    return posterior.model(probs)


def short_print_weights(printings: Sequence[CardPrinting], set_id: str) -> dict[str, int]:
    """R11: pool weights of the sv07 Double Rares (Dachsbun ex 76, every other 121)."""
    if set_id != R11_PRINTING.split(":")[1]:
        return {}
    pool = build_pools(p for p in printings if p.set_id == set_id)[DOUBLE_RARE]
    if R11_PRINTING not in pool:
        raise ValueError(f"{R11_PRINTING} is not a Double Rare of {set_id}")
    short, other = R11_WEIGHTS
    return {p: short if p == R11_PRINTING else other for p in pool}


# --- Running ------------------------------------------------------------------


def spec_context(
    cfg: ExperimentConfig,
    spec: RunSpec,
    set_id: str,
    printings: Sequence[CardPrinting],
    rates: Sequence[PullRateObservation],
    observations: Sequence[PriceObservation],
) -> SetContext:
    return build_context(
        cfg,
        set_id,
        printings,
        rates,
        observations,
        layout=spec.layout,
        prior=spec.prior,
        weight=spec.weight,
        columns=spec.columns,
        exclude_top=spec.exclude_top,
        multiplicity=short_print_weights(printings, set_id) if spec.short_print else None,
    )


@cache
def _context(config: Path, root: Path, spec_name: str, set_id: str) -> SetContext:
    cfg = load_experiment(config)
    spec = next(s for s in run_specs(cfg) if s.name == spec_name)
    d = processed_dir(root, cfg)
    return spec_context(
        cfg,
        spec,
        set_id,
        read_records(d / "printings.parquet", CardPrinting),
        read_records(d / "pull_rates.parquet", PullRateObservation),
        read_records(d / "prices.parquet", PriceObservation),
    )


Task = tuple[Path, Path, str, str, int, int, int, int]


def _work(task: Task) -> dict[str, Any]:
    config, root, spec_name, set_id, job_index, seed, draws, runs = task
    cfg = load_experiment(config)
    spec = next(s for s in run_specs(cfg) if s.name == spec_name)
    ctx = _context(config, root, spec_name, set_id)
    models = [bound_model(ctx.posterior, spec.bound)] if spec.bound else None
    result = run_job(
        ctx, jobs(cfg)[job_index], job_index, seed=seed, draws=draws, runs=runs, models=models
    )
    return {"run": spec_name, **dataclasses.asdict(result)}


def _cost(task: Task, cfg: ExperimentConfig) -> float:
    _, _, spec_name, _, job_index, _, draws, runs = task
    job = jobs(cfg)[job_index]
    weight = 30.0 if job.estimand == "E2" else job.n_packs / 10 + 1
    return (1 if spec_name.startswith("R4") else draws) * runs * weight


def run_robustness(
    config: Path,
    *,
    root: Path,
    out: Path,
    only: Sequence[str] | None = None,
    draws: int | None = None,
    runs: int | None = None,
    workers: int | None = None,
) -> Path:
    """Run every robustness run spec (or ``only`` those) and write their results."""
    cfg = load_experiment(config)
    draws = draws or cfg.simulation.epistemic_draws
    main_runs = runs or cfg.simulation.aleatory_runs
    config_sha = hashlib.sha256(config.read_bytes()).hexdigest()
    target = out / f"{cfg.name}-{config_sha[:8]}-k{draws}-m{main_runs}" / "robustness"
    specs = [s for s in run_specs(cfg) if only is None or s.name in only]
    tasks: list[Task] = []
    spec_runs = {}
    for spec in specs:
        m = spec.runs or main_runs
        if runs and spec.runs:  # smoke tests: scale R7 down with the main runs
            m = max(1, spec.runs * runs // cfg.simulation.aleatory_runs)
        spec_runs[spec.name] = m
        for set_id in spec.sets or cfg.sets:
            for j, job in enumerate(jobs(cfg)):
                if job.estimand in spec.estimands:
                    tasks.append(
                        (
                            config.resolve(),
                            root.resolve(),
                            spec.name,
                            set_id,
                            j,
                            cfg.simulation.seed,
                            draws,
                            m,
                        )
                    )
    tasks.sort(key=lambda t: -_cost(t, cfg))
    workers = workers or min(len(tasks), os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_work, tasks))
    labels = [j.label for j in jobs(cfg)]
    files = {}
    for spec in specs:
        mine = sorted(
            (r for r in results if r["run"] == spec.name),
            key=lambda r: (cfg.sets.index(r["set_id"]), labels.index(r["job"]["label"])),
        )
        folder = target / spec.name
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "results.json"
        path.write_text(json.dumps(mine, sort_keys=True) + "\n", encoding="utf-8")
        files[spec.name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "spec": dataclasses.asdict(spec) | {"columns": [c.scenario.name for c in spec.columns]},
            "aleatory_runs": spec_runs[spec.name],
        }
    manifest_path = target / "manifest.json"
    previous = (
        json.loads(manifest_path.read_text(encoding="utf-8"))["runs"]
        if manifest_path.exists()
        else {}
    )
    manifest = {
        "config": str(config.resolve().relative_to(root.resolve())),
        "config_sha256": config_sha,
        "seed": cfg.simulation.seed,
        "epistemic_draws": draws,
        "pokequant": __version__,
        "created_at": datetime.now(UTC).isoformat(),
        "runs": previous | files,
        "variants": [dataclasses.asdict(v) for v in variants()],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", "utf-8")
    return target


# --- Reading results ----------------------------------------------------------

_SCENARIO_KEYED = ("a_metrics", "a_se", "b_metrics", "mean_model")
_EXTRA_KEYED = ("break_even_booster_price", "acquisition", "basket_size")


def relabel(result: Result, replaces: Mapping[str, str]) -> Result:
    """A job result restricted to the main scenarios, some taken from value columns."""

    def pick(d: Mapping[str, Any]) -> dict[str, Any]:
        return {s: d[replaces.get(s, s)] for s in MAIN_SCENARIOS if replaces.get(s, s) in d}

    out = {k: v for k, v in result.items() if k not in _SCENARIO_KEYED}
    out.update({k: pick(result[k]) for k in _SCENARIO_KEYED})
    out["scenarios"] = [s for s in MAIN_SCENARIOS if replaces.get(s, s) in result["scenarios"]]
    out["extra"] = {k: pick(v) if k in _EXTRA_KEYED else v for k, v in result["extra"].items()}
    return out


def variant_results(folder: Path, variant: Variant) -> list[Result]:
    raw = json.loads((folder / variant.run / "results.json").read_text(encoding="utf-8"))
    return [relabel(r, variant.replaces) for r in raw]


def _verdict(a: Sequence[float], se: Sequence[float], b: float, metric: str, single: bool) -> str:
    """ADR 0011 over draws; for one model, |A - B| > 3 Monte Carlo SE (ADR 0012, item 3)."""
    if not single:
        return compare(np.asarray(a), b, DIRECTION[metric])[1]
    diff = a[0] - b
    if diff == 0:
        return "tie"
    if abs(diff) <= 3 * se[0]:
        return "undetermined"
    return "decisive: A" if DIRECTION[metric] * diff > 0 else "decisive: B"


def check_conclusions(
    results: Sequence[Result], booster_cost: float, *, single_model: bool = False
) -> dict[str, Any]:
    """C1-C3 of ADR 0012 for one variant, with the cases that fail."""
    c1: list[str] = []
    c2: list[str] = []
    c3: list[str] = []
    break_even: dict[str, dict[str, tuple[float, float, float]]] = {}
    for res in results:
        sid, label = res["set_id"], res["job"]["label"]
        if "central" not in res["scenarios"]:
            continue
        a = res["a_metrics"]["central"]
        se = res["a_se"]["central"]
        if res["job"]["estimand"] == "E1":
            if single_model:
                upper = a["mean"][0] + 1.96 * se["mean"][0]
            else:
                upper = epistemic_interval(np.asarray(a["mean"]))[1]
            if not upper < 0:
                c1.append(f"{sid} {label}")
            if sid not in break_even:
                be = res["extra"]["break_even_booster_price"]
                break_even[sid] = {}
                for s in ("central", "gross"):
                    if s not in be:
                        continue
                    x = np.asarray(be[s])
                    if single_model:
                        low = high = float(x[0])
                    else:
                        low, high = epistemic_interval(x)
                    break_even[sid][s] = (float(x.mean()), low, high)
                    if not high < booster_cost:
                        c2.append(f"{sid} {s}")
        if res["job"]["estimand"] == "E2" or res["job"]["n_packs"] >= 10:
            for m in CONCLUSION_METRICS:
                b = res["b_metrics"]["central"][m]
                v = _verdict(a[m], se[m], b, m, single_model)
                if v != "decisive: B":
                    c3.append(f"{sid} {label} {m}: {v}")
    return {
        "C1": {"holds": not c1, "fails": c1},
        "C2": {"holds": not c2, "fails": c2},
        "C3": {"holds": not c3, "fails": c3},
        "break_even": break_even,
    }


def hypothesis_statuses(results: Sequence[Result]) -> dict[str, str]:
    full = [r for r in results if set(MAIN_SCENARIOS) <= set(r["scenarios"])]
    return {h: v["status"] for h, v in hypotheses(full).items()} if full else {}


def advantage(results: Sequence[Result], label: str, scenario: str = "central") -> dict[str, Any]:
    """Posterior mean of mean Π_A - Π_B for one E1 job, per set."""
    out = {}
    for res in results:
        if res["job"]["label"] == label and scenario in res["scenarios"]:
            a = np.asarray(res["a_metrics"][scenario]["mean"])
            out[res["set_id"]] = float(a.mean() - res["b_metrics"][scenario]["mean"])
    return out


def central_rows(results: Sequence[Result]) -> list[dict[str, Any]]:
    return [r for res in results for r in comparison_rows(res) if r["scenario"] == "central"]
