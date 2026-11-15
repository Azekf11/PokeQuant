"""Tests for the booster model types and their analytic probabilities."""

import json
import math
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from pokequant_core.model import (
    BoosterModel,
    Slot,
    expected_packs,
    p_at_least_one,
    p_card_in_slot,
    p_hit,
    packs_for_probability,
)

FIXTURE = Path(__file__).parent / "fixtures" / "toy_set.json"


@pytest.fixture
def toy() -> BoosterModel:
    return BoosterModel.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


class TestSlot:
    def test_probabilities_must_sum_to_one(self) -> None:
        with pytest.raises(ValidationError, match="sum to 1"):
            Slot(slot_id="s", outcomes={"a": 0.5, "b": 0.4})

    def test_negative_probability_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Slot(slot_id="s", outcomes={"a": 1.2, "b": -0.2})

    def test_empty_slot_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Slot(slot_id="s", outcomes={})

    @given(st.lists(st.floats(min_value=0.01, max_value=1.0), min_size=1, max_size=8))
    def test_any_normalised_distribution_is_accepted(self, weights: list[float]) -> None:
        total = sum(weights)
        slot = Slot(slot_id="s", outcomes={f"r{i}": w / total for i, w in enumerate(weights)})
        assert math.isclose(sum(slot.outcomes.values()), 1.0, abs_tol=1e-9)


class TestBoosterModel:
    def test_toy_fixture_is_valid(self, toy: BoosterModel) -> None:
        assert toy.n_cards_per_pack == 3
        assert toy.rarities == {"common", "rare", "hit"}

    def test_rarity_without_cards_rejected(self) -> None:
        with pytest.raises(ValidationError, match="no card"):
            BoosterModel(
                product_id="p",
                set_id="s",
                version="v",
                cards_by_rarity={"common": ["c1"]},
                slots=[Slot(slot_id="x", outcomes={"common": 0.5, "rare": 0.5})],
            )

    def test_card_listed_under_two_rarities_rejected(self) -> None:
        with pytest.raises(ValidationError, match="more than one rarity"):
            BoosterModel(
                product_id="p",
                set_id="s",
                version="v",
                cards_by_rarity={"common": ["c1"], "rare": ["c1"]},
                slots=[Slot(slot_id="x", outcomes={"common": 0.5, "rare": 0.5})],
            )

    def test_unknown_card_lookup_raises(self, toy: BoosterModel) -> None:
        with pytest.raises(KeyError):
            toy.rarity_of("not-a-card")


class TestAnalyticProbabilities:
    def test_card_in_slot_is_rarity_rate_over_cards_in_rarity(self, toy: BoosterModel) -> None:
        rare_slot = toy.slots[2]
        assert p_card_in_slot(toy, rare_slot, "toy-005") == pytest.approx(0.9 / 2)
        assert p_card_in_slot(toy, rare_slot, "toy-007") == pytest.approx(0.1)
        assert p_card_in_slot(toy, rare_slot, "toy-001") == 0.0

    def test_hit_probability_combines_independent_slots(self, toy: BoosterModel) -> None:
        # toy-001 can appear in both common slots with probability 1/4 each.
        assert p_hit(toy, "toy-001") == pytest.approx(1 - (1 - 0.25) ** 2)
        assert p_hit(toy, "toy-007") == pytest.approx(0.1)

    def test_hit_probability_is_a_probability(self, toy: BoosterModel) -> None:
        for cards in toy.cards_by_rarity.values():
            for card in cards:
                assert 0.0 <= p_hit(toy, card) <= 1.0


def test_packs_until_hit_closed_forms() -> None:
    assert p_at_least_one(0.01, 0) == 0.0
    assert p_at_least_one(0.5, 2) == pytest.approx(0.75)
    assert p_at_least_one(1.0, 3) == 1.0
    assert expected_packs(0.0125) == pytest.approx(80.0)
    assert expected_packs(0.0) == math.inf
    n = packs_for_probability(0.01, 0.5)
    assert p_at_least_one(0.01, n) >= 0.5 > p_at_least_one(0.01, n - 1)
    assert n == 69
    with pytest.raises(ValueError):
        packs_for_probability(0.0, 0.5)
    with pytest.raises(ValueError):
        p_at_least_one(1.2, 1)


@given(p=st.floats(1e-6, 0.999), n=st.integers(0, 2_000))
def test_p_at_least_one_is_a_monotone_probability(p: float, n: int) -> None:
    q = p_at_least_one(p, n)
    assert 0.0 <= q <= 1.0
    assert p_at_least_one(p, n + 1) >= q


@given(p=st.floats(1e-4, 0.99), target=st.floats(0.01, 0.99))
def test_packs_for_probability_is_minimal(p: float, target: float) -> None:
    n = packs_for_probability(p, target)
    assert p_at_least_one(p, n) >= target
    assert n == 1 or p_at_least_one(p, n - 1) < target
