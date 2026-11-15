<!-- Version 2. Sources: research/reports/data_audit.md, homogeneity.csv, pull_rate_checks.md, valuation.md; ADRs 0005-0010. -->

# 2. Data

Every input of the model has a dated source, listed in Appendix A. This
section describes the three kinds of data (pull rates, catalogue and prices),
the cost parameters, and the checks each input passed.

## 2.1 Pull rates

Per-pack rarity rates come from the Poké Life pull-rate evidence registry,
version 2026-11-13 (CC BY 4.0). It holds 234 rarity rows for 36 English sets,
compiled from 75 reviewed openings, of which 53 are flagged as qualifying.
Each row gives hits, packs, a rate and a 95 % interval for one hit rarity
(Double Rare and above, and ACE SPEC Rare). The rows of the selected sets pool
two openings: the TCGplayer Authentication Center (8,300 to 9,000 packs per
rarity row, reconstructed from its published margins) and one YouTube opening
series.

Two features of the registry matter for the model. First, its counts are
reconstructed: hits and packs were back-calculated from a published rate and
margin rather than tallied, for all 17 rows of the selected sets. If the
published margins were not binomial, posteriors built on these counts
overstate precision, so one robustness test halves their weight. Second, the
rarest outcomes rest on few hits: 64 to 86 Hyper Rares and 121 to 138 Special
Illustration Rares per set. This is why the uncertainty on the rates is
propagated rather than fixed at point estimates.

I checked the registry in three ways (Section 5.4 gives the details). Its
rates match the tables printed in the TCGplayer articles, read on 2026-11-15,
for all 33 single-source rows of the seven sets added in Section 5.2. Pooling
the two openings is not rejected by a χ² homogeneity test in any of the 16
testable rows (Holm–Bonferroni, 5 %). And in a held-out test, the TCGplayer
counts alone predict the second opening's hits inside the 95 % predictive
interval in 20 of 20 rows.

## 2.2 Sets and catalogue

The set selection rule (ADR 0005) was committed before any data were
analysed. A set is eligible if it is an English set of the Scarlet & Violet
series or later, with at least 5,000 packs measured, complete rarity rows, a
complete catalogue and at least 90 % price coverage of its Rare-and-above
cards. Of the 36 sets, 15 are eligible. They are ranked by data quality, and
the top three are Destined Rivals (sv10), Surging Sparks (sv08) and Stellar
Crown (sv07). The other twelve are used in Section 5.2.

The catalogue comes from TCGdex (MIT licence), fetched on 2026-11-15. For the
three sets, the number of cards in each hit rarity matches the registry
exactly, and the ingestion rejects any snapshot where the two sources
disagree. Table 1 summarises the selected sets.

**Table 1.** Selected sets.

| | Stellar Crown | Surging Sparks | Destined Rivals |
|---|---|---|---|
| TCGdex id, release | sv07, 2024-09-13 | sv08, 2024-11-08 | sv10, 2025-05-30 |
| Packs measured, maximum over rows | 10,800 | 11,254 | 12,446 |
| Rarity rows (high confidence) | 6 (6) | 6 (6) | 5 (5) |
| Catalogue size | 175 | 252 | 244 |

*Source:* Poké Life registry 2026-11-13; TCGdex 2026-11-15;
`research/reports/data_audit.md` and `valuation.md`. Of the 1,126 printings
a pack of the three sets can contain, 1,119 have a market price. The seven
others are in Stellar Crown; they take the median price of their pool
(central) or zero (adverse).

## 2.3 Prices

Cards are valued at the TCGplayer market price in USD, relayed by TCGdex on
2026-11-15, with every observation time-stamped by the provider (2026-11-14,
22:22 to 22:24 UTC). The market price is a provider aggregate of recent sales
and listings, not a single transaction, and card condition is not specified.
Listing prices are never used as transaction values. Prices are used with the
permission of TCGdex for this non-commercial project; only derived statistics
are published (ADR 0009). Section 5.3 replaces them with Cardmarket's 30-day
average sale prices as a check.

## 2.4 Costs

A seller receives the net liquidation value

ℓ(c) = max{0, p(c)(1 − h)(1 − f_m − f_p) − f_0 − s},  (1)

and a buyer pays the acquisition cost a(c) = p(c)(1 + f_b) + s_b, one card per
transaction, where p(c) is the market price of printing c. Table 2 gives the
three cost scenarios and the source of each value.

**Table 2.** Cost scenarios (USD) and sources.

| Parameter | Gross | Central | Adverse | Source |
|---|---|---|---|---|
| Booster price b | 4.49 | 4.49 | 5.49 | Assumption: US retail price at launch; b\* is reported so any b can be used |
| Marketplace fee f_m | 0 | 10.75 % | 10.75 % | TCGplayer seller fee page, read 2026-11-15 |
| Payment fee f_p, fixed fee f_0 | 0, 0 | 2.5 %, 0.30 | 2.5 %, 0.30 | TCGplayer seller fee page, read 2026-11-15 |
| Shipping per sale s, per purchase s_b | 0, 0 | 1.00, 1.00 | 4.50, 4.50 | Assumption: untracked (central) or tracked (adverse) letter |
| Liquidity haircut h | 0 | 0.15 | 0.30 | Assumption; anchored on Heck et al. [-@heck2026sales] in robustness test R10 |

The gross scenario is a reference without frictions, never the main result.
Under central costs a card is worth selling only if its price exceeds about
1.76 USD, since the fixed fee and shipping alone cost 1.30 USD.
