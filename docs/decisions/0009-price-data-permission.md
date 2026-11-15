# 0009: Price data permission (Gate G2 follow-up)

- Status: accepted
- Date: 2026-11-15
- Decided by: author
- Follows: [ADR 0007](0007-gate-g2-price-data.md) (conditional GO, deadline end of S5)

## Context

ADR 0007 made the use of prices conditional on an answer from TCGdex (option
P1) and PkmnPrices (option P2) about publishing statistics derived from their
prices. On 2026-11-15, before the deadline, the author reported that **both
providers authorised the use of their price data for this project**, on the
basis that it is a personal, non-commercial research project. The author
describes the permission as unrestricted.

What this record rests on:

- The answers were received by the author and are kept by the author; they
  are not reproduced in the repository (private correspondence).
- The channel and exact wording are not recorded here. If the paper or a
  reviewer requires it, the author can produce the written answers.

What the permission cannot cover: TCGdex and PkmnPrices relay prices that
originate from TCGplayer and Cardmarket (and, for PkmnPrices, eBay). Their own
terms on republication through aggregators were not read
(`data/manifests/sources.yaml`, open questions).

## Decision

1. **Gate G2 is resolved: option P1.** TCGdex prices, already ingested in S3,
   are the price source for S6. PkmnPrices is authorised as a secondary
   source; using it would require an adapter and is not planned.
2. **Derived statistics may be published**: distributions, quantiles, basket
   values, simulation results and figures computed from prices, each with the
   price date, currency, type and attribution.
3. **Raw prices stay out of the repository** for now, although the providers
   allow more: the upstream marketplaces' terms are unverified, and derived
   statistics are enough for the paper. Replication uses the ingestion
   scripts plus the checksums in each run's `manifest.json`. Publishing a
   frozen raw price snapshot would need a new ADR after checking those terms.
4. Unchanged from ADR 0007: prices are labelled by type (listing / provider
   market), never presented as realised sales, and always combined with
   liquidity-haircut scenarios. The paper is non-commercial, consistent with
   the basis of the permission.
5. Attribution used in the paper and in figures: "Price data: TCGdex
   (tcgdex.dev), relaying TCGplayer (USD) and Cardmarket (EUR) prices; used
   with permission." No specific wording was requested.

## Consequences

- S6 can value cards with observed provider prices instead of the P4
  fallback (price scenarios only); the paper may report observed results,
  within the limits of listing and provider-market prices.
- The set selection (ADR 0005) and the `prereg-v1` protocol were fixed before
  any price value was seen. A few raw price payloads were displayed during S3
  to check their format; no analysis has used price values so far.
- `sources.yaml`, the ingestion licence note and the paper's §3 now cite this
  ADR.
