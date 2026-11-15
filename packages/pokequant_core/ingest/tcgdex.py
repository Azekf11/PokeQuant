"""TCGdex adapter: sets, card printings and typed price observations (ADR 0008).

Prices are provider aggregates or listing statistics, never realised sales.
A missing or zero price produces no observation (and a ``Skipped`` entry).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pokequant_core.ids import make_printing_id, normalise_rarity
from pokequant_core.ingest.http import CachedClient, Fetched
from pokequant_core.schemas import CardPrinting, CardSet, PriceObservation, PriceType

API = "https://api.tcgdex.net/v2/en"
SOURCE = "tcgdex"
LANGUAGE = "en"
LICENSE_NOTE = "TCGdex pricing field, used with permission; derived statistics only (ADR 0009)"

# TCGplayer statistic -> price type
TCGPLAYER_FIELDS: dict[str, tuple[str, PriceType]] = {
    "lowPrice": ("low", "listing"),
    "midPrice": ("mid", "listing"),
    "highPrice": ("high", "listing"),
    "directLowPrice": ("direct_low", "listing"),
    "marketPrice": ("market", "provider_market"),
}
TCGPLAYER_VARIANTS = {"normal": "normal", "reverse-holofoil": "reverse", "holofoil": "holo"}
# Cardmarket statistic -> price type (plain names; "-holo" suffix handled separately)
CARDMARKET_FIELDS: dict[str, tuple[str, PriceType]] = {
    "low": ("low", "listing"),
    "trend": ("trend", "provider_market"),
    "avg": ("avg", "provider_market"),
    "avg1": ("avg1", "provider_market"),
    "avg7": ("avg7", "provider_market"),
    "avg30": ("avg30", "provider_market"),
}
CARDMARKET_META = {"updated", "unit", "idProduct"}
PRINTING_FLAGS = ("normal", "reverse", "holo")


@dataclass(frozen=True)
class Skipped:
    """A value deliberately not ingested, with the reason (for the ingestion report)."""

    ref: str
    reason: str


@dataclass(frozen=True)
class ParsedCard:
    printings: list[CardPrinting]
    prices: list[PriceObservation]
    skipped: list[Skipped]


def set_path(raw_dir: Path, set_id: str) -> Path:
    return raw_dir / f"set-{set_id}.json"


def card_path(raw_dir: Path, card_id: str) -> Path:
    return raw_dir / "cards" / f"{card_id}.json"


def series_path(raw_dir: Path, series_id: str) -> Path:
    return raw_dir / f"series-{series_id}.json"


def parse_set(fetched: Fetched) -> CardSet:
    d = fetched.data
    return CardSet(
        set_id=d["id"],
        name=d["name"],
        series=d["serie"]["id"],
        release_date=date.fromisoformat(d["releaseDate"]),
        language=LANGUAGE,
        card_count_official=d["cardCount"]["official"],
        card_count_total=d["cardCount"]["total"],
        source=SOURCE,
        fetched_at=fetched.fetched_at,
    )


def _positive(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if value > 0 else None


def parse_card(fetched: Fetched) -> ParsedCard:
    d = fetched.data
    card_id, set_id, number = d["id"], d["set"]["id"], d["localId"]
    flags: dict[str, bool] = d.get("variants") or {}
    skipped = [
        Skipped(card_id, f"unsupported variant {flag!r}")
        for flag, present in flags.items()
        if present and flag not in PRINTING_FLAGS
    ]
    variants = [v for v in PRINTING_FLAGS if flags.get(v)]
    printings = [
        CardPrinting(
            printing_id=make_printing_id(LANGUAGE, set_id, number, v),
            card_id=card_id,
            set_id=set_id,
            number=number,
            name=d["name"],
            rarity=normalise_rarity(d["rarity"]),
            variant=v,
            language=LANGUAGE,
            image_ref=d.get("image"),
            source=SOURCE,
            fetched_at=fetched.fetched_at,
        )
        for v in variants
    ]

    pricing: dict[str, Any] = d.get("pricing") or {}
    prices: list[PriceObservation] = []

    def observe(variant: str, currency: str, venue: str, stat: str, ptype: PriceType,
                value: Any, updated: str) -> None:  # fmt: skip
        amount = _positive(value)
        ref = f"{card_id}:{venue}:{variant}:{stat}"
        if amount is None:
            skipped.append(Skipped(ref, "missing or non-positive price"))
            return
        if variant not in variants:
            skipped.append(Skipped(ref, f"no {variant!r} printing for this card"))
            return
        prices.append(
            PriceObservation(
                printing_id=make_printing_id(LANGUAGE, set_id, number, variant),
                condition="unspecified",
                currency=currency,
                amount=amount,
                price_type=ptype,
                statistic=stat,
                venue=venue,
                observed_at=datetime.fromisoformat(updated),
                fetched_at=fetched.fetched_at,
                source=SOURCE,
                source_url=f"{API}/cards/{card_id}",
                license_note=LICENSE_NOTE,
            )
        )

    tcg = pricing.get("tcgplayer") or {}
    for key, block in tcg.items():
        if key in {"unit", "updated"}:
            continue
        variant = TCGPLAYER_VARIANTS.get(key)
        if variant is None or not isinstance(block, dict):
            skipped.append(Skipped(f"{card_id}:tcgplayer:{key}", "unmapped TCGplayer variant"))
            continue
        for field, (stat, ptype) in TCGPLAYER_FIELDS.items():
            observe(
                variant, tcg["unit"], "tcgplayer", stat, ptype, block.get(field), tcg["updated"]
            )

    cm = pricing.get("cardmarket") or {}
    if cm:
        base = "normal" if flags.get("normal") else "holo"
        holo_variant = "reverse" if flags.get("normal") and flags.get("reverse") else None
        for key, value in cm.items():
            if key in CARDMARKET_META:
                continue
            name, _, suffix = key.partition("-")
            if name not in CARDMARKET_FIELDS or suffix not in {"", "holo"}:
                skipped.append(Skipped(f"{card_id}:cardmarket:{key}", "unmapped Cardmarket field"))
                continue
            stat, ptype = CARDMARKET_FIELDS[name]
            variant = base if not suffix else holo_variant
            if variant is None and _positive(value) is None:
                skipped.append(
                    Skipped(f"{card_id}:cardmarket:{key}", "missing or non-positive price")
                )
                continue
            if variant is None:
                skipped.append(
                    Skipped(f"{card_id}:cardmarket:{key}", "ambiguous '-holo' variant (ADR 0008)")
                )
                continue
            observe(variant, cm["unit"], "cardmarket", stat, ptype, value, cm["updated"])

    return ParsedCard(printings, prices, skipped)


def fetch_set(client: CachedClient, raw_dir: Path, set_id: str) -> Fetched:
    return client.get_json(f"{API}/sets/{set_id}", set_path(raw_dir, set_id))


def fetch_cards(client: CachedClient, raw_dir: Path, set_fetched: Fetched) -> Iterator[Fetched]:
    for brief in set_fetched.data["cards"]:
        yield client.get_json(f"{API}/cards/{brief['id']}", card_path(raw_dir, brief["id"]))


def fetch_series(client: CachedClient, raw_dir: Path, series_id: str) -> Fetched:
    return client.get_json(f"{API}/series/{series_id}", series_path(raw_dir, series_id))


def catalogue_names(series_payloads: Iterable[Fetched]) -> dict[str, str]:
    """TCGdex set_id -> set name, over every set of the given series."""
    return {s["id"]: s["name"] for serie in series_payloads for s in serie.data["sets"]}
