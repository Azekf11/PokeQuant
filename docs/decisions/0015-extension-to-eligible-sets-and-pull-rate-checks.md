# 0015: Extension to the other eligible sets and pull-rate checks (prereg-v4)

- Status: accepted
- Date: 2026-11-15
- Decided by: author
- Extends: [ADR 0005](0005-set-selection-rule.md), [ADR 0011](0011-operational-comparison-rules.md),
  [ADR 0012](0012-operational-robustness-tests.md), model specification §5 (homogeneity)
- Parameters: [research/experiments/extension_sets.yaml](../../research/experiments/extension_sets.yaml)

## Context

The main analysis (`analysis-v1`) covers the three top-ranked sets of ADR 0005.
Twelve other sets met every eligibility criterion. With three sets, H4 across
sets rests on very little variation. The pull rates are also the least
checked input: every count is reconstructed from a published rate and margin,
and the only check so far is the homogeneity test between pooled datasets
(no rejection).

**What was seen before this record.** While checking whether the twelve sets
can be ingested, the following were displayed: the Poké Life registry rows
(rates, counts, datasets) of the twelve sets; the pull-rate tables printed in
the seven TCGplayer articles of the sets that fit the main layout (read
2026-11-15 in a browser); ingestion row counts. In doing so, one data issue was
noticed: the Paradox Rift and Paldea Evolved articles print the same Ultra
Rare (6.64 % ± 0.53 %) and Illustration Rare (7.70 % ± 0.56 %) rates. A
timing run of the extension configuration was made; its outputs were deleted
unread. No price value and no result of the twelve sets has been viewed.

## Decision

An **exploratory extension**, pre-registered under the tag `prereg-v4`. It
changes nothing in `analysis-v1`; its results are reported in a separate
section of the paper.

1. **Evaluable sets.** An eligible set (ADR 0005) is evaluated if (a) it passes
   the ingestion validation and (b) every registry rarity of the set maps to a
   slot of the main layout `tcgplayer`. No new layout is introduced. Applied to
   the twelve sets:
   - evaluable: Scarlet & Violet (sv01), Paldea Evolved (sv02), Obsidian Flames
     (sv03), Paradox Rift (sv04), Temporal Forces (sv05), Twilight Masquerade
     (sv06), Journey Together (sv09);
   - not evaluable: Mega Evolution (me01), Phantasmal Flames (me02), Chaos
     Rising (me04), Pitch Black (me05), whose "Mega Hyper Rare" has no slot in
     the main layout; 30th Celebration, whose registry rarity "Classic
     Collection" is absent from the catalogue (ingestion fails).
2. **Analysis.** The main experiment is repeated on the ten evaluable sets
   (the three main sets included) with `extension_sets.yaml`: same seed,
   prior, draws, runs, scenarios, estimands, price basis and snapshot. The
   checks C1–C3 of ADR 0012 are reported by set, and H1–H4 of ADR 0011 over
   the ten sets. Robustness tests are not repeated.
3. **Source check (S1).** Each registry rate of the seven added sets is
   compared with the rate printed in the set's TCGplayer article. The printed
   values are committed in `research/reports/extension/tcgplayer_published_rates.csv`.
   A row agrees if the registry rate equals the printed rate to the printed
   precision (two decimals, in %). Rows that pool a second dataset are
   reported as pooled and not tested for equality.
4. **Duplicate flag (F1).** A set is flagged if, in its primary source, two or
   more rarities have the same printed rate and margin as the same rarities of
   another set. The rule was written after the Paradox Rift / Paldea Evolved
   duplicate was noticed (see above); both sets are flagged, since the source
   does not say which table is right. C1–C3 and H4 across sets are also
   reported without flagged sets.
5. **Held-out predictive check (P1).** For every registry row that pools the
   TCGplayer dataset with a second dataset (the 16 rows of the homogeneity test
   plus the Journey Together rows pooled with a second dataset), the TCGplayer
   counts alone (reconstructed as in the homogeneity test) give a Jeffreys
   Beta posterior; its beta-binomial predictive distribution for the second
   dataset's number of packs is compared with the second dataset's hits.
   Report the two-sided mid-p predictive p-value, whether the hits fall in the
   central 95 % predictive interval, and the share of rows that do. Holm
   correction at family-wise level 0.05. The pooling of the main analysis is
   supported if no row is rejected.
6. **Reporting.** `research/reports/extension_sets.md` (C1–C3, b\*, H1–H4) and
   `research/reports/pull_rate_checks.md` (S1, F1, P1). Card prices stay
   private (ADR 0009); only derived statistics are committed.

## Consequences

- H4 across sets is tested on ten sets instead of three.
- The pull-rate inputs are traced back to their primary source and tested out
  of sample, not only for homogeneity.
- Sets released after 2025 (Mega Evolution series) stay out until their pack
  layout is documented; that would need a new ADR.
