# 0007 — Gate G2: price data

- Status: accepted
- Date: 2026-11-15
- Decided by: author, on the recommendation of the
  [data audit report §6](../../research/reports/data_audit.md#6-gate-g2--recommendation)

## Context

Gate G2 (end of S2) asks whether usable, legally reusable price data exists.
The audit found that pull rates (Poké Life, CC BY 4.0) and the catalogue
(TCGdex, MIT) are usable, and that prices exist for every relevant card
through TCGdex, but only as listing and provider-market types, with unclear
publication rights. No open source offers realised-sale prices. Prices are
first needed in S6.

## Decision

**Conditional GO.**

1. S3–S5 proceed: ingestion, booster model and Monte Carlo engine do not depend
   on prices.
2. The author asks TCGdex (primary, option P1) and PkmnPrices (secondary,
   option P2) whether derived statistics computed from their prices may be
   published, and under which attribution.
3. Until an answer allows it, price data is used **locally only**: raw prices
   are never committed and no figure based on them is published.
4. **Deadline: end of S5.** Without a favourable answer, S6 switches to option
   P4 — price scenarios plus a limited case study — and the paper makes no
   claim about observed market profitability.
5. Whatever the source, prices are labelled by type (listing / provider
   market), never presented as realised sales, and always combined with
   liquidity haircut scenarios.

## Consequences

- The research critical path is not blocked.
- The scope of the economic conclusions depends on the answers; the
  decision taken at the S5 deadline is recorded in a follow-up ADR.
