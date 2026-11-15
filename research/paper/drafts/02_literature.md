<!-- Draft written in week S11. Read status of every reference: research/paper/references.bib (`note` field). Only Heck et al. (2026) and preprint versions of Acerbi & Tasche (2002) and Gordy & Juneja (2010) were read in full; other works are cited for what their abstracts state. -->

# 2. Related literature

The paper draws on five strands of work. For most of them we cite only what
the published abstract states, and the `note` field of each bibliography entry
records what was read.

## 2.1 Collectibles as assets

The returns on collectibles are well studied, and this strand of work stresses
transaction costs. Burton and Jacobsen [-@burton1999measuring] survey how such
returns are measured. Dimson and Spaenjers [-@dimson2011expost] report the
long-run performance of stamps, while Mei and Moses [-@mei2002art] and
Renneboog and Spaenjers [-@renneboog2013buying] study art.

Recent work comes closer to our object by covering sealed products.
Dobrynskaya and Kishilova [-@dobrynskaya2022lego] study LEGO sets as an
investment, and Wang and Langelett [-@wang2023sealed] examine sealed
trading-card products as investments and portfolio diversifiers. Mota
[-@mota2026capm] builds an index of sealed Magic: The Gathering booster boxes.
Dobrynskaya and Strelnikov [-@dobrynskaya2025videogame] turn to video-game
items, some of which are obtained from randomised loot boxes.

These studies ask whether holding a collectible pays. Our question is narrower
and comes earlier: what does it cost to *obtain* cards by opening packs rather
than buying them?

## 2.2 Pokémon cards and their markets

Academic work on Pokémon cards concerns price determinants, grading and market
efficiency. Danz [-@danz2026gotta] relates prices to scarcity and sentiment in
a large panel of sets and tests weak-form efficiency; access to this thesis is
restricted, and we know its abstract only. Baro [-@baro2026hedonic] estimates
a hedonic model of graded card prices in a paper that is linked to a
commercial product. Sharma [-@sharma2026grading] measures grading premiums
over the 2020–2022 boom and bust.

The hedonic approach goes back to Rosen [-@rosen1974hedonic], and among its
applications to cards is the study of baseball cards by Mullin and Dunn
[-@mullin2002baseball]. For a game that sells randomised packs, the most
relevant hedonic result is Hughes [-@hughes2022rarity]: in Magic: The
Gathering, a card's rarity designation, which is set through pack odds,
carries a price premium of its own.

A field study bears directly on our liquidity assumptions. Heck et al.
[-@heck2026sales] listed 300 Pokémon cards on eBay for one year. Of these
cards, 73 % sold, holo cards sold faster than others, and posted prices acted
as a ceiling on realised prices. We use these figures to anchor one robustness
scenario (R10). Because they come from a different sample and platform, we
label them as transferred evidence.

## 2.3 Booster packs, loot boxes and odds disclosure

Booster packs belong to the family of randomised products, and several papers
model the design and pricing of such products: Chen et al. [-@chen2021lootbox]
for loot boxes, Gan [-@gan2021gacha] for gacha games, and Hu, Qin and Sekar
[-@hu2024blindbox] for blind boxes.

A public-health literature links spending on loot boxes and on physical
booster packs to problem gambling [@zendle2018lootbox; @zendle2021booster;
@xiao2025cardpack]. Odds-disclosure rules are not always followed: Xiao et al.
[-@xiao2023odds] report poor compliance with the UK industry's self-regulation
on loot-box probability disclosure. For the English sets we study, the
official product description gives only the number of cards per pack. We
therefore estimate pull rates from community openings and treat them as
uncertain (§3, §4).

## 2.4 Practitioner tools

Online guides and calculators already compute the expected value of a pack
from a price snapshot and published odds, and some also simulate the
distribution of a pack's value with fixed odds (S1 review,
`research/protocol/literature_review.md`). A pack-level Monte Carlo is
therefore not a contribution in itself, and neither is the observation that
the mean of a skewed value distribution exceeds its median.

The closest formal treatment is Mota [-@mota2026valuation], which we read in
full. It models a sealed Magic: The Gathering product slot by slot, defines
the expected value of opening it, and calls the difference between the sealed
price and that expected value the "sealed-opened spread". Under perfect
markets the spread is zero. The paper then lists the frictions that move it
away from zero: a proportional transaction cost, a minimum value below which a
card is not worth selling, a liquidity factor per card, variance and risk
aversion, the irreversibility of opening, and a gambling premium. Its
numerical example uses a hypothetical set.

Our model shares its starting point, namely the slot-level expected value, a
threshold below which cards are not sold, and a liquidity discount, but it
differs in four ways. First, it uses real data: pull rates measured on
community openings and dated market prices for three sets. Second, the slot
probabilities are uncertain, whereas Mota treats them as known and leaves a
Bayesian treatment of this uncertainty to future work. Third, our model
reports the whole distribution of outcomes and its tail, not only the expected
value and the variance. Finally, it compares opening with buying the same
value directly, at equal budget and for a target card, while Mota compares the
sealed price with the expected value of the contents.

## 2.5 Risk measures and nested simulation

We report the 5 % conditional value-at-risk (CVaR, or expected shortfall), a
coherent risk measure [@artzner1999coherent]. Rockafellar and Uryasev
[-@rockafellar2000cvar; -@rockafellar2002cvar] study its optimisation and its
extension to general loss distributions.

Our simulated profits are discrete, with masses at a few values; a one-pack
budget, for example, often yields the same loss in many runs. Acerbi and
Tasche [-@acerbi2002coherence] show that a suitably defined expected shortfall
is coherent for any distribution with a finite mean loss, discrete or not
(their Prop. 3.1), and that minus the average of the ⌊nα⌋ worst simulated
outcomes converges to it (Prop. 4.1). With α = 5 % and 20,000 runs, this
average is our estimator, and it rests on 1,000 tail samples.

For the pull rates, we separate the uncertainty on the rates themselves
(epistemic) from the randomness of the packs (aleatory)
[@derkiureghian2009aleatory]. Rates follow Beta and Dirichlet posteriors under
a Jeffreys prior [@jeffreys1946invariant], and Jeffreys intervals perform well
for binomial proportions [@brown2001interval].

On nested simulation, Gordy and Juneja [-@gordy2010nested] study a design that
estimates a risk measure of a conditional expectation. They show that, as the
budget grows, the inner sample size should grow only as its cube root, and the
number of outer scenarios as its two-thirds power.

Our design answers a different question, since we do not estimate a risk
measure of the conditional mean. Every metric is computed *within* one draw of
the rates, on 20,000 simulated runs, and the draws are used only to obtain its
posterior interval. Within-draw tail estimates need many inner runs, whereas
the interval needs only enough outer draws for stable 2.5 % and 97.5 %
quantiles. This is why we use a 200 × 20,000 design, and robustness test R7
checks its stability (§7).

## 2.6 Position of this paper

To our knowledge, no published study of the Pokémon TCG combines:

1. Bayesian uncertainty on community-estimated pull rates, propagated through
   a nested Monte Carlo;
2. typed market prices converted into net realisable values with explicit
   fees and liquidity scenarios;
3. coherent tail-risk measures;
4. two pre-registered comparisons with direct purchase: spending an equal
   budget, and acquiring a target card.

This statement rests on the works listed above. The closest of them, Mota
[-@mota2026valuation], was read in full; most of the others were read at
abstract level.
