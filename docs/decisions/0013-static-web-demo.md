# 0013: Static web demo instead of a live API

- Status: accepted
- Date: 2026-11-15
- Decided by: author
- Refines: roadmap week S9 (FastAPI + React) and the MVP scope of the
  [project charter](../PROJECT_CHARTER.md)

## Context

The roadmap plans a FastAPI backend and a React + TypeScript + Plotly front
end for S9, with a fallback: "static site reading precomputed results (no live
backend)". Two facts favour the fallback.

1. **Price rights.** ADR 0009 allows derived statistics to be published, but
   not raw prices. A live `simulate` or `compare` endpoint needs every card's
   price on a public server. A user could then recover single-card prices by
   choosing narrow inputs.
2. **Time and surface.** The paper is the deliverable. A static site has no
   server, no quota to enforce and no secret to keep. It can be hosted free on
   GitHub Pages. S10 has far less to secure.

The charter asks for costs that are "visible and editable". Risk metrics need
a full simulation, but the break-even booster price does not. For given costs,
it is a sum over the cards of a set: b*(k, F) = E[Σ max(0, k·p(c) − F)], with
k = (1 − haircut)(1 − fee rates) and F the fixed cost per card sold. A grid of
this function is a derived statistic, because every cell sums over all the
cards of a set.

## Decision

1. S9 ships the fallback: a static site in `apps/web/` (HTML, CSS and
   JavaScript, no build step and no third-party script). It reads one file,
   `apps/web/data/results.json`, written by `scripts/export_web.py` from a run
   of the main experiment.
2. The export holds only aggregates:
   - comparison rows (metric means, 95 % intervals and verdicts);
   - break-even prices;
   - E2 targets, named by rarity only;
   - hypothesis statuses;
   - a break-even grid over k ∈ [0.30, 1.00] (step 0.025) and
     F ∈ [0, 6] USD (step 0.10), per set, with its 95 % interval over the
     posterior draws.

   The export fails if it contains a printing identifier or a card-level key
   (`pokequant_core.web.card_level_leaks`).
3. The site follows the six steps of the user journey:
   1. set;
   2. cost scenario;
   3. break-even price, with editable costs;
   4. budget (E1);
   5. target card (E2);
   6. hypotheses, limits, downloads and provenance.

   The price date, price type, currency and the "not financial advice"
   notice stay visible at the top of the page.
4. Only the break-even price reacts to edited costs. Risk metrics stay those
   of the three pre-registered scenarios, and the page says so.
5. No FastAPI service is built for v1. A live API remains possible later, if
   a source grants redistribution of raw prices. It would then go to the
   backlog.

## Consequences

- The site can be deployed by GitHub Pages from `apps/web/`. The data is
  also written as `data/results.js`, which the page loads as a script, so
  no request is made at run time.
- The roadmap's S10 security items shrink:
  - rate limiting and CORS do not apply (there is no backend);
  - a strict Content-Security-Policy and the absence of third-party scripts
    replace them;
  - the dependency audit and secret scan still apply.
- The demo stays consistent with the paper: it shows the numbers of the
  frozen run, and regenerating the run regenerates the demo.
