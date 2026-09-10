.DEFAULT_GOAL := help

.PHONY: help install dev-setup lint format typecheck security-check secrets-scan test test-cov test-fast pre-commit-install pre-commit-run verify tf-fmt tf-validate tf-security docker-build docker-up docker-down run-api run-worker review-cli dev clean

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

pre-commit-install:  ## Install git pre-commit, commit-msg, and pre-push hooks
	pre-commit install --install-hooks

pre-commit-run:  ## Run every pre-commit hook against all files
	pre-commit run --all-files

verify:  ## Run the full local gate - matches CI's Quality Gate
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) security-check
	$(MAKE) tf-fmt
	$(MAKE) tf-validate
	$(MAKE) test-cov
	@echo "All local quality gates passed."

tf-fmt:  ## Check Terraform formatting
	terraform fmt -check -recursive infrastructure/terraform/

tf-validate:  ## Validate every Terraform module and environment
	@set -e; \
	for d in $$(find infrastructure/terraform -name '*.tf' -exec dirname {} \; | sort -u); do \
		echo "validate $$d"; \
		(cd $$d && terraform init -backend=false -input=false >/dev/null && terraform validate); \
	done

tf-security:  ## Scan Terraform for misconfigurations (requires trivy)
	trivy config infrastructure/ --severity HIGH,CRITICAL

lint:  ## Run Ruff linter and formatter checks
	ruff check .
	ruff format --check .

format:  ## Format code automatically using Ruff
	ruff check --fix .
	ruff format .

typecheck:  ## Run static type checking across all modules
	mypy packages agents apps cli

security-check:  ## Run SAST (Bandit) and dependency audit (pip-audit)
	bandit -c pyproject.toml -r packages agents apps cli
	pip-audit --desc on --strict

secrets-scan:  ## Scan the working tree and history for committed secrets
	pre-commit run gitleaks --all-files

test:  ## Run pytest test suite
	pytest -v tests/

test-cov:  ## Run pytest with the coverage gate (identical to CI)
	# Scope and fail-under come from pyproject.toml so local and CI agree.
	pytest tests/

test-fast:  ## Run the test suite without the coverage gate
	pytest tests/ --no-cov -q

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
