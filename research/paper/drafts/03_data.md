<!-- Draft generated in week S3; numbers from snapshot 2026-11-13. -->

# 3. Data

Pull-rate figures in this section come from the Poké Life registry snapshot
dated 2026-11-13 and catalogue figures from TCGdex responses fetched on
2026-11-15; all are reproducible from the committed snapshot and data-audit
outputs.

## 3.1 Sources

**Pull rates.** Per-pack rarity rates are taken from the Poké Life pull-rate
evidence registry, which aggregates published openings (case breaks, store
tallies, streamed box openings and the TCGplayer Authentication Center). We use
the immutable dated version 2026-11-13. It contains 234 rarity rows covering
36 English-language sets, and a companion file describing 75 reviewed openings,
53 of which are flagged as qualifying. The registry is published under
CC BY 4.0 and is redistributed in the replication package with the required
attribution: Poké Life, "Pokémon TCG pull-rate evidence registry,"
https://www.poke-life.com/data/ (accessed 2026-11-15), CC BY 4.0. Intervals
are Beta posteriors under a Jeffreys prior [@jeffreys1946invariant]. Curation
is largely automated, with human review of a sample only; the operator is not
named and the licence of the underlying openings is not stated. We treat the
registry as a documented secondary compilation, not as primary evidence.

**Catalogue.** Card lists, numbers and rarities come from TCGdex, whose card
database is released under the MIT licence. Raw TCGdex responses are not
committed, because they embed price fields and image URLs whose rights are
unclear; they can be re-fetched by script.

**Prices.** TCGdex also exposes price fields from two providers: TCGplayer
(USD; low, mid and high listing prices and a market price) and Cardmarket
(EUR; a low listing price, a trend price and averages). In the typology of the
protocol, these are *active listings* and *provider-market aggregates*. None
is a realised-sale price, and no open source of realised sales was identified.
Each value is attached to one printing (normal, reverse or holo) by a fixed
rule (ADR 0008); values that cannot be attributed to a single printing are
discarded and counted in the ingestion manifest rather than guessed.
Both TCGdex and the secondary provider PkmnPrices authorised their use for
this non-commercial project (ADR 0009). Prices are labelled by type, never
presented as transaction values, and always combined with liquidity-haircut
scenarios; only derived statistics are published, never raw prices. Field evidence supports this
caution: in a one-year study of 300 Pokémon cards listed on eBay, 73 % sold
and posted prices acted as a ceiling on realised prices [@heck2026sales].
The permission does not extend to the terms of the originating marketplaces,
which were not reviewed; this is one more reason not to redistribute raw
prices. Attribution: price data from TCGdex (tcgdex.dev), relaying TCGplayer
and Cardmarket prices, used with permission. This section uses price
*coverage* only.

## 3.2 Set selection

The protocol requires one to three sets chosen by a data-coverage audit. The
selection rule (ADR 0005) was committed before the snapshot and the catalogue
were analysed and before any price value was inspected. A set is eligible if
(1) it is an English-language set in the snapshot; (2) it belongs to the
Scarlet & Violet series or later, with a single 10-card booster whose
composition is publicly documented; (3) at least 5,000 packs were measured
(maximum of `packs` over its rarity rows); (4) every row from Double Rare
upwards has non-missing hits, packs and interval; (5) its TCGdex catalogue is
complete, with a rarity for every card; and (6) at least 90 % of its cards of
rarity Rare and above have at least one price field. Eligible sets are ranked
lexicographically by the share of rows with non-reconstructed counts, the
share of rows with high confidence, packs measured, and release date (older
first). The top three are selected by script.

Of the 36 sets, 15 are eligible. Of the 21 others, 12 belong to earlier series
and 9 have fewer than 5,000 packs. Two criteria do not discriminate: no
eligible set has a non-reconstructed row, and all reach 100 % price coverage.
The ranking is thus decided by the share of high-confidence rows, then by
packs. Among the nine sets with only high-confidence rows, the three with the
most packs are Destined Rivals (sv10), Surging Sparks (sv08) and Stellar Crown
(sv07). Chaos Rising (me04) has more packs (13,819) but ranks eleventh, as
only 80 % of its rows are high confidence. Next in line are Journey Together
(sv09), Scarlet & Violet (sv01) and Paradox Rift (sv04).

**Table 1 — Coverage and quality of the selected sets**

