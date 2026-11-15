"""Entity schemas — the minimal data model of the charter (§5.3) and protocol (§3.2).

Every record is immutable and rejects unknown fields. A missing value is a
missing record (or ``None`` where the schema allows it), never a zero.
Timestamps must be timezone-aware.

Liquidity observations (sales count, time to sale) are not available from any
open source (data audit, S2); they enter later as labelled scenarios in
``CostScenario``, not as observations.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from pokequant_core.ids import Variant, make_printing_id, parse_printing_id

PriceType = Literal["listing", "provider_market", "sold", "window_median", "estimate"]
Currency = Literal["USD", "EUR"]
Venue = Literal["tcgplayer", "cardmarket"]
Confidence = Literal["high", "moderate", "limited", "estimated"]
Rate = Annotated[float, Field(ge=0.0, le=1.0)]  # a share in [0, 1]


class Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CardSet(Record):
    set_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    series: str = Field(min_length=1)
    release_date: date
    language: str = Field(pattern=r"^[a-z]{2}$")
    card_count_official: int = Field(ge=0)
    card_count_total: int = Field(ge=0)
    source: str
    fetched_at: AwareDatetime

    @model_validator(mode="after")
    def _counts(self) -> CardSet:
        if self.card_count_total < self.card_count_official:
            raise ValueError("card_count_total cannot be below card_count_official")
        return self


class CardPrinting(Record):
    printing_id: str
    card_id: str = Field(min_length=1)  # provider card ID, e.g. TCGdex "sv08-001"
    set_id: str
    number: str
    name: str = Field(min_length=1)
    rarity: str = Field(min_length=1)  # normalised, see ids.normalise_rarity
    variant: Variant
    language: str
    image_ref: str | None = None  # reference only; images are never stored
    source: str
    fetched_at: AwareDatetime

    @model_validator(mode="after")
    def _id_consistent(self) -> CardPrinting:
        expected = make_printing_id(self.language, self.set_id, self.number, self.variant)
        if self.printing_id != expected:
            raise ValueError(
                f"printing_id {self.printing_id!r} does not match fields ({expected!r})"
            )
        return self


class PullRateObservation(Record):
    """Observed rate of a rarity, per pack (``scope="pack"``) or per documented slot."""

    set_id: str
    scope: str = Field(min_length=1)  # "pack" or a slot_id
    rarity: str = Field(min_length=1)
    cards_in_rarity: int | None = Field(default=None, gt=0)
    hits: int = Field(ge=0)
    packs: int = Field(gt=0)
    rate: float = Field(ge=0.0)
    ci_low: float = Field(ge=0.0)
    ci_high: float = Field(ge=0.0)
    confidence: Confidence
    counts_reconstructed: bool
    dataset_ids: tuple[str, ...] = Field(min_length=1)
    source: str
    source_version: str
    source_url: str

    @model_validator(mode="after")
    def _interval(self) -> PullRateObservation:
        if not self.ci_low <= self.rate <= self.ci_high:
            raise ValueError(
                f"rate {self.rate} outside its interval [{self.ci_low}, {self.ci_high}]"
            )
        return self


class PriceObservation(Record):
    printing_id: str
    condition: str = Field(min_length=1)  # "unspecified" when the provider does not say
    grade: str | None = None
    currency: Currency
    amount: float = Field(gt=0.0)
    price_type: PriceType
    statistic: str = Field(min_length=1)  # provider field, e.g. "market", "trend", "avg30"
    venue: Venue
    sample_count: int | None = Field(default=None, ge=0)
    observed_at: AwareDatetime  # provider's own update time
    fetched_at: AwareDatetime
    source: str
    source_url: str
    license_note: str | None = None

    @field_validator("printing_id")
    @classmethod
    def _valid_id(cls, value: str) -> str:
        parse_printing_id(value)
        return value

    @model_validator(mode="after")
    def _chronology(self) -> PriceObservation:
        if self.observed_at > self.fetched_at:
            raise ValueError("price observed after it was fetched: invalid timestamp")
        return self


class CostScenario(Record):
    """Transaction costs and liquidity assumptions (labelled scenario, not data)."""

    name: str = Field(min_length=1)
    currency: Currency
    booster_cost: float = Field(gt=0.0)  # per booster, incl. taxes and shipping
    marketplace_fee_rate: Rate
    payment_fee_rate: Rate
    selling_fixed_fee: float = Field(default=0.0, ge=0.0)  # per sale
    shipping_per_sale: float = Field(default=0.0, ge=0.0)
    buyer_fee_rate: Rate
    buyer_shipping: float = Field(default=0.0, ge=0.0)
    liquidity_haircut: Rate
    grading_fee: float | None = Field(default=None, ge=0.0)  # extension only
    description: str = ""


class SimulationRun(Record):
    run_id: str = Field(min_length=1)
    seed: int = Field(ge=0)
    n_trials: int = Field(gt=0)
    model_version: str = Field(min_length=1)
    data_snapshot_ids: tuple[str, ...] = Field(min_length=1)
    parameters: dict[str, Any]
    created_at: AwareDatetime
