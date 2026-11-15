"""Command-line entry point: ``pokequant ingest ...``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from pokequant_core.ingest import pipeline
from pokequant_core.ingest.http import CachedClient, SourceUnavailableError
from pokequant_core.ingest.validate import ValidationError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pokequant")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="build the processed tables from raw snapshots")
    ingest.add_argument("--pokelife", required=True, help="Poké Life snapshot version (date)")
    ingest.add_argument("--tcgdex", required=True, help="TCGdex cache folder (date)")
    ingest.add_argument("--sets", required=True, help="comma-separated TCGdex set IDs")
    ingest.add_argument("--offline", action="store_true", help="use only cached raw files")
    ingest.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    sets = [s.strip() for s in args.sets.split(",") if s.strip()]
    try:
        with CachedClient(offline=args.offline) as client:
            result = pipeline.run(args.root, args.pokelife, args.tcgdex, sets, client)
    except (SourceUnavailableError, ValidationError) as error:
        print(f"ingestion failed: {error}", file=sys.stderr)
        return 1
    print(f"wrote {result.out_dir}")
    for name, info in result.manifest["outputs"].items():
        print(f"  {name:<11} {info['rows']:>6} rows  sha256 {info['sha256'][:12]}")
    for reason, count in result.manifest["skipped"].items():
        print(f"  skipped {count:>6} x {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
