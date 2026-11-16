<!-- Version 3. Sources: research/reports/robustness.md (ADR 0012), extension_sets.md (ADR 0015), sales_benchmark.md (ADR 0014), pull_rate_checks.md (ADR 0015), mega_sets.md and mega/pull_rate_checks.md (ADR 0016). -->

# 5. Robustness and extensions

I check three conclusions, all under central costs. C1: the 95 % interval of
the mean profit of opening is below zero for every set and budget. C2: the
upper 95 % bound of b\* is below 4.49, both central and gross. C3: buying is
decisively better on the mean, the median and the CVaR for every budget of
ten boosters or more and every target.

## 5.1 Pre-registered robustness tests

Each of the sixteen variants changes one assumption and keeps the seed, the
draws and the runs; variants that change only card values reuse the
simulated openings of the main run, so differences come from the assumption,
not from simulation noise. Table 4 reports the results.

C1 and C3 hold in every variant. C2 fails once: with cards valued at the
median of TCGplayer's listing and market statistics (R1), the gross b\* of
Stellar Crown has a mean of 4.42 but an upper bound of 4.53. The central b\*
stays between 0.54 and 1.74, at most 39 % of the retail price. Liquidation
assumptions set the size of the gap: a haircut of 0.50 roughly halves b\*,
and excluding the 1 % most valuable printings lowers it by 0.46 to 0.83
(Figure 7). Pull-rate assumptions barely matter: the prior, the effective
sample size and the slot of the Hyper Rare leave b\* unchanged at two
decimals, and setting every rate at a bound of its interval moves it by at
most 0.15. With fewer runs per draw, only comparisons at a one-booster
budget, where the strategies differ by less than 0.40, change verdict; H2
depends on such a comparison, so I report it as supported but fragile.

**Table 4.** Robustness variants: central break-even price b\* (posterior
mean) and conclusions C1–C3.

| Variant | b\* sv07 | b\* sv08 | b\* sv10 | C1 | C2 | C3 |
|---|---|---|---|---|---|---|
| Baseline | 1.42 | 1.03 | 1.13 | yes | yes | yes |
| R1 median of price statistics | 1.51 | 1.12 | 1.26 | yes | no | yes |
| R2 haircut 0.30 / 0.50 | 1.12 / 0.73 | 0.81 / 0.54 | 0.90 / 0.60 | yes | yes | yes |
| R3 selling costs × 0.5 / × 1.5 | 1.74 / 1.17 | 1.25 / 0.85 | 1.34 / 0.95 | yes | yes | yes |
| R4 rates at lower / upper bounds | 1.30 / 1.54 | 0.91 / 1.17 | 0.99 / 1.28 | yes | yes | yes |
| R5 top 1 % of printings excluded | 0.59 | 0.57 | 0.64 | yes | yes | yes |
| R7 1,000 / 10,000 / 100,000 runs | 1.42 | 1.03 | 1.13 | yes | yes | yes |
| R8 uniform prior | 1.42 | 1.03 | 1.13 | yes | yes | yes |
| R9b half effective sample size | 1.42 | 1.03 | 1.13 | yes | yes | yes |
| R10 haircut 0.27 (Heck et al.) | 1.18 | 0.86 | 0.95 | yes | yes | yes |
| R11 short-printed Double Rare | 1.42 | n/a | n/a | yes | yes | yes |
| R12 Hyper Rare in the rare slot | 1.42 | 1.03 | 1.13 | yes | yes | yes |

*Source:* `research/reports/robustness.md`, with intervals. Paired variants
(R2, R3, R4, R7) pass every check in both settings.

![Figure 7. Change from the baseline of the central break-even price (top) and of the mean advantage of opening over buying at 36 boosters (bottom), by robustness test.](../../reports/figures/tornado.png)

## 5.2 Ten sets

ADR 0015 (tag `prereg-v4`) extends the experiment to the seven other
eligible sets that fit the main pack layout: Scarlet & Violet, Paldea
Evolved, Obsidian Flames, Paradox Rift, Temporal Forces, Twilight Masquerade
and Journey Together. The run uses the configuration, seed and price snapshot
of the main run; the three main sets are re-simulated with new random streams
and their central and gross b\* are identical to two decimals.

![Figure 8. Break-even booster price b\* in the ten evaluable sets, central costs and gross reference. Posterior mean and 95 % interval over 200 pull-rate draws. Asterisks mark the two sets flagged by the duplicate rule of Section 5.4.](../figures/fig8_ten_sets.png)

C1 and C3 hold in all ten sets: opening loses on average for every budget,
and buying is decisively better on the three metrics for every budget of ten
boosters or more and every target. The central b\* ranges from 0.60 (Journey
Together) to 2.38 (Paldea Evolved) (Figure 8). C2 fails for two sets whose
gross b\* exceeds the retail price: 5.29 [5.12, 5.48] for Paldea Evolved and
5.00 [4.87, 5.18] for Temporal Forces. Their pack's expected market value is
above its price, and the loss from opening comes entirely from selling costs.
Without frictions, opening one or ten of their boosters has a positive mean
but loses money in more than half of the runs, a clear case of H1.

