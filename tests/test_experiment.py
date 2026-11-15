from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from pokequant_core.experiment import ExperimentConfig, load_experiment

EXPERIMENTS = Path(__file__).resolve().parents[1] / "research/experiments"


@pytest.mark.parametrize("path", sorted(EXPERIMENTS.glob("*.yaml")), ids=lambda p: p.name)
def test_every_experiment_config_is_valid(path: Path) -> None:
    load_experiment(path)


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
