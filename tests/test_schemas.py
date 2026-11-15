"""Entity schemas (ADR 0008, protocol §3.2)."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from pokequant_core.schemas import (
    CardPrinting,
    CardSet,
    CostScenario,
    PriceObservation,
    PullRateObservation,
    SimulationRun,
)

FETCHED = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)


def price(**overrides: Any) -> PriceObservation:
    fields: dict[str, Any] = {
        "printing_id": "en:sv08:001:normal",
        "condition": "unspecified",
        "currency": "USD",
        "amount": 1.25,
        "price_type": "provider_market",
        "statistic": "market",
        "venue": "tcgplayer",
        "observed_at": FETCHED - timedelta(hours=1),
        "fetched_at": FETCHED,
        "source": "tcgdex",
        "source_url": "https://api.tcgdex.net/v2/en/cards/sv08-001",
    }
    fields.update(overrides)
    return PriceObservation(**fields)


def pull_rate(**overrides: Any) -> PullRateObservation:
    fields: dict[str, Any] = {
        "set_id": "sv08",
        "scope": "pack",
        "rarity": "double rare",
        "cards_in_rarity": 18,
        "hits": 100,
        "packs": 1000,
        "rate": 0.1,
        "ci_low": 0.08,
        "ci_high": 0.12,
        "confidence": "high",
        "counts_reconstructed": True,
        "dataset_ids": ("SSP-001",),
        "source": "pokelife",
        "source_version": "2026-11-13",
        "source_url": "https://www.poke-life.com/data/v/2026-11-13/pull-rates.csv",
    }
    fields.update(overrides)
    return PullRateObservation(**fields)


class TestPriceObservation:
    def test_valid(self) -> None:
        assert price().amount == 1.25

    @pytest.mark.parametrize("amount", [0.0, -1.0])
    def test_non_positive_amount_rejected(self, amount: float) -> None:
        # A missing price is a missing row, never a zero (charter).
        with pytest.raises(ValidationError):
            price(amount=amount)

    def test_unknown_currency_rejected(self) -> None:
        with pytest.raises(ValidationError):
            price(currency="GBP")

    def test_unknown_price_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            price(price_type="guess")

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            price(observed_at=datetime(2026, 11, 14))

    def test_observation_after_fetch_rejected(self) -> None:
        with pytest.raises(ValidationError, match="after it was fetched"):
            price(observed_at=FETCHED + timedelta(days=1))

    def test_malformed_printing_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            price(printing_id="sv08-001")

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            price(colour="blue")


class TestPullRateObservation:
    def test_valid(self) -> None:
        assert pull_rate().rate == 0.1

    def test_rate_outside_interval_rejected(self) -> None:
        with pytest.raises(ValidationError, match="interval"):
            pull_rate(rate=0.2)

    def test_zero_packs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            pull_rate(packs=0)

    def test_needs_at_least_one_dataset(self) -> None:
        with pytest.raises(ValidationError):
            pull_rate(dataset_ids=())

    def test_cards_in_rarity_may_be_unknown(self) -> None:
        assert pull_rate(cards_in_rarity=None).cards_in_rarity is None


class TestCatalogue:
    def test_printing_id_must_match_fields(self) -> None:
        with pytest.raises(ValidationError, match="does not match"):
            CardPrinting(
                printing_id="en:sv08:001:normal",
                card_id="sv08-001",
                set_id="sv08",
                number="001",
                name="Exeggcute",
                rarity="common",
                variant="reverse",
                language="en",
                source="tcgdex",
                fetched_at=FETCHED,
            )

    def test_set_total_not_below_official(self) -> None:
        with pytest.raises(ValidationError):
            CardSet(
                set_id="sv08",
                name="Surging Sparks",
                series="sv",
                release_date=date(2024, 11, 8),
                language="en",
                card_count_official=191,
                card_count_total=100,
                source="tcgdex",
                fetched_at=FETCHED,
            )


class TestScenarioAndRun:
    def test_fee_rates_bounded(self) -> None:
        with pytest.raises(ValidationError):
            CostScenario(
                name="bad",
                currency="USD",
                booster_cost=4.5,
                marketplace_fee_rate=1.2,
                payment_fee_rate=0.03,
                buyer_fee_rate=0.0,
                liquidity_haircut=0.0,
            )

    def test_run_requires_snapshots(self) -> None:
        with pytest.raises(ValidationError):
            SimulationRun(
                run_id="r1",
                seed=1,
                n_trials=10,
                model_version="toy-1",
                data_snapshot_ids=(),
                parameters={},
                created_at=FETCHED,
            )
