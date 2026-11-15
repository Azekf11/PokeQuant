# Quality assurance (week S10)

State on 2026-11-15, branch `week/09-web`. Scope: the Python engine and the
static web demo of [ADR 0013](../../docs/decisions/0013-static-web-demo.md).
There is no backend, so the roadmap's API items (rate limiting, CORS, API
error handling) do not apply.

## 1. Automated checks (CI)

| Job | What it checks | Result |
|---|---|---|
| Lint, types, tests | ruff, ruff format, mypy (strict), pytest | 144 tests pass |
| Secret scan | gitleaks over the full git history | no finding |
| Web demo journey test | Playwright, system Chrome (`apps/web/tests/journey.spec.js`) | 3 tests pass |
| Dependency audit | `pip-audit` on the locked Python dependencies; `npm audit` on the test tooling | no known vulnerability |

**Journey test.** It follows the six steps of the demo:

1. it chooses a set;
2. it chooses the adverse scenario and checks the booster price;
3. it edits the costs and checks the gain, loss and missing-input messages;
4. it chooses a budget of 100 boosters and checks the table and chart;
5. it checks the two E2 targets;
6. it checks the hypotheses, the CSV download and the provenance.

It also checks three security properties:

- no console error;
- no request outside the local server;
- a Content-Security-Policy without `unsafe-inline`.

The same test checks that the page has no horizontal scroll at 375 px and
that the set picker works with the arrow keys.

**Dependency audit.** The npm audit first flagged `@playwright/test` 1.48.2,
which had a high-severity advisory (GHSA-7mvr-c777-76hp, browser download
without certificate check). The tooling was upgraded to 1.64.1, which
removed the finding. The demo itself ships no third-party code.

## 2. Security

| Item | Status |
|---|---|
| Secrets | None needed: the demo reads a static file. No key in the browser or in git (gitleaks). |
| Third-party code in the page | None. No CDN, font or analytics request. |
| Content-Security-Policy | `default-src 'self'`, `script-src 'self'`, no inline script or style attribute. The page sets it with a meta tag; the Compose demo also sends it as a header, with `frame-ancestors 'none'`, `nosniff` and `no-referrer`. |
| User input | Four numeric fields, clamped to fixed ranges; no input is sent anywhere. |
| Published data | Aggregates only. The export fails if it contains a printing identifier or a card-level key (ADR 0009, `pokequant_core.web.card_level_leaks`, tested). |
| Deployed files | GitHub Pages publishes only the page, its assets and its data, not the test tooling. The Compose demo returns 404 for `node_modules/`, `tests/` and `package*.json` (checked with curl). |

## 3. Reproducibility

- `make check` passes on a clean checkout.
- The web export is deterministic for a given run. `scripts/export_web.py`
  rewrites `apps/web/data/results.json`, and the break-even grid reproduces
  the run's break-even prices to within 1e-4 USD in every set and scenario
  (gross, central and adverse; tested on toy data in `tests/test_web.py`,
  checked on the main run).
- The demo shows the run identifier, seed and results checksum of the run it
  displays.

## 4. Performance

| File | Size |
|---|---|
| `index.html`, `style.css`, `app.js`, `icon.svg` | 38 KB in total |
| `data/results.js` | 196 KB (52 KB gzipped) |

There is no request after the page load. Charts are inline SVG and are
redrawn on resize.

## 5. Accessibility

Checks done:

- every chart has a table view;
- the charts' series have a legend and use the validated categorical colours
  (blue and orange), with text in ink colours;
- colour is never the only cue (verdicts are written out);
- pickers are ARIA radio groups that work with the keyboard;
- focus is visible;
- the light and dark themes have their own colour steps.

Not done: a screen-reader pass and an automated contrast audit (Lighthouse or
axe). These are listed as limits, not as passed checks.

## 6. Local demo

```bash
docker compose up        # http://localhost:8080
```

`compose.yaml` serves `apps/web/` read-only with nginx 1.27.2 (Alpine). This
was tested on Docker 29.6.2: the page and data return 200, and the test
tooling returns 404.
