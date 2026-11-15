from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ingest_fixtures import CARDS, FETCHED_AT, SERIES, SET

from pokequant_core.ingest.http import Fetched
from pokequant_core.ingest.tcgdex import ParsedCard, catalogue_names, parse_card, parse_set


def fetched(data: Any) -> Fetched:
    return Fetched(data=data, fetched_at=FETCHED_AT, sha256="0" * 64, url="https://x")


def prices(parsed: ParsedCard) -> set[tuple[str, str, str, str, float]]:
    return {
        (p.printing_id.split(":")[-1], p.venue, p.statistic, p.price_type, p.amount)
        for p in parsed.prices
    }


def reasons(parsed: ParsedCard) -> dict[str, str]:
    return {s.ref: s.reason for s in parsed.skipped}


def test_parse_set_reads_series_from_payload() -> None:
    s = parse_set(fetched(SET))
    assert (s.set_id, s.series, s.card_count_total) == ("zz01", "zz", 4)
    assert catalogue_names([fetched(SERIES)]) == {"zz01": "Test Set", "zz02": "Other Set"}


def test_normal_and_reverse_card_maps_every_venue() -> None:
    parsed = parse_card(fetched(CARDS[0]))
    assert [p.printing_id for p in parsed.printings] == [
        "en:zz01:001:normal",
        "en:zz01:001:reverse",
    ]
    assert prices(parsed) == {
        ("normal", "cardmarket", "trend", "provider_market", 0.10),
        ("normal", "cardmarket", "avg30", "provider_market", 0.12),
        ("reverse", "cardmarket", "trend", "provider_market", 0.30),  # "-holo" -> reverse
        ("normal", "tcgplayer", "market", "provider_market", 0.11),
        ("normal", "tcgplayer", "low", "listing", 0.05),
        ("reverse", "tcgplayer", "market", "provider_market", 0.25),
    }
    assert reasons(parsed)["zz01-001:tcgplayer:reverse:low"] == "missing or non-positive price"


def test_holo_only_card_base_is_holo_and_holo_suffix_is_ambiguous() -> None:
    parsed = parse_card(fetched(CARDS[1]))
    assert prices(parsed) == {
        ("holo", "cardmarket", "trend", "provider_market", 1.50),
        ("holo", "tcgplayer", "market", "provider_market", 1.75),
    }
    r = reasons(parsed)
    assert r["zz01-002:cardmarket:trend-holo"] == "ambiguous '-holo' variant (ADR 0008)"
    assert r["zz01-002:cardmarket:holo:low"] == "missing or non-positive price"  # zero is missing


def test_unmapped_variant_and_rarity_normalisation() -> None:
    parsed = parse_card(fetched(CARDS[2]))
    assert parsed.printings[0].rarity == "special illustration rare"
    assert reasons(parsed)["zz01-003:tcgplayer:unlimited"] == "unmapped TCGplayer variant"


def test_card_without_pricing_has_printings_only() -> None:
    parsed = parse_card(fetched(CARDS[3]))
    assert [p.variant for p in parsed.printings] == ["reverse", "holo"]
    assert parsed.prices == [] and parsed.skipped == []


def test_observed_at_is_the_provider_update_time() -> None:
    p = parse_card(fetched(CARDS[1])).prices[0]
    assert p.observed_at == datetime(2026, 1, 2, 8, 0, tzinfo=UTC)
    assert p.fetched_at == FETCHED_AT
