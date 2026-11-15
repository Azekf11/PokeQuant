# 0014: Sale-price benchmark and weekly price panel (prereg-v3)

- Status: accepted
- Date: 2026-11-15
- Decided by: author
- Extends: protocol §5 and §7.0b (`prereg-v1`), [ADR 0009](0009-price-data-permission.md),
  [ADR 0011](0011-operational-comparison-rules.md), [ADR 0012](0012-operational-robustness-tests.md)
- Parameters: [research/experiments/sales_benchmark.yaml](../../research/experiments/sales_benchmark.yaml)

## Context

The main analysis (`analysis-v1`) values cards at the TCGplayer market price,
a provider aggregate, on one date. The paper lists two limits that follow from
this (§8.5): the price is not an observed sale, and the conclusions are tested
at one date only. The Gate G2 audit (ADR 0007) found no open source of
realised-sale prices.

A second search on 2026-11-15, after `analysis-v1`, found the following:

- Cardmarket's API documentation (API 2.0, *Price Guide*, read 2026-11-15)
  defines AVG1, AVG7 and AVG30 as "the average sale price over the last day /
  7 days / 30 days". The endpoint is marked deprecated "as this feature was
  made generally available via the website".
- Cardmarket publishes that price guide as a public daily JSON file for
  Pokémon (`price_guide_6.json`: 80,854 entries, `createdAt`
  2026-11-15T02:47:59+01:00) together with a product list
  (`products_singles_6.json`).
- TCGdex already relays these Cardmarket fields (`avg1`, `avg7`, `avg30`,
  `trend`, `low`, with `-holo` variants). They are in the 2026-11-15 snapshot
  and are typed `provider_market` by the ingestion (ADR 0008 handles the
  `-holo` variants).
- Rejected: PkmnPrices eBay sold data (paid plan only; no budget), and
  automated collection of eBay or TCGplayer sale pages (their terms forbid
  it).

The 30-day average sale price is therefore the best free sale-based price we
have. It is a venue aggregate with unknown sample size and unspecified
condition, on the European market and in EUR. It is not a per-sale record.

**What was seen before this record.** While checking formats, the Cardmarket
fields of one Common card (sv08-040) and one unrelated entry of the official
file were displayed. No Cardmarket value of the three sets has been
summarised or analysed.

## Decision

This is an **exploratory extension** pre-registered under the tag
`prereg-v3`. It changes nothing in `analysis-v1`, and its results are
reported in a separate section of the paper (version 2).

1. **Sale-based price.** Cardmarket `avg30` (EUR) of each printing, as relayed
   by TCGdex, with the variant mapping of the main ingestion. It is called
   "30-day average sale price" in reports and is never presented as a single
   transaction.
2. **Currency.** EUR amounts are converted to USD with the ECB euro reference
   rate (USD per EUR, series `EXR.D.USD.EUR.SP00.A`) of the last published day
   on or before the snapshot date. The rate and its date are reported.
3. **Q1: conclusions under sale-based values.** For each set and snapshot, the
   break-even booster price b\* is computed exactly in each of the 200
   posterior draws of the main experiment (same seed, prior and layout):
   b\* = Σ over printings of P(printing in a pack) × ℓ(printing). Mean profit
   for n boosters is n (b\* − b), so b\* decides C1 and C2 of §7:
   - C1′ holds if the upper 97.5 % bound of the central b\* is below 4.49 USD;
   - C2′ holds if the upper 97.5 % bound of the gross b\* is below 4.49 USD.

   Cost scenarios and the missing-price rule (central: pool median) are those
   of the main experiment. A set whose hit printings have fewer than 80 %
   `avg30` coverage is reported as not evaluable for that snapshot.
4. **Q2: price-type gap.** Over the hit printings (Double Rare and above,
   ACE SPEC included) with both prices observed:
   - cross-venue ratio r = avg30 (in USD) / TCGplayer market;
   - within-venue ratio r_cm = avg30 / Cardmarket trend (both EUR).

   Report n, the median, the quartiles and a bootstrap 95 % interval of the
   median (10,000 resamples, seed 20261115), by set. Groups with fewer than 5
   printings are not reported (rule of the valuation report). The implied
   haircut 1 − median(r) is compared with the scenario haircuts (0.15, 0.27,
   0.30). This comparison is descriptive: r mixes two markets and two price
   types.
5. **Q3: weekly panel.** Snapshots on Sundays from 2026-11-15 to 2027-01-10
   (nine dates, 2026-12-13 included). At each date, Q1 is computed with both
   price bases (TCGplayer market and avg30 in USD). The date part of H4
   (protocol §7.0b) is evaluated on this panel: H4 is supported across dates
   if C1′ or C2′ changes between two dates for a set and a price basis. A
   missed date stays missing and is never filled.
6. **V1: relay check.** At each panel date, the TCGdex-relayed `avg30` is
   compared with Cardmarket's official file for the same day, matched on
   `idProduct`. Report the share of matched printings equal within 0.01 EUR.
   A share below 95 % is flagged in the report. Because TCGdex updates once a
   day, the two files may be a day apart.
7. **Publication.** Only derived statistics are committed: b\* quantiles,
   coverage, ratio quantiles, the exchange rate and the check share. Raw
   prices and the Cardmarket files stay local, as in ADR 0009. The terms of
   use of Cardmarket's public files were not read. They are used for the
   relay check only.
8. **Automation.** A scheduled GitHub Actions workflow takes each weekly
   snapshot and commits the derived panel rows under the author's identity.

## Consequences

- The paper can test its two main price limits with real sale-based data at
  no cost, while keeping the main analysis untouched.
- The sale-based price is a European venue average. A difference from the
  main results may come from the market, the price type or both. Q2 reports
  this mix and does not separate it.
- b\* answers C1 and C2 exactly. C3, buying versus opening at equal budget,
  needs the full simulation and is outside this extension.
