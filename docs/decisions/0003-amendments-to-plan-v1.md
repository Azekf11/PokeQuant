# 0003 — Amendments to the v1.0 plan

- Status: accepted
- Date: 2026-11-14

## Context

The internal documents *Cahier des charges et plan de stage* and *Protocole
scientifique et plan du papier* (v1.0, 2 Nov 2026) define a 12-week plan. Their
scope, deliverables and decision gates are kept. A few process and method
points were under-specified.

## Decision

Adopt amendments A1–A10, detailed in [`ROADMAP.md` §2](../ROADMAP.md#2-amendments-to-the-v10-plan):

- A1 Week-0 bootstrap with CI and decision log.
- A2 Two-stage pre-registration via git tags `prereg-v1` (end S1) and `prereg-v2` (end S4).
- A3 Engine developed on synthetic data from S2, in parallel with the data audit.
- A4 Dirichlet posterior for multi-outcome slots; Beta only for binary rates.
- A5 Explicit nested Monte Carlo (epistemic outer / aleatory inner) with MC standard errors.
- A6 Paper sections drafted progressively (S3, S4, S5).
- A7 Analysis freeze tag `analysis-v1` at end of S8, before web work.
- A8 Publication route (Zenodo DOI, SSRN / arXiv preprint) decided in S1.
- A9 Literature read in full before any novelty claim.
- A10 One branch and PR per week, merged only when the exit criterion is met.

## Consequences

- The research critical path no longer depends on the web product.
- Pre-registration becomes verifiable (tag timestamps).
- The protocol's pull-rate posterior is corrected for multi-outcome slots.
