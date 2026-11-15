<!-- Draft written in week S7. Source of truth: research/reports/results.md (run main-94de09e8-k200-m20000). Figures come in S11. -->

# 6. Results

All figures are in USD and are conditional on the TCGplayer market prices of
2026-11-15 and on the cost scenarios of §5.2. Intervals are 95 % intervals
over 200 posterior draws of the pull rates. Each draw rests on 20,000
simulated openings.

## 6.1 Break-even booster price

The expected liquidation value of one booster sets the price below which
opening has a positive expected net profit:

- **Gross reference** (no fees or shipping): 4.29 [4.18, 4.39] for Stellar
  Crown, 3.44 [3.31, 3.56] for Surging Sparks and 3.78 [3.65, 3.91] for
  Destined Rivals. All three are below the assumed price of 4.49.
- **Central scenario**: 1.42, 1.03 and 1.13. A single card's fixed selling cost
  (fee and shipping, 1.30) exceeds the market value of most cards, so commons,
  uncommons, rares and most reverse holos contribute nothing.
- **Adverse scenario**: between 0.52 and 0.78.

## 6.2 E1: opening a budget and selling everything

**Opening loses money on average.** In the central scenario, for every set
and budget, the mean net profit of opening is negative and its 95 % interval
excludes zero. Opening 36 boosters (161.64) loses between 110.56 (Stellar
Crown) and 124.56 (Surging Sparks) on average. The median loss is larger
still, and the probability of a loss is between 0.87 and 1.00.

**Buying cards directly also loses**, through the round-trip cost. Strategy
B buys the most expensive cards that fit the budget and sells them back,
which costs 46 to 51 for the same 36-booster budget. That is less than half
the expected loss of opening.

**The verdicts:**

- The direct purchase is decisively better on the mean, the median and the
  CVaR 5 % in 35 of the 36 central comparisons.
- The one exception is the mean for Stellar Crown at a one-booster budget,
  which is undetermined.
- Under the gross reference, opening still loses on average for every set and
  budget, and B is decisively better on all three metrics.

## 6.3 E2: acquiring the most valuable card

The targets are each set's most expensive printing: an Illustration Rare for
Stellar Crown and a Special Illustration Rare for the two other sets. In the
latter two sets, the top-price target and the top Special Illustration Rare
are the same card.

**These targets are rare.** Their per-pack probabilities correspond to one
pack in 168 [158, 179] for Stellar Crown, one in 904 [765, 1,072] for Surging
Sparks and one in 1,008 [875, 1,174] for Destined Rivals.

**Opening is rarely cheaper than buying.** In the central scenario, opening
until the target appears is cheaper than buying it in 4 % to 14 % of
simulated runs, depending on set and target. The mean extra cost of opening
ranges from 468 to 3,145. Buying the target is decisively better on the mean,
the median and the CVaR 5 % for every set and target, under all three cost scenarios. The one exception is
the median for Stellar Crown under the gross reference, where opening is
cheaper in 52 % of runs and the verdict is undetermined.

## 6.4 Pre-registered hypotheses

- **H1, supported, only in the adverse scenario at a one-booster budget.** For
  Stellar Crown and Surging Sparks, opening one booster has a higher mean than
  buying one card, yet a lower median and a higher CVaR. The mechanism is
  mechanical: a single direct purchase pays 4.50 of shipping. The evidence
  for H1 is therefore narrow. Elsewhere, mean, median and CVaR rank the
  strategies the same way.
- **H2, supported in one comparison.** For Stellar Crown's top-price target,
  under the gross reference, the median favours opening at the posterior-mean
  pull rates. Once rate uncertainty is propagated, the verdict becomes
  undetermined. No comparison in the central scenario changes.
- **H3, supported.** For every set and every budget of 10 boosters or more,
  fees and liquidity costs reduce the advantage of opening over buying, with
  a 95 % interval above zero. In E2, they lower the probability that opening
  beats buying by 0.12 to 0.38. At a one-booster budget the change has the
  opposite sign, because a one-card basket bears the whole fixed cost of one
  sale.
- **H4, not supported across sets.** The decisive winner is B in every set,
  for every budget and target, except where the verdict is undetermined. The
  half of H4 that compares price dates awaits the 2026-12-13 snapshot.

## 6.5 Gate G7

The roadmap allows a profitability conclusion only if credible net prices
are integrated. Here, net values combine the seller fees published by
TCGplayer with explicit assumptions on shipping and liquidity haircut. The
main conclusion does not rest on those assumptions: opening loses on average
even in the gross reference, without fees, shipping or haircut. It does rest
on the market price, a provider aggregate rather than an observed sale price;
§7 tests its sensitivity.
