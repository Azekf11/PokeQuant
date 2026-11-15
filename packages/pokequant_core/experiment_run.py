"""``pokequant run <config>``: run every set and job of an experiment, write the results.

Output, under ``results/<run_id>/``:

- ``results.json``: per job, every metric of Strategy A for every epistemic
  draw and scenario, with Monte Carlo standard errors, Strategy B, and the run
  at the posterior-mean model;
- ``comparisons.csv``: one row per set, job, scenario and metric;
- ``hypotheses.json``: the verdicts of H1-H4 (ADR 0011);
- ``manifest.json``: the ``SimulationRun`` record, input hashes, and the hash
  of ``results.json``.
"""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

from pokequant_core import __version__
from pokequant_core.analysis import comparison_rows, hypotheses
from pokequant_core.comparator import SetContext, build_context, jobs, run_job
from pokequant_core.experiment import ExperimentConfig, load_experiment
from pokequant_core.ingest.store import read_records
from pokequant_core.schemas import (
    CardPrinting,
    PriceObservation,
    PullRateObservation,
    SimulationRun,
)


def processed_dir(root: Path, cfg: ExperimentConfig) -> Path:
    name = cfg.data.processed or f"pokelife-{cfg.data.pokelife}_tcgdex-{cfg.data.tcgdex}"
    return root / "data/processed" / name


@cache
def _context(config: Path, root: Path, set_id: str) -> SetContext:
    cfg = load_experiment(config)
    d = processed_dir(root, cfg)
    return build_context(
        cfg,
        set_id,
        read_records(d / "printings.parquet", CardPrinting),
        read_records(d / "pull_rates.parquet", PullRateObservation),
        read_records(d / "prices.parquet", PriceObservation),
    )


def _work(task: tuple[Path, Path, str, int, int, int, int]) -> dict[str, Any]:
    config, root, set_id, job_index, seed, draws, runs = task
    cfg = load_experiment(config)
    ctx = _context(config, root, set_id)
    result = run_job(ctx, jobs(cfg)[job_index], job_index, seed=seed, draws=draws, runs=runs)
    return dataclasses.asdict(result)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_experiment(
    config: Path,
    *,
    root: Path,
    out: Path,
    draws: int | None = None,
    runs: int | None = None,
    workers: int | None = None,
) -> Path:
    cfg = load_experiment(config)
    draws = draws or cfg.simulation.epistemic_draws
    runs = runs or cfg.simulation.aleatory_runs
    seed = cfg.simulation.seed
    config_sha = _sha256(config)
    run_id = f"{cfg.name}-{config_sha[:8]}-k{draws}-m{runs}"
    target = out / run_id
    target.mkdir(parents=True, exist_ok=True)

    tasks = [
        (config.resolve(), root.resolve(), s, j, seed, draws, runs)
        for s in cfg.sets
        for j in range(len(jobs(cfg)))
    ]
    workers = workers or min(len(tasks), os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_work, tasks))

    results_path = target / "results.json"
    results_path.write_text(json.dumps(results, sort_keys=True) + "\n", encoding="utf-8")
    rows = [r for res in results for r in comparison_rows(res)]
    with (target / "comparisons.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (target / "hypotheses.json").write_text(
        json.dumps(hypotheses(results), indent=2) + "\n", encoding="utf-8"
    )

    data = processed_dir(root, cfg)
    data_manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    run = SimulationRun(
        run_id=run_id,
        seed=seed,
        n_trials=draws,
        model_version=f"pokequant {__version__}; layout {cfg.product.layout}",
        data_snapshot_ids=(
            f"pokelife {cfg.data.pokelife}",
            f"tcgdex {cfg.data.tcgdex}",
            f"prices sha256 {data_manifest['outputs']['prices']['sha256']}",
        ),
        parameters={
            "config": str(config.resolve().relative_to(root.resolve())),
            "config_sha256": config_sha,
            "epistemic_draws": draws,
            "aleatory_runs": runs,
            "sets": cfg.sets,
            "jobs": [j.label for j in jobs(cfg)],
            "scenarios": [s.name for s in cfg.cost_scenarios],
        },
        created_at=datetime.now(UTC),
    )
    manifest = {
        "run": run.model_dump(mode="json"),
        "results_sha256": _sha256(results_path),
        "inputs_sha256": {k: v["sha256"] for k, v in data_manifest["outputs"].items()},
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target
