.DEFAULT_GOAL := help

.PHONY: help install dev-setup lint format typecheck security-check test test-cov pre-commit-install docker-build docker-up docker-down run-api run-worker review-cli dev clean

help:  ## Display this help message
	@echo "EDGE Content Engine - SDLC Commands"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install production and development dependencies in editable mode
	pip install --upgrade pip
	pip install -e ".[dev]"

dev-setup: install pre-commit-install  ## Bootstrap full local development environment
	@echo "Copying environment file if missing..."
	@test -f .env || cp .env.example .env
	@echo "Development setup complete. Remember to populate API keys in .env"

pre-commit-install:  ## Install git pre-commit hooks
	pre-commit install --install-hooks

lint:  ## Run Ruff linter and formatter checks
	ruff check .
	ruff format --check .

format:  ## Format code automatically using Ruff
	ruff check --fix .
	ruff format .

typecheck:  ## Run static type checking across all modules
	mypy packages agents apps cli

security-check:  ## Run SAST security scanning (Bandit) and dependency audit (pip-audit)
	bandit -c pyproject.toml -r packages agents apps cli
	pip-audit --desc on

test:  ## Run pytest test suite
	pytest -v tests/

test-cov:  ## Run pytest with code coverage report and fail threshold
	pytest --cov=packages --cov=agents --cov=apps --cov=cli --cov-report=term-missing --cov-report=xml tests/

docker-build:  ## Build the production-ready multi-stage Docker container
	docker build -t edge-content-engine:latest .

docker-up:  ## Start the full local container stack via Docker Compose
	docker compose up --build -d

docker-down:  ## Stop the local container stack
	docker compose down

run-api:  ## Start the FastAPI review and webhook API locally
	uvicorn apps.api.main:app --reload --port 8000

run-worker:  ## Start the asynchronous background worker runner
	python -m apps.workers.runner

review-cli:  ## Launch the terminal interactive editorial review CLI
	python -m cli.main review

dev:  ## Run worker and API concurrently for local testing
	@echo "Starting local EDGE Content Engine..."
	python -m apps.workers.runner & uvicorn apps.api.main:app --reload --port 8000

clean:  ## Remove build, cache, test, and temporary artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage coverage.xml .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
