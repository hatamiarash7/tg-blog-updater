.PHONY: clean install dev lock run build test lint format check docker-build help
.DEFAULT_GOAL := help

PYTHON_FILES := tg_blog_updater tests

clean: ## Remove build and test caches
	rm -rf dist .pytest_cache .mypy_cache

install: ## Install runtime dependencies
	poetry install --only main

dev: ## Install runtime, dev, and test dependencies
	poetry install --with dev,test

lock: ## Refresh poetry.lock without upgrading versions
	poetry lock

run: ## Run the bot
	poetry run python -m tg_blog_updater

build: clean ## Build a wheel and sdist
	poetry build

test: ## Run tests
	poetry run pytest

format: ## Format Python files with black and isort
	poetry run black $(PYTHON_FILES)
	poetry run isort $(PYTHON_FILES)

lint: ## Check formatting, flake8, and pylint
	poetry run black --check $(PYTHON_FILES)
	poetry run isort --check-only $(PYTHON_FILES)
	poetry run flake8 $(PYTHON_FILES)
	poetry run pylint $(PYTHON_FILES) --rcfile=.pylintrc

check: lint test ## Lint and test

docker-build: ## Build a local image
	docker build --tag tg-blog-updater:local .

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
