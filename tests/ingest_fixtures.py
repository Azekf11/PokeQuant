"""Synthetic raw snapshots for the ingestion tests.

Everything here is invented: a fictitious set ``zz01`` with four cards and
made-up prices, and a matching Poké Life-style registry. No real price is
stored in the repository (ADR 0007).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pokequant_core.ingest.http import write_sidecar
from pokequant_core.ingest.tcgdex import API

FETCHED_AT = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)
UPDATED = "2026-01-02T08:00:00.000Z"
PL_VERSION = "2026-01-01"
TD_VERSION = "2026-01-02"


def card(
    number: str, name: str, rarity: str, variants: list[str], pricing: dict[str, Any] | None
) -> dict[str, Any]:
    return {
        "id": f"zz01-{number}",
        "localId": number,
        "name": name,
        "rarity": rarity,
        "image": f"https://assets.example/zz01/{number}",
        "set": {"id": "zz01", "name": "Test Set"},
        "variants": {v: v in variants for v in ("normal", "reverse", "holo", "firstEdition")},
        "pricing": pricing,
    }


def cardmarket(**values: float | None) -> dict[str, Any]:
    return {"updated": UPDATED, "unit": "EUR", "idProduct": 1, **values}


def tcgplayer(**blocks: dict[str, float | None]) -> dict[str, Any]:
    return {"updated": UPDATED, "unit": "USD", **blocks}


CARDS = [
    card(
        "001",
        "Sproutling",
        "Common",
        ["normal", "reverse"],
        {
            "cardmarket": cardmarket(trend=0.10, avg30=0.12, **{"trend-holo": 0.30}),
            "tcgplayer": tcgplayer(
                normal={"marketPrice": 0.11, "lowPrice": 0.05},
                **{"reverse-holofoil": {"marketPrice": 0.25, "lowPrice": None}},
            ),
        },
    ),
    card(
        "002",
        "Testmon ex",
        "Double rare",
        ["holo"],
        {
            "cardmarket": cardmarket(trend=1.50, low=0.0, **{"trend-holo": 2.0}),
            "tcgplayer": tcgplayer(holofoil={"marketPrice": 1.75}),
        },
    ),
    card(
        "003",
        "Testmon ex",
        "Special Illustration Rare",
        ["holo"],
        {"tcgplayer": tcgplayer(holofoil={"marketPrice": 80.0}, unlimited={"marketPrice": 1.0})},
    ),
    card("004", "Rarebird", "Rare", ["reverse", "holo"], None),
]

SET = {
    "id": "zz01",
    "name": "Test Set",
    "serie": {"id": "zz", "name": "Test Series"},
    "releaseDate": "2025-01-01",
    "cardCount": {"official": 3, "total": 4},
    "cards": [{"id": c["id"], "localId": c["localId"], "name": c["name"]} for c in CARDS],
}
SERIES = {
    "id": "zz",
    "name": "Test Series",
    "sets": [{"id": "zz01", "name": "Test Set"}, {"id": "zz02", "name": "Other Set"}],
}

PULL_RATES_HEADER = (
    "set_id,set_name,rarity_id,rarity,cards_in_rarity,hits,packs,rate,"
    "ci95_lower,ci95_upper,confidence,counts_reconstructed,datasets"
)
PULL_RATES_ROWS = [
    "test-set,Test Set,double-rare,Double Rare,1,170,1000,0.17,0.147,0.195,high,true,TS-001 TS-002",
    "test-set,Test Set,sir,Special Illustration Rare,1,12,1000,0.012,0.0065,0.0204,"
    "limited,false,TS-001",
    "other-set,Other Set,double-rare,Double Rare,5,10,100,0.1,0.052,0.171,limited,true,OS-001",
    "elsewhere,Elsewhere,double-rare,Double Rare,5,10,100,0.1,0.052,0.171,limited,true,EW-001",
]


def write_json(path: Path, payload: Any, url: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    write_sidecar(path, url, FETCHED_AT)


def build_root(root: Path, pull_rates_rows: list[str] | None = None) -> Path:
    """Create a minimal repository layout with synthetic raw snapshots under ``root``."""
    raw = root / "data/raw/tcgdex" / TD_VERSION
    write_json(raw / "set-zz01.json", SET, f"{API}/sets/zz01")
    write_json(raw / "series-zz.json", SERIES, f"{API}/series/zz")
    for c in CARDS:
        write_json(raw / "cards" / f"{c['id']}.json", c, f"{API}/cards/{c['id']}")

    pl_rel = f"data/raw/pokelife/{PL_VERSION}/"
    pl_dir = root / pl_rel
    pl_dir.mkdir(parents=True)
    rows = PULL_RATES_ROWS if pull_rates_rows is None else pull_rates_rows
    csv_bytes = ("\n".join([PULL_RATES_HEADER, *rows]) + "\n").encode()
    (pl_dir / "pull-rates.csv").write_bytes(csv_bytes)
    manifest = {
        "snapshots": [
            {
                "source": "pokelife",
                "version": PL_VERSION,
                "path": pl_rel,
                "files": [
                    {
                        "name": "pull-rates.csv",
                        "url": "https://example.org/pull-rates.csv",
                        "sha256": hashlib.sha256(csv_bytes).hexdigest(),
                    }
                ],
            }
        ]
    }
    (root / "data/manifests").mkdir(parents=True)
    (root / "data/manifests/snapshots.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    return root
