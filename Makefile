.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

test: ## run all tests
	pytest -v

lint: ## format code with black and isort
	black .
	isort .

test-cov: ## run tests with coverage
	pytest --cov=getpaid_elavon --cov-report=html --cov-report=term -v

coverage: ## check code coverage
	coverage run --source getpaid_elavon runtests.py tests
	coverage report -m
	coverage html
