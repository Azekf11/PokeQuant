"""Week S2 data audit: apply the set selection rule of ADR 0005.

Reads a dated Poké Life snapshot, fetches the TCGdex catalogue for candidate
sets (cached on disk, polite rate), and writes a coverage matrix with the
eligibility and ranking of every candidate set.

Price *presence* is checked; price *values* are never printed or written
(ADR 0005: the selection must not depend on prices).

Usage:
    uv run python scripts/audit_sets.py --pokelife 2026-11-13 --fetch-date 2026-11-15
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
TCGDEX = "https://api.tcgdex.net/v2/en"
USER_AGENT = "PokeQuant-research/0.1 (+https://github.com/Azekf11/PokeQuant)"
SERIES = ("sv", "me")  # ADR 0005 criterion 2: Scarlet & Violet series or later
MIN_PACKS = 5000  # criterion 3
MIN_PRICE_COVERAGE = 0.90  # criterion 6
# Poké Life rarity ids from "Double Rare" upwards (criterion 4): every hit rarity
# in the registry except none: the registry only lists Double Rare and above
# for these series, so all rows are checked.
NON_HIT_RARITIES = {"Common", "Uncommon", "None", ""}
PRICE_META_KEYS = {"unit", "updated", "idProduct", "productId"}


@dataclass
class SetAudit:
    pokelife_id: str
    name: str
    tcgdex_id: str | None = None
    release_date: str | None = None
    packs: int = 0
    rarity_rows: int = 0
    share_not_reconstructed: float = 0.0
    share_high_confidence: float = 0.0
    rows_complete: bool = False
    catalogue_expected: int | None = None
    catalogue_found: int = 0
    catalogue_complete: bool = False
    rare_plus_cards: int = 0
    rare_plus_priced: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def price_coverage(self) -> float:
        return self.rare_plus_priced / self.rare_plus_cards if self.rare_plus_cards else 0.0

    @property
    def eligible(self) -> bool:
        return not self.failures


def load_pokelife(snapshot_dir: Path) -> dict[str, list[dict[str, str]]]:
    by_set: dict[str, list[dict[str, str]]] = defaultdict(list)
    with (snapshot_dir / "pull-rates.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_set[row["set_id"]].append(row)
    return by_set


def get_json(client: httpx.Client, url: str, cache: Path) -> Any:
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    for attempt in range(4):
        try:
            response = client.get(url)
            response.raise_for_status()
            break
        except httpx.HTTPError:
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(response.text, encoding="utf-8")
    time.sleep(0.2)  # be considerate: ~5 requests/s at most
    return response.json()


def has_price(pricing: dict[str, Any] | None) -> bool:
    """True if any provider reports at least one positive numeric price field."""

    def walk(node: Any) -> bool:
        if isinstance(node, dict):
            return any(walk(v) for k, v in node.items() if k not in PRICE_META_KEYS)
        return isinstance(node, int | float) and not isinstance(node, bool) and node > 0

    return bool(pricing) and walk(pricing)


def audit(pokelife_dir: Path, raw_tcgdex: Path) -> list[SetAudit]:
    registry = load_pokelife(pokelife_dir)
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as client:
        tcgdex_sets: dict[str, dict[str, Any]] = {}
        for serie in SERIES:
            data = get_json(client, f"{TCGDEX}/series/{serie}", raw_tcgdex / f"series-{serie}.json")
            for s in data["sets"]:
                tcgdex_sets[s["name"].casefold()] = s

        audits = []
        for set_id, rows in sorted(registry.items()):
            a = SetAudit(pokelife_id=set_id, name=rows[0]["set_name"])
            a.packs = max(int(r["packs"]) for r in rows if r["packs"])
            a.rarity_rows = len(rows)
            a.share_not_reconstructed = sum(
                r["counts_reconstructed"] == "false" for r in rows
            ) / len(rows)
            a.share_high_confidence = sum(r["confidence"] == "high" for r in rows) / len(rows)
            a.rows_complete = all(
                r["hits"] and r["packs"] and r["ci95_lower"] and r["ci95_upper"] for r in rows
            )
            audits.append(a)

            match = tcgdex_sets.get(a.name.casefold())
            if match is None:
                a.failures.append("C2 not in SV/ME series")
                continue
            a.tcgdex_id = match["id"]
            if a.packs < MIN_PACKS:
                a.failures.append(f"C3 packs < {MIN_PACKS}")
            if not a.rows_complete:
                a.failures.append("C4 incomplete rarity rows")
            if a.failures:
                continue  # do not fetch catalogues of sets already excluded

            detail = get_json(
                client, f"{TCGDEX}/sets/{a.tcgdex_id}", raw_tcgdex / f"set-{a.tcgdex_id}.json"
            )
            a.release_date = detail.get("releaseDate")
            a.catalogue_expected = detail["cardCount"]["total"]
            for brief in detail["cards"]:
                card = get_json(
                    client,
                    f"{TCGDEX}/cards/{brief['id']}",
                    raw_tcgdex / "cards" / f"{brief['id']}.json",
                )
                rarity = card.get("rarity") or ""
                if rarity:
                    a.catalogue_found += 1
                if rarity not in NON_HIT_RARITIES:
                    a.rare_plus_cards += 1
                    a.rare_plus_priced += has_price(card.get("pricing"))
            a.catalogue_complete = a.catalogue_found == a.catalogue_expected == len(detail["cards"])
            if not a.catalogue_complete:
                a.failures.append("C5 catalogue incomplete")
            if a.price_coverage < MIN_PRICE_COVERAGE:
                a.failures.append(f"C6 price coverage < {MIN_PRICE_COVERAGE:.0%}")
    return audits


def rank(audits: list[SetAudit]) -> list[SetAudit]:
    eligible = [a for a in audits if a.eligible]
    return sorted(
        eligible,
        key=lambda a: (
            -a.share_not_reconstructed,
            -a.share_high_confidence,
            -a.packs,
            a.release_date or "9999",
        ),
    )


def write_outputs(audits: list[SetAudit], ranking: list[SetAudit], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    position = {a.pokelife_id: i + 1 for i, a in enumerate(ranking)}
    columns = [
        "rank", "pokelife_id", "name", "tcgdex_id", "release_date", "packs", "rarity_rows",
        "share_not_reconstructed", "share_high_confidence", "catalogue_expected",
        "catalogue_found", "rare_plus_cards", "rare_plus_priced", "price_coverage",
        "eligible", "failures",
    ]  # fmt: skip
    ordered = sorted(audits, key=lambda a: (position.get(a.pokelife_id, 999), -a.packs))
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for a in ordered:
            writer.writerow([
                position.get(a.pokelife_id, ""), a.pokelife_id, a.name, a.tcgdex_id or "",
                a.release_date or "", a.packs, a.rarity_rows,
                f"{a.share_not_reconstructed:.2f}", f"{a.share_high_confidence:.2f}",
                a.catalogue_expected if a.catalogue_expected is not None else "",
                a.catalogue_found, a.rare_plus_cards, a.rare_plus_priced,
                f"{a.price_coverage:.3f}" if a.rare_plus_cards else "",
                a.eligible, "; ".join(a.failures),
            ])  # fmt: skip


def reconcile_rarities(
    selected: list[SetAudit], pokelife_dir: Path, raw_tcgdex: Path, out_csv: Path
) -> bool:
    """Compare card counts per rarity: TCGdex catalogue vs Poké Life `cards_in_rarity`.

    Returns True if every Poké Life rarity row matches the catalogue count.
    """
    registry = load_pokelife(pokelife_dir)
    all_match = True
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tcgdex_id", "rarity", "tcgdex_cards", "pokelife_cards", "match"])
        for a in selected:
            detail = json.loads((raw_tcgdex / f"set-{a.tcgdex_id}.json").read_text("utf-8"))
            counts: dict[str, int] = defaultdict(int)
            for brief in detail["cards"]:
                card_file = raw_tcgdex / "cards" / f"{brief['id']}.json"
                card = json.loads(card_file.read_text("utf-8"))
                counts[(card.get("rarity") or "").casefold()] += 1
            pokelife = {
                r["rarity"].casefold(): r["cards_in_rarity"] for r in registry[a.pokelife_id]
            }
            for rarity in sorted(set(counts) | set(pokelife)):
                expected = pokelife.get(rarity, "")
                match = expected == "" or int(expected) == counts.get(rarity, 0)
                all_match &= match
                writer.writerow([a.tcgdex_id, rarity, counts.get(rarity, 0), expected, match])
    return all_match


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pokelife", required=True, help="Poké Life snapshot date (folder name)")
    parser.add_argument("--fetch-date", required=True, help="TCGdex cache folder date")
    parser.add_argument(
        "--out", default="research/reports/data_audit_coverage.csv", help="Output CSV path"
    )
    args = parser.parse_args()

    pokelife_dir = ROOT / "data/raw/pokelife" / args.pokelife
    raw_tcgdex = ROOT / "data/raw/tcgdex" / args.fetch_date
    out = ROOT / args.out
    audits = audit(pokelife_dir, raw_tcgdex)
    ranking = rank(audits)
    write_outputs(audits, ranking, out)
    selected = ranking[:3]
    rarities_ok = reconcile_rarities(
        selected, pokelife_dir, raw_tcgdex, out.with_name("data_audit_rarities.csv")
    )
    print(f"{sum(a.eligible for a in audits)} eligible of {len(audits)} sets")
    print("Selected (ADR 0005):", ", ".join(f"{a.name} ({a.tcgdex_id})" for a in selected))
    print("Rarity counts match Poké Life:", rarities_ok)


if __name__ == "__main__":
    main()
