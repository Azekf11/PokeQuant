# Contributing

## Workflow

- `main` always passes CI and reflects validated work.
- **Small changes** (typo, doc fix, config tweak): commit directly on `main`.
- **Everything else**: one branch per roadmap week, `week/NN-topic`
  (e.g. `week/02-data-audit`), or `fix/...` / `feat/...` for unplanned work.
  Merge through a pull request once CI is green and the week's exit criterion
  ([roadmap](docs/ROADMAP.md)) is met.
- Ideas outside the current week go to a GitHub issue labelled `backlog`,
  not into code (anti-scope-creep rule).
- Any change of scope, data source, method or tooling gets an ADR in
  [`docs/decisions/`](docs/decisions/).

## Commits

[Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `data:` (new snapshot
or manifest), `research:` (protocol, experiments, paper).

## Before opening a PR

```bash
make check   # ruff lint + format check + mypy + pytest
```

- New code has tests; probabilistic code has property tests and, where
  possible, an analytic comparison.
- No secret, API key, non-redistributable dataset or unlicensed image is
  committed. Keys live in `.env` (see `.env.example`), never in git.
- Every price carries date, currency, condition and price type; every rate
  carries its sample size and interval. A missing value is never replaced by 0.

## Research integrity

- Pre-registered items (tags `prereg-v1`, `prereg-v2`) are not changed silently:
  a deviation is documented in an ADR and reported in the paper.
- Notebooks are for exploration only; official results come from versioned
  configs and scripts.
- Negative and inconclusive results are reported.
