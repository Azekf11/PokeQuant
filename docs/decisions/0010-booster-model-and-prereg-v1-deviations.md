# 0010: Booster model choices and deviations from `prereg-v1`

- Status: accepted
- Date: 2026-11-15
- Decided by: author
- Refines: protocol §4, §6–7 (`prereg-v1`); detailed in
  [model_spec.md](../../research/protocol/model_spec.md) and
  [research/experiments/main.yaml](../../research/experiments/main.yaml)

## Context

S4 fixes the booster model and the experiment configuration before tag
`prereg-v2`. The data audit (S2) and the pack-structure sources read in S4
make some `prereg-v1` items impossible or underspecified. Protocol rule:
a deviation is never silent; it is recorded here and reported in the paper.

## Decision

Deviations from `prereg-v1`:

1. **Robustness test 9 is replaced.** "Exclude rows with reconstructed counts"
   would leave no data: all 17 rows of the selected sets are reconstructed.
   Replacement **R9b**: halve the effective sample size of every row (weight
   w = ½ in the Beta/Dirichlet posteriors).
2. **Valuation venue.** The main analysis values cards with TCGplayer (USD)
   market prices, whose seller fees were verified on TCGplayer's fee page.
   Cardmarket (EUR) prices are used only in an exploratory comparison: its fee
   schedule could not be read from an official page.
3. **Booster cost is a scenario, not an observation.** No source of sealed
   product prices is in the data. Central b = 4.49 USD (US suggested retail
   price reported at the Scarlet & Violet launch), adverse b = 5.49 USD, and
   the break-even price b\* is reported for every set (it does not depend on b).

Choices that refine `prereg-v1` without changing it:

4. Slot layout from the TCGplayer pull-rate articles (rev1: ACE SPEC; rev2:
   IR, SIR, HR; rare slot: DR, UR). Conflicting Hyper Rare placement
   (PokéBeach, 2023) becomes robustness **R12**.
5. Slot Dirichlet posteriors put the registry rates of one slot on the smallest
   denominator among its rows (conservative common sample size).
6. New robustness tests: **R11** (Dachsbun ex short print in sv07, from the
   TCGplayer note), **R12** (Hyper Rare slot), **R13** (TCGplayer-only rates,
   triggered only if the homogeneity rule rejects pooling; it did not).
7. Basic Energy and code card are valued at 0.
8. A card without a TCGplayer market price is valued at the median price of
   its pool in the central scenario and at 0 in the adverse scenario; the
   share of such cards is reported (missing ≠ 0 in the data; the valuation
   choice is explicit).

## Consequences

- `prereg-v2` = `prereg-v1` + model_spec.md + experiments/main.yaml + this ADR.
- The paper lists items 1–3 as deviations and items 4–8 as specification.
- No price value has been used in any analysis at the time of this decision.
