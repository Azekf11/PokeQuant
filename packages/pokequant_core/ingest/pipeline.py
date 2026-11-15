"""Ingestion pipeline: raw snapshots -> validated, deterministic Parquet tables.

Inputs are the committed Poké Life snapshot (checksums verified against
``data/manifests/snapshots.yaml``) and a dated TCGdex cache folder. Outputs go
to ``data/processed/pokelife-<v>_tcgdex-<v>/`` (git-ignored): one Parquet file
per table and a ``manifest.json`` with input and output checksums and counts of
skipped values. The manifest carries no run time, so re-running on the same
inputs yields byte-identical outputs (idempotent import).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pokequant_core import __version__
from pokequant_core.ingest import pokelife, tcgdex
from pokequant_core.ingest.http import CachedClient, Fetched
from pokequant_core.ingest.store import write_records
from pokequant_core.ingest.validate import KEYS, Tables, validate
from pokequant_core.schemas import CardPrinting, PriceObservation

SNAPSHOTS = Path("data/manifests/snapshots.yaml")


@dataclass(frozen=True)
class IngestResult:
    out_dir: Path
    manifest: dict[str, Any]


def _digest_inputs(fetched: Iterable[Fetched]) -> dict[str, Any]:
    items = sorted({(f.url, f.sha256, f.fetched_at.isoformat()) for f in fetched})
    lines = "".join(f"{url} {sha}\n" for url, sha, _ in items)
    return {
        "files": len(items),
        "sha256": hashlib.sha256(lines.encode()).hexdigest(),
        "fetched_at_min": min(t for *_, t in items),
        "fetched_at_max": max(t for *_, t in items),
    }


def output_dir(
    root: Path, pokelife_version: str, tcgdex_version: str, name: str | None = None
) -> Path:
    return (
        root / "data/processed" / (name or f"pokelife-{pokelife_version}_tcgdex-{tcgdex_version}")
    )


def run(
    root: Path,
    pokelife_version: str,
    tcgdex_version: str,
    set_ids: Iterable[str],
    client: CachedClient,
    out_name: str | None = None,
) -> IngestResult:
    selected = sorted(set(set_ids))
    if not selected:
        raise ValueError("no set selected")

    # Poké Life: verify the committed snapshot before reading it.
    snapshot = pokelife.verify_snapshot(root / SNAPSHOTS, root, pokelife_version)
    pl_files = {f["name"]: f for f in snapshot["files"]}

    # TCGdex: sets, their series (the name catalogue for set matching), then every card.
    raw = root / "data/raw/tcgdex" / tcgdex_version
    set_payloads = [tcgdex.fetch_set(client, raw, s) for s in selected]
    sets = [tcgdex.parse_set(f) for f in set_payloads]
    series = [tcgdex.fetch_series(client, raw, s) for s in sorted({x.series for x in sets})]
    printings: list[CardPrinting] = []
    prices: list[PriceObservation] = []
    skipped: Counter[str] = Counter()
    card_payloads: list[Fetched] = []
    for set_payload in set_payloads:
        for card in tcgdex.fetch_cards(client, raw, set_payload):
            card_payloads.append(card)
            parsed = tcgdex.parse_card(card)
            printings += parsed.printings
            prices += parsed.prices
            skipped.update(s.reason for s in parsed.skipped)

    loaded = pokelife.load_pull_rates(
        root / snapshot["path"],
        pokelife_version,
        tcgdex.catalogue_names(series),
        pl_files["pull-rates.csv"]["url"],
    )
    pull_rates = [o for o in loaded.observations if o.set_id in selected]

    tables = Tables(sets=sets, printings=printings, pull_rates=pull_rates, prices=prices)
    validate(tables)

    out = output_dir(root, pokelife_version, tcgdex_version, out_name)
    outputs = {}
    for name, key in KEYS.items():
        records = getattr(tables, name)
        sha = write_records(records, key, out / f"{name}.parquet")
        outputs[name] = {"rows": len(records), "sha256": sha}

    manifest: dict[str, Any] = {
        "pipeline": {"package": "pokequant", "version": __version__},
        "sets": selected,
        "inputs": {
            "pokelife": {
                "version": pokelife_version,
                "files": {name: f["sha256"] for name, f in sorted(pl_files.items())},
            },
            "tcgdex": {
                "version": tcgdex_version,
                **_digest_inputs([*set_payloads, *series, *card_payloads]),
            },
        },
        "outputs": outputs,
        "skipped": dict(sorted(skipped.items())),
        "pokelife_sets_outside_catalogue": loaded.unmatched_sets,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return IngestResult(out, manifest)
