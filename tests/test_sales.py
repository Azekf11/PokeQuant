"""Sale-price benchmark (ADR 0014): exchange rate, conversion, exact b*, ratios."""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest
from test_booster import printings, rates
from test_comparator import CFG, context, observations

from pokequant_core.comparator import jobs, run_job
from pokequant_core.sales import (
    FxRate,
    break_even,
    break_even_draws,
    paired_ratios,
    parse_ecb,
    ratio_summary,
    to_usd,
    with_basis,
)
from pokequant_core.schemas import PriceObservation
from pokequant_core.valuation import PriceBasis, PriceVector


def ecb_payload(points: dict[str, float | None]) -> dict[str, object]:
    days = list(points)
    return {
        "structure": {"dimensions": {"observation": [{"values": [{"id": d} for d in days]}]}},
        "dataSets": [
            {
                "series": {
                    "0:0:0:0:0": {
                        "observations": {str(i): [v] for i, v in enumerate(points.values())}
                    }
                }
            }
        ],
    }


def test_parse_ecb_takes_the_last_rate_on_or_before_the_date() -> None:
    payload = ecb_payload({"2026-11-12": 1.10, "2026-11-13": 1.11, "2026-11-16": 1.20})
    assert parse_ecb(payload, date(2026, 11, 15)) == (1.11, date(2026, 11, 13))
    assert parse_ecb(payload, date(2026, 11, 16)) == (1.20, date(2026, 11, 16))
    with pytest.raises(ValueError):
        parse_ecb(payload, date(2026, 11, 1))


def test_parse_ecb_skips_missing_values() -> None:
    payload = ecb_payload({"2026-11-12": 1.10, "2026-11-13": None})
    assert parse_ecb(payload, date(2026, 11, 15)) == (1.10, date(2026, 11, 12))


def cardmarket(statistic: str = "avg30") -> list[PriceObservation]:
    return [
        o.model_copy(update={"venue": "cardmarket", "currency": "EUR", "statistic": statistic})
        for o in observations()
    ]


def test_to_usd_converts_only_the_chosen_cardmarket_statistic() -> None:
    fx = FxRate(2.0, date(2026, 11, 13), "https://example.org")
    eur = cardmarket()
    usd = to_usd([*eur, *cardmarket("trend"), *observations()], "avg30", fx)
    assert len(usd) == len(eur)
    assert all(u.currency == "USD" and u.venue == "cardmarket" for u in usd)
    assert [u.amount for u in usd] == pytest.approx([2 * o.amount for o in eur])


def test_exact_break_even_matches_the_main_engine() -> None:
    ctx = context()
    result = run_job(ctx, jobs(CFG)[0], 0, seed=7, draws=3, runs=400)
    exact = break_even_draws(ctx, 7, 3)
    for k, s in enumerate(ctx.scenarios):
        assert exact[:, k] == pytest.approx(result.extra["break_even_booster_price"][s])


def test_gross_break_even_scales_with_the_exchange_rate() -> None:
    fx = FxRate(2.0, date(2026, 11, 13), "https://example.org")
    every = [*observations(), *to_usd(cardmarket(), "avg30", fx)]
    day = date(2026, 11, 15)
    cfg = CFG.model_copy(
        update={"simulation": CFG.simulation.model_copy(update={"epistemic_draws": 4})}
    )
    us = break_even(
        with_basis(cfg, day, "tcgplayer", "market"),
        "zz",
        printings(),
        rates(),
        every,
        "tcgplayer_market",
        ["gross", "central"],
    )
    eu = break_even(
        with_basis(cfg, day, "cardmarket", "avg30"),
        "zz",
        printings(),
        rates(),
        every,
        "cardmarket_avg30_usd",
        ["gross", "central"],
    )
    assert eu[0].mean == pytest.approx(2 * us[0].mean)
    assert eu[1].mean > us[1].mean  # fixed costs: less than proportional, still higher
    assert us[0].coverage == eu[0].coverage == 1.0


def test_ratio_summary_is_reproducible_and_brackets_the_median() -> None:
    x = list(np.linspace(0.5, 1.5, 41))
    a, b = ratio_summary(x, 2000, 1), ratio_summary(x, 2000, 1)
    assert a == b and a.n == 41
    assert a.median == pytest.approx(1.0)
    assert a.low <= a.median <= a.high and a.q1 < a.median < a.q3
    with pytest.raises(ValueError):
        ratio_summary([], 10, 1)


def test_paired_ratios_skip_unpriced_printings() -> None:
    basis = PriceBasis(
        "tcgplayer", "USD", "provider_market", "market", "unspecified", date(2026, 11, 15)
    )
    num = PriceVector(basis, {"a": 2.0, "b": 3.0})
    den = PriceVector(basis, {"a": 1.0, "c": 4.0})
    assert paired_ratios(num, den, ["a", "b", "c", "d"]) == [2.0]
