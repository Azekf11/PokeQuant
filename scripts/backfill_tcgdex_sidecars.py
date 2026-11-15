"""Backfill ``.meta.json`` sidecars for a TCGdex cache written before S3.

The S2 audit (``scripts/audit_sets.py``) cached raw TCGdex responses without
metadata. This one-off script records, for each cached file, its URL, its
SHA-256 and a fetch time taken from the file's modification time, flagged as
backfilled. Existing sidecars are left untouched.

Usage: uv run python scripts/backfill_tcgdex_sidecars.py data/raw/tcgdex/2026-11-15
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from pokequant_core.ingest.http import meta_path, write_sidecar
from pokequant_core.ingest.tcgdex import API

NOTE = "fetched_at backfilled from file mtime (cache written by scripts/audit_sets.py, S2)"


def url_for(raw_dir: Path, path: Path) -> str:
    relative = path.relative_to(raw_dir)
    if relative.parts[0] == "cards":
        return f"{API}/cards/{path.stem}"
    kind, _, ident = path.stem.partition("-")
    if kind == "set":
        return f"{API}/sets/{ident}"
    if kind == "series":
        return f"{API}/series/{ident}"
    raise ValueError(f"unexpected cache file {relative}")


def backfill(raw_dir: Path) -> int:
    written = 0
    for path in sorted(raw_dir.rglob("*.json")):
        if path.name.endswith(".meta.json") or meta_path(path).exists():
            continue
        fetched_at = datetime.fromtimestamp(path.stat().st_mtime, UTC)
        write_sidecar(path, url_for(raw_dir, path), fetched_at, note=NOTE)
        written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("raw_dir", type=Path)
    args = parser.parse_args()
    print(f"{backfill(args.raw_dir)} sidecar(s) written in {args.raw_dir}")


if __name__ == "__main__":
    main()
