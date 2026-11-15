# Data audit: week S2

Date: 2026-11-15. Reproduce with:

```bash
uv run python scripts/audit_sets.py --pokelife 2026-11-13 --fetch-date 2026-11-15
```

Outputs: [`data_audit_coverage.csv`](data_audit_coverage.csv) (all 36 sets of
the registry, eligibility and ranking) and
[`data_audit_rarities.csv`](data_audit_rarities.csv) (rarity reconciliation
for the selected sets). The selection rule ([ADR 0005](../../docs/decisions/0005-set-selection-rule.md))
was committed before any data was analysed.

## 1. Pull rates: Poké Life registry (snapshot 2026-11-13)

- 234 rarity rows over **36 sets** (the site covers 167 sets, but only these
  36 have rarity-level rates in the open files).
- Rows report **per-pack rates of hit rarities only** (Double Rare and above,
  plus ACE SPEC). Common, Uncommon and Rare have no row.
- Confidence: 178 high, 38 moderate, 18 limited.
- **Every Scarlet & Violet / Mega Evolution set with ≥ 5 000 packs has
  reconstructed counts** (`counts_reconstructed = true` on every row): hits and
  packs were back-calculated from published rates and margins. Ranking
  criterion 1 of ADR 0005 therefore does not discriminate between eligible
  sets.
- Each rate pools 1–3 openings (`datasets.csv`), dominated by the TCGplayer
  Authentication Center plus YouTube openings. Example: Surging Sparks and
  Stellar Crown each pool TCGplayer + one YouTube store channel; Destined Rivals
  pools TCGplayer + a second channel (Poké Life's own openings are flagged
  non-qualifying).

## 2. Catalogue: TCGdex (fetched 2026-11-15)

- All 15 candidate sets are complete: every card listed in the set has a
  rarity, and the count equals the official total.
- For the three selected sets, the number of cards per hit rarity in TCGdex
  **matches exactly** Poké Life's `cards_in_rarity` (rarity reconciliation
  file). This validates the within-rarity uniform model input.

## 3. Prices: presence only

- TCGdex returns at least one positive price field for **100 %** of the cards
  of rarity Rare and above in all 15 candidate sets (criterion 6 does not
  discriminate). No price value was inspected.
- Price types available through TCGdex: listing (TCGplayer low/mid/high,
  Cardmarket low) and provider market (TCGplayer market, Cardmarket
  trend/averages). **No realised-sale price.** Redistribution rights unclear
  (S1).

## 4. Selection (ADR 0005)

| Rank | Set | TCGdex | Release | Packs | High-confidence rows | Hit rarities |
|---|---|---|---|---|---|---|
| 1 | Destined Rivals | sv10 | 2025-05-30 | 12 446 | 5/5 | DR, IR, UR, SIR, HR |
| 2 | Surging Sparks | sv08 | 2024-11-08 | 11 254 | 6/6 | DR, ACE, IR, UR, SIR, HR |
| 3 | Stellar Crown | sv07 | 2024-09-13 | 10 800 | 6/6 | DR, ACE, IR, UR, SIR, HR |

Next in line: Journey Together (sv09), Scarlet & Violet (sv01), Paradox Rift
(sv04). Twelve other sets were eligible; 21 failed (series before Scarlet &
Violet, or fewer than 5 000 packs).

## 5. Consequences for later weeks

1. **Slot model (S4, Gate G4).** The registry gives per-pack hit rates, not
   slot distributions. The official product page only states "10 cards, 1
   Basic Energy, 1 code card". The base slots (commons, uncommons, reverse
   holos) and the rule that turns per-pack hit rates into slot outcomes must be
   documented from community sources and treated as **scenarios** where
   uncertain. Hit rarities may appear in more than one physical position
   (rare slot and reverse-holo slots), so per-pack rates are not mutually
   exclusive slot outcomes: the protocol's Beta-per-rate case applies, the
   Dirichlet case only to a slot whose outcomes are documented as exclusive.
2. **Reconstructed counts (S4).** Posteriors built from reconstructed counts
   overstate precision if the published margin was not binomial. Robustness
   test 9 (protocol §7.2) cannot exclude them (it would leave no data), so it
   becomes: widen the posterior (e.g. halve the effective sample size) and
   check whether conclusions change.
3. **Heterogeneity (S4).** Two or three datasets per set allow a test of
   homogeneity between TCGplayer and YouTube openings before pooling.

## 6. Gate G2: recommendation

Criterion: *usable, legally reusable price data*. Status: **conditional GO**.

- Pull rates and catalogue are usable and redistributable (or re-fetchable).
- Prices exist for every relevant card but only as listing / provider-market
  types, with unclear publication rights. Prices are first needed in **S6**,
  so S3–S5 can proceed without them.
- Recommended path: option **P1** (TCGdex provider-market prices kept locally,
  only derived statistics published) **if TCGdex confirms** it is acceptable,
  and **P2** (PkmnPrices) as a second request. **P4** (price scenarios +
  limited case study) remains the guaranteed fallback.
- Hard deadline: if no answer allows P1 or P2 by the end of S5, S6 switches
  to P4 and the paper makes no claim on observed market profitability.

**Decision (2026-11-15): conditional GO**, recorded in
[ADR 0007](../../docs/decisions/0007-gate-g2-price-data.md).
