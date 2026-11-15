.PHONY: install lint format typecheck test check data reproduce

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
