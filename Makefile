.PHONY: clean install dev lock run build test lint help
.DEFAULT_GOAL := help

clean: ## Clean build files
	rm -rf dist

install: ## Install dependencies
	poetry install

dev: ## Install dependencies - dev env
	poetry install --with=dev,test

lock: ## Update poetry.lock
	poetry lock

run: ## Run project
	poetry run python -m tg_blog_updater

build: clean ## Build package
	poetry build

test: ## Run tests
	poetry run pytest

lint: ## Lint files
	find . -name "*.py" -not -ipath "./.venv/*" | xargs python3 -m pylint --rcfile=.pylintrc --ignore-patterns=test_.*?py

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'