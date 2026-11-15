"""Experiment configuration (research/experiments/*.yaml), validated on load."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, model_validator

from pokequant_core.booster import LAYOUTS
from pokequant_core.schemas import CostScenario, Currency, Record


class DataRefs(Record):
    pokelife: str
    tcgdex: str
    reference_date: date
    h4_snapshot_date: date


class Product(Record):
    id: str
    layout: str
    non_card_value: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _known_layout(self) -> Product:
        if self.layout not in LAYOUTS:
            raise ValueError(f"unknown layout {self.layout!r}")
        return self


class MissingPrice(Record):
    central: Literal["pool_median", "zero"]
    adverse: Literal["pool_median", "zero"]


class Pricing(Record):
    venue: Literal["tcgplayer", "cardmarket"]
    currency: Currency
    statistic: str
    price_type: Literal["listing", "provider_market", "sold"]
    condition: str
    missing_price: MissingPrice


class E1(Record):
    budgets_in_packs: list[int] = Field(min_length=1)
    basket_rule: str


class E2(Record):
    targets: list[dict[str, str]] = Field(min_length=1)
    cap_rule: str


class Estimands(Record):
    E1: E1
    E2: E2


class Simulation(Record):
    seed: int = Field(ge=0)
    epistemic_draws: int = Field(gt=0)
    aleatory_runs: int = Field(gt=0)
    alpha: float = Field(gt=0.0, lt=0.5)

    @model_validator(mode="after")
    def _enough_tail_samples(self) -> Simulation:
        if self.alpha * self.aleatory_runs < 1000:  # protocol 7.0
            raise ValueError("fewer than 1000 tail samples per epistemic draw")
        return self


class Estimation(Record):
    prior: float = Field(gt=0.0)
    weight: float = Field(gt=0.0, le=1.0)


class RobustnessTest(Record):
    id: str
    test: str


class ExperimentConfig(Record):
    name: str
    description: str
    sets: list[str] = Field(min_length=1)
    data: DataRefs
    product: Product
    pricing: Pricing
    liquidation_rule: str
    acquisition_rule: str
    cost_scenarios: list[CostScenario] = Field(min_length=1)
    estimands: Estimands
    simulation: Simulation
    estimation: Estimation
    robustness: list[RobustnessTest]

    @model_validator(mode="after")
    def _consistency(self) -> ExperimentConfig:
        names = [s.name for s in self.cost_scenarios]
        if len(set(names)) != len(names):
            raise ValueError("cost scenario names must be unique")
        if not {"central", "adverse"} <= set(names):
            raise ValueError("central and adverse cost scenarios are required (protocol 7.1)")
        if any(s.currency != self.pricing.currency for s in self.cost_scenarios):
            raise ValueError("cost scenarios must use the pricing currency")
        ids = [t.id for t in self.robustness]
        if len(set(ids)) != len(ids):
            raise ValueError("robustness IDs must be unique")
        return self

    def scenario(self, name: str) -> CostScenario:
        return next(s for s in self.cost_scenarios if s.name == name)


def load_experiment(path: Path) -> ExperimentConfig:
    return ExperimentConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