| | Destined Rivals | Surging Sparks | Stellar Crown |
|---|---|---|---|
| TCGdex id | sv10 | sv08 | sv07 |
| Release date (TCGdex) | 2025-05-30 | 2024-11-08 | 2024-09-13 |
| Packs, maximum over rows (range) | 12,446 (8,655–12,446) | 11,254 (10,828–11,254) | 10,800 (10,581–10,800) |
| Rarity rows | 5 | 6 | 6 |
| High-confidence rows | 5/5 | 6/6 | 6/6 |
| Rows with reconstructed counts | 5/5 | 6/6 | 6/6 |
| Qualifying datasets pooled | 2 | 2 | 2 |
| Catalogue size (TCGdex = official total) | 244 | 252 | 175 |
| Hit-rarity cards, TCGdex = Poké Life | 79 | 87 | 50 |
| Rare-and-above cards with a price field | 97/97 | 103/103 | 65/65 |

*Notes.* Hit rarities are Double Rare, Illustration Rare, Ultra Rare, Special
Illustration Rare and Hyper Rare, plus ACE SPEC Rare for sv08 and sv07.
"Hit-rarity cards" sums the per-rarity card counts; the TCGdex and Poké Life
counts agree rarity by rarity. In Destined Rivals the Double Rare row draws on
one dataset only; the other rows pool two. A third Destined Rivals opening
(the registry operator's own) is flagged non-qualifying and not pooled. Price
coverage counts the presence of a positive price field, not its value.
Sources: `data/raw/pokelife/2026-11-13/`, `research/reports/data_audit_*.csv`.

## 3.3 Pull-rate data: characteristics and limitations

**Hit rarities only.** For the three sets, the registry reports per-pack rates
(hits divided by packs) for hit rarities only. Common, Uncommon and Rare have
no row, although they account for 165 of 244, 165 of 252 and 125 of 175
catalogue cards respectively. The rates are not slot distributions: a hit
rarity may appear in more than one physical position (rare and reverse-holo
slots), and the official product description gives only the card count, one
Basic Energy and one code card. The card-count match with TCGdex validates
the number of cards per rarity, not the assumption that cards are equally
likely within a rarity, which the registry cannot test. The ingestion pipeline
re-checks the per-rarity card counts and rejects any snapshot in which the two
sources disagree. *Consequences for the methodology:* the slot structure
must be documented from community sources and treated as scenarios where
uncertain; per-pack rates are modelled with one Beta posterior per rarity, the
Dirichlet case being reserved for slots whose outcomes are documented as
mutually exclusive; and the treatment of low-value cards is specified
separately.

**Reconstructed counts.** All 17 rows of the selected sets carry
`counts_reconstructed = true` (174 of 234 rows registry-wide): hits and packs
were back-calculated from a published rate and margin rather than tallied. If
the published margins were not binomial, posteriors built from these counts
overstate precision. Within a set, rows also have different denominators
(Table 1), so rarities do not share a common sample of packs. *Consequence:*
the pre-registered robustness test that excludes reconstructed rows would
leave no data; it is replaced by a widened-posterior check (for example,
halving the effective sample size), to be recorded as a deviation.

**Small counts at the top.** The rarest outcomes rest on few hits: Hyper Rare
counts are 86, 64 and 76 (rates 0.691 % [0.557, 0.848], 0.570 %
[0.443, 0.722] and 0.712 % [0.565, 0.885], 95 % intervals as reported), and
Special Illustration Rare counts are 130, 138 and 121. Because jackpot cards
concentrate in these rarities, their uncertainty is propagated rather than
fixed at point estimates.

**Pooling of heterogeneous openings.** Each selected rate pools two qualifying
datasets: the TCGplayer Authentication Center and one YouTube opening series.
Surging Sparks and Stellar Crown share the same store-affiliated channel;
Destined Rivals uses a different one. Registry-wide, rows pool one, two or three
datasets (166, 48 and 20 rows). The openings were published at or around
release (2024-09-13 to 2025-05-30), so the rates describe early product;
stability across later print runs is not observed, nor is the
representativeness of openings that were chosen for publication. *Consequence:* homogeneity
between datasets is tested before pooling where per-dataset counts can be
recovered; otherwise pooling is stated as an assumption.

## 3.4 Exclusions and licensing

Japanese sets, which the registry keeps in a separate section, are excluded:
the protocol restricts the main analysis to English products, and an English
and a Japanese card are distinct observations. Sets from series before
Scarlet & Violet are excluded by criterion 2; they use different booster
formats and series-specific rarity labels (for example Rainbow Rare or Trainer
Gallery). Sets below 5,000 measured packs, including several special sets, are
excluded by criterion 3.

No card image is used or redistributed: the rights to TCGdex images are not
stated, and card names and numbers are used as facts only, without
affiliation with the rights holder. Raw prices are never committed or
redistributed (ADRs 0006, 0007 and 0009); only derived statistics are
published. The replication package contains the
pull-rate snapshot (CC BY 4.0, with attribution) and the scripts that re-fetch
the catalogue. Other sources were examined but not used: the Pokémon TCG API
(deprecated, no stated licence), the TCGplayer and Cardmarket APIs (closed to
new access) and eBay sold-price history (restricted).
