.PHONY: install lint format typecheck test coverage check data reproduce paper web-test

install:  ## Create the environment and install git hooks
	uv sync
	uv run pre-commit install

lint:  ## Lint and check formatting
	uv run ruff check .
	uv run ruff format --check .

format:  ## Auto-fix lint issues and format
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

test:
	uv run pytest

coverage:  ## Line coverage of the package by the test suite
	uv run pytest --cov=pokequant_core --cov-report=term

check: lint typecheck test  ## Everything CI runs (except the secret scan)

# --- Analysis (frozen at tag analysis-v1) -------------------------------------
CONFIG := research/experiments/main.yaml
RUN := results/main-$(shell shasum -a 256 $(CONFIG) | cut -c1-8)-k200-m20000

data:  ## Processed tables from the committed pull rates and the local TCGdex cache
	uv run pokequant ingest --pokelife 2026-11-13 --tcgdex 2026-11-15 --sets sv07,sv08,sv10 --offline

reproduce: data  ## Every report, table and figure of the paper (about 3 h on 8 cores)
	uv run python scripts/validate_engine.py
	uv run python scripts/valuation_report.py
	uv run pokequant run $(CONFIG)
	uv run python scripts/results_report.py $(RUN)
	uv run pokequant robustness $(CONFIG)
	uv run python scripts/robustness_report.py $(RUN)
	uv run python scripts/paper_figures.py $(RUN)
	uv run python scripts/export_web.py $(RUN)
	uv run python scripts/build_paper.py

paper:  ## Working paper (Markdown, HTML and PDF; the PDF needs a local Chrome)
	uv run python scripts/build_paper.py --pdf

web-test:  ## Journey test of the web demo (needs Node and a local Chrome)
	cd apps/web && npm ci --no-audit --no-fund && npx playwright test
