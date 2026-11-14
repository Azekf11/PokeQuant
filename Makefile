.PHONY: install lint format typecheck test check

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
