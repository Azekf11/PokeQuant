# Project charter

Condensed from the internal scoping document (*Cahier des charges*, v1.0,
2 Nov 2026). This file is the reference for scope decisions; any substantial
change goes through an ADR in [`decisions/`](decisions/).

**Steering rule:** build a reproducible, honest tool before an ambitious
product. Scientific scope comes before attractive features.

## Positioning

PokéQuant is an independent research / fan project with **no affiliation** with
The Pokémon Company, Nintendo, Creatures or Game Freak. Pokémon names, logos and
card images belong to their owners; the Pokémon logo is never used as project
branding. The project publishes experimental analyses, **not financial advice**.

## Research question

To what extent is opening Pokémon TCG boosters an economically competitive
acquisition strategy compared with buying cards directly on the secondary
market, once pull-rate uncertainty, value dispersion, fees and liquidity are
taken into account?

Sub-questions, hypotheses and metrics: see
[`research/protocol/protocol.md`](../research/protocol/protocol.md).

## In scope (MVP)

- Catalogue of cards and sets for **1–3 sets**, chosen after a data audit.
- Published pull rates from a documented source, with sample size, interval,
  date and confidence level.
- Slot-based booster model when the structure is documented. Cards are never
  assumed equiprobable.
- Reproducible Monte Carlo engine (seed, exportable parameters, tests).
- Valuation from dated, **typed** price snapshots (listing, provider market,
  sold, estimate).
- Opening vs direct-purchase comparator with fees and liquidity scenarios.
- Simple web interface, methodology documentation, CSV/JSON export, public repo.

## Out of scope (MVP) — red lines

- Computer vision predicting PSA 10 from a photo.
- 6- or 12-month price prediction without sufficient history and temporal validation.
- Marketplace scraping or circumventing API restrictions — **forbidden**.
- All languages, all sets, all variants, all graders.
- Personalised buy/sell recommendations or return promises.
- Blockchain, tokens, user accounts, payments, real portfolios, social features.

**Anti-scope-creep rule:** a new feature must answer a research question,
improve the reliability of a measurement, or remove friction directly tied to
the MVP. Otherwise it goes to the backlog.

## Units of analysis

- **Primary:** one simulated opening of a defined sealed product (booster type,
  set, slot configuration).
- **Secondary:** one card printing identified by set, number, variant, language
  and condition. Two printings are never merged under an ambiguous identifier.

## Data policy

- Every observation carries source, URL, UTC timestamp, version, currency,
  language, condition/grade and collection method.
- No price without a date. No rate without a sample size or confidence level.
- No scraping behind login, CAPTCHA or technical protection; no quota, token or
  geo-restriction circumvention.
- Access right ≠ redistribution right. If redistribution is ambiguous, store
  only identifiers and links to the source.
- The site shows a warning when a source is old, poorly documented or not comparable.

## MVP acceptance criteria

- Same data + parameters + seed ⇒ same results.
- Displayed rates always show provenance, number of observations and interval when available.
- A missing value is never silently replaced by zero.
- Listed prices, aggregated prices and realised sales are clearly distinguished.
- Transaction costs are visible and editable; gross and net results are separate.
- Every chart shows its collection date and dataset scope.
- Data limitations are visible without opening the technical docs.
- No API key in the browser or in git.

## Supervisor rules — re-read every week

1. No new feature until the current milestone is validated.
2. No chart without a definition of the variable and its source.
3. No price without date, currency, condition and price type.
4. No probability without model, sample and uncertainty.
5. No conclusion without baseline and sensitivity analysis.
6. No scraping, no circumvention of terms of use.
7. No deep learning for show.
8. No paper that turns exploratory results into certainties.
9. If the data cannot answer the question, shrink the question — never fabricate data.
10. Reproducibility matters as much as model performance.
