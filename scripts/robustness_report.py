"""Generate research/reports/robustness.md and the tornado plot from the robustness runs.

Reads results/<run_id>/robustness/ written by
`pokequant robustness research/experiments/main.yaml` and the main run
results/<run_id>/results.json. Every check follows ADR 0012; no per-card price
is published (ADR 0009).

Usage: uv run python scripts/robustness_report.py results/<run_id>
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from pokequant_core.experiment import load_experiment
from pokequant_core.metrics import DIRECTION, compare, epistemic_interval
from pokequant_core.robustness import (
    Variant,
    advantage,
    check_conclusions,
    hypothesis_statuses,
    variant_results,
    variants,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "research/reports/robustness.md"
FIGURE = ROOT / "research/reports/figures/tornado.png"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
FIRST, SECOND = "#2a78d6", "#eb6834"  # categorical slots 1 and 2
TICK = {True: "yes", False: "**no**"}


def name(v: Variant) -> str:
    return "baseline" if v.id == "baseline" else f"{v.id}: {v.label}"


def tornado(rows: list[tuple[str, list[Variant]]], data: dict[str, Any], sets: list[str]) -> None:
    """Deviation from the baseline of b* (central) and of the n=36 advantage, per set."""
    base = data["baseline"]
    measures = (
        ("be", "Break-even booster price b*, central (USD)"),
        ("adv", "Mean advantage of opening, 36 boosters, central (USD)"),
    )

    def dev(v: Variant, key: str, s: str) -> float | None:
        x = data[name(v)][key].get(s)
        return None if x is None else x - base[key][s]

    order = sorted(
        rows,
        key=lambda r: max(
            (abs(d) for v in r[1] for s in sets for d in [dev(v, "be", s)] if d is not None),
            default=0.0,
        ),
    )
    fig, axes = plt.subplots(2, len(sets), figsize=(3.4 * len(sets), 7.5), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    for r, (key, title) in enumerate(measures):
        for c, s in enumerate(sets):
            ax = axes[r][c]
            ax.set_facecolor(SURFACE)
            for y, (_, group) in enumerate(order):
                for k, v in enumerate(group):
                    d = dev(v, key, s)
                    if d is None:
                        continue
                    ax.barh(
                        y + (0.2 if len(group) > 1 and k else -0.2 if len(group) > 1 else 0),
                        d,
                        height=0.36 if len(group) > 1 else 0.6,
                        color=SECOND if k else FIRST,
                        edgecolor=SURFACE,
                        linewidth=1,
                    )
            ax.axvline(0, color=INK, linewidth=0.8)
            ax.grid(axis="x", color=GRID, linewidth=0.6)
            ax.set_axisbelow(True)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            ax.tick_params(colors=MUTED, labelsize=8)
            ax.set_title(f"{s}: baseline {base[key][s]:.2f}", fontsize=9, color=INK)
            if c == 0:
                ax.set_yticks(range(len(order)), [g for g, _ in order], fontsize=8, color=INK)
        fig.text(
            0.5,
            0.965 - r * 0.485,
            title + ": change from baseline",
            ha="center",
            fontsize=10,
            color=INK,
        )
    handles = [Rectangle((0, 0), 1, 1, color=x) for x in (FIRST, SECOND)]
    fig.legend(
        handles,
        ["single or first setting", "second setting"],
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.96), h_pad=3)
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=150, metadata={"Software": None})
    plt.close(fig)


def r7_table(folder: Path, all_variants: Sequence[Variant], sets: list[str]) -> list[str]:
    runs = [
        ("1,000", "R7-m1000"),
        ("10,000", "R7-m10000"),
        ("20,000 (baseline)", "values"),
        ("100,000", "R7-m100000"),
    ]
    lines = [
        "| Set | Runs per draw | mean Π (n=36) | MC SE | CVaR 5 % (n=36) | MC SE "
        "| P(K < a), top_sir | MC SE | Verdicts changed vs baseline |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    # One variant per run; "values" stands for the baseline (no replaced column).
    by_run = {v.run: v for v in all_variants if v.id in ("baseline", "R7")}
    base = {(r["set_id"], r["job"]["label"]): r for r in variant_results(folder, by_run["values"])}
    for s in sets:
        for label, run in runs:
            res = {
                (r["set_id"], r["job"]["label"]): r for r in variant_results(folder, by_run[run])
            }
            e1, e2 = res[s, "n=36"], res[s, "top_sir"]
            cells = []
            for r, m in ((e1, "mean"), (e1, "cvar05"), (e2, "p_gain")):
                a = np.asarray(r["a_metrics"]["central"][m])
                lo, hi = epistemic_interval(a)
                fmt = "{:.3f}" if m == "p_gain" else "{:.2f}"
                cells.append(f"{fmt.format(a.mean())} [{fmt.format(lo)}, {fmt.format(hi)}]")
                cells.append(fmt.format(float(np.median(r["a_se"]["central"][m]))))
            changed = sum(
                1
                for key, r in res.items()
                if key[0] == s
                for m in ("mean", "median", "cvar05")
                if _verdict(r, m) != _verdict(base[key], m)
            )
            lines.append(f"| {s} | {label} | " + " | ".join(cells) + f" | {changed} of 18 |")
    return lines


def _verdict(r: dict[str, Any], m: str) -> str:
    a = np.asarray(r["a_metrics"]["central"][m])
    return compare(a, r["b_metrics"]["central"][m], DIRECTION[m])[1]


def main(run_dir: Path) -> None:
    folder = run_dir / "robustness"
    manifest = json.loads((folder / "manifest.json").read_text())
    main_manifest = json.loads((run_dir / "manifest.json").read_text())
    cfg = load_experiment(ROOT / manifest["config"])
    cost = cfg.scenario("central").booster_cost
    sets = list(cfg.sets)
    all_variants = variants()

    data: dict[str, Any] = {}
    for v in all_variants:
        res = variant_results(folder, v)
        c = check_conclusions(res, cost, single_model=v.single_model)
        hyp = {} if v.single_model else hypothesis_statuses(res)
        if v.id == "R11":
            hyp = {h: x for h, x in hyp.items() if h != "H4"}  # one set: H4 not applicable
        data[name(v)] = {
            "variant": v,
            "checks": c,
            "be": {s: x["central"][0] for s, x in c["break_even"].items()},
            "be_ci": c["break_even"],
            "adv": advantage(res, "n=36"),
            "hyp": hyp,
            "n_jobs": len(res),
        }

    # Baseline vs the main run: same draws, same openings (CRN), same numbers.
    main_res = {
        (r["set_id"], r["job"]["label"]): r
        for r in json.loads((run_dir / "results.json").read_text())
    }
    worst = 0.0
    for r in variant_results(folder, all_variants[0]):
        m = main_res[r["set_id"], r["job"]["label"]]
        for s in r["scenarios"]:
            for k, xs in r["a_metrics"][s].items():
                worst = max(worst, float(np.max(np.abs(np.asarray(xs) - m["a_metrics"][s][k]))))

    rows: list[tuple[str, list[Variant]]] = []
    for v in all_variants:
        if v.id in ("baseline", "R7"):
            continue  # R7 does not change b*; see its own table
        group = next((g for g in rows if g[0] == v.id), None)
        if group:
            group[1].append(v)
        else:
            rows.append((v.id, [v]))
    tornado(rows, data, sets)

    base_h = data["baseline"]["hyp"]
    lines = [
        "# Robustness and sensitivity (Table 4)",
        "",
        "Generated by `scripts/robustness_report.py` from",
        f"`{run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir}/robustness`",
        f"(seed {manifest['seed']}, {manifest['epistemic_draws']} epistemic draws; config",
        f"`{manifest['config']}`, sha256 `{manifest['config_sha256'][:12]}…`). Test definitions",
        "and the checks C1-C3: [ADR 0012]"
        "(../../docs/decisions/0012-operational-robustness-tests.md).",
        "Regenerate with:",
        "",
        "```bash",
        f"uv run pokequant robustness {manifest['config']}",
        f"uv run python scripts/robustness_report.py results/{run_dir.name}",
        "```",
        "",
        "Every variant uses the seed of the main run. Variants that only change card",
        "values (R1, R2, R3, R10) are value columns of one run and are valued on the",
        "very same simulated openings as the baseline (common random numbers). The",
        "baseline of that run reproduces the main run",
        f"`{main_manifest['run']['run_id']}`: the largest difference over every metric,",
        f"draw and scenario is {worst:.2e} USD.",
        "",
        "Conclusions checked (central scenario):",
        "",
        "- **C1**: opening loses on average, for every set and budget (95 % interval",
        "  of mean Π_A below 0);",
        f"- **C2**: the break-even booster price b* is below {cost:.2f} USD, central and",
        "  gross, for every set (upper 95 % bound);",
        "- **C3**: buying is decisively better on mean, median and CVaR 5 % for every",
        "  set, every budget of 10 boosters or more and every E2 target.",
        "",
        "## 1. Table 4: conclusions under each variant",
        "",
        "b* is the central break-even booster price (posterior mean, USD); Δ36 is the",
        "mean advantage of opening over buying for a 36-booster budget (mean Π_A -",
        "Π_B, USD, central). Hypothesis columns show a status only when it differs",
        "from the baseline (`=` otherwise).",
        "",
        "| Variant | "
        + " | ".join(f"b* {s}" for s in sets)
        + " | "
        + " | ".join(f"Δ36 {s}" for s in sets)
        + " | C1 | C2 | C3 | H1 | H2 | H3 |",
        "|---|" + "---|" * (2 * len(sets) + 6),
    ]
    for key, d in data.items():
        c = d["checks"]
        be = " | ".join(f"{d['be'][s]:.2f}" if s in d["be"] else "n/a" for s in sets)
        adv = " | ".join(f"{d['adv'][s]:.1f}" if s in d["adv"] else "n/a" for s in sets)
        cols: list[str] = []
        for h in ("H1", "H2", "H3"):
            st = d["hyp"].get(h)
            cols.append(
                "n/a" if st is None else "=" if st == base_h[h] or key == "baseline" else st
            )
        if key == "baseline":
            cols = [base_h[h] for h in ("H1", "H2", "H3")]
        lines.append(
            f"| {key} | {be} | {adv} | {TICK[c['C1']['holds']]} | {TICK[c['C2']['holds']]} "
            f"| {TICK[c['C3']['holds']]} | " + " | ".join(cols) + " |"
        )
    lines += [
        "",
        "R4 rows are single models at the bounds of every hit rate (no epistemic",
        "draws; decisive means |A - B| > 3 Monte Carlo SE). R5 runs E1 only. R11",
        "concerns sv07 only. `n/a`: not applicable.",
        "",
        "## 2. Where a conclusion fails",
        "",
    ]
    failures = [
        (key, ck, item)
        for key, d in data.items()
        for ck in ("C1", "C2", "C3")
        for item in d["checks"][ck]["fails"]
    ]
    if failures:
        lines += [f"- {key}, {ck}: {item}" for key, ck, item in failures]
    else:
        lines.append("- None: C1, C2 and C3 hold in every variant.")
    held = {ck: sum(d["checks"][ck]["holds"] for d in data.values()) for ck in ("C1", "C2", "C3")}
    lines += [
        "",
        f"Summary over {len(data)} rows (baseline included): C1 holds in {held['C1']},",
        f"C2 in {held['C2']}, C3 in {held['C3']}.",
        "",
        "## 3. Break-even booster price with intervals",
        "",
        "| Variant | "
        + " | ".join(f"{s} central" for s in sets)
        + " | "
        + " | ".join(f"{s} gross" for s in sets)
        + " |",
        "|---|" + "---|" * (2 * len(sets)),
    ]
    for key, d in data.items():
        if d["variant"].id == "R7":
            continue
        cells = []
        for sc in ("central", "gross"):
            for s in sets:
                x = d["be_ci"].get(s, {}).get(sc)
                cells.append(
                    "n/a"
                    if x is None
                    else f"{x[0]:.2f}"
                    if x[1] == x[2]
                    else f"{x[0]:.2f} [{x[1]:.2f}, {x[2]:.2f}]"
                )
        lines.append(f"| {key} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## 4. Tornado plot",
        "",
        "![Tornado plot](figures/tornado.png)",
        "",
        "Change from the baseline of the central b* (top) and of the 36-booster mean",
        "advantage of opening (bottom). Paired tests (R2, R3, R4) show both settings:",
        "blue is the first (h = 0.30, x0.5, lower bounds), orange the second.",
        "",
        "## 5. R7: number of simulated runs",
        "",
        "Posterior mean [95 % interval] over the 200 draws and median Monte Carlo",
        "standard error within a draw, central scenario. The last column counts",
        "the mean, median and CVaR verdicts (6 jobs x 3 metrics) that differ from",
        "the baseline.",
        "",
        *r7_table(folder, all_variants, sets),
        "",
        "## 6. R6 and R13",
        "",
        "- **R6 (several sets).** The main run already compares the three sets; the",
        "  across-set half of H4 is not supported (see results.md, §4).",
        "- **R13 (TCGplayer-only rates).** Not run: the homogeneity rule did not reject",
        "  pooling (ADR 0010, item 6).",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(ROOT)} and {FIGURE.relative_to(ROOT)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
