# 0001: Repository layout and tooling

- Status: accepted
- Date: 2026-11-14

## Context

The scoping document (§5.1–5.2) proposes a monorepo with `apps/`, `packages/`,
`data/`, `research/`, `notebooks/`, `tests/`, `docs/`, `scripts/`, and warns
against creating a folder for every idea.

## Decision

- Follow the proposed layout, but **create a folder only when the week that
  needs it starts** (`apps/` in S9, `notebooks/` and `scripts/` when first used).
- Python ≥ 3.11, dependencies managed with **uv** (`pyproject.toml` + `uv.lock`
  committed). Build backend: hatchling. The importable package is
  `pokequant_core`, located at `packages/pokequant_core/`.
- Dependencies are added in the week that first uses them, not up front.
- Quality: ruff (lint + format), mypy (strict on the package), pytest
  (+ hypothesis for property tests). Pre-commit runs the same tools.
- CI: GitHub Actions: lint, format check, types, tests, gitleaks secret scan.
- Research reports go to `research/reports/` (data audit, validation,
  robustness, QA), which the v1.0 layout did not name explicitly.

## Consequences

- One command runs every check: `make check`.
- The layout stays small and every folder has a reason to exist.
