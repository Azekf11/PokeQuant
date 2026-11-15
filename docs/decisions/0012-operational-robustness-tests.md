# 0012 — Operational definitions of the robustness tests

- Status: accepted
- Date: 2026-11-15
- Decided by: author
- Refines: protocol §7.2 (`prereg-v1`), the `robustness` list of
  [research/experiments/main.yaml](../../research/experiments/main.yaml) and
  [ADR 0010](0010-booster-model-and-prereg-v1-deviations.md) (`prereg-v2`)

## Context

`prereg-v2` lists robustness tests R1–R13 by name only. Week S8 turns them into
code, and some need details that the list leaves open: which statistics R1
takes the median of, which fees R3 scales, how the R4 bounds are set, and what
"a conclusion holds" means.

These details are fixed here **before any robustness run**. The main results
(run `main-94de09e8-k200-m20000`, ADR 0011) are already known when this record
is written. To avoid tuning a test after seeing its effect, every parameter
below either comes from `prereg-v2` or from a source cited there. None is
chosen by looking at a robustness result.

## Decision

**Common rules.**

1. Every variant uses the seed, epistemic draws (200) and aleatory runs
   (20,000) of the main experiment, except R7. With the same posterior, the
   same seed therefore gives the same simulated openings (common random
   numbers): a variant that only changes card values differs from the
   baseline by its values alone.
2. A variant that changes the central scenario keeps the gross and adverse
   scenarios of the main experiment unchanged.
3. Decision rules are those of ADR 0011. For a variant with a single model
   (R4), a comparison is decisive when |A − B| exceeds 3 Monte Carlo standard
   errors (the "posterior mean" rule of ADR 0011).

**Tests.**

| ID | Operational definition |
|---|---|
| R1 | p(c) = median of the TCGplayer statistics available for the printing at t0 (low, mid, high, direct low, market). Listing statistics are asking prices (protocol §5.1). This variant is therefore labelled *indicative*, and its basis is recorded with price type `estimate`. Applied to all three scenarios. |
| R2 | Central scenario with liquidity haircut h = 0.30, then h = 0.50. |
| R3 | Central scenario with every selling and shipping cost scaled by 0.5, then by 1.5. This covers the marketplace and payment fee rates, the fixed selling fee, seller shipping and buyer shipping; the buyer fee rate is 0. |
| R4 | One model per bound: in every slot, each hit rarity is set to the 2.5 % (low) or 97.5 % (high) quantile of its marginal posterior, Beta(α_k, Σα − α_k). The residual pool takes the rest. No epistemic draws; 20,000 runs. |
| R5 | The ⌈1 % × N⌉ drawable printings of a set with the highest central market price (N = drawable printings with an observed price) are worth 0 when opened, and Strategy B cannot buy them. Imputed prices are unchanged. Applies to E1 and the break-even price; E2 is not applicable, because its targets are the most valuable cards. |
| R6 | The three sets compared in the main run (H4, across sets). There is no new run. |
| R7 | 1,000, 10,000 and 100,000 aleatory runs per draw, 200 draws each. The variant at 1,000 runs has 50 samples in the 5 % tail; it is reported as a stability check, not as a result. |
| R8 | Uniform prior, a₀ = 1, instead of Jeffreys. |
| R9b | Weight w = 0.5 on every registry row (ADR 0010, item 1). |
| R10 | Central scenario with h = 0.27, which is 1 minus the 73 % of listed cards sold within one year in Heck et al. (2026). Unsold cards are valued at 0, sold cards at their price. This is evidence transferred from eBay listings of a different card sample, and is labelled as such. |
| R11 | sv07 only. Within the Double Rare pool, Dachsbun ex (en:sv07:067:holo) has relative weight 0.76 and every other Double Rare has weight 1.21. These are the per-card pull rates in the TCGplayer Stellar Crown article, 0.76 % ± 0.18 % against 1.21 % ± 0.23 %. The total Double Rare rate is unchanged. |
| R12 | Layout `hyper-in-rare-slot`. |
| R13 | Not run: the homogeneity rule did not reject pooling (ADR 0010, item 6). |

**What is tested.** The main run supports three conclusions. Each one is
checked in every variant where it applies.

- **C1.** In the central scenario, opening loses money on average. For every
  set and E1 budget, the 95 % interval of mean Π_A lies below 0. For R4, the
  test is mean + 1.96 SE < 0.
- **C2.** The central break-even booster price is below the central booster
  cost (4.49 USD) for every set: the upper bound of its 95 % interval is below
  4.49. The same check is made on the gross break-even price.
- **C3.** In the central scenario, Strategy B is decisively better on the
  mean, the median and the CVaR 5 % for every set, for E1 budgets of 10
  boosters or more and for every E2 target.

The statuses of H1–H3 are also recomputed for every variant that has all
three scenarios. Under protocol §10 ("conclusion hinges on one fragile rate or
price"), a conclusion is **robust** if it holds in every variant. Otherwise,
the report names the variants in which it fails and the paper states the
conclusion with that limit.

## Consequences

- `pokequant robustness <config>` runs every variant and writes one results
  folder per variant. `scripts/robustness_report.py` writes
  `research/reports/robustness.md`, Table 4 and the tornado plot.
- R1 uses asking prices. It cannot strengthen a conclusion; it can only
  reveal that a conclusion depends on the market statistic.
- Under common random numbers, a variant whose verdict differs from the
  baseline's owes the difference to its assumption, not to simulation noise.
