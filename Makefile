.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## run all tests
	uv run pytest -v

lint: ## check code with ruff
	uv run ruff check .

format: ## format code with ruff
	uv run ruff format .

fix: ## format and fix code with ruff
	uv run ruff check --fix .
	uv run ruff format .

test-cov: ## run tests with coverage
	uv run pytest --cov=getpaid_elavon --cov-report=html --cov-report=term -v
