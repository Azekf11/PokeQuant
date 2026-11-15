"""Cross-table checks run before anything is written.

Per-record rules live in the schemas; this module checks what a single record
cannot: primary-key uniqueness, referential integrity, one currency per venue,
and agreement between the pull-rate registry and the card catalogue (rarity
names and card counts).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from pokequant_core.schemas import CardPrinting, CardSet, PriceObservation, PullRateObservation

KEYS: dict[str, Callable[[Any], tuple[Any, ...]]] = {
    "sets": lambda r: (r.set_id,),
    "printings": lambda r: (r.printing_id,),
    "pull_rates": lambda r: (r.set_id, r.scope, r.rarity),
    "prices": lambda r: (r.printing_id, r.venue, r.statistic, r.condition, r.observed_at),
}


class ValidationError(ValueError):
    """The ingested tables are inconsistent; ``errors`` lists every problem found."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__(f"{len(errors)} validation error(s):\n- " + "\n- ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Tables:
    sets: list[CardSet]
    printings: list[CardPrinting]
    pull_rates: list[PullRateObservation]
    prices: list[PriceObservation]


def duplicates(records: Sequence[Any], key: Callable[[Any], tuple[Any, ...]]) -> list[Any]:
    counts = Counter(key(r) for r in records)
    return sorted((k for k, n in counts.items() if n > 1), key=repr)


def check(tables: Tables) -> list[str]:
    errors: list[str] = []
    for name, key in KEYS.items():
        dup = duplicates(getattr(tables, name), key)
        if dup:
            errors.append(f"{name}: {len(dup)} duplicate key(s), e.g. {dup[:3]}")
    for name in ("sets", "printings", "pull_rates"):
        if not getattr(tables, name):
            errors.append(f"{name}: no records")

    set_ids = {s.set_id for s in tables.sets}
    printing_ids = {p.printing_id for p in tables.printings}
    errors += [
        f"printing {p.printing_id}: unknown set"
        for p in tables.printings
        if p.set_id not in set_ids
    ]
    errors += [
        f"price for unknown printing {p.printing_id}"
        for p in tables.prices
        if p.printing_id not in printing_ids
    ]

    currencies: dict[str, set[str]] = {}
    for price in tables.prices:
        currencies.setdefault(price.venue, set()).add(price.currency)
    errors += [
        f"prices: venue {venue} mixes currencies {sorted(found)}"
        for venue, found in sorted(currencies.items())
        if len(found) > 1
    ]

    # Distinct cards (not printings) per (set, rarity) in the catalogue.
    distinct_cards = {(p.set_id, p.rarity, p.card_id) for p in tables.printings}
    cards = Counter((set_id, rarity) for set_id, rarity, _ in distinct_cards)
    for obs in tables.pull_rates:
        if obs.set_id not in set_ids:
            errors.append(f"pull rate {obs.set_id}/{obs.rarity}: unknown set")
            continue
        n = cards.get((obs.set_id, obs.rarity), 0)
        if n == 0:
            errors.append(f"pull rate {obs.set_id}/{obs.rarity}: rarity absent from catalogue")
        elif obs.cards_in_rarity is not None and obs.cards_in_rarity != n:
            errors.append(
                f"pull rate {obs.set_id}/{obs.rarity}: registry says {obs.cards_in_rarity} "
                f"cards, catalogue has {n}"
            )
    return errors


def validate(tables: Tables) -> None:
    errors = check(tables)
    if errors:
        raise ValidationError(errors)
