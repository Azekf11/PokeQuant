<!-- Draft written in week S11. Numbers: research/reports/results.md and research/reports/robustness.md (run main-94de09e8-k200-m20000). -->

# 1. Introduction

A Pokémon Trading Card Game booster pack is a lottery over cards. Each English
pack holds ten game cards, plus a Basic Energy and a code card. Most cards are
worth less than the cost of selling them, while a small number of rare
printings trade for tens or hundreds of dollars. A collector who wants those
cards can either open packs and sell what they do not keep, or buy the cards
directly on the secondary market.

Online guides and calculators settle the choice with an expected value: the
sum over cards of price × pull rate, compared with the price of a pack. That
number hides four things:

1. The distribution. The value of a pack is very skewed, so its mean says
   little about what a typical opening returns.
2. The odds. For English sets the pull rates are not published; they are
   estimated from community openings, with sampling error.
3. The costs. A listed or aggregated market price is not what a seller
   receives. Fees, shipping and the discount needed to sell all intervene,
   and a fixed cost per sale wipes out the value of cheap cards.
4. The alternative. The relevant comparison is between opening and buying
   the same value directly, rather than between opening and doing nothing,
   and buying has costs too.

This paper asks, for three recent English sets, to what extent opening
boosters is an economically competitive way to acquire cards, compared with
buying them directly, once pull-rate uncertainty, value dispersion, fees and
liquidity are taken into account. We answer with two estimands, both fixed
before any price was analysed. The first, E1 (budget liquidation), sets
spending a budget on boosters and selling every card against buying the most
expensive single cards the budget allows and selling them back. The second,
E2 (target acquisition), sets opening boosters until a chosen card appears
against buying that card.

We model a booster slot by slot. Rarity rates follow Dirichlet posteriors
estimated from community openings, and we propagate their uncertainty through
a nested Monte Carlo of 200 posterior draws of the rates, each with 20,000
simulated runs. Cards are valued at a dated provider market price and
converted into net realisable values under three pre-registered cost
scenarios. Alongside means we report medians, probabilities of loss and the
5 % conditional value-at-risk, each with its Monte Carlo error and its
interval over pull-rate uncertainty. Hypotheses, metrics, decision rules,
scenarios and robustness tests were registered in two stages, as signed git
tags, before the results existed, and every table and figure is regenerated
by one command.

Under the central scenario, opening loses money on average for every set and
budget. The break-even booster price, below which opening would have a
positive expected profit, is 1.03 to 1.42 USD against a retail price of 4.49
USD; without any fee, shipping or haircut it is still 3.44 to 4.29 USD.
Opening 36 boosters loses 111 to 125 USD on average. Buying cards directly
also loses money through its round-trip costs, but less than half as much,
and it is decisively better on the mean, the median and the CVaR in 35 of 36
comparisons. For a collector who wants a set's most valuable card, opening
until it appears is cheaper than buying it in only 4 % to 14 % of simulated
runs.

These conclusions survive sixteen pre-registered variants (§7): other price
statistics, haircuts up to 0.50, halved or increased selling costs, pull
rates at the bounds of their intervals, another prior, the exclusion of the
1 % most valuable cards, and up to 100,000 runs per draw. In every variant
opening loses on average and buying is decisively better. The break-even
booster price stays between 0.54 and 1.74 USD, and the gross break-even price
stays below the retail price in every variant but one, where its upper bound
exceeds it.

Our contribution is not a new expected-value calculator. It is a
reproducible and pre-registered framework that combines four elements: (1) a
slot-level booster model, (2) Bayesian uncertainty on community pull rates,
(3) typed prices converted into net values, and (4) tail-risk measures in a
comparison with direct purchase. The code, configurations, pull-rate snapshot
and every derived result are public. Raw prices are not redistributed, but
the scripts that fetch them and the checksums of the snapshot are.

The paper is organised as follows. Section 2 reviews related work. Section 3
describes the data. Section 4 sets out the model and the simulation engine,
and Section 5 the pre-registered design. Section 6 reports the results and
Section 7 their robustness. Section 8 discusses limits and implications, and
Section 9 concludes.
