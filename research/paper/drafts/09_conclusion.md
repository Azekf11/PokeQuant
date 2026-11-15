<!-- Draft written in week S11. No new result. -->

# 9. Conclusion

Is opening Pokémon TCG boosters a competitive way to acquire cards? For three
recent English sets, valued at the TCGplayer market prices of 2026-11-15,
under explicit costs and propagated pull-rate uncertainty, the answer is no.
Opening loses money on average: a booster's expected net resale value is
about a quarter to a third of its retail price. Buying cards directly also
costs money, through fees and shipping, but less than half as much for the
same budget. In the central scenario buying is decisively better on the mean,
the median and the 5 % conditional value-at-risk, for every budget of ten
boosters or more and for every target card. Chasing one valuable card is
rarely cheaper by opening, since opening until it appears costs less than
buying it in only 4 % to 14 % of simulated runs.

These conclusions hold in all sixteen pre-registered robustness variants,
with one exception at the margin: under indicative asking-price statistics,
the upper bound of one set's gross break-even price exceeds the retail price.

The results do not show that opening is never worthwhile, because the model
prices neither the entertainment of opening nor the cards a collector keeps.
Prices and costs also differ at another date, in another market or for older
sets, and the prices we use are a provider's market estimate rather than
observed sales.

The contribution of the paper is a reproducible and pre-registered framework
that combines a slot-level booster model, Bayesian uncertainty on community
pull rates, typed prices converted into net values, and tail-risk measures.
The same framework can be rerun on new sets, new price snapshots or new cost
assumptions by editing one configuration file.

Some work remains. A second price snapshot (2026-12-13) will test the date
half of H4. If a source with redistribution rights becomes available,
realised-sale data would replace the market-price assumption. Grading
(protocol §11) and sealed-product holding returns are natural extensions, but
they need data this study does not have.
