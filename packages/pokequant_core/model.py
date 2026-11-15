"""Slot-based booster model (protocol §4.1).

A booster is a sequence of slots. Each slot draws a rarity r with probability
P(R_s = r); a card is then drawn within that rarity. Within a rarity, cards are
equally likely unless a later model version states otherwise — this is an
explicit assumption, recorded in ``BoosterModel.assumptions``.

This module only holds the model structure and its closed-form probabilities.
Estimation of the rates (S4) and simulation (S5) live elsewhere.
"""

from __future__ import annotations

import math
from functools import cached_property

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SUM_TOLERANCE = 1e-9


class Slot(BaseModel):
    """One card position in a booster and its rarity distribution P(R_s = r)."""

    model_config = ConfigDict(frozen=True)

    slot_id: str = Field(min_length=1)
    outcomes: dict[str, float] = Field(min_length=1)

    @field_validator("outcomes")
    @classmethod
    def _check_distribution(cls, outcomes: dict[str, float]) -> dict[str, float]:
        if any(not 0.0 <= p <= 1.0 for p in outcomes.values()):
            raise ValueError("slot probabilities must lie in [0, 1]")
        total = math.fsum(outcomes.values())
        if not math.isclose(total, 1.0, abs_tol=SUM_TOLERANCE):
            raise ValueError(f"slot probabilities must sum to 1 (got {total!r})")
        return outcomes


class BoosterModel(BaseModel):
    """A sealed product described as independent slots over a card list."""

    model_config = ConfigDict(frozen=True)

    product_id: str = Field(min_length=1)
    set_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    cards_by_rarity: dict[str, list[str]]
    slots: list[Slot] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_consistency(self) -> BoosterModel:
        seen: dict[str, str] = {}
        for rarity, cards in self.cards_by_rarity.items():
            for card in cards:
                if card in seen:
                    raise ValueError(
                        f"card {card!r} is listed under more than one rarity "
                        f"({seen[card]!r}, {rarity!r})"
                    )
                seen[card] = rarity
        for slot in self.slots:
            for rarity, p in slot.outcomes.items():
                if p > 0 and not self.cards_by_rarity.get(rarity):
                    raise ValueError(
                        f"slot {slot.slot_id!r} can draw rarity {rarity!r}, which has no card"
                    )
        return self

    @property
    def n_cards_per_pack(self) -> int:
        return len(self.slots)

    @property
    def rarities(self) -> set[str]:
        return set(self.cards_by_rarity)

    @cached_property
    def _rarity_index(self) -> dict[str, str]:
        return {card: r for r, cards in self.cards_by_rarity.items() for card in cards}

    def rarity_of(self, card: str) -> str:
        """Rarity of a card; raises ``KeyError`` for an unknown card."""
        return self._rarity_index[card]


def p_card_in_slot(model: BoosterModel, slot: Slot, card: str) -> float:
    """P(C = c in slot s) = P(R_s = rarity(c)) · P(C = c | R_s = rarity(c))."""
    rarity = model.rarity_of(card)
    p_rarity = slot.outcomes.get(rarity, 0.0)
    if p_rarity == 0.0:
        return 0.0
    return p_rarity / len(model.cards_by_rarity[rarity])


def p_hit(model: BoosterModel, card: str) -> float:
    """P(at least one copy of ``card`` in one booster), slots independent.

    P(hit c) = 1 - ∏_s [1 - P(C = c in slot s)]. Valid only under the slot
    independence assumption (protocol §4.1).
    """
    p_miss = math.prod(1.0 - p_card_in_slot(model, slot, card) for slot in model.slots)
    return 1.0 - p_miss


def _check_probability(p: float) -> None:
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"probability must lie in [0, 1] (got {p})")


def p_at_least_one(p: float, n: int) -> float:
    """P(≥ 1 hit in n independent packs) = 1 - (1 - p)ⁿ (protocol §4.5)."""
    _check_probability(p)
    if n < 0:
        raise ValueError(f"number of packs must be non-negative (got {n})")
    if p == 1.0:
        return 1.0 if n > 0 else 0.0
    return -math.expm1(n * math.log1p(-p))


def expected_packs(p: float) -> float:
    """E[N] = 1 / p for N ~ Geometric(p), the number of packs up to the first hit."""
    _check_probability(p)
    if p == 0.0:
        return math.inf
    return 1.0 / p


def packs_for_probability(p: float, target: float) -> int:
    """Smallest n with P(≥ 1 hit in n packs) ≥ ``target``; raises if p = 0."""
    _check_probability(p)
    if not 0.0 < target < 1.0:
        raise ValueError(f"target must lie in (0, 1) (got {target})")
    if p == 0.0:
        raise ValueError("a hit with probability 0 is never reached")
    if p == 1.0:
        return 1
    n = math.ceil(math.log1p(-target) / math.log1p(-p))
    while p_at_least_one(p, n) < target:  # guard against rounding in the logarithms
        n += 1
    while n > 1 and p_at_least_one(p, n - 1) >= target:
        n -= 1
    return n
