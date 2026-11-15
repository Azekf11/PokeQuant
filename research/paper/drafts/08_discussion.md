<!-- Draft written in week S11. No new result in this section; numbers refer to §6 and §7. -->

# 8. Discussion

## 8.1 Why opening loses

**The fixed cost of a sale.** In the central scenario, selling one card costs
at least 1.30 USD (the fixed fee and shipping) on top of fees proportional to
the price. A card is worth selling only if its market price exceeds about
1.76 USD. Most cards in a pack are worth less than that: in 79 % (Stellar
Crown) to 86 % (Destined Rivals) of simulated packs, no card clears the
threshold, and the pack's net value is zero (Figure 3). The value of opening
is concentrated in rare hits. The most valuable cards appear once in 168 to
1,008 packs on average.

**The gross reference.** Even without any fee, shipping or haircut, the
expected market value of a pack is below its retail price: 3.44 to 4.29 USD
against 4.49 USD. This is a statement about the provider's market prices on
one date. It does not mean that every pack is sold above its value, nor that
collectors behave irrationally. Opening has a value of its own that the
model does not price: the entertainment of the draw, and the cards a
collector keeps.

**Buying has costs too.** Direct purchase is not free. Buying and reselling
the most expensive cards a budget allows costs the shipping of each card and
the round-trip fees. With a one-booster budget under the adverse scenario,
these fixed costs make buying worse than opening on the mean, but not on the
median or the tail, for two of the three sets (H1). The comparison therefore
depends on the number of cards bought, not only on their value.

## 8.2 What the risk measures add

The mean alone would mislead in two ways:

1. **The tail.** In E2, opening until a target appears has a long tail. In
   the worst 5 % of runs, opening costs on average 1,750 to 10,700 USD more
   than buying the card (CVaR 5 %, central scenario).
2. **The typical outcome.** In E1, the median outcome of opening is worse than
   its mean, because rare hits pull the mean up.

Reporting the median, the probability of loss and the CVaR does not change
the verdict here, since buying wins on all three. It does change the size of
the gap.

## 8.3 What the uncertainty on pull rates changes

Propagating the uncertainty on pull rates widens every interval. It changes a
verdict only once in the main run: for Stellar Crown's top target under gross
prices, where the median is close to a tie (H2). The conclusions do not hinge
on the precise rates. This is expected, given that the gap between opening and
buying is large compared with the uncertainty on the rates.

## 8.4 What the robustness tests add

The robustness tests (§7) separate two kinds of assumption:

- **Liquidation assumptions move the size of the result.** The haircut,
  the selling costs and the exclusion of the most valuable cards move the
  break-even booster price by up to 0.83 USD and the gap at 36 boosters by up
  to 30 USD. None of them reverses a conclusion.
- **Pull-rate assumptions barely move it.** The prior, the effective sample
  size, the slot of Hyper Rares and the short print leave the central
  break-even price unchanged at two decimals. Even every rate at a bound of its
  interval moves it by at most 0.15 USD.

The only verdicts that depend on the simulation itself are comparisons at a
one-booster budget, where the two strategies differ by less than 0.40 USD.
There the decision rule, a share of posterior draws, also absorbs simulation
noise within each draw. A verdict close to the threshold should therefore be
read as a near tie, whichever side it falls on.

## 8.5 Limits

**Prices.**

- Cards are valued at a provider's market price on a single date (2026-11-15).
  This is an aggregate of recent sales and listings, not an observed
  transaction for each card.
- Card condition is not specified.
- The liquidity haircut is an assumption. One robustness test anchors it on
  observed sell-through rates, but those come from another platform and
  another card sample.
- A second snapshot (2026-12-13) will test whether the conclusions hold at
  another date. Until then, H4 is tested across sets only.

**Costs.**

- Fees are TCGplayer's published fees for standard sellers.
- Shipping and haircuts are scenarios.
- Each card is sold or bought alone. A seller who bundles cards, or a buyer
  who orders several cards from one seller, would pay less shipping per card.
  This would raise the value of opening and lower the cost of buying, so its
  net effect on the comparison is not signed a priori. The three cost
  scenarios and the robustness tests on fees bracket part of this effect.

**Pull rates.**

- The rates come from community openings compiled by a third party. For
  the selected sets, every count is reconstructed from a published rate and
  sample size (R9b halves their weight).
- The uncertainty is propagated, but a bias common to all openings, such as
  over-reporting of good packs, would not be.
- The slot layout follows the source of the data, and an alternative layout
  is tested (R12).
- Three assumptions are not testable with the data:
  - slots are independent;
  - printings are equally likely within a rarity, except the one documented
    short print;
  - English packs have no special collation.

**Scope.**

- Three recent English sets, one product (the booster pack), the US market
  and one price date.
- Graded cards, sealed products, long holding periods and time-varying prices
  are out of scope.
- The results do not generalise to older sets, other languages or other
  markets, where prices, costs and pull rates differ.

**Literature.** Most related works were read at abstract level only (§2).
The novelty claim should be checked against the full texts of the closest
papers.

## 8.6 Implications

For a collector who wants specific cards, the results support buying them
directly, unless the booster price is far below retail. In the central
scenario, the break-even booster price is roughly a quarter to a third of the
retail price. For a collector who opens packs for the experience, the results
put a price on that experience: 3.07 to 3.46 USD per pack, on average, in
the central scenario.

The method is general. It needs:

- per-rarity pull rates with sample sizes;
- a documented slot layout;
- a typed price snapshot;
- explicit costs.

Updating the analysis for a new set or a new date means updating the
configuration and the data snapshots, then rerunning `make reproduce`.
