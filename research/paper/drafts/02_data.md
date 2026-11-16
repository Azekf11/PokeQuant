<!-- Version 3. Sources: research/reports/data_audit.md, homogeneity.csv, pull_rate_checks.md, valuation.md; ADRs 0005-0010. -->

# 2. Data

Every input has a dated source, listed in Appendix A.

## 2.1 Pull rates

Per-pack rarity rates come from the Poké Life pull-rate evidence registry,
version 2026-11-13 (CC BY 4.0): 234 rarity rows for 36 English sets, compiled
from 75 reviewed openings. Each row gives hits, packs, a rate and a 95 %
interval for one hit rarity (Double Rare and above, and ACE SPEC Rare). The
rows of the selected sets pool two openings: the TCGplayer Authentication
Center (8,300 to 9,000 packs per row, reconstructed from its published
margins) and one YouTube opening series. All 17 rows of the selected sets
have counts back-calculated from a published rate and margin, so one
robustness test halves their weight. The rarest outcomes rest on few hits
(64 to 86 Hyper Rares and 121 to 138 Special Illustration Rares per set),
which is why rate uncertainty is propagated rather than fixed. The registry
matches its primary source, pooling the two openings is not rejected by a χ²
homogeneity test in any of the 16 testable rows (Holm–Bonferroni, 5 %), and a
held-out predictive check finds no inconsistency (Section 5.4).

## 2.2 Sets and catalogue

The selection rule (ADR 0005) was committed before any data were analysed: an
English set of the Scarlet & Violet series or later, with at least 5,000
packs measured, complete rarity rows, a complete catalogue and at least 90 %
price coverage of its Rare-and-above cards. Of 36 sets, 15 are eligible; the
top three by data quality are Destined Rivals (sv10), Surging Sparks (sv08)
and Stellar Crown (sv07). Seven of the other twelve are used in Section 5.2
and the four Mega Evolution sets in Section 5.5; 30th Celebration, whose
catalogue lacks one of its rarities, is not used. The catalogue comes from
TCGdex (MIT licence), fetched on 2026-11-15; its number of cards in each hit
rarity matches the registry exactly (Table 1).

**Table 1.** Selected sets.

| | Stellar Crown | Surging Sparks | Destined Rivals |
|---|---|---|---|
| TCGdex id, release | sv07, 2024-09-13 | sv08, 2024-11-08 | sv10, 2025-05-30 |
| Packs measured, maximum over rows | 10,800 | 11,254 | 12,446 |
| Rarity rows (high confidence) | 6 (6) | 6 (6) | 5 (5) |
| Catalogue size | 175 | 252 | 244 |

*Source:* Poké Life registry 2026-11-13; TCGdex 2026-11-15;
`research/reports/data_audit.md` and `valuation.md`. Of the 1,126 printings
a pack can contain, 1,119 have a market price; the seven others (Stellar
Crown) take the median price of their pool (central) or zero (adverse).

## 2.3 Prices and costs

Cards are valued at the TCGplayer market price in USD, relayed by TCGdex on
2026-11-15 and time-stamped by the provider (2026-11-14, 22:22 to 22:24 UTC).
It is a provider aggregate of recent sales and listings, not a single
transaction, and card condition is not specified. Prices are used with the
permission of TCGdex for this non-commercial project, and only derived
statistics are published (ADR 0009). Section 5.3 replaces them with
Cardmarket's 30-day average sale prices as a check.

A seller receives the net liquidation value

ℓ(c) = max{0, p(c)(1 − h)(1 − f_m − f_p) − f_0 − s},  (1)

and a buyer pays a(c) = p(c)(1 + f_b) + s_b, one card per transaction, where
p(c) is the market price of printing c (Table 2).

**Table 2.** Cost scenarios (USD) and sources.

| Parameter | Gross | Central | Adverse | Source |
|---|---|---|---|---|
| Booster price b | 4.49 | 4.49 | 5.49 | Assumption: US retail price at launch; b\* is reported so any b can be used |
| Marketplace fee f_m | 0 | 10.75 % | 10.75 % | TCGplayer seller fee page, read 2026-11-15 |
| Payment fee f_p, fixed fee f_0 | 0, 0 | 2.5 %, 0.30 | 2.5 %, 0.30 | TCGplayer seller fee page, read 2026-11-15 |
| Shipping per sale s, per purchase s_b | 0, 0 | 1.00, 1.00 | 4.50, 4.50 | Assumption: untracked (central) or tracked (adverse) letter |
| Liquidity haircut h | 0 | 0.15 | 0.30 | Assumption; anchored on Heck et al. [-@heck2026sales] in test R10 |

The gross scenario is a reference without frictions, never the main result.
Under central costs a card is worth selling only above about 1.76 USD, since
the fixed fee and shipping alone cost 1.30 USD.
