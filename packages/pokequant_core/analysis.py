"""Comparison tables and pre-registered hypothesis verdicts (protocol §7.0b, ADR 0011).

Works on serialised job results (plain dicts, as written to ``results.json``),
so that every verdict can be recomputed from the results files alone.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from pokequant_core.metrics import DIRECTION, METRICS, compare, epistemic_interval

Result = dict[str, Any]
H2_METRICS = ("mean", "median", "p_loss", "cvar05")
MEAN_MODEL_SE = 3.0  # "decisive at the posterior mean": |A - B| > 3 MC standard errors


def comparison_rows(result: Result) -> list[dict[str, Any]]:
    """One row per scenario and metric: A over draws, B, share, verdicts."""
    rows = []
    for s in result["scenarios"]:
        for m in METRICS:
            a = np.asarray(result["a_metrics"][s][m])
            b = float(result["b_metrics"][s][m])
            share, verdict = compare(a, b, DIRECTION[m])
            low, high = epistemic_interval(a)
            mm = result["mean_model"][s]
            diff = mm["value"][m] - b
            se = mm["se"][m]
            if abs(diff) > MEAN_MODEL_SE * se and diff != 0:
                point = "A" if DIRECTION[m] * diff > 0 else "B"
            else:
                point = "unclear"
            rows.append(
                {
                    "set_id": result["set_id"],
                    "estimand": result["job"]["estimand"],
                    "label": result["job"]["label"],
                    "scenario": s,
                    "metric": m,
                    "a_mean": float(a.mean()),
                    "a_low": low,
                    "a_high": high,
                    "a_mc_se": float(np.median(result["a_se"][s][m])),
                    "b": b,
                    "share_a_better": share,
                    "verdict": verdict,
                    "mean_model_a": mm["value"][m],
                    "mean_model_se": se,
                    "mean_model_winner": point,
                }
            )
    return rows


def _winner(verdict: str) -> str | None:
    return verdict.removeprefix("decisive: ") if verdict.startswith("decisive") else None


def hypotheses(results: Sequence[Result]) -> dict[str, dict[str, Any]]:
    rows = [r for res in results for r in comparison_rows(res)]
    index = {(r["set_id"], r["label"], r["scenario"], r["metric"]): r for r in rows}
    cases = sorted({(r["set_id"], r["label"], r["scenario"]) for r in rows})

    h1 = []
    for set_id, label, s in cases:
        ev = _winner(index[set_id, label, s, "mean"]["verdict"])
        for other in ("median", "cvar05"):
            w = _winner(index[set_id, label, s, other]["verdict"])
            if ev and w and w != ev:
                h1.append(f"{set_id} {label} {s}: mean favours {ev}, {other} favours {w}")
    for res in results:
        for s in res["scenarios"]:
            mean = np.asarray(res["a_metrics"][s]["mean"])
            loss = np.asarray(res["a_metrics"][s]["p_loss"])
            if np.mean((mean > 0) & (loss > 0.5)) >= 0.90:
                h1.append(
                    f"{res['set_id']} {res['job']['label']} {s}: A has EV > 0 and P(loss) > 0.5"
                )

    h2 = []
    for r in rows:
        if r["metric"] not in H2_METRICS or r["mean_model_winner"] == "unclear":
            continue
        if _winner(r["verdict"]) != r["mean_model_winner"]:
            h2.append(
                f"{r['set_id']} {r['label']} {r['scenario']} {r['metric']}: "
                f"{r['mean_model_winner']} at the posterior mean, {r['verdict']} over draws"
            )

    h3 = []
    for res in results:
        if not {"gross", "central"} <= set(res["scenarios"]):
            continue
        metric = "mean" if res["job"]["estimand"] == "E1" else "p_gain"

        def advantage(s: str, metric: str = metric, res: Result = res) -> np.ndarray:
            a = np.asarray(res["a_metrics"][s][metric])
            return a - (res["b_metrics"][s][metric] if metric == "mean" else 0.0)

        change = advantage("gross") - advantage("central")
        low, high = epistemic_interval(change)
        line = (
            f"{res['set_id']} {res['job']['label']}: change in {metric} advantage "
            f"gross - central = {change.mean():.3f} [{low:.3f}, {high:.3f}]"
        )
        h3.append((low > 0, line))

    h4 = []
    by_label: dict[str, dict[str, str | None]] = {}
    for set_id, label, s in cases:
        if s == "central":
            by_label.setdefault(label, {})[set_id] = _winner(
                index[set_id, label, s, "mean"]["verdict"]
            )
    for label, winners in sorted(by_label.items()):
        decided = {w for w in winners.values() if w}
        line = f"{label}: " + ", ".join(f"{k} {v or 'undetermined'}" for k, v in winners.items())
        h4.append((len(decided) > 1, line))

    return {
        "H1": {"status": "supported" if h1 else "not supported", "evidence": h1},
        "H2": {"status": "supported" if h2 else "not supported", "evidence": h2},
        "H3": {
            "status": "supported" if any(ok for ok, _ in h3) else "not supported",
            "evidence": [line + (" *" if ok else "") for ok, line in h3],
        },
        "H4": {
            "status": ("supported" if any(ok for ok, _ in h4) else "not supported")
            + " (sets only; second price snapshot pending)",
            "evidence": [line for _, line in h4],
        },
    }