H4 across sets is now supported, but only at a one-booster budget: opening
has the higher mean for Paldea Evolved, Temporal Forces and Stellar Crown, by
0.08 to 1.07 USD, and buying for five other sets. Stellar Crown's one-booster
verdict, undetermined in the main run (opening better in 89.5 % of draws),
becomes decisive here (92 %) with different random streams: the near tie of
Section 5.1. Every hypothesis keeps its status without the two flagged sets
(`research/reports/extension_sets.md`).

## 5.3 Sale prices

As a check on the TCGplayer market price, a provider aggregate, I revalued
every card at Cardmarket's 30-day average sale price (`avg30`, defined by the
venue's API documentation), relayed by TCGdex for 2026-11-15 and converted at
the European Central Bank rate of 1.1052 USD per EUR (2026-11-13), and
recomputed b\* in each posterior draw (ADR 0014, tag `prereg-v3`, registered
before the values were analysed).

**Table 5.** Break-even booster price b\* at Cardmarket sale prices,
2026-11-15 (USD).

| | Stellar Crown | Surging Sparks | Destined Rivals |
|---|---|---|---|
| Central, TCGplayer market price | 1.42 [1.35, 1.49] | 1.03 [0.95, 1.12] | 1.13 [1.04, 1.22] |
| Central, Cardmarket 30-day sales | 1.16 [1.10, 1.21] | 2.42 [2.32, 2.53] | 1.71 [1.55, 1.86] |
| Gross, Cardmarket 30-day sales | 2.89 [2.80, 2.98] | 4.75 [4.61, 4.91] | 3.46 [3.25, 3.68] |

*Source:* `research/reports/sales_benchmark.md`. Hit-printing coverage 100 %.

C1 holds in every set: under central costs, opening still loses on average
at sale prices. C2 fails for Surging Sparks, whose gross b\* of 4.75 exceeds
4.49. Over hit printings, the median ratio of the Cardmarket sale average to
the TCGplayer market price is 0.94 [0.87, 1.03] for Stellar Crown and 1.22
[1.14, 1.31] and 1.23 [1.16, 1.33] for the two other sets (bootstrap, 49 to
87 printings), so the central haircut is not visible in this comparison,
although it mixes two markets and two price types. A weekly panel until
2027-01-10 will test the date half of H4.

## 5.4 Pull-rate checks

Three checks were pre-registered (ADR 0015). First, for the seven added sets,
all 33 single-source registry rows equal the rate printed in the TCGplayer
article to two decimals. Second, the Paradox Rift and Paldea Evolved articles
print the same Ultra Rare (6.64 % ± 0.53 %) and Illustration Rare (7.70 % ±
0.56 %) rates; two independent samples rarely agree this closely, so both
sets are flagged, and removing them changes no conclusion. Third, a Jeffreys
posterior on the TCGplayer counts alone predicts the second opening's hits
inside the 95 % beta-binomial predictive interval in all 20 pooled rows
(smallest two-sided p-value 0.161, none rejected after Holm correction), so
pooling the two openings is consistent with the data.

## 5.5 Mega Evolution sets

The four Mega Evolution sets have a top rarity, the Mega Hyper Rare (MHR),
with no documented slot: the TCGplayer articles place the other hit rarities
as in the main layout and say the MHR replaced the Hyper Rare, but not where
it sits. ADR 0016 (tag `prereg-v5`) therefore runs them under two layouts with
the same random streams, the MHR in the second reverse slot (central) or in
the rare slot, and keeps a conclusion only if it holds under both.

**Table 6.** Mega Evolution sets, central costs (USD).

| Set | b\*, MHR in reverse slot | b\*, MHR in rare slot | Gross b\* | Opening 36 boosters | Buying |
|---|---|---|---|---|---|
| Mega Evolution | 1.03 [0.88, 1.21] | 1.03 [0.88, 1.21] | 3.57 [3.36, 3.81] | −124.52 [−129.94, −118.09] | −45.88 |
| Phantasmal Flames | 1.49 [1.29, 1.67] | 1.50 [1.29, 1.73] | 3.99 [3.72, 4.24] | −108.08 [−115.44, −101.10] | −87.83 |
| Chaos Rising | 0.48 [0.43, 0.54] | 0.48 [0.42, 0.55] | 2.65 [2.58, 2.72] | −144.22 [−146.17, −142.12] | −50.55 |
| Pitch Black | 0.71 [0.59, 0.83] | 0.72 [0.59, 0.83] | 2.96 [2.78, 3.13] | −136.07 [−140.56, −131.38] | −48.56 |

*Source:* `research/reports/mega_sets.md`. Gross b\* and the profits use the
central layout.

The slot makes no difference: the MHR appears in about one pack in 1,000
(TCGplayer prints 1 in 956 to 1 in 1,260), and moving it changes the mean b\*
by at most 0.01. C1, C2 and C3 hold in all four sets under both layouts. Over
the fourteen sets, H4 keeps the status of Section 5.2: the winner differs
only at a one-booster budget, where none of the four new sets favours
opening. The pull-rate checks find nothing: the one single-source row
matches its printed rate, no set is flagged, and all 19 pooled rows fall
inside the 95 % predictive interval (smallest p-value 0.174).
