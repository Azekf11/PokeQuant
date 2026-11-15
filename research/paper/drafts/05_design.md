<!-- Draft written at prereg-v2 (week S4). Source of truth: research/experiments/main.yaml. -->

# 5. Experimental design

All choices in this section were fixed and tagged (`prereg-v2`) before any
price value entered an analysis. Departures from the first-stage registration
(`prereg-v1`) are listed in §5.6.

## 5.1 Product and booster model

The product is one English booster pack of Stellar Crown (sv07), Surging
Sparks (sv08) or Destined Rivals (sv10). A pack is modelled as ten card slots:
four Commons, three Uncommons, two reverse-holo slots and one rare slot; the
Basic Energy and the code card are given no value. The slot of each hit rarity
follows the publisher of the pull-rate data, the TCGplayer Authentication
Center: ACE SPEC Rares replace the first reverse holo; Illustration Rares,
Special Illustration Rares and Hyper Rares replace the second; Double Rares and
Ultra Rares occupy the rare slot. One earlier source places Hyper Rares in the
rare slot instead, and we treat this alternative as a robustness scenario.
Within a slot, outcomes are mutually exclusive. Slots are assumed independent
and printings within a pool equally likely, an assumption that the TCGplayer
per-card counts support with one reported exception (a short-printed Double
Rare in Stellar Crown, tested as a scenario).

Each random slot has a Dirichlet posterior with a Jeffreys prior on the
registry counts. Because rows of one set have different denominators, the
rates of one slot are placed on the smallest of them. The registry intervals
are reproduced exactly by Jeffreys intervals on its counts, and an
approximate χ² test does not reject homogeneity between the two pooled
openings in any of the 16 testable rows (Holm–Bonferroni, 5 %).

## 5.2 Prices and transaction costs

Cards are valued at the TCGplayer market price (USD) of the reference
snapshot, t₀ = 2026-11-15, a provider-market aggregate rather than a
realised-sale price. A seller receives

ℓ(c) = max(0, p(c)(1 − h)(1 − f_m − f_p) − f_0 − s),

and a buyer pays a(c) = p(c)(1 + f_b) + s_b, one card per transaction. Three
cost scenarios are fixed (all in USD):

| Scenario | Booster b | f_m | f_p | f_0 | s | s_b | h |
|---|---|---|---|---|---|---|---|
| Gross (reference only) | 4.49 | 0 | 0 | 0 | 0 | 0 | 0 |
| Central | 4.49 | 10.75 % | 2.5 % | 0.30 | 1.00 | 1.00 | 15 % |
| Adverse | 5.49 | 10.75 % | 2.5 % | 0.30 | 4.50 | 4.50 | 30 % |

The fee rates are TCGplayer's published fees for standard sellers. The booster
price, shipping and liquidity haircut h are assumptions; the break-even
booster price is reported so that readers can substitute their own b. A card
without a market price takes the median price of its pool (central) or zero
(adverse).

## 5.3 Strategies and estimands

Experiment E1 concerns budget liquidation. With budgets of 1, 10, 36 and 100
packs, Strategy A opens the packs and sells every card, while Strategy B buys,
at t₀, the most expensive printings of the set that fit the same budget
(greedy rule in decreasing order of a(c)) and sells them back.

Experiment E2 concerns target acquisition. For two targets per set (the most
expensive printing and the most expensive Special Illustration Rare at t₀),
Strategy A opens packs until the target appears, capped at
n_max = ⌈3 / p_hit⌉ (a failure then buys the target), and sells every other
card. Strategy B simply buys the target.

## 5.4 Simulation and metrics

Two nested loops separate the two kinds of uncertainty: 200 draws of the slot
probabilities from their posteriors (epistemic) and, for each, 20,000 simulated
runs (aleatory), so that every 5 % tail rests on 1,000 samples. Metrics are
those of §4: mean, median, P(loss), quantiles, VaR and CVaR at 5 % (reported as
positive losses), break-even booster price, P(target in n packs) and expected
packs, each with its Monte Carlo standard error and its 95 % interval over
epistemic draws. The random seed is fixed (20261115). Table 2 (Appendix D)
lists every simulation parameter.

## 5.5 Robustness

The robustness checks are defined as follows. R1 uses an alternative price
statistic, R2 haircuts of 30 % and 50 %, and R3 fees and shipping ± 50 %. R4 sets the pull rates at their interval bounds, R5 excludes
the 1 % most valuable printings, R6 compares sets, R7 varies the number of
simulated runs and R8 uses a uniform prior. R9b halves the effective sample
size. R10 anchors haircuts on observed sell-through (transferred evidence),
R11 models the short-printed Double Rare and R12 places the Hyper Rare in the
rare slot. R13, TCGplayer-only rates, was planned only if pooling were
rejected; it was not. Hypothesis H4 compares the three sets and a second price
snapshot (2026-12-13).

## 5.6 Deviations from the first-stage registration

1. The pre-registered test excluding reconstructed counts is replaced by R9b:
   every row of the selected sets has reconstructed counts.
2. Valuation uses TCGplayer prices only. Cardmarket is exploratory, because
   its fee schedule cannot be verified from an official page.
3. The booster price is a scenario, not an observation.
