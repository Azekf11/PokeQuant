"""Approximate homogeneity test between the datasets pooled in each registry row.

Implements the decision rule of research/protocol/model_spec.md §5:
TCGplayer counts are backed out of the published rate p and 95 % half-width h
(n = p(1 - p)(z / h)^2, hits = p·n), the second dataset is the pooled
registry row minus TCGplayer, and a Pearson chi-squared test (1 d.f.) is run per
row, with Holm-Bonferroni across rows at family-wise level 0.05.

Usage: uv run python scripts/check_homogeneity.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from pokequant_core.estimation import homogeneity_test

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "research/reports/tcgplayer_published_rates.csv"
REGISTRY = ROOT / "data/raw/pokelife/2026-11-13/pull-rates.csv"
OUT = ROOT / "research/reports/homogeneity.csv"
POKELIFE_SET = {"sv07": "stellar-crown", "sv08": "surging-sparks", "sv10": "destined-rivals"}
Z = 1.959964
FAMILY_ALPHA = 0.05


def holm(p_values: list[float], alpha: float) -> list[bool]:
    """Holm-Bonferroni: True where the hypothesis is rejected."""
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    rejected = [False] * len(p_values)
    for rank, i in enumerate(order):
        if p_values[i] > alpha / (len(p_values) - rank):
            break
        rejected[i] = True
    return rejected


def main() -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as f:
        registry = {(r["set_id"], r["rarity"]): r for r in csv.DictReader(f)}
    rows: list[dict[str, object]] = []
    p_values: list[float] = []
    with PUBLISHED.open(newline="", encoding="utf-8") as f:
        for pub in csv.DictReader(f):
            pooled = registry[(POKELIFE_SET[pub["set_id"]], pub["rarity"])]
            if len(pooled["datasets"].split()) < 2:
                continue
            p, h = float(pub["rate_pct"]) / 100, float(pub["ci95_halfwidth_pct"]) / 100
            n1 = round(p * (1 - p) * (Z / h) ** 2)
            x1 = round(p * n1)
            n2, x2 = int(pooled["packs"]) - n1, int(pooled["hits"]) - x1
            test = homogeneity_test([(x1, n1), (x2, n2)])
            p_values.append(test.p_value)
            rows.append(
                {
                    "set_id": pub["set_id"],
                    "rarity": pub["rarity"],
                    "datasets": pooled["datasets"],
                    "tcgplayer_hits": x1,
                    "tcgplayer_packs": n1,
                    "other_hits": x2,
                    "other_packs": n2,
                    "rate_tcgplayer": round(x1 / n1, 5),
                    "rate_other": round(x2 / n2, 5),
                    "chi2": round(test.chi2, 4),
                    "p_value": round(test.p_value, 4),
                    "min_expected": round(test.min_expected, 1),
                }
            )
    rejected = holm(p_values, FAMILY_ALPHA)
    for row, rej in zip(rows, rejected, strict=True):
        row["holm_reject_at_0.05"] = rej
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} rows tested, {sum(rejected)} rejected (Holm, FWER {FAMILY_ALPHA})")
    for r in rows:
        print(
            f"{r['set_id']} {r['rarity']:<26} {r['rate_tcgplayer']:.4f} vs {r['rate_other']:.4f}"
            f"  p={r['p_value']:.3f}{'  REJECT' if r['holm_reject_at_0.05'] else ''}"
        )


if __name__ == "__main__":
    main()
