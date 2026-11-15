"""Sale-price benchmark and weekly price panel (ADR 0014, tag prereg-v3).

For one snapshot date, computes:
- Q1: the break-even booster price b* (posterior mean and 95 % interval) per set
  with TCGplayer market prices and with Cardmarket 30-day average sale prices
  converted to USD at the ECB reference rate;
- Q2: ratios avg30 (USD) / TCGplayer market and avg30 / Cardmarket trend over
  the hit printings, with a bootstrap interval of the median;
- V1: share of printings whose TCGdex-relayed avg30 equals Cardmarket's
  official price guide (only when that file is available for the date).

Rows are written to research/reports/price_panel.csv, price_ratios.csv and
price_relay_check.csv (derived statistics only, ADR 0009), then the report
research/reports/sales_benchmark.md is regenerated from all dates.

Run `pokequant ingest --pokelife 2026-11-13 --tcgdex <date> --sets sv07,sv08,sv10`
first. Usage: uv run python scripts/sales_benchmark.py --date 2026-11-15 [--offline]
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from pokequant_core.comparator import build_context, drawable_pools
from pokequant_core.experiment import load_experiment
from pokequant_core.ingest.http import CachedClient, SourceUnavailableError
from pokequant_core.ingest.store import read_records
from pokequant_core.sales import (
    HIT_POOLS,
    FxRate,
    break_even,
    ecb_rate,
    paired_ratios,
    ratio_summary,
    to_usd,
    with_basis,
)
from pokequant_core.schemas import (
    CardPrinting,
    Currency,
    PriceObservation,
    PullRateObservation,
    Venue,
)
from pokequant_core.valuation import PriceBasis, PriceVector, select_prices

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "research/experiments/main.yaml"
BENCH = ROOT / "research/experiments/sales_benchmark.yaml"
REPORTS = ROOT / "research/reports"
PANEL = REPORTS / "price_panel.csv"
RATIOS = REPORTS / "price_ratios.csv"
RELAY = REPORTS / "price_relay_check.csv"
REPORT = REPORTS / "sales_benchmark.md"
SET_NAMES = {"sv07": "Stellar Crown", "sv08": "Surging Sparks", "sv10": "Destined Rivals"}
BASES = {
    "tcgplayer_market": ("tcgplayer", "market"),
    "cardmarket_avg30_usd": ("cardmarket", "avg30"),
}


def _replace_rows(path: Path, day: str, rows: Sequence[dict[str, Any]], fields: list[str]) -> None:
    """Rewrite ``path`` with the rows of ``day`` replaced (one CSV per table)."""
    old: list[dict[str, str]] = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            old = [r for r in csv.DictReader(f) if r["date"] != day]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in sorted([*old, *rows], key=lambda r: (str(r["date"]), str(r.get("set", "")))):
            w.writerow(r)


def _fmt(x: float) -> str:
    return f"{x:.4f}"


def _tcgdex_updated(folder: Path, sets: Sequence[str]) -> str:
    """Latest Cardmarket update time relayed by TCGdex for the sets (to the hour)."""
    stamps = set()
    for card in folder.joinpath("cards").glob("*.json"):
        if card.name.endswith(".meta.json") or card.name.split("-")[0] not in sets:
            continue
        cm = (json.loads(card.read_text(encoding="utf-8")).get("pricing") or {}).get("cardmarket")
        if cm and cm.get("updated"):
            stamps.add(str(cm["updated"])[:13])
    return max(stamps) if stamps else ""


def relay_check(
    day: date, raw: Path, sets: Sequence[str], client: CachedClient, url: str, tol: float
) -> dict[str, Any] | None:
    """Compare TCGdex-relayed avg30 with Cardmarket's official guide (same day)."""
    path = raw / "cardmarket" / day.isoformat() / "price_guide_6.json"
    if not path.exists() and day != datetime.now(UTC).date():
        return None  # the official file only exists for "today"
    try:
        guide = client.get_json(url, path).data
    except SourceUnavailableError:
        return None
    by_id = {g["idProduct"]: g for g in guide["priceGuides"]}
    matched = equal = close = 0
    for card in sorted((raw / "tcgdex" / day.isoformat() / "cards").glob("*.json")):
        if card.name.endswith(".meta.json") or card.name.split("-")[0] not in sets:
            continue
        cm = (json.loads(card.read_text(encoding="utf-8")).get("pricing") or {}).get("cardmarket")
        if not cm or cm.get("avg30") is None or cm.get("idProduct") not in by_id:
            continue
        official = by_id[cm["idProduct"]].get("avg30")
        if official is None:
            continue
        matched += 1
        gap = abs(float(official) - float(cm["avg30"]))
        equal += gap <= tol
        close += gap <= 0.05 * max(float(official), 0.01)
    return {
        "date": day.isoformat(),
        "matched": matched,
        "equal_share": _fmt(equal / matched) if matched else "",
        "within_5pct_share": _fmt(close / matched) if matched else "",
        "tcgdex_updated": _tcgdex_updated(raw / "tcgdex" / day.isoformat(), sets),
        "guide_created": guide.get("createdAt", ""),
    }


