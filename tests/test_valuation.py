"""Valuation: typed prices, missing-price rules, l(c) and a(c) (protocol §5-6.1)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from test_schemas import FETCHED, price

from pokequant_core.experiment import load_experiment
from pokequant_core.schemas import CostScenario
from pokequant_core.valuation import (
    PriceBasis,
    PriceBasisError,
    PriceVector,
    acquisition_price,
    impute,
    liquidation_value,
    sale_threshold,
    select_prices,
    value_cards,
    window_median,
)

ROOT = Path(__file__).resolve().parents[1]
T0 = date(2026, 11, 15)
BASIS = PriceBasis("tcgplayer", "USD", "provider_market", "market", "unspecified", T0)
SCENARIOS = {
    s.name: s for s in load_experiment(ROOT / "research/experiments/main.yaml").cost_scenarios
}


def scenario(**overrides: float) -> CostScenario:
    return SCENARIOS["central"].model_copy(update=overrides)


def test_select_keeps_only_the_exact_basis() -> None:
    obs = [
        price(printing_id="en:sv08:001:normal", amount=1.0),
        price(printing_id="en:sv08:002:normal", amount=2.0, statistic="low", price_type="listing"),
        price(printing_id="en:sv08:003:normal", amount=3.0, currency="EUR", venue="cardmarket"),
        price(printing_id="en:sv08:004:normal", amount=4.0, grade="PSA 10"),
    ]
    v = select_prices(obs, BASIS)
    assert dict(v.prices) == {"en:sv08:001:normal": 1.0}


def test_select_refuses_look_ahead_and_stale_prices() -> None:
    late = price(observed_at=FETCHED + timedelta(days=2), fetched_at=FETCHED + timedelta(days=2))
    old = price(printing_id="en:sv08:002:normal", observed_at=FETCHED - timedelta(days=30))
    assert select_prices([late, old], BASIS).prices == {}


def test_select_rejects_duplicates() -> None:
    with pytest.raises(PriceBasisError):
        select_prices([price(), price(amount=2.0)], BASIS)


def test_missing_is_absent_never_zero() -> None:
    with pytest.raises(ValueError, match="missing is absent"):
        PriceVector(BASIS, {"en:sv08:001:normal": 0.0})


def test_listing_prices_are_never_transaction_values() -> None:
    listing = PriceVector(PriceBasis("tcgplayer", "USD", "listing", "low", "unspecified", T0), {})
    with pytest.raises(PriceBasisError, match="not a transaction value"):
        value_cards(listing, {}, scenario(), "pool_median")


def test_currency_must_match_the_scenario() -> None:
    eur = PriceVector(
        PriceBasis("cardmarket", "EUR", "provider_market", "trend", "unspecified", T0), {}
    )
    with pytest.raises(PriceBasisError, match="EUR"):
        value_cards(eur, {}, scenario(), "pool_median")


def test_imputation_rules() -> None:
    v = PriceVector(BASIS, {"a": 1.0, "b": 3.0, "c": 10.0})
    pools = {"p": ["a", "b", "c", "x"], "q": ["y"]}
    with pytest.raises(ValueError, match="no observed price"):
        impute(v, pools, "pool_median")
    pools = {"p": ["a", "b", "c", "x"]}
    filled, imputed = impute(v, pools, "pool_median")
    assert filled["x"] == 3.0 and imputed == {"x"}
    filled, imputed = impute(v, pools, "zero")
    assert filled["x"] == 0.0 and imputed == {"x"}
    filled, imputed = impute(v, pools, "exclude")
    assert "x" not in filled and imputed == frozenset()


def test_central_scenario_by_hand() -> None:
    s = SCENARIOS["central"]
    # 100 * 0.85 * (1 - 0.1075 - 0.025) - 0.30 - 1.00
    assert liquidation_value(100.0, s) == pytest.approx(85 * 0.8675 - 1.30)
    assert acquisition_price(100.0, s) == pytest.approx(101.0)
    assert liquidation_value(0.10, s) == 0.0  # bulk is worth nothing sold alone
    assert sale_threshold(s) == pytest.approx(1.30 / (0.85 * 0.8675))
    assert liquidation_value(sale_threshold(s) + 1e-9, s) >= 0


def test_gross_scenario_is_the_market_price() -> None:
    s = SCENARIOS["gross"]
    assert liquidation_value(7.5, s) == acquisition_price(7.5, s) == 7.5


@given(
    p=st.floats(0, 10_000),
    h=st.floats(0, 1),
    fm=st.floats(0, 0.5),
    fp=st.floats(0, 0.5),
    f0=st.floats(0, 5),
    s=st.floats(0, 10),
    fb=st.floats(0, 0.5),
    sb=st.floats(0, 10),
)
def test_liquidation_never_exceeds_acquisition(
    p: float, h: float, fm: float, fp: float, f0: float, s: float, fb: float, sb: float
) -> None:
    sc = scenario(
        liquidity_haircut=h,
        marketplace_fee_rate=fm,
        payment_fee_rate=fp,
        selling_fixed_fee=f0,
        shipping_per_sale=s,
        buyer_fee_rate=fb,
        buyer_shipping=sb,
    )
    assert 0 <= liquidation_value(p, sc) <= p <= acquisition_price(p, sc)


def test_value_cards_records_its_basis_and_imputations() -> None:
    v = PriceVector(BASIS, {"a": 2.0, "b": 50.0})
    cv = value_cards(v, {"p": ["a", "b", "c"]}, SCENARIOS["adverse"], "zero")
    assert cv.basis == BASIS and cv.scenario == "adverse" and cv.missing_rule == "zero"
    assert cv.imputed == {"c"} and cv.liquidation["c"] == 0.0
    assert cv.liquidation["a"] == 0.0 < cv.liquidation["b"] < 50.0 < cv.acquisition["b"]


def test_window_median() -> None:
    d = [PriceBasis("tcgplayer", "USD", "provider_market", "market", "unspecified",
                    T0 + timedelta(days=7 * k)) for k in range(3)]  # fmt: skip
    vs = [
        PriceVector(d[0], {"a": 1.0, "b": 5.0}),
        PriceVector(d[1], {"a": 3.0}),
        PriceVector(d[2], {"a": 2.0, "c": 9.0}),
    ]
    w = window_median(vs)
    assert w.basis.price_type == "window_median" and w.basis.reference_date == d[2].reference_date
    assert dict(w.prices) == {"a": 2.0}  # b and c are priced in only 1 of 3 snapshots
    other = PriceVector(PriceBasis("tcgplayer", "USD", "provider_market", "low", "unspecified",
                                   T0 + timedelta(days=30)), {})  # fmt: skip
    with pytest.raises(PriceBasisError):
        window_median([*vs, other])
