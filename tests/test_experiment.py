from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from pokequant_core.experiment import ExperimentConfig, load_experiment

EXPERIMENTS = Path(__file__).resolve().parents[1] / "research/experiments"


# Parameter files of extensions (they name a base experiment) are not experiments.
CONFIGS = [p for p in sorted(EXPERIMENTS.glob("*.yaml")) if "base_experiment:" not in p.read_text()]


@pytest.mark.parametrize("path", CONFIGS, ids=lambda p: p.name)
def test_every_experiment_config_is_valid(path: Path) -> None:
    load_experiment(path)


def test_sales_benchmark_parameters_point_to_the_main_experiment() -> None:
    bench = yaml.safe_load((EXPERIMENTS / "sales_benchmark.yaml").read_text(encoding="utf-8"))
    assert bench["base_experiment"] == "research/experiments/main.yaml"
    assert (
        bench["q1"]["booster_cost"]
        == load_experiment(EXPERIMENTS / "main.yaml").scenario("central").booster_cost
    )


def test_main_config_matches_the_selected_sets_and_tcgplayer_fees() -> None:
    cfg = load_experiment(EXPERIMENTS / "main.yaml")
    assert cfg.sets == ["sv07", "sv08", "sv10"]  # ADR 0005 selection
    central = cfg.scenario("central")
    assert (central.marketplace_fee_rate, central.payment_fee_rate) == (0.1075, 0.025)
    assert cfg.scenario("adverse").liquidity_haircut > central.liquidity_haircut
    assert "R9b" in {t.id for t in cfg.robustness}


def raw() -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load((EXPERIMENTS / "main.yaml").read_text())
    return data


def test_too_few_tail_samples_is_rejected() -> None:
    data = raw()
    data["simulation"]["aleatory_runs"] = 10_000  # 5 % of 10 000 = 500 < 1000
    with pytest.raises(ValidationError, match="tail samples"):
        ExperimentConfig.model_validate(data)


def test_missing_adverse_scenario_is_rejected() -> None:
    data = raw()
    data["cost_scenarios"] = [s for s in data["cost_scenarios"] if s["name"] != "adverse"]
    with pytest.raises(ValidationError, match="adverse"):
        ExperimentConfig.model_validate(data)


def test_unknown_layout_is_rejected() -> None:
    data = raw()
    data["product"]["layout"] = "made-up"
    with pytest.raises(ValidationError, match="layout"):
        ExperimentConfig.model_validate(data)


def test_extension_config_differs_from_main_only_where_adr_0015_says() -> None:
    from pokequant_core.experiment_run import processed_dir

    main = load_experiment(EXPERIMENTS / "main.yaml")
    ext = load_experiment(EXPERIMENTS / "extension_sets.yaml")
    assert set(main.sets) < set(ext.sets) and len(ext.sets) == 10
    for field in ("product", "pricing", "cost_scenarios", "estimands", "simulation", "estimation"):
        assert getattr(ext, field) == getattr(main, field), field
    root = Path("/repo")
    assert (
        processed_dir(root, main) == root / "data/processed/pokelife-2026-11-13_tcgdex-2026-11-15"
    )
    assert processed_dir(root, ext).name == ext.data.processed


# Frozen configurations: the run id hashes the file bytes, so even a comment edit
# would give a run id different from the one every report and the paper cite.
FROZEN = {"main.yaml": "94de09e8", "extension_sets.yaml": "f3420df5"}


@pytest.mark.parametrize("name", sorted(FROZEN))
def test_frozen_configs_keep_the_hash_of_their_reported_run(name: str) -> None:
    digest = hashlib.sha256((EXPERIMENTS / name).read_bytes()).hexdigest()
    assert digest[:8] == FROZEN[name]