def run(day: date, offline: bool) -> None:
    cfg = load_experiment(MAIN)
    bench = yaml.safe_load(BENCH.read_text(encoding="utf-8"))
    processed = ROOT / f"data/processed/pokelife-{cfg.data.pokelife}_tcgdex-{day.isoformat()}"
    if not processed.exists():
        raise SystemExit(
            f"missing {processed}; run `pokequant ingest --pokelife {cfg.data.pokelife} "
            f"--tcgdex {day.isoformat()} --sets {','.join(cfg.sets)}` first"
        )
    printings = read_records(processed / "printings.parquet", CardPrinting)
    rates = read_records(processed / "pull_rates.parquet", PullRateObservation)
    observations = read_records(processed / "prices.parquet", PriceObservation)
    with CachedClient(offline=offline) as client:
        fx: FxRate = ecb_rate(client, day, ROOT / "data/raw/ecb")
        relay = relay_check(
            day,
            ROOT / "data/raw",
            cfg.sets,
            client,
            bench["relay_check"]["official_file"],
            float(bench["relay_check"]["tolerance_eur"]),
        )
    usd = to_usd(observations, bench["sale_price"]["statistic"], fx)
    every = [*observations, *usd]
    q1 = bench["q1"]
    panel_rows: list[dict[str, Any]] = []
    ratio_rows: list[dict[str, Any]] = []
    for set_id in cfg.sets:
        for basis_name, (venue, stat) in BASES.items():
            c = with_basis(cfg, day, venue, stat)
            for be in break_even(c, set_id, printings, rates, every, basis_name, q1["scenarios"]):
                evaluable = be.coverage >= q1["min_hit_coverage"]
                panel_rows.append(
                    {
                        "date": day.isoformat(),
                        "set": set_id,
                        "basis": basis_name,
                        "scenario": be.scenario,
                        "mean": _fmt(be.mean),
                        "low": _fmt(be.low),
                        "high": _fmt(be.high),
                        "hit_coverage": _fmt(be.coverage),
                        "holds": ("yes" if be.high < q1["booster_cost"] else "no")
                        if evaluable
                        else "not evaluable",
                        "usd_per_eur": _fmt(fx.usd_per_eur),
                        "fx_date": fx.rate_date.isoformat(),
                    }
                )
        ctx = build_context(
            with_basis(cfg, day, "tcgplayer", "market"), set_id, printings, rates, observations
        )
        pools = drawable_pools(ctx.posterior)
        hits = [p for name in HIT_POOLS for p in pools.get(name, [])]

        def vec(venue: Venue, cur: Currency, stat: str) -> PriceVector:
            return select_prices(
                every, PriceBasis(venue, cur, "provider_market", stat, "unspecified", day)
            )

        avg30_usd = vec("cardmarket", "USD", "avg30")
        pairs = {
            "avg30_usd/tcgplayer_market": (avg30_usd, vec("tcgplayer", "USD", "market")),
            "avg30/cardmarket_trend": (
                vec("cardmarket", "EUR", "avg30"),
                vec("cardmarket", "EUR", "trend"),
            ),
        }
        for name, (num, den) in pairs.items():
            r = paired_ratios(num, den, hits)
            row: dict[str, Any] = {
                "date": day.isoformat(),
                "set": set_id,
                "ratio": name,
                "n": len(r),
            }
            if len(r) >= bench["q2"]["min_n"]:
                s = ratio_summary(r, bench["q2"]["bootstrap_resamples"], bench["q2"]["seed"])
                row.update(
                    median=_fmt(s.median),
                    q1=_fmt(s.q1),
                    q3=_fmt(s.q3),
                    low=_fmt(s.low),
                    high=_fmt(s.high),
                )
            ratio_rows.append(row)
    d = day.isoformat()
    _replace_rows(PANEL, d, panel_rows, list(panel_rows[0]))
    _replace_rows(
        RATIOS, d, ratio_rows, ["date", "set", "ratio", "n", "median", "q1", "q3", "low", "high"]
    )
    if relay is not None:
        _replace_rows(RELAY, d, [relay], list(relay))
    write_report(bench)
    print(f"wrote {PANEL.name}, {RATIOS.name}, {REPORT.name} for {d}")


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_report(bench: dict[str, Any]) -> None:
    panel, ratios, relay = _read(PANEL), _read(RATIOS), _read(RELAY)
    dates = sorted({r["date"] for r in panel})
    last = dates[-1]
    lines = [
        "# Sale-price benchmark and weekly price panel",
        "",
        "Generated by `scripts/sales_benchmark.py` (ADR 0014, tag `prereg-v3`). Exploratory",
        "extension: the main analysis (`analysis-v1`) is unchanged. Cardmarket `avg30` is",
        "the venue's average sale price over the last 30 days (EUR), converted to USD at",
        "the ECB reference rate. Derived statistics only (ADR 0009).",
        "",
        f"Snapshot dates so far: {', '.join(dates)} "
        f"({len(dates)} of {len(bench['panel']['dates'])} planned).",
        "",
        f"## Q1. Break-even booster price b* on {last} (USD, posterior mean [95 % interval])",
        "",
        "| Set | Basis | Scenario | b* | Hit coverage | Holds (upper < 4.49) |",
        "|---|---|---|---|---|---|",
    ]
    for r in (r for r in panel if r["date"] == last):
        lines.append(
            f"| {SET_NAMES.get(r['set'], r['set'])} | {r['basis']} | {r['scenario']} | "
            f"{float(r['mean']):.2f} [{float(r['low']):.2f}, {float(r['high']):.2f}] | "
            f"{float(r['hit_coverage']):.0%} | {r['holds']} |"
        )
    fx = next(r for r in panel if r["date"] == last)
    lines += [
        "",
        f"Exchange rate: {float(fx['usd_per_eur']):.4f} USD per EUR (ECB, {fx['fx_date']}).",
        "C1' is the central row, C2' the gross row (ADR 0014, item 3).",
        "",
        f"## Q2. Price ratios over hit printings on {last}",
        "",
        "| Set | Ratio | n | Median [95 % CI] | Quartiles | Implied haircut 1 - median |",
        "|---|---|---|---|---|---|",
    ]
    for r in (r for r in ratios if r["date"] == last):
        if r.get("median"):
            med = float(r["median"])
            hair = f"{1 - med:.2f}" if r["ratio"].endswith("tcgplayer_market") else "n/a"
            lines.append(
                f"| {SET_NAMES.get(r['set'], r['set'])} | {r['ratio']} | {r['n']} | "
                f"{med:.2f} [{float(r['low']):.2f}, {float(r['high']):.2f}] | "
                f"{float(r['q1']):.2f}-{float(r['q3']):.2f} | {hair} |"
            )
        else:
            lines.append(
                f"| {SET_NAMES.get(r['set'], r['set'])} | {r['ratio']} | {r['n']} | "
                "fewer than 5 printings | n/a | n/a |"
            )
    haircuts = ", ".join(f"{h:.2f}" for h in bench["q2"]["haircuts_compared"])
    lines += [
        "",
        f"Scenario haircuts for comparison: {haircuts}. The cross-venue ratio mixes two",
        "markets (EU, US) and two price types, so the implied haircut is descriptive only.",
        "",
        "## Q3. Panel over dates (central and gross b*, posterior mean)",
        "",
        "| Date | Set | Basis | Central b* | Gross b* | C1' | C2' |",
        "|---|---|---|---|---|---|---|",
    ]
    key = {(r["date"], r["set"], r["basis"], r["scenario"]): r for r in panel}
    for d in dates:
        for s in SET_NAMES:
            for b in BASES:
                c, g = key.get((d, s, b, "central")), key.get((d, s, b, "gross"))
                if c and g:
                    lines.append(
                        f"| {d} | {SET_NAMES[s]} | {b} | {float(c['mean']):.2f} | "
                        f"{float(g['mean']):.2f} | {c['holds']} | {g['holds']} |"
                    )
    lines += ["", "**H4 (dates).** "]
    if len(dates) < 2:
        lines[-1] += "Not testable yet: one snapshot date."
    else:
        changed = sorted(
            {
                (s, b)
                for s in SET_NAMES
                for b in BASES
                for sc in ("central", "gross")
                if len({key[(d, s, b, sc)]["holds"] for d in dates if (d, s, b, sc) in key}) > 1
            }
        )
        lines[-1] += (
            "Supported: C1' or C2' changes across dates for "
            + ", ".join(f"{SET_NAMES[s]} ({b})" for s, b in changed)
            + "."
            if changed
            else f"Not supported over {len(dates)} dates: C1' and C2' never change."
        )
    lines += ["", "## V1. Relay check (TCGdex avg30 vs Cardmarket official price guide)", ""]
    if relay:
        lines += [
            "| Date | Matched printings | Equal within 0.01 EUR | Within 5 % | "
            "Official file created | TCGdex Cardmarket update (UTC hour) |",
            "|---|---|---|---|---|---|",
        ]
        for r in relay:
            share = float(r["equal_share"]) if r["equal_share"] else float("nan")
            flag = " (below 95 %: flagged)" if share < bench["relay_check"]["flag_below"] else ""
            close = float(r["within_5pct_share"]) if r.get("within_5pct_share") else float("nan")
            lines.append(
                f"| {r['date']} | {r['matched']} | {share:.1%}{flag} | {close:.1%} | "
                f"{r['guide_created']} | {r.get('tcgdex_updated', '')} |"
            )
        lines += [
            "",
            "The pre-registered criterion is equality within 0.01 EUR. The 5 % column and",
            "the update times are a diagnostic added after the first run (not",
            "pre-registered). TCGdex's Cardmarket prices predate the official file,",
            "so part of the gap is probably one day of new sales.",
        ]
    else:
        lines.append("No official file was available for the snapshot dates so far.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", type=date.fromisoformat, default=datetime.now(UTC).date())
    parser.add_argument("--offline", action="store_true")
    parser.add_argument(
        "--panel-only", action="store_true", help="do nothing unless --date is a panel date"
    )
    args = parser.parse_args()
    if args.panel_only:
        bench = yaml.safe_load(BENCH.read_text(encoding="utf-8"))
        planned = {str(d) for d in bench["panel"]["dates"]}
        if args.date.isoformat() not in planned:
            print(f"{args.date} is not a panel date (ADR 0014); nothing to do")
            return
    run(args.date, args.offline)


if __name__ == "__main__":
    main()
