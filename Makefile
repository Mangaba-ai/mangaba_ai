.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
PYTHON     := uv run python
UV         := uv
PYTEST     := uv run pytest
RUFF       := uv run ruff
BLACK      := uv run black
ISORT      := uv run isort
MYPY       := uv run mypy
DOCKER_COMPOSE := docker compose

DOCKER_FILE_VECTORSTORES := docker-compose.vectorstores.yml

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-28s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
.PHONY: install install-dev install-all sync

install: ## Install base dependencies
	$(UV) sync

install-dev: ## Install base + dev dependencies
	$(UV) sync --extra dev

install-all: ## Install all optional dependencies + dev
	$(UV) sync --extra all --extra dev

sync: ## Sync lockfile without changing it
	$(UV) sync

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------
.PHONY: lint format check typecheck

lint: ## Run ruff linter with auto-fix
	$(RUFF) check . --fix

format: ## Run ruff formatter + isort
	$(RUFF) format .
	$(ISORT) .

check: ## Lint + format check (no writes, CI-safe)
	$(RUFF) check .
	$(RUFF) format . --check
	$(ISORT) . --check-only

typecheck: ## Run mypy type checking
	$(MYPY) mangaba/

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
.PHONY: test test-unit test-integration test-fast test-cov

test: ## Run full test suite with coverage
	$(PYTEST)

test-unit: ## Run only unit tests
	$(PYTEST) -m unit

test-integration: ## Run only integration tests
	$(PYTEST) -m integration

test-fast: ## Run tests without coverage (faster)
	$(PYTEST) --no-cov

test-cov: ## Run tests and open HTML coverage report
	$(PYTEST)
	open htmlcov/index.html

# ---------------------------------------------------------------------------
# Docker — vector stores
# ---------------------------------------------------------------------------
.PHONY: docker-up docker-down docker-logs docker-ps docker-reset

docker-up: ## Start Redis + Postgres vector store services
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE_VECTORSTORES) up -d

docker-down: ## Stop vector store services
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE_VECTORSTORES) down

docker-logs: ## Tail logs from vector store services
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE_VECTORSTORES) logs -f

docker-ps: ## Show running vector store containers
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE_VECTORSTORES) ps

docker-reset: ## Stop services and remove volumes (destructive)
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE_VECTORSTORES) down -v

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
.PHONY: env-setup env-validate

env-setup: ## Copy .env.example to .env (skips if .env exists)
	@test -f .env && echo ".env already exists, skipping." || cp .env.example .env

env-validate: ## Validate environment variables
	$(PYTHON) scripts/validate_env.py

# ---------------------------------------------------------------------------
# Build & publish
# ---------------------------------------------------------------------------
.PHONY: build clean

build: ## Build distribution packages
	$(UV) build

clean: ## Remove build artifacts and cache files
	rm -rf dist/ build/ *.egg-info htmlcov/ .coverage coverage.xml .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------
.PHONY: all ci

all: lint test ## Run lint + full test suite

ci: check test ## Run CI pipeline (check-only lint + tests)
