# Defence questions

Short answers to the ten questions of protocol §12, with pointers to the
evidence. Numbers refer to the frozen analysis (tag `analysis-v1`, run
`main-94de09e8-k200-m20000`).

## 1. What exactly is your scientific contribution beyond the website?

A reproducible and pre-registered comparison of two ways to acquire Pokémon
TCG cards, opening boosters and buying singles. It combines four elements:

1. a slot-level booster model;
2. Bayesian uncertainty on community pull rates, propagated through a nested
   Monte Carlo;
3. typed market prices converted into net realisable values under explicit
   cost scenarios;
4. tail-risk measures.

The contribution is not an expected-value calculator: those exist (paper
§2.4). It is the combination, the pre-registration (tags `prereg-v1` and
`prereg-v2`), and the evidence that the conclusions survive twelve
robustness tests. The website only displays the frozen results
(ADR 0013).

## 2. What are the pull-rate sources and why is their sample credible?

The Poké Life registry, version 2026-11-13 (CC BY 4.0). It compiles openings
published by TCGplayer's Authentication Center and other sources. For the
three sets, the rates rest on at least 5,000 measured packs per set (the
selection rule, ADR 0005). The registry's own intervals are reproduced
exactly by Jeffreys intervals on its counts, and a homogeneity test between
pooled openings rejects none of the 16 testable rows.

The sample is not a random sample of packs. A common bias would not be
captured by the intervals. This is stated as a limit (paper §8.4). R9b halves
the weight of every row to mimic a smaller effective sample, and R4 sets the
rates at their interval bounds.

## 3. How do you handle structural differences between boosters and sets?

Each set has its own pools of cards and its own posterior rates, under one
documented slot layout (TCGplayer articles, `research/protocol/model_spec.md`).
Rarities absent from a set (no ACE SPEC in Destined Rivals) are absent from
its model. The one conflict in the sources, the slot of Hyper Rares, is a
robustness scenario (R12). So is the one documented short print (R11).

## 4. Why this prior, and how do results change with another one?

Jeffreys (a₀ = ½) is the standard reference prior for proportions, and it
reproduces the registry's intervals. With a uniform prior (R8), the
break-even prices and verdicts barely move. See [Table 4](../research/reports/robustness.md).

## 5. What is the difference between listing price, aggregated price and realised sale?

- A **listing price** is what a seller asks.
- An **aggregated (provider market) price** is a provider's summary of recent
  activity. Here it is TCGplayer's market price, relayed by TCGdex.
- A **realised sale** is a transaction price.

The analysis uses the aggregated price, never presents it as a sale, and
refuses listing prices as transaction values in code
(`valuation.PriceBasisError`). R1 replaces it with the median of all the
statistics, labelled indicative. R2 and R10 apply larger liquidity haircuts.

## 6. How do you turn an observed price into a net realisable value?

ℓ(c) = max(0, p(c)(1 − h)(1 − f_m − f_p) − f_0 − s): the price after a
liquidity haircut, minus the marketplace and payment fees, the fixed fee and
the shipping of one sale, floored at zero (a card not worth selling is kept).
A buyer pays a(c) = p(c)(1 + f_b) + s_b. Values are in
`research/experiments/main.yaml`; fee rates are TCGplayer's published fees.

## 7. Why compare strategies at identical budget and horizon?

Because otherwise the comparison mixes the strategy with the amount spent or
the time held:

- **E1** gives both strategies the same budget at the same date and
  liquidates everything at once.
- **E2** compares two ways to obtain the same card at the same date.

Neither holds cards over time, so price changes do not enter. The second
price snapshot (2026-12-13) tests the date, not a holding strategy.

## 8. What are the main selection and survivorship biases?

- **Sets.** They were chosen by a data-coverage rule committed before any
  price was seen (ADR 0005), so they are well-documented recent sets, not a
  random sample of sets.
- **Openings.** Openings published online may over-represent good packs.
- **Prices.** Market prices exist only for cards that trade. Missing prices
  are imputed from the pool median (central) or set to zero (adverse), and
  never silently to zero in the central case.
- **Targets.** The E2 targets are each set's most expensive cards at t₀, an
  ex-post choice by construction. They are fixed by a rule, not picked by
  hand.

## 9. Which conclusions hold in adverse scenarios?

All three main conclusions hold in the adverse scenario:

- opening loses on average;
- the break-even price is below the booster price;
- buying is decisively better for budgets of 10 boosters or more and for
  every target.

At a one-booster budget, opening has the better mean in every set, because a
single direct purchase pays 4.50 USD of tracked shipping. Buying still has the
better median and CVaR in two sets, and they tie in the third.

Under the robustness variants, see [robustness.md](../research/reports/robustness.md)
and paper §7.

## 10. Which conclusions can you not draw from your data?

- Whether opening is profitable at other dates, in other markets or for other
  sets.
- Whether realised sale prices match the market prices used. No open source
  of realised sales was available.
- Anything about graded cards, sealed-product investment or holding returns.
- Any personal financial advice. The results are conditional on stated prices
  and costs, and opening also has an entertainment value that the model does
  not price.
