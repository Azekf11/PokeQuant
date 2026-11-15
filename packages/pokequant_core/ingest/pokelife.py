"""Poké Life adapter: per-pack pull-rate observations from a committed snapshot."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from pokequant_core.ids import normalise_rarity
from pokequant_core.schemas import PullRateObservation

SOURCE = "pokelife"


@dataclass(frozen=True)
class PullRateLoad:
    observations: list[PullRateObservation]
    unmatched_sets: list[str]  # Poké Life set IDs absent from the catalogue (reported)


def verify_snapshot(manifest_path: Path, root: Path, version: str) -> dict[str, Any]:
    """Check every file of a Poké Life snapshot against its manifest entry; return the entry."""
    manifest: dict[str, Any] = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    for snap in manifest["snapshots"]:
        if snap["source"] == SOURCE and snap["version"] == version:
            for f in snap["files"]:
                digest = hashlib.sha256((root / snap["path"] / f["name"]).read_bytes()).hexdigest()
                if digest != f["sha256"]:
                    raise ValueError(f"{f['name']} does not match the manifest checksum")
            return dict(snap)
    raise KeyError(f"no {SOURCE} snapshot {version!r} in {manifest_path}")


def map_set_ids(names: Mapping[str, str], catalogue_names: Mapping[str, str]) -> dict[str, str]:
    """Map Poké Life set IDs to TCGdex set IDs by exact case-insensitive name (ADR 0008).

    ``names``: Poké Life set_id -> set name. ``catalogue_names``: TCGdex set_id -> name.
    Unmatched sets are left out; an ambiguous name raises.
    """
    by_name: dict[str, list[str]] = {}
    for set_id, name in catalogue_names.items():
        by_name.setdefault(name.casefold(), []).append(set_id)
    mapping = {}
    for pl_id, name in names.items():
        matches = by_name.get(name.casefold(), [])
        if len(matches) > 1:
            raise ValueError(f"ambiguous set name {name!r}: {matches}")
        if matches:
            mapping[pl_id] = matches[0]
    return mapping


def load_pull_rates(
    snapshot_dir: Path, version: str, catalogue_names: Mapping[str, str], source_url: str
) -> PullRateLoad:
    """Read ``pull-rates.csv``; keep rows whose set maps to a TCGdex set (ADR 0008)."""
    with (snapshot_dir / "pull-rates.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    mapping = map_set_ids({r["set_id"]: r["set_name"] for r in rows}, catalogue_names)
    observations = [
        PullRateObservation(
            set_id=mapping[r["set_id"]],
            scope="pack",
            rarity=normalise_rarity(r["rarity"]),
            cards_in_rarity=int(r["cards_in_rarity"]) if r["cards_in_rarity"] else None,
            hits=int(r["hits"]),
            packs=int(r["packs"]),
            rate=float(r["rate"]),
            ci_low=float(r["ci95_lower"]),
            ci_high=float(r["ci95_upper"]),
            confidence=r["confidence"],
            counts_reconstructed={"true": True, "false": False}[r["counts_reconstructed"]],
            dataset_ids=tuple(r["datasets"].split()),
            source=SOURCE,
            source_version=version,
            source_url=source_url,
        )
        for r in rows
        if r["set_id"] in mapping
    ]
    unmatched = sorted({r["set_id"] for r in rows} - set(mapping))
    return PullRateLoad(observations, unmatched)
