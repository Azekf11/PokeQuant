# PokéQuant — Roadmap (12 weeks + week 0)

This roadmap follows the 12-week plan of the internal scoping document
(*Cahier des charges et plan de stage*, v1.0, 2 Nov 2026) and the research
protocol (*Protocole scientifique et plan du papier*, v1.0, 2 Nov 2026).
It keeps their order, deliverables and decision gates, and adds the amendments
listed in [§2](#2-amendments-to-the-v10-plan). Amendments are also recorded in
[ADR 0003](decisions/0003-amendments-to-plan-v1.md).

**Final goal:** a reproducible working paper — *Opening or Buying? A
Probabilistic and Risk-Adjusted Comparison of Pokémon TCG Booster Acquisition
and Secondary-Market Purchases* — backed by a public Python engine and a minimal
web demo.

**Golden rule:** if time runs short, cut the number of sets and the web
features. Never cut validation, pre-registration or robustness steps.

---

## 1. Calendar

Dates are indicative; the plan is tracked by week number. Weeks 6–7 overlap the
end-of-year holidays — if they are taken off, every following week shifts by
the same amount.

| Week | Dates (2026–27) | Theme | Track | Gate / tag |
|---|---|---|---|---|
| S0 | 14–15 Nov | Repository bootstrap | infra | — |
| S1 | 16–22 Nov | Scoping, literature, source register | research | tag `prereg-v1` |
| S2 | 23–29 Nov | Data audit (+ engine skeleton on toy data) | research + core | **Gate G2** |
| S3 | 30 Nov–6 Dec | Data schema, canonical IDs, ingestion | core | — |
| S4 | 7–13 Dec | Probabilistic booster model, rate estimation | core + research | **Gate G4**, tag `prereg-v2` |
| S5 | 14–20 Dec | Monte Carlo engine, analytic validation | core | — |
| S6 | 21–27 Dec | Valuation, fees, net realisable price | core | — |
| S7 | 28 Dec–3 Jan | Strategy comparator, risk metrics | core + research | **Gate G7** |
| S8 | 4–10 Jan | Sensitivity, uncertainty, robustness | research | **Gate G8**, tag `analysis-v1` |
| S9 | 11–17 Jan | API + minimal web interface | product | — |
| S10 | 18–24 Jan | QA, security, performance, docs | product | **Gate G10**, tag `v1.0.0-rc1` |
| S11 | 25–31 Jan | Working paper, figures, reproducibility | research | — |
| S12 | 1–7 Feb | Critical review, release, publication | all | tag `v1.0.0` |

Critical path for the paper: **S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → S11 → S12**.
S9–S10 (product) never feed the paper; they consume its frozen engine.

---

## 2. Amendments to the v1.0 plan

| # | Change | Why |
|---|---|---|
| A1 | **Week 0 bootstrap**: CI (lint, types, tests, secret scan), conventions, decision log from day one. | The Definition of Done (§8.4) is cheaper to satisfy continuously than at the end. |
| A2 | **Two-stage pre-registration** as git tags: `prereg-v1` (end S1: question, hypotheses, metrics, sign conventions) and `prereg-v2` (end S4: sets, product, budgets, baskets, central and adverse scenarios, robustness list) — before any price-based result exists. Optional mirror on OSF. | The protocol requires hypotheses and scenarios to be fixed *before* analysis (§1.3, §7.1) but never says when or how. A signed tag is a verifiable timestamp. |
| A3 | **Engine on synthetic data from S2**, in parallel with the data audit. | Decouples engine risk from data risk, and produces the redistributable toy dataset that tests need (protocol §10). |
| A4 | **Dirichlet posterior for multi-outcome slots**; Beta only for binary hit / no-hit rates. | Independent Betas per rarity do not sum to 1 within a slot. With Jeffreys prior, a slot with k mutually exclusive outcomes gets Dirichlet(x₁+½,…,x_k+½). When registry rates are *per-pack hit rates* (outcomes not mutually exclusive), they are modelled per pack, not per slot. |
| A5 | **Explicit nested Monte Carlo**: outer loop = K draws of parameters (epistemic), inner loop = M simulated packs (aleatory). Every reported metric carries a Monte Carlo standard error; tail metrics require enough tail samples (e.g. N ≥ 10⁵ for CVaR 5 %). | Makes the aleatory / epistemic split of protocol §4.3 operational and auditable. |
| A6 | **Paper written progressively**: §3 Data drafted in S3, §4 Methodology in S5, §5 Experimental design at `prereg-v2`. S11 becomes assembly + results + discussion. | Writing everything in S11 is the most common cause of slippage and of methods sections that drift from the code. |
| A7 | **Analysis freeze** (`analysis-v1`) at the end of S8, before web work. `make reproduce` regenerates every figure and table from frozen configs. | Prevents results from changing while the product is being built. |
| A8 | **Publication route decided early**: GitHub release + Zenodo DOI, preprint on SSRN and/or arXiv (q-fin.GN or stat.AP). The arXiv endorsement requirement is checked in S1. A JOSS software paper is a possible later step (eligibility to verify). | Endorsement and review lead times are outside our control. |
| A9 | **Literature first**: the two references flagged in the protocol (Princeton thesis 2026 on Pokémon TCG market dynamics; SSRN paper on hedonic valuation of graded cards) are located and read in full in S1, before any novelty claim is written. | Protocol §2: they are leads to verify, not proof of novelty. |
| A10 | **Weekly branch + PR**, merged only when the week's exit criterion is met. | Makes "no new feature until the current milestone is validated" (supervisor rule 1) mechanical. |

---

## 3. Week-by-week plan

Each week has a branch (`week/NN-topic`), a GitHub milestone, a deliverable that
lives in the repository, and an exit criterion. A week is closed by merging its
PR into `main`.

### S0 — Repository bootstrap *(done in this commit)*
- [x] Repository layout, `pyproject.toml` (uv), MIT licence, `CITATION.cff`.
- [x] CI: ruff, mypy, pytest, gitleaks. Pre-commit hooks.
- [x] Project charter, roadmap, decision log, contribution rules.
- [x] Draft protocol transcribed from the internal v1.0 documents.

**Exit:** `make check` passes locally and in CI.

### S1 — Scoping, literature, source register · branch `week/01-scoping`
- [x] Locate the Princeton (2026) thesis and the SSRN hedonic-pricing paper; 40 verified references across the six axes → `research/paper/references.bib`, notes in `research/protocol/literature_review.md`.
- [ ] Read in full the closest papers (Mota 2026, Baro 2026, Sharma 2026, Danz 2026 — restricted) — *author action, see scoping note §3*.
- [x] Write a provisional novelty statement relative to existing calculators and papers.
- [x] Source register `data/manifests/sources.yaml`: for each source — URL, access method, key/quota, licence or ToS, redistribution right (yes / no / unclear), price types offered, date checked.
- [x] Re-check the ToS of Poké Life (CC BY 4.0), Pokémon TCG API, TCGdex, PkmnPrices, TCGdb, TCGplayer, Cardmarket, eBay.
- [x] Finalise `research/protocol/protocol.md` v1: question, Q1–Q5, H1–H4 with decision rules, estimands E1/E2, metric definitions **with sign conventions**, variables.
- [x] Check the publication route → [ADR 0004](decisions/0004-publication-route.md).
- [ ] Author review of protocol v1, then tag `prereg-v1`.

**Deliverable:** protocol v1, source register, bibliography, [scoping note](../research/protocol/scoping_note.md).
**S1 finding that matters for G2:** no price source is redistributable without written permission; options P1–P4 are listed in the scoping note.
**Exit:** question, hypotheses, scope and variables frozen → tag `prereg-v1`.

### S2 — Data audit · branch `week/02-data-audit`
- [ ] Snapshot the Poké Life registry into `data/raw/pokelife/<YYYY-MM-DD>/` with SHA-256 checksums and attribution (CC BY 4.0 allows redistribution with attribution — confirm, then allow-list it in `.gitignore`).
- [ ] Compare Pokémon TCG API and TCGdex for coverage of candidate sets → ADR choosing the catalogue source.
- [ ] Inventory freely accessible price data: which price *types* (listing / provider market / sold / window median), currencies, conditions, dates, display and publication rights.
- [ ] Coverage matrix per candidate set: pull-rate sample size N, slot documentation, % of cards priced, price type → select 1–3 sets by a rule written *before* looking at prices → ADR.
- [ ] *(parallel, A3)* `pokequant_core.model`: `Slot`, `BoosterModel` types + a synthetic toy set in `tests/fixtures/`.

**Deliverable:** `research/reports/data_audit.md` + versioned sample.
**Exit:** every field has a source, a date and a licence/condition.
**Gate G2:** if usable, legally reusable price data is insufficient → switch to a simulation study plus a limited case study. Never invent data.

### S3 — Data schema and ingestion · branch `week/03-ingestion`
- [ ] Pydantic models for `Set`, `CardPrinting`, `PullRateObservation`, `BoosterModel`, `PriceObservation`, `CostScenario`, `SimulationRun` (+ liquidity fields from protocol §3.2).
- [ ] Canonical `printing_id` scheme (set, number, variant, language) → ADR. Two printings are never merged under an ambiguous ID.
- [ ] Provider adapters behind one interface (httpx, on-disk cache, timeouts, retries with backoff); keys only from environment variables.
- [ ] Raw snapshots are immutable; transformations write Parquet to `data/processed/`; DuckDB views for analysis.
- [ ] Validation: duplicates, missing values (**never silently 0**), wrong types, inconsistent currencies, invalid dates, unavailable source — each with a test.
- [ ] CLI: `pokequant ingest <source> --snapshot <date>`.
- [ ] *(A6)* Draft paper §3 Data.

**Deliverable:** schema + ingestion pipeline.
**Exit:** imports are idempotent (two runs → identical output hash); duplicates and invalid values are detected.

### S4 — Probabilistic booster model · branch `week/04-booster-model`
- [ ] `research/protocol/model_spec.md`: slots, P(R_s = r), P(C = c | R_s = r, s, set), exclusivity / replacement / guaranteed-card rules; every unknown rule is a named, parameterised scenario.
- [ ] Rate estimation: Beta / Dirichlet posteriors with Jeffreys prior (A4); cases x = 0, x = n; reconstructed counts flagged and down-weighted; heterogeneity test across datasets (χ² or hierarchical check).
- [ ] Analytic functions: P(c in slot), P(hit c) under slot independence, P(≥1 hit in n packs), expected packs to hit (geometric).
- [ ] Property tests (hypothesis): probabilities ≥ 0, each slot sums to 1, integer card counts, no negative values.
- [ ] Experiment configs `research/experiments/*.yaml`: sets, product, budgets, **baskets defined ex ante**, central and adverse scenarios, robustness list.

**Deliverable:** model spec + tested estimation module.
**Exit:** slot structure documented; rates coherent → tag `prereg-v2`.
**Gate G4:** if the booster structure is not documented → model only observable slots and present unknowns as scenarios. Never fabricate an exact distribution.

### S5 — Monte Carlo engine and validation · branch `week/05-monte-carlo`
- [ ] Vectorised NumPy engine; `numpy.random.Generator(PCG64)` seeded through `SeedSequence`; nested loops (A5).
- [ ] Every run writes a `SimulationRun` manifest: seed, N, model version, data snapshot IDs, parameters, timestamp.
- [ ] Validation: one-slot two-card toy case vs exact mean/variance; simulated frequencies vs theory; hit counts vs binomial; error decay ∝ 1/√N for N = 10³…10⁶; reproducibility (same seed + data + model ⇒ identical output).
- [ ] `research/reports/validation.md` and its figures generated by a script.
- [ ] *(A6)* Draft paper §4 Methodology.

**Deliverable:** engine + validation report.
**Exit:** simulation converges to theoretical results on toy cases.

### S6 — Valuation and costs · branch `week/06-valuation`
- [ ] Typed prices: `listing`, `provider_market`, `sold`, `window_median`. Types are never mixed without an explicit rule; enforced by types and tests.
- [ ] Card value V(c, t): price type, time window, condition; documented policy for missing prices (excluded or scenario, never 0) and for low-value bulk (lot value, or 0 in the prudent scenario).
- [ ] `CostScenario`: seller fees, payment fees, shipping/insurance, taxes; liquidity scenarios (fast sale, slow sale, haircut) clearly labelled as assumptions.
- [ ] Dated price snapshots. Hedonic regression only if the data has enough observations and variation — otherwise document why not.

**Deliverable:** valuation model v1 + dated snapshots.
**Exit:** no confusion between listed price and realised sale anywhere in code or outputs.

### S7 — Strategy comparator and risk metrics · branch `week/07-comparator`
- [ ] Strategy A (open n = ⌊B / b⌋ boosters) and Strategy B (pre-registered target or basket). Strategy C (grading) excluded from main results.
- [ ] Metrics with MC standard errors: net EV, median, P(loss), quantiles 5/25/75/95 %, VaR 5 %, CVaR 5 %, break-even booster price, P(target hit), expected packs to hit.
- [ ] Runner: `pokequant run research/experiments/<config>.yaml` → `results/<run_id>/` (JSON + CSV + manifest) — this is also export F06.

**Deliverable:** reproducible comparison report.
**Exit:** results exportable; assumptions editable in config only.
**Gate G7:** if credible net prices cannot be integrated → no profitability conclusion is published.

### S8 — Robustness and sensitivity · branch `week/08-robustness`
- [ ] The seven robustness tests of protocol §7.2, plus prior sensitivity (Jeffreys vs uniform) and CI-bound scenarios.
- [ ] Tornado plot and Table 4; multi-set comparison if data allows.
- [ ] `research/reports/robustness.md`.
- [ ] `make reproduce` regenerates every paper figure and table from the configs.
- [ ] Ask 1–2 external readers now for a review in S11.

**Deliverable:** robustness report.
**Exit:** every conclusion comes with intervals and limits.
**Gate G8:** GO / NO-GO on the publishability criteria (protocol §11) → tag `analysis-v1` (analysis freeze).

### S9 — API and minimal web · branch `week/09-web`
- [ ] `apps/api/` FastAPI: sets, pull rates, simulate (bounded N), compare, export; OpenAPI contract.
- [ ] `apps/web/` React + TypeScript + Plotly: the six steps of the minimal user journey; provenance, dates, uncertainty and limitation banners always visible.
- [ ] Fallback if late: static site reading precomputed results (no live backend).

**Deliverable:** documented API + web prototype.
**Exit:** full MVP user journey works end to end.

### S10 — QA, security, documentation · branch `week/10-qa`
- [ ] Playwright journey test; API tests (validation, limits, errors, no secret leakage).
- [ ] Rate limiting, CORS, input bounds, dependency audit, secret scanning.
- [ ] Docker Compose for a local demo; README screenshots.
- [ ] `research/reports/qa.md`.

**Deliverable:** release candidate `v1.0.0-rc1`.
**Exit:** no secret in client; quotas; errors handled.
**Gate G10:** if security, licences or reproducibility are not satisfactory → delay public release.

### S11 — Working paper · branch `week/11-paper`
- [ ] Assemble the manuscript in `research/paper/` following protocol §8; figures Fig. 1–7 and Tables 1–4 from `make reproduce` only.
- [ ] Results, robustness, discussion (incl. negative / inconclusive results), conclusion, abstract, appendix.
- [ ] External review.

**Deliverable:** preprint v0 + reproducible repository.
**Exit:** every figure regenerates from the repository.

### S12 — Review, release, publication · branch `week/12-release`
- [ ] Address review; write answers to the ten defence questions (protocol §14) in `docs/FAQ.md`.
- [ ] Tag `v1.0.0`, Zenodo DOI, update `CITATION.cff`.
- [ ] Deploy site; 5–8 min presentation and demo video.
- [ ] Submit preprint.

**Exit:** publication checklist validated.

---

## 4. Weekly routine

- **Monday:** re-read the supervisor rules in the [project charter](PROJECT_CHARTER.md); open the week's branch and milestone.
- **During the week:** any scope change → ADR in `docs/decisions/`. New ideas → GitHub issue labelled `backlog`, not code.
- **End of week:** check the exit criterion, open the PR, merge only if CI is green and the criterion is met.
