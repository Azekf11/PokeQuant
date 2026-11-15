"""Nested Monte Carlo runs with reproducible seeding and a run manifest (A5).

Outer loop: K epistemic draws of the slot probabilities. Inner loop: M
aleatory runs at fixed probabilities. Every draw gets its own child stream from
one ``SeedSequence``, so results do not depend on the order of execution.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from pokequant_core import __version__
from pokequant_core.booster import SetPosterior
from pokequant_core.metrics import METRICS, Summary, summarise
from pokequant_core.model import BoosterModel
from pokequant_core.schemas import SimulationRun

FloatArray = NDArray[np.float64]
Experiment = Callable[[BoosterModel, np.random.Generator], FloatArray]


def generators(seed: int, n: int) -> list[np.random.Generator]:
    """``n`` independent PCG64 generators derived from one seed."""
    return [np.random.Generator(np.random.PCG64(s)) for s in np.random.SeedSequence(seed).spawn(n)]


@dataclass(frozen=True)
class NestedResult:
    summaries: list[Summary]  # one per epistemic draw
    run: SimulationRun

    def metric(self, name: str) -> FloatArray:
        """A metric across epistemic draws."""
        return np.array([s.value[name] for s in self.summaries])


def run_nested(
    posterior: SetPosterior,
    experiment: Experiment,
    *,
    seed: int,
    epistemic_draws: int,
    data_snapshot_ids: Sequence[str],
    parameters: dict[str, Any],
    run_id: str,
) -> NestedResult:
    """Run ``experiment`` (one aleatory sample of profits) on each posterior draw.

    Draw 0 of the parameter stream draws the slot probabilities; each epistemic
    draw then has its own aleatory stream.
    """
    param_rng, *aleatory = generators(seed, epistemic_draws + 1)
    models = posterior.sample_models(param_rng, epistemic_draws)
    summaries = [summarise(experiment(m, rng)) for m, rng in zip(models, aleatory, strict=True)]
    run = SimulationRun(
        run_id=run_id,
        seed=seed,
        n_trials=epistemic_draws,
        model_version=f"pokequant {__version__}; {models[0].version}",
        data_snapshot_ids=tuple(data_snapshot_ids),
        parameters={
            **parameters,
            "set_id": posterior.set_id,
            "prior": posterior.prior,
            "weight": posterior.weight,
            "metrics": sorted(METRICS),
        },
        created_at=datetime.now(UTC),
    )
    return NestedResult(summaries, run)


def write_manifest(result: NestedResult, path: Path) -> str:
    """Write the run manifest and per-draw metrics as JSON; return the results hash.

    The hash covers the results only (not the creation time), so identical
    seed, data and model give an identical hash.
    """
    results = [{"value": s.value, "mc_se": s.mc_se} for s in result.summaries]
    payload = json.dumps(results, sort_keys=True).encode()
    digest = hashlib.sha256(payload).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"run": result.run.model_dump(mode="json"), "results_sha256": digest, "draws": results},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return digest
