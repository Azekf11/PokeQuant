<!-- Version 2. Numbers: research/reports/results.md and robustness.md (run main-94de09e8-k200-m20000, tag analysis-v1). Read status of every reference: references.bib, `note` field. -->

# 1. Introduction

A booster pack of the Pokémon Trading Card Game is a lottery over cards. An
English pack holds ten game cards. Most are worth less than the cost of
selling them, while a few rare printings trade for tens or hundreds of
dollars. A collector who wants those cards can open packs and sell what they
do not keep, or buy the cards directly. Online guides settle the choice with
an expected value, the sum over cards of price times pull rate, compared with
the price of a pack. That number leaves out four things. The value of a pack
is highly skewed, so its mean says little about a typical opening. Pull rates
for English sets are not published by the manufacturer and must be estimated
from community openings. A market price is not what a seller receives once
fees, shipping and the discount needed to sell are paid. And the relevant
alternative is to buy the same cards, which has costs too.

This paper asks to what extent opening boosters is an economically
competitive way to acquire cards, compared with buying them directly. I study
three recent English sets, Stellar Crown, Surging Sparks and Destined Rivals,
and two comparisons fixed before any price was analysed. In the first (E1),
a budget is spent on boosters and every card is sold, or the same budget buys
the most expensive single cards and they are sold back. In the second (E2),
packs are opened until a chosen card appears, or that card is bought.

The method has three parts. A booster is modelled slot by slot, with rarity
probabilities given Dirichlet posteriors estimated from community openings.
Cards are valued at a dated provider market price and converted into net
realisable values under three cost scenarios. A nested Monte Carlo simulation
then propagates both the uncertainty on the pull rates (200 posterior draws)
and the randomness of the packs (20,000 runs per draw). I report means,
medians, probabilities of loss and the 5 % conditional value-at-risk, each
with its Monte Carlo error and its interval over pull-rate uncertainty.
Hypotheses, metrics, decision rules and robustness tests were registered as
signed git tags before the results existed, and one command regenerates every
table and figure.

Three findings stand out. First, opening loses money on average. Under
central costs, the break-even booster price, below which opening has a
positive expected profit, is 1.03 to 1.42 USD against a retail price of 4.49
USD. Without any fee, shipping or haircut it is still 3.44 to 4.29 USD.
Second, buying is the better way to acquire cards. Opening 36 boosters
loses 111 to 125 USD on average; buying and reselling the same value loses
46 to 51 USD. Buying is decisively better on the mean, the median and the
CVaR in 35 of 36 budget comparisons. Third, chasing one valuable card by
opening rarely pays: opening until the set's most valuable card appears is
cheaper than buying it in only 4 % to 14 % of simulated runs. These results
survive sixteen pre-registered robustness variants and three pre-registered
extensions. On eleven further sets, opening still loses on average and buying
still wins for every budget of ten boosters or more, although for two sets a
pack's gross market value exceeds its retail price. At European sale prices,
opening still loses on average under central costs.

**Related literature.** Studies of collectibles as assets measure long-run
returns and stress transaction costs [@burton1999measuring;
@dimson2011expost; @mei2002art; @renneboog2013buying], and recent work covers
LEGO sets, sealed trading-card products and video-game items
[@dobrynskaya2022lego; @wang2023sealed; @dobrynskaya2025videogame]. These
papers ask whether holding a collectible pays; I ask an earlier question,
what it costs to obtain one. Work on Pokémon cards concerns price
determinants, grading and market efficiency [@danz2026gotta;
@baro2026hedonic; @sharma2026grading], and a field study of 300 cards listed
on eBay for a year found that 73 % sold and that posted prices acted as a
ceiling on realised prices [@heck2026sales]; I use it to anchor one liquidity
scenario. Booster packs belong to the family of randomised products studied
as loot boxes, gacha and blind boxes [@chen2021lootbox; @gan2021gacha;
@hu2024blindbox], with a public-health literature linking them to problem
gambling [@zendle2018lootbox; @zendle2021booster]. The closest formal work,
Mota [-@mota2026valuation], models a sealed Magic: The Gathering product slot
by slot and lists the frictions that separate its price from the expected
value of its contents, with a hypothetical numerical example. I share the
slot-level expected value and the sale threshold, but use measured pull rates
and dated prices, treat the rates as uncertain, report the full distribution
and its tail, and compare opening with buying. The risk measure is the
expected shortfall [@artzner1999coherent; @acerbi2002coherence], and the
separation of epistemic and aleatory uncertainty follows Der Kiureghian and
Ditlevsen [-@derkiureghian2009aleatory].

The paper proceeds as follows. Section 2 describes the data and how each
input was checked. Section 3 sets out the model and the simulation. Section 4
reports the results, Section 5 the robustness tests and extensions, and
Section 6 concludes. The appendix lists the source of every input, the
validation of the engine and the pre-registration record.
