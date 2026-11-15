"""Card valuation: typed prices, missing-price rules, liquidation and acquisition values.

Protocol §5-6.1 and model_spec. A price vector always carries its *basis*
(venue, currency, price type, statistic, condition, reference date); vectors with
different bases are never combined, and an asking price (``listing``) is never
used as a transaction value.

- p(c): the provider price of printing c at the reference date t0;
- l(c) = max(0, p(c) (1 - h) (1 - f_m - f_p) - f_0 - s): what a seller receives,
  one card per sale (``CostScenario``);
- a(c) = p(c) (1 + f_b) + s_b: what a buyer pays, one card per order.

Always l(c) <= p(c) <= a(c).
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from pokequant_core.schemas import CostScenario, Currency, PriceObservation, PriceType, Venue

MissingRule = Literal["pool_median", "zero", "exclude"]
# Price types that may stand for a transaction value. "listing" (asking price)
# and "estimate" never do (protocol §5.1).
TRANSACTION_TYPES: frozenset[str] = frozenset({"provider_market", "sold", "window_median"})


class PriceBasisError(ValueError):
    """Prices of different kinds would be mixed, or misused."""


@dataclass(frozen=True)
class PriceBasis:
    venue: Venue
    currency: Currency
    price_type: PriceType
    statistic: str
    condition: str
    reference_date: date  # t0: no observation after the end of this day (UTC) is used


@dataclass(frozen=True)
class PriceVector:
    """Observed prices of one basis; a printing without an observation is absent."""

    basis: PriceBasis
    prices: Mapping[str, float]
    observed_at: Mapping[str, datetime] = field(default_factory=dict)

    def __post_init__(self) -> None:
        bad = [p for p, v in self.prices.items() if not v > 0]
        if bad:
            raise ValueError(f"prices must be positive (missing is absent, not 0): {bad[:3]}")


def _end_of_day(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min, tzinfo=UTC)


def select_prices(
    observations: Iterable[PriceObservation], basis: PriceBasis, *, max_age_days: int = 7
) -> PriceVector:
    """The observations matching ``basis`` exactly, without look-ahead or stale values.

    An observation made after t0, or more than ``max_age_days`` before it, is
    left out (the printing is then missing). Two observations of one printing on
    one basis are an error.
    """
    end = _end_of_day(basis.reference_date)
    start = end - timedelta(days=max_age_days + 1)
    prices: dict[str, float] = {}
    seen: dict[str, datetime] = {}
    for o in observations:
        if (o.venue, o.currency, o.price_type, o.statistic, o.condition) != (
            basis.venue,
            basis.currency,
            basis.price_type,
            basis.statistic,
            basis.condition,
        ):
            continue
        if o.grade is not None or not start <= o.observed_at < end:
            continue
        if o.printing_id in prices:
            raise PriceBasisError(f"two prices for {o.printing_id} on one basis")
        prices[o.printing_id] = o.amount
        seen[o.printing_id] = o.observed_at
    return PriceVector(basis, prices, seen)


def window_median(vectors: Sequence[PriceVector]) -> PriceVector:
    """Median over several dated snapshots of one basis (price type ``window_median``).

    The result is dated at the last snapshot; only printings priced in a strict
    majority of the snapshots are kept.
    """
    if not vectors:
        raise ValueError("need at least one snapshot")
    first = vectors[0].basis
    for v in vectors:
        b = v.basis
        if (b.venue, b.currency, b.price_type, b.statistic, b.condition) != (
            first.venue,
            first.currency,
            first.price_type,
            first.statistic,
            first.condition,
        ):
            raise PriceBasisError("window median over snapshots of different bases")
    if len({v.basis.reference_date for v in vectors}) != len(vectors):
        raise ValueError("snapshots must have distinct dates")
    last = max(v.basis.reference_date for v in vectors)
    ids = {p for v in vectors for p in v.prices}
    prices = {}
    for p in sorted(ids):
        values = [v.prices[p] for v in vectors if p in v.prices]
        if 2 * len(values) > len(vectors):
            prices[p] = float(statistics.median(values))
    basis = PriceBasis(
        first.venue, first.currency, "window_median", first.statistic, first.condition, last
    )
    return PriceVector(basis, prices)


def impute(
    prices: PriceVector, pools: Mapping[str, Sequence[str]], rule: MissingRule
) -> tuple[dict[str, float], frozenset[str]]:
    """Price of every pool printing, and the set of printings whose price was imputed.

    ``pool_median``: median observed price of the printing's pool;
    ``zero``: 0 (prudent scenario only); ``exclude``: missing printings are left
    out, and the caller must not simulate a model that can draw them.
    """
    out: dict[str, float] = {}
    imputed: set[str] = set()
    for name, members in pools.items():
        observed = [prices.prices[p] for p in members if p in prices.prices]
        for p in members:
            if p in prices.prices:
                out[p] = prices.prices[p]
                continue
            if rule == "exclude":
                continue
            if rule == "zero":
                out[p] = 0.0
            elif not observed:
                raise ValueError(f"pool {name!r} has no observed price to impute from")
            else:
                out[p] = float(statistics.median(observed))
            imputed.add(p)
    return out, frozenset(imputed)


def liquidation_value(price: float, s: CostScenario) -> float:
    """l(c): net amount received by a seller for one card sold alone."""
    net = (
        price * (1 - s.liquidity_haircut) * (1 - s.marketplace_fee_rate - s.payment_fee_rate)
        - s.selling_fixed_fee
        - s.shipping_per_sale
    )
    return max(0.0, net)


def acquisition_price(price: float, s: CostScenario) -> float:
    """a(c): total paid by a buyer for one card bought alone."""
    return price * (1 + s.buyer_fee_rate) + s.buyer_shipping


@dataclass(frozen=True)
class CardValues:
    """Values of every pool printing under one price basis, cost scenario and missing rule."""

    basis: PriceBasis
    scenario: str
    missing_rule: MissingRule
    price: dict[str, float]  # p(c), observed or imputed
    imputed: frozenset[str]
    liquidation: dict[str, float]  # l(c)
    acquisition: dict[str, float]  # a(c); meaningful for observed prices only


def value_cards(
    prices: PriceVector,
    pools: Mapping[str, Sequence[str]],
    scenario: CostScenario,
    rule: MissingRule,
) -> CardValues:
    if prices.basis.price_type not in TRANSACTION_TYPES:
        raise PriceBasisError(
            f"price type {prices.basis.price_type!r} is not a transaction value (protocol §5.1)"
        )
    if prices.basis.currency != scenario.currency:
        raise PriceBasisError(
            f"prices in {prices.basis.currency}, scenario {scenario.name!r} in {scenario.currency}"
        )
    price, imputed = impute(prices, pools, rule)
    return CardValues(
        basis=prices.basis,
        scenario=scenario.name,
        missing_rule=rule,
        price=price,
        imputed=imputed,
        liquidation={p: liquidation_value(v, scenario) for p, v in price.items()},
        acquisition={p: acquisition_price(v, scenario) for p, v in price.items()},
    )


def sale_threshold(s: CostScenario) -> float:
    """Price below which a card sold alone is worth nothing to the seller: l(c) = 0."""
    keep = (1 - s.liquidity_haircut) * (1 - s.marketplace_fee_rate - s.payment_fee_rate)
    if keep <= 0:
        return float("inf")
    return (s.selling_fixed_fee + s.shipping_per_sale) / keep
