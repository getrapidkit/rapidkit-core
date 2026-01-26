# RapidKit Community Makefile
.PHONY: help \
	install install-dev install-pre-commit install-all install-tools \
	dev-setup check-hooks verify-env commit-check \
	test test-cov test-all test-community test-cov-community lint format clean build pre-commit-all \
	module-integrity

# ===============================
# HELP
# ===============================
help: ## Show available commands
	@echo "RapidKit Community Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ===============================
# DEPENDENCIES
# ===============================
install: ## Install runtime dependencies
	poetry install --no-dev

install-dev: ## Install all development dependencies
	poetry install

install-pre-commit: ## Install pre-commit hooks
	poetry run pre-commit install
	poetry run pre-commit install --hook-type commit-msg

install-all: install-dev install-pre-commit ## Install dev deps + hooks

install-tools: ## Install optional tooling (ruff, hadolint, shellcheck, ...)
	./scripts/setup-dev-environment.sh

# ===============================
# QUICK SETUP
# ===============================
dev-setup: install-all install-tools format lint test check-hooks ## Prepare a full dev env
	@echo "Community environment ready."
	@echo ""
	@echo "Common commands:"
	@echo "  make test           - Run community suite"
	@echo "  make test-cov       - Run community suite with coverage (>=60%)"
	@echo "  make test-all       - Run full pytest (maintainers only)"

# ===============================
# QUALITY CHECKS
# ===============================
check-hooks: ## Verify pre-commit hooks exist
	@if [ -x .git/hooks/pre-commit ] && [ -x .git/hooks/commit-msg ]; then \
		echo "Pre-commit hooks are installed"; \
	else \
		echo "Hooks missing. Run 'make install-pre-commit'"; \
		exit 1; \
	fi

verify-env: ## Verify core tooling
	@echo "Inspecting toolchain..."
	@command -v python >/dev/null 2>&1 && python --version || echo "Python not found"
	@command -v poetry >/dev/null 2>&1 && poetry --version || echo "Poetry not found"
	@command -v pre-commit >/dev/null 2>&1 && pre-commit --version || echo "pre-commit not found"

commit-check: ## Sample commit message validation
	poetry run python scripts/check_commit_message.py "feat: add user authentication"
	poetry run python scripts/check_commit_message.py "fix: resolve memory leak"
	-poetry run python scripts/check_commit_message.py "Fixed bug"
	-poetry run python scripts/check_commit_message.py "Fix Docker issues"

# ===============================
# TESTING
# ===============================
POETRY ?= poetry

test: ## Run community pytest suite (no coverage)
	$(POETRY) run pytest $(ARGS) tests

test-cov: ## Run community pytest suite with coverage gate (>=60%)
	$(POETRY) run pytest --cov=src --cov-config=pyproject.toml --cov-report=term --cov-report=xml:coverage-community.xml --cov-fail-under=60 $(ARGS) tests

test-all: ## Run full pytest suite (maintainers only)
	$(POETRY) run pytest $(ARGS)

test-community: ## Alias for community suite without coverage
	@$(MAKE) test ARGS="$(ARGS)"

test-cov-community: ## Alias for community suite with coverage gate (>=60%)
	@$(MAKE) test-cov ARGS="$(ARGS)"

module-integrity: ## Validate settings module structure & smoke tests
	poetry run python scripts/check_module_integrity.py

# ===============================
# LINT & FORMAT
# ===============================
lint: ## Run ruff + mypy
	poetry run ruff check src tests
	poetry run mypy src

format: ## Run black + autofix with ruff
	poetry run black src tests
	poetry run ruff check --fix src tests

# ===============================
# CLEAN
# ===============================
clean: ## Remove build & cache artifacts
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/ .mypy_cache/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ===============================
# BUILD & RELEASE
# ===============================
build: ## Build package artifacts
	poetry build

# ===============================
# PRE-COMMIT HELPERS
# ===============================
pre-commit-all: ## Run all pre-commit checks
	poetry run pre-commit run --all-files
