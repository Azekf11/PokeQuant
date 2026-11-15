"""Command-line entry point: ``pokequant ingest``, ``run <config>``, ``robustness <config>``."""

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
    run = commands.add_parser("run", help="run an experiment config and write its results")
    run.add_argument(
        "config", type=Path, help="experiment YAML, e.g. research/experiments/main.yaml"
    )
    run.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    run.add_argument("--out", type=Path, default=Path("results"), help="results folder")
    run.add_argument("--draws", type=int, help="override epistemic draws (smoke tests)")
    run.add_argument("--runs", type=int, help="override aleatory runs per draw (smoke tests)")
    run.add_argument("--workers", type=int, help="worker processes (default: CPU count)")
    rob = commands.add_parser("robustness", help="run the robustness tests of a config")
    rob.add_argument("config", type=Path, help="experiment YAML")
    rob.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    rob.add_argument("--out", type=Path, default=Path("results"), help="results folder")
    rob.add_argument("--only", help="comma-separated run names, e.g. values,R8")
    rob.add_argument("--draws", type=int, help="override epistemic draws (smoke tests)")
    rob.add_argument("--runs", type=int, help="override aleatory runs per draw (smoke tests)")
    rob.add_argument("--workers", type=int, help="worker processes (default: CPU count)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "run":
        from pokequant_core.experiment_run import run_experiment

        out = run_experiment(
            args.config,
            root=args.root,
            out=args.out,
            draws=args.draws,
            runs=args.runs,
            workers=args.workers,
        )
        print(f"wrote {out}")
        return 0
    if args.command == "robustness":
        from pokequant_core.robustness import run_robustness

        only = [s.strip() for s in args.only.split(",")] if args.only else None
        out = run_robustness(
            args.config,
            root=args.root,
            out=args.out,
            only=only,
            draws=args.draws,
            runs=args.runs,
            workers=args.workers,
        )
        print(f"wrote {out}")
        return 0
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
