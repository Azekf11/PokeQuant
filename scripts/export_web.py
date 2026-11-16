"""Export the aggregate results read by the static web demo (apps/web/data/results.json).

The demo shows fourteen sets: the three main sets from the main run
(analysis-v1), the seven sets added by the ten-set run (ADR 0015) and the four
Mega Evolution sets from the central-layout run (ADR 0016). The hypotheses are
those of the main run; H4 is also given over the fourteen sets (ten-set run and
Mega run, as in research/reports/mega_sets.md).

Only derived statistics leave the machine (ADR 0009): metrics over simulated
openings, break-even prices, hypothesis statuses and a pre-computed break-even
grid. No printing identifier and no per-card price is written; E2 targets are
named by rarity only. The output is deterministic for given runs, so the
committed file can be checked against a fresh export.

Usage: uv run python scripts/export_web.py results/<main run> results/<ten-set run>
       results/<Mega run> [--out apps/web/data/results.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from pokequant_core.analysis import comparison_rows, hypotheses
from pokequant_core.comparator import build_context
from pokequant_core.experiment import ExperimentConfig, load_experiment
from pokequant_core.experiment_run import processed_dir
from pokequant_core.ingest.store import read_records
from pokequant_core.metrics import epistemic_interval
from pokequant_core.schemas import CardPrinting, CardSet, PriceObservation, PullRateObservation
from pokequant_core.web import break_even_grid, card_level_leaks

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps/web/data/results.json"
METRICS = ("mean", "median", "p_loss", "cvar05", "q05", "q95", "p_gain")
PRICE_ATTRIBUTION = (
    "Price data: TCGdex (tcgdex.dev), relaying TCGplayer (USD) prices; used with permission."
)
RATE_ATTRIBUTION = (
    'Pull rates: Poké Life, "Pokémon TCG pull-rate evidence registry," '
    "https://www.poke-life.com/data/ (version 2026-11-13, accessed 2026-11-15). CC BY 4.0."
)
CATALOGUE_ATTRIBUTION = "Card catalogue: TCGdex (tcgdex.dev), MIT."


def r(x: float, digits: int = 4) -> float:
    return float(round(float(x), digits))


def summary(values: list[float] | np.ndarray, digits: int = 4) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    low, high = epistemic_interval(arr)
    return {"mean": r(arr.mean(), digits), "low": r(low, digits), "high": r(high, digits)}


def scenario_info(cfg: ExperimentConfig) -> list[dict[str, Any]]:
    out = []
    for s in cfg.cost_scenarios:
        keep = (1 - s.liquidity_haircut) * (1 - s.marketplace_fee_rate - s.payment_fee_rate)
        out.append(
            {
                "name": s.name,
                "booster_cost": s.booster_cost,
                "marketplace_fee_rate": s.marketplace_fee_rate,
                "payment_fee_rate": s.payment_fee_rate,
                "selling_fixed_fee": s.selling_fixed_fee,
                "shipping_per_sale": s.shipping_per_sale,
                "buyer_shipping": s.buyer_shipping,
                "liquidity_haircut": s.liquidity_haircut,
                "keep": r(keep, 6),
                "fixed": r(s.selling_fixed_fee + s.shipping_per_sale, 6),
                "description": " ".join(s.description.split()),
            }
        )
    return out


GROUPS = {
    "main": "Main analysis (pre-registered, tag analysis-v1)",
    "extension": "Ten-set extension (ADR 0015, tag prereg-v4)",
    "mega": "Mega Evolution extension (ADR 0016, tag prereg-v5)",
}
FLAGGED = ("sv02", "sv04")  # duplicate rule F1, research/reports/pull_rate_checks.md
MAIN_SETS = ("sv07", "sv08", "sv10")


def set_note(group: str, set_id: str) -> str:
    if group == "extension" and set_id in FLAGGED:
        return (
            "Its primary source prints two rates identical to another set's (duplicate rule "
            "F1); removing the two flagged sets changes no conclusion."
        )
    if group == "mega":
        return (
            "The slot of the Mega Hyper Rare is not documented. Shown: second reverse slot; "
            "with the rare slot instead, the break-even price moves by at most 0.01 USD."
        )
    return ""


def run_part(run_dir: Path, root: Path, group: str, keep: tuple[str, ...] | None) -> dict[str, Any]:
    """Rows, break-even prices, E2 targets and grids of the kept sets of one run."""
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    run = manifest["run"]
    params = run["parameters"]
    cfg = load_experiment(root / params["config"])
    sets = [s for s in cfg.sets if keep is None or s in keep]
    data = processed_dir(root, cfg)
    printings = read_records(data / "printings.parquet", CardPrinting)
    rates = read_records(data / "pull_rates.parquet", PullRateObservation)
    prices = read_records(data / "prices.parquet", PriceObservation)
    names = {s.set_id: s.name for s in read_records(data / "sets.parquet", CardSet)}
    rarity = {p.printing_id: p.rarity for p in printings}
    kept = [res for res in results if res["set_id"] in sets]

    rows = []
    for res in kept:
        for row in comparison_rows(res):
            if row["metric"] not in METRICS:
                continue
            rows.append(
                {
                    "set": row["set_id"],
                    "estimand": row["estimand"],
                    "label": row["label"],
                    "scenario": row["scenario"],
                    "metric": row["metric"],
                    "a_mean": r(row["a_mean"]),
                    "a_low": r(row["a_low"]),
                    "a_high": r(row["a_high"]),
                    "a_mc_se": r(row["a_mc_se"], 6),
                    "b": r(row["b"]),
                    "share_a_better": r(row["share_a_better"], 3),
                    "verdict": row["verdict"],
                }
            )
    break_even = {}
    e2 = []
    for res in kept:
        if res["job"]["label"] == "n=1":
            be = res["extra"]["break_even_booster_price"]
            break_even[res["set_id"]] = {s: summary(be[s]) for s in res["scenarios"]}
        if res["job"]["estimand"] == "E2":
            e2.append(
                {
                    "set": res["set_id"],
                    "label": res["job"]["label"],
                    "rarity": rarity[res["extra"]["target"]],
                    "packs_per_hit": summary(1 / np.asarray(res["extra"]["p_hit"]), 1),
                    "n_max": res["extra"]["n_max"],
                }
            )
    grids = {}
    for i, set_id in enumerate(cfg.sets):
        if set_id not in sets:
            continue
        ctx = build_context(cfg, set_id, printings, rates, prices)
        if ctx.index != i:
            raise RuntimeError("set order differs from the config")
        grids[set_id] = break_even_grid(ctx, cfg.simulation.seed, params["epistemic_draws"])
    leaks = card_level_leaks({"rows": rows, "e2": e2, "grids": grids}, rarity)
    if leaks:
        raise RuntimeError(f"card-level data in the web export (ADR 0009): {leaks[:5]}")
    return {
        "cfg": cfg,
        "results": results,
        "run": {
            "group": group,
            "label": GROUPS[group],
            "run_id": run["run_id"],
            "config": params["config"],
            "seed": run["seed"],
            "results_sha256": manifest["results_sha256"],
        },
        "sets": [
            {
                "id": s,
                "name": names.get(s, s),
                "group": group,
                "run_id": run["run_id"],
                "note": set_note(group, s),
            }
            for s in sets
        ],
        "rows": rows,
        "break_even": break_even,
        "e2": e2,
        "grids": grids,
    }


def export(main_dir: Path, ten_dir: Path, mega_dir: Path, root: Path) -> dict[str, Any]:
    main = run_part(main_dir, root, "main", None)
    added = tuple(s for s in load_experiment_of(ten_dir, root).sets if s not in MAIN_SETS)
    ten = run_part(ten_dir, root, "extension", added)
    mega = run_part(mega_dir, root, "mega", None)
    parts = (main, ten, mega)
    cfg = main["cfg"]
    for part in parts[1:]:
        other = part["cfg"]
        if scenario_info(other) != scenario_info(cfg) or (
            other.estimands.E1.budgets_in_packs != cfg.estimands.E1.budgets_in_packs
        ):
            raise RuntimeError(f"{part['run']['run_id']}: scenarios or budgets differ")
    run = main["run"]
    verdicts = hypotheses(main["results"])
    h4_all = hypotheses([*ten["results"], *mega["results"]])["H4"]
    return {
        "meta": {
            "title": "Opening or Buying?",
            "run_id": run["run_id"],
            "config": run["config"],
            "seed": run["seed"],
            "epistemic_draws": cfg.simulation.epistemic_draws,
            "aleatory_runs": cfg.simulation.aleatory_runs,
            "results_sha256": run["results_sha256"],
            "runs": [p["run"] for p in parts],
            "price_date": "2026-11-15",
            "price_type": "TCGplayer market price (provider aggregate, not a realised sale)",
            "currency": "USD",
            "condition": "unspecified",
            "attribution": [PRICE_ATTRIBUTION, RATE_ATTRIBUTION, CATALOGUE_ATTRIBUTION],
        },
        "sets": [s for p in parts for s in p["sets"]],
        "groups": GROUPS,
        "scenarios": scenario_info(cfg),
        "budgets": list(cfg.estimands.E1.budgets_in_packs),
        "rows": [x for p in parts for x in p["rows"]],
        "break_even": {k: v for p in parts for k, v in p["break_even"].items()},
        "e2": [x for p in parts for x in p["e2"]],
        "hypotheses": {
            h: {"status": v["status"], "evidence": v["evidence"]} for h, v in verdicts.items()
        },
        "h4_all_sets": {
            "status": h4_all["status"],
            "evidence": h4_all["evidence"],
            "runs": [ten["run"]["run_id"], mega["run"]["run_id"]],
        },
        "break_even_grid": {k: v for p in parts for k, v in p["grids"].items()},
    }


def load_experiment_of(run_dir: Path, root: Path) -> ExperimentConfig:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    return load_experiment(root / manifest["run"]["parameters"]["config"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("main_run", type=Path)
    parser.add_argument("ten_set_run", type=Path)
    parser.add_argument("mega_run", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    payload = export(args.main_run, args.ten_set_run, args.mega_run, args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    args.out.write_text(text + "\n", "utf-8")
    # Same payload as a script, loaded by the page without any request at run time.
    args.out.with_suffix(".js").write_text(f"window.POKEQUANT = {text};\n", "utf-8")
    print(f"wrote {args.out} and .js ({args.out.stat().st_size / 1024:.0f} KiB each)")


if __name__ == "__main__":
    main()
