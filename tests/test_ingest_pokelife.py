from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pokequant_core.ingest.pokelife import load_pull_rates, map_set_ids, verify_snapshot

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/snapshots.yaml"
SNAPSHOT = ROOT / "data/raw/pokelife/2026-11-13"


def test_committed_snapshot_matches_manifest() -> None:
    snap = verify_snapshot(MANIFEST, ROOT, "2026-11-13")
    assert {f["name"] for f in snap["files"]} == {"pull-rates.csv", "datasets.csv", "evidence.json"}


def test_tampered_snapshot_is_rejected(tmp_path: Path) -> None:
    copy = tmp_path / "data/raw/pokelife/2026-11-13"
    shutil.copytree(SNAPSHOT, copy)
    with (copy / "pull-rates.csv").open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError, match=r"pull-rates\.csv"):
        verify_snapshot(MANIFEST, tmp_path, "2026-11-13")


def test_unknown_version_is_an_error() -> None:
    with pytest.raises(KeyError):
        verify_snapshot(MANIFEST, ROOT, "1999-01-01")


def test_set_mapping_is_exact_case_insensitive_and_rejects_ambiguity() -> None:
    catalogue = {"sv08": "Surging Sparks", "sv03.5": "151"}
    names = {"surging-sparks": "surging sparks", "151": "151", "x": "Surging"}
    assert map_set_ids(names, catalogue) == {"surging-sparks": "sv08", "151": "sv03.5"}
    with pytest.raises(ValueError, match="ambiguous"):
        map_set_ids({"a": "Dup"}, {"s1": "Dup", "s2": "dup"})


def test_load_committed_pull_rates_for_one_set() -> None:
    loaded = load_pull_rates(SNAPSHOT, "2026-11-13", {"sv08": "Surging Sparks"}, "https://x")
    rows = loaded.observations
    assert {o.set_id for o in rows} == {"sv08"}
    assert len(rows) == 6
    hyper = next(o for o in rows if o.rarity == "hyper rare")
    assert (hyper.hits, hyper.cards_in_rarity, hyper.scope) == (64, 6, "pack")
    assert all(o.counts_reconstructed and o.source_version == "2026-11-13" for o in rows)
    assert "surging-sparks" not in loaded.unmatched_sets
    assert "destined-rivals" in loaded.unmatched_sets
