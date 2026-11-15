"""Figures of the paper (protocol §8), written to research/paper/figures/.

Figures 1-2 are diagrams of the pipeline and of the slot model. Figures 3-5
re-simulate openings at the posterior-mean pull rates with their own random
streams (seed, set, 3, k), so they never reuse the streams of the main run.
Figures 6-7 read the main run and, for Figure 6, its robustness variants.
Figure 8 shows the convergence of the Monte Carlo estimates against the exact
mean, and Figure 9 the posterior draws of the break-even price; both also
write the numbers quoted in the paper to research/reports/simulation_diagnostics.md.
No per-card price is shown (ADR 0009).

Usage: uv run python scripts/paper_figures.py results/<run_id>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from pokequant_core.booster import LAYOUTS
from pokequant_core.comparator import SetContext, _stream, build_context
from pokequant_core.experiment import ExperimentConfig, load_experiment
from pokequant_core.experiment_run import processed_dir
from pokequant_core.ingest.store import read_records
from pokequant_core.metrics import epistemic_interval
from pokequant_core.schemas import CardPrinting, CardSet, PriceObservation, PullRateObservation
from pokequant_core.simulate import simulate_e1, slot_card_probabilities

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = ROOT / "research/reports/simulation_diagnostics.md"
CONVERGENCE_RUNS = 100_000
OUT = ROOT / "research/paper/figures"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")  # categorical slots 1-3 (sets, or A/B)
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
PACKS = 200_000  # single-pack values for Figure 3
RUNS = 20_000
SOURCE = "Prices: TCGplayer market price (provider aggregate), USD, 2026-11-15."

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK2,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "legend.frameon": False,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
    }
)


def save(fig: Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(f"wrote {OUT / name}")


def source_note(fig: Figure, text: str) -> None:
    fig.text(0.0, -0.08, text, fontsize=7, color=MUTED, ha="left", va="top")


# --- Figure 1: pipeline -----------------------------------------------------------


def _box(ax: Axes, x: float, y: float, w: float, h: float, title: str, body: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            fc="#f9f9f7",
            ec=MUTED,
            lw=0.8,
        )
    )
    ax.text(
        x + w / 2,
        y + h - 0.07,
        title,
        ha="center",
        va="top",
        fontsize=8.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + w / 2,
        y + h - 0.2,
        body,
        ha="center",
        va="top",
        fontsize=7.2,
        color=INK2,
        linespacing=1.35,
    )


def _arrow(ax: Axes, a: tuple[float, float], b: tuple[float, float]) -> None:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=9, color=INK2, lw=0.9))


def figure_1() -> None:
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    ax.set_xlim(-0.05, 4.42)
    ax.set_ylim(0, 2.1)
    ax.axis("off")
    w, h = 1.0, 0.62
    _box(ax, 0.0, 1.4, w, h, "Pull rates", "Poké Life registry\nversion 2026-11-13\n(CC BY 4.0)")
    _box(ax, 0.0, 0.72, w, h, "Catalogue", "TCGdex cards,\nnumbers, rarities\n(MIT)")
    _box(ax, 0.0, 0.04, w, h, "Prices", "TCGdex: TCGplayer\nmarket price, USD\n2026-11-15")
    _box(
        ax,
        1.12,
        1.06,
        w,
        h,
        "Booster model",
        "10 slots; Dirichlet\nposteriors (Jeffreys)\n§4.1-4.2",
    )
    _box(
        ax, 1.12, 0.04, w, h, "Card values", "Net sale l(c), purchase\na(c); 3 cost scenarios\n§5.2"
    )
    _box(
        ax,
        2.24,
        0.55,
        w,
        h,
        "Monte Carlo",
        "nested: 200 rate draws\nx 20,000 runs; seed\n20261115 (§4.3)",
    )
    _box(
        ax,
        3.35,
        1.06,
        w,
        h,
        "Results",
        "E1, E2 metrics with\nMC errors, intervals,\nverdicts, H1-H4 (§6)",
    )
    _box(ax, 3.35, 0.04, w, h, "Robustness", "R1-R12 variants,\nchecks C1-C3,\nTable 4 (§7)")
    _arrow(ax, (w, 1.71), (1.12, 1.46))
    _arrow(ax, (w, 1.03), (1.12, 1.30))
    _arrow(ax, (w, 1.03), (1.12, 0.45))
    _arrow(ax, (w, 0.35), (1.12, 0.35))
    _arrow(ax, (1.12 + w, 1.30), (2.24, 1.0))
    _arrow(ax, (1.12 + w, 0.35), (2.24, 0.75))
    _arrow(ax, (2.24 + w, 1.0), (3.35, 1.3))
    _arrow(ax, (2.24 + w, 0.75), (3.35, 0.4))
    ax.text(
        2.24 + w / 2,
        1.42,
        "Config main.yaml\n(tag prereg-v2)",
        ha="center",
        va="bottom",
        fontsize=7.2,
        color=INK2,
    )
    _arrow(ax, (2.24 + w / 2, 1.41), (2.24 + w / 2, 0.55 + h))
    save(fig, "fig1_pipeline.png")


# --- Figure 2: slot model -------------------------------------------------------


SHORT = {
    "reverse": "reverse holo",
    "ace spec rare": "ACE SPEC Rare",
    "illustration rare": "Illustration Rare",
    "special illustration rare": "Special Illus. Rare",
    "hyper rare": "Hyper Rare",
    "rare": "Rare",
    "double rare": "Double Rare",
    "ultra rare": "Ultra Rare",
    "common": "Common",
    "uncommon": "Uncommon",
}


def figure_2(ctx: SetContext) -> None:
    """Slot structure with posterior-mean outcome probabilities of one set."""
    model = ctx.posterior.mean_model()
    probs = {s.slot_id: s.outcomes for s in model.slots}
    layout = LAYOUTS["tcgplayer"]
    widths = [2.9 if spec.hits else 0.5 for spec in layout.slots]
    fig, ax = plt.subplots(figsize=(7.2, 2.2))
    ax.axis("off")
    ax.set_xlim(0, sum(widths) + 0.1)
    ax.set_ylim(0.2, 0.95)
    x = 0.0
    for spec, w in zip(layout.slots, widths, strict=True):
        random = bool(spec.hits)
        ax.add_patch(
            FancyBboxPatch(
                (x + 0.05, 0.72),
                w - 0.1,
                0.2,
                boxstyle="round,pad=0,rounding_size=0.05",
                fc=SERIES[0] if random else "#f0efec",
                ec="none",
            )
        )
        ax.text(
            x + w / 2,
            0.82,
            spec.slot_id,
            ha="center",
            va="center",
            fontsize=8.5,
            color="white" if random else INK,
            fontweight="bold",
        )
        if random:
            ranked = sorted(probs[spec.slot_id].items(), key=lambda kv: -kv[1])
            for k, (name, p) in enumerate(ranked):
                y = 0.62 - 0.11 * k
                ax.text(
                    x + 0.12,
                    y,
                    SHORT.get(name, name),
                    ha="left",
                    va="center",
                    fontsize=7,
                    color=INK2,
                )
                ax.text(
                    x + w - 0.12,
                    y,
                    f"{100 * p:.2f} %",
                    ha="right",
                    va="center",
                    fontsize=7,
                    color=INK,
                )
        else:
            ax.text(
                x + w / 2,
                0.62,
                SHORT[spec.residual],
                ha="center",
                va="top",
                fontsize=6.5,
                color=INK2,
                rotation=90,
            )
        x += w
    ax.set_title(
        f"Slot model of one booster ({ctx.set_id}): posterior-mean probabilities "
        "of the random slots",
        loc="left",
    )
    source_note(
        fig,
        "Rates: Poké Life registry, version 2026-11-13. Grey slots always hold "
        "a card of their pool; the Basic Energy and code card are not modelled.",
    )
    save(fig, "fig2_slots.png")


# --- Figures 3-5: re-simulated openings -------------------------------------------


def pack_values(ctx: SetContext, seed: int, key: int, n_packs: int, runs: int) -> np.ndarray:
    """Sum of l(c) over n packs, shape (runs, scenarios), at the posterior-mean rates."""
    cm = ctx.compile(ctx.posterior.mean_model())
    values = ctx.value_matrix(cm)
    zero = np.zeros(len(ctx.scenarios))
    return simulate_e1(
        cm, values, _stream(seed, ctx.index, 3, key), n_packs=n_packs, booster_cost=zero, runs=runs
    )


def figure_3(contexts: list[SetContext], names: dict[str, str], seed: int, cost: float) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    for ax, scenario in zip(axes, ("gross", "central"), strict=True):
        for color, ctx in zip(SERIES, contexts, strict=True):
            v = pack_values(ctx, seed, 0, 1, PACKS)[:, ctx.scenarios.index(scenario)]
            x = np.sort(v)
            ccdf = 1.0 - np.arange(1, x.size + 1) / x.size
            keep = x > 0
            ax.step(
                x[keep],
                np.maximum(ccdf[keep], 1 / x.size),
                where="post",
                color=color,
                lw=1.4,
                label=f"{names[ctx.set_id]} (mean {v.mean():.2f})",
            )
        ax.axvline(cost, color=INK2, lw=1, ls="--")
        ax.text(
            cost * 1.08,
            0.5,
            f"booster {cost:.2f}",
            color=INK2,
            fontsize=7,
            rotation=90,
            va="center",
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Value of one pack, USD (log)")
        ax.set_title(f"{scenario.capitalize()} values", loc="left")
        ax.legend(fontsize=7, loc="lower left")
    axes[0].set_ylabel("P(value > x) (log)")
    source_note(
        fig,
        f"{PACKS:,} simulated packs per set at the posterior-mean pull rates. "
        f"{SOURCE} Gross: market price; central: net of fees, shipping, haircut.",
    )
    save(fig, "fig3_pack_value.png")


def figure_4(
    contexts: list[SetContext],
    names: dict[str, str],
    seed: int,
    results: list[dict[str, Any]],
    cost: float,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
    for ax, ctx in zip(axes, contexts, strict=True):
        k = ctx.scenarios.index("central")
        profit = pack_values(ctx, seed, 1, 36, RUNS)[:, k] - 36 * cost
        x = np.sort(profit)
        ax.step(
            x,
            np.arange(1, x.size + 1) / x.size,
            where="post",
            color=SERIES[0],
            lw=1.6,
            label="A: open 36",
        )
        res = next(r for r in results if r["set_id"] == ctx.set_id and r["job"]["label"] == "n=36")
        b = res["b_metrics"]["central"]["mean"]
        ax.axvline(b, color=SERIES[1], lw=1.6, label="B: buy (fixed)")
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_title(names[ctx.set_id], loc="left")
        ax.set_xlabel("Net profit Π, USD")
    axes[0].set_ylabel("P(Π ≤ x)")
    axes[0].legend(fontsize=7, loc="upper left")
    source_note(
        fig,
        f"Central scenario, budget 36 x {cost:.2f} USD. {RUNS:,} simulated runs "
        f"at the posterior-mean pull rates. {SOURCE}",
    )
    save(fig, "fig4_profit_cdf.png")


def figure_5(contexts: list[SetContext], names: dict[str, str], seed: int, cost: float) -> None:
    prices = np.linspace(0.25, 6.0, 116)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
    for ax, ctx in zip(axes, contexts, strict=True):
        k = ctx.scenarios.index("central")
        for color, (key, n) in zip(SERIES, enumerate((1, 10, 36), start=2), strict=True):
            total = pack_values(ctx, seed, key, n, RUNS)[:, k]
            p_loss = (total[None, :] < n * prices[:, None]).mean(axis=1)
            ax.plot(prices, p_loss, color=color, lw=1.6, label=f"n = {n}")
        ax.axvline(cost, color=INK2, lw=1, ls="--")
        ax.set_title(names[ctx.set_id], loc="left")
        ax.set_xlabel("Booster price, USD")
        ax.set_ylim(-0.02, 1.02)
    axes[0].set_ylabel("P(loss) of opening")
    axes[0].legend(fontsize=7, loc="lower right")
    source_note(
        fig,
        f"Central costs; dashed line: {cost:.2f} USD. {RUNS:,} runs per budget at "
        f"the posterior-mean pull rates. {SOURCE}",
    )
    save(fig, "fig5_ploss_price.png")


# --- Figures 6-7: from the run --------------------------------------------------


def figure_6(run_dir: Path, names: dict[str, str], cost: float) -> None:
    """Central break-even price under pull-rate assumptions (posterior mean, 95 % interval)."""
    folder = run_dir / "robustness"
    rows: list[tuple[str, str, str]] = [
        ("Main (Jeffreys, w = 1)", "main", ""),
        ("Rates at 2.5 % bound (R4)", "R4-low", ""),
        ("Rates at 97.5 % bound (R4)", "R4-high", ""),
        ("Uniform prior (R8)", "R8", ""),
        ("Half weight (R9b)", "R9b", ""),
        ("Hyper Rare in rare slot (R12)", "R12", ""),
        ("Short-printed Double Rare (R11)", "R11", ""),
    ]
    data: dict[str, list[dict[str, Any]]] = {
        "main": json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    }
    for _, run, _ in rows[1:]:
        path = folder / run / "results.json"
        if path.exists():
            data[run] = json.loads(path.read_text(encoding="utf-8"))
    sets = list(names)
    fig, axes = plt.subplots(1, len(sets), figsize=(7.2, 2.9), sharey=True)
    for ax, (color, set_id) in zip(axes, zip(SERIES, sets, strict=True), strict=True):
        labels = []
        for y, (label, run, _) in enumerate(rows):
            res = next(
                (
                    r
                    for r in data.get(run, [])
                    if r["set_id"] == set_id and r["job"]["label"] == "n=1"
                ),
                None,
            )
            labels.append(label)
            if res is None:
                continue
            be = np.asarray(res["extra"]["break_even_booster_price"]["central"])
            low, high = epistemic_interval(be) if be.size > 1 else (be[0], be[0])
            ax.plot([low, high], [y, y], color=color, lw=2, solid_capstyle="round")
            ax.plot(be.mean(), y, "o", color=color, ms=5, mec="white", mew=1)
        ax.set_yticks(range(len(rows)), labels)
        ax.invert_yaxis()
        ax.set_title(names[set_id], loc="left")
        ax.set_xlabel("Break-even price, USD")
        ax.grid(axis="y", visible=False)
    source_note(
        fig,
        "Central scenario. Dot: mean over pull-rate draws; bar: 95 % interval "
        "(R4: single model). R11 applies to Stellar Crown only. "
        f"Booster price {cost:.2f} USD (off scale). {SOURCE}",
    )
    save(fig, "fig6_breakeven_rates.png")


def figure_7(results: list[dict[str, Any]], names: dict[str, str]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), sharey=True, sharex=True)
    for ax, set_id in zip(axes, names, strict=True):
        for res in results:
            if res["set_id"] != set_id or res["job"]["estimand"] != "E1":
                continue
            n = res["job"]["n_packs"]
            a = res["a_metrics"]["central"]
            am, ac = float(np.mean(a["mean"])), float(np.mean(a["cvar05"]))
            b = res["b_metrics"]["central"]
            ax.plot([ac, b["cvar05"]], [am, b["mean"]], color=GRID, lw=1, zorder=1)
            ax.plot(ac, am, "o", color=SERIES[0], ms=6, mec="white", mew=1, zorder=2)
            ax.plot(
                b["cvar05"], b["mean"], "s", color=SERIES[1], ms=5.5, mec="white", mew=1, zorder=2
            )
            ax.annotate(
                f"n={n}",
                (ac, am),
                textcoords="offset points",
                xytext=(5, -3),
                fontsize=7,
                color=INK2,
            )
        ax.set_xscale("symlog", linthresh=10)
        ax.set_title(names[set_id], loc="left")
        ax.set_xlabel("CVaR 5 % (loss), USD")
    axes[0].set_ylabel("Mean net profit Π, USD")
    axes[0].plot([], [], "o", color=SERIES[0], label="A: open")
    axes[0].plot([], [], "s", color=SERIES[1], label="B: buy")
    axes[0].legend(fontsize=7, loc="lower left")
    source_note(
        fig,
        "Central scenario, E1 budgets of n boosters; A: mean over 200 pull-rate "
        f"draws. Up and left is better. {SOURCE}",
    )
    save(fig, "fig7_mean_cvar.png")


# --- Figures 8-9: the simulation itself ----------------------------------------------


def running_cvar(x: np.ndarray, checkpoints: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """CVaR (positive loss) of x[:m] for each m in checkpoints."""
    out = []
    for m in checkpoints:
        k = int(np.ceil(alpha * m))
        out.append(-np.sort(x[:m])[:k].mean())
    return np.asarray(out)


def figure_8(
    contexts: list[SetContext], names: dict[str, str], seed: int, cost: float
) -> list[str]:
    """Running Monte Carlo estimates against the exact mean, 36 boosters, central."""
    n = 36
    checkpoints = np.unique(np.logspace(2, np.log10(CONVERGENCE_RUNS), 60).astype(int))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    lines = [
        "| Set | Exact mean Π | MC mean, 100 runs | MC mean, 100,000 runs | |error| / SE "
        "| CVaR 5 %, 1,000 runs | CVaR 5 %, 100,000 runs |",
        "|---|---|---|---|---|---|---|",
    ]
    for color, ctx in zip(SERIES, contexts, strict=True):
        k = ctx.scenarios.index("central")
        cm = ctx.compile(ctx.posterior.mean_model())
        exact = n * (float(slot_card_probabilities(cm).sum(axis=0) @ ctx.value_matrix(cm)[:, k]))
        exact -= n * cost
        profit = pack_values(ctx, seed, 4, n, CONVERGENCE_RUNS)[:, k] - n * cost
        m = checkpoints
        csum = np.cumsum(profit)[m - 1]
        csq = np.cumsum(profit**2)[m - 1]
        mean = csum / m
        se = np.sqrt(np.maximum(csq / m - mean**2, 0) / m)
        ax = axes[0]
        ax.fill_between(m, mean - 1.96 * se, mean + 1.96 * se, color=color, alpha=0.18, lw=0)
        ax.plot(m, mean, color=color, lw=1.4, label=names[ctx.set_id])
        ax.axhline(exact, color=color, lw=0.8, ls="--")
        cvar = running_cvar(profit, m)
        axes[1].plot(m, cvar, color=color, lw=1.4, label=names[ctx.set_id])
        i100 = int(np.searchsorted(m, 100))
        i1000 = int(np.searchsorted(m, 1000))
        lines.append(
            f"| {names[ctx.set_id]} | {exact:.2f} | {mean[i100]:.2f} | {mean[-1]:.2f} "
            f"| {abs(mean[-1] - exact) / se[-1]:.2f} | {cvar[i1000]:.2f} | {cvar[-1]:.2f} |"
        )
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Simulated runs m")
    axes[0].set_ylabel("Mean net profit, USD")
    axes[0].set_title("Running mean", loc="left")
    axes[0].legend(fontsize=7, loc="lower right")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Simulated runs m")
    axes[1].set_ylabel("CVaR 5 %, USD (loss)")
    axes[1].set_title("Running CVaR 5 %", loc="left")
    source_note(
        fig,
        f"Opening {n} boosters at {cost:.2f} USD, central scenario, posterior-mean pull rates; "
        f"one stream of {CONVERGENCE_RUNS:,} runs per set.\nLeft: band ±1.96 Monte Carlo SE; "
        "dashed line: exact mean 36 (sum of P(c in a pack) l(c) - b). " + SOURCE,
    )
    save(fig, "fig8_mc_convergence.png")
    return lines


def figure_9(results: list[dict[str, Any]], names: dict[str, str], cost: float) -> list[str]:
    """Posterior draws of the break-even booster price (epistemic uncertainty)."""
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
    lines = [
        "| Set | Scenario | Draws | Mean b* | SD over draws | 2.5 % | 97.5 % "
        "| Within-draw MC SE of mean Π (36 boosters) | SD over draws of mean Π |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for ax, scenario in zip(axes, ("central", "gross"), strict=True):
        for y, (color, set_id) in enumerate(zip(SERIES, names, strict=True)):
            res = next(r for r in results if r["set_id"] == set_id and r["job"]["label"] == "n=1")
            be = np.asarray(res["extra"]["break_even_booster_price"][scenario])
            jitter = np.random.default_rng(y).uniform(-0.18, 0.18, be.size)
            ax.plot(be, y + jitter, "o", color=color, ms=2.2, alpha=0.55, mec="none")
            low, high = epistemic_interval(be)
            ax.plot([low, high], [y - 0.32, y - 0.32], color=INK2, lw=1.4)
            ax.plot(be.mean(), y - 0.32, "|", color=INK, ms=8)
            r36 = next(r for r in results if r["set_id"] == set_id and r["job"]["label"] == "n=36")
            within = float(np.median(r36["a_se"][scenario]["mean"]))
            between = float(np.std(r36["a_metrics"][scenario]["mean"], ddof=1))
            lines.append(
                f"| {names[set_id]} | {scenario} | {be.size} | {be.mean():.2f} "
                f"| {be.std(ddof=1):.3f} | {low:.2f} | {high:.2f} | {within:.2f} | {between:.2f} |"
            )
        ax.set_yticks(range(len(names)), [names[s] for s in names])
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Break-even booster price b*, USD")
        ax.set_title(f"{scenario.capitalize()} scenario", loc="left")
    axes[1].axvline(cost, color=INK2, lw=0.9, ls="--")
    axes[1].set_title(f"Gross scenario (dashed: {cost:.2f} USD)", loc="left")
    source_note(
        fig,
        "Each dot is one of the 200 posterior draws of the pull rates; bar: 95 % interval, "
        "tick: mean. Dashed: retail booster price. " + SOURCE,
    )
    save(fig, "fig9_breakeven_draws.png")
    return lines


def write_diagnostics(run_id: str, convergence: list[str], draws: list[str]) -> None:
    text = [
        "# Simulation diagnostics",
        "",
        f"Generated by `scripts/paper_figures.py` from run `{run_id}`. Numbers quoted in the",
        "paper's methods section (Figures 8 and 9).",
        "",
        "## Convergence to the exact mean (Figure 8)",
        "",
        "Opening 36 boosters, central scenario, posterior-mean pull rates. The exact mean is",
        "36 (sum over printings of P(printing in a pack) x l(printing) - booster price).",
        "",
        *convergence,
        "",
        "## Epistemic and aleatory uncertainty (Figure 9)",
        "",
        "Break-even booster price over the 200 posterior draws of the main run, and, for the",
        "mean profit of opening 36 boosters, the within-draw Monte Carlo standard error",
        "(median over draws) against the standard deviation across draws.",
        "",
        *draws,
        "",
    ]
    DIAGNOSTICS.write_text("\n".join(text), encoding="utf-8")
    print(f"wrote {DIAGNOSTICS}")


def contexts_for(cfg: ExperimentConfig) -> tuple[list[SetContext], dict[str, str]]:
    d = processed_dir(ROOT, cfg)
    printings = read_records(d / "printings.parquet", CardPrinting)
    rates = read_records(d / "pull_rates.parquet", PullRateObservation)
    prices = read_records(d / "prices.parquet", PriceObservation)
    names = {s.set_id: s.name for s in read_records(d / "sets.parquet", CardSet)}
    ctxs = [build_context(cfg, s, printings, rates, prices) for s in cfg.sets]
    return ctxs, {s: names[s] for s in cfg.sets}


def main(run_dir: Path) -> None:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    cfg = load_experiment(ROOT / manifest["run"]["parameters"]["config"])
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    seed = cfg.simulation.seed
    cost = cfg.scenario("central").booster_cost
    contexts, names = contexts_for(cfg)
    figure_1()
    figure_2(contexts[cfg.sets.index("sv08")])
    figure_3(contexts, names, seed, cost)
    figure_4(contexts, names, seed, results, cost)
    figure_5(contexts, names, seed, cost)
    figure_6(run_dir, names, cost)
    figure_7(results, names)
    convergence = figure_8(contexts, names, seed, cost)
    draws = figure_9(results, names, cost)
    write_diagnostics(run_dir.name, convergence, draws)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
