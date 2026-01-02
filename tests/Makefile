# =============================================================================
# Databricks Health Monitor - Test Makefile
# =============================================================================
#
# Usage:
#   make help          - Show available commands
#   make test          - Run all tests (excluding slow)
#   make test-unit     - Run unit tests only (fast)
#   make test-integration - Run integration tests (requires Spark)
#   make coverage      - Run tests with coverage report
#
# =============================================================================

.PHONY: all test test-unit test-integration test-ml test-alerting test-pipelines \
        test-all coverage lint format clean help install

# Default target
help:
	@echo "=============================================="
	@echo "Databricks Health Monitor - Test Commands"
	@echo "=============================================="
	@echo ""
	@echo "Test Commands:"
	@echo "  make test              - Run all tests (excluding slow)"
	@echo "  make test-unit         - Run unit tests only (fast, no Spark)"
	@echo "  make test-integration  - Run integration tests (requires Spark)"
	@echo "  make test-ml           - Run ML model tests"
	@echo "  make test-alerting     - Run alerting module tests"
	@echo "  make test-pipelines    - Run pipeline tests"
	@echo "  make test-all          - Run ALL tests including slow"
	@echo ""
	@echo "Coverage Commands:"
	@echo "  make coverage          - Run tests with HTML coverage report"
	@echo "  make coverage-xml      - Run tests with XML coverage (for CI)"
	@echo "  make coverage-check    - Run coverage and fail if below threshold"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              - Run linters (ruff, mypy)"
	@echo "  make format            - Format code with black"
	@echo "  make check             - Run all checks (lint + test-unit)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean             - Remove test artifacts"
	@echo "  make install           - Install dev dependencies"
	@echo "  make watch             - Run tests on file changes"
	@echo ""

# =============================================================================
# CONFIGURATION
# =============================================================================

PYTHON := python
PYTEST := $(PYTHON) -m pytest
SRC_DIR := ../src
TEST_DIR := .
COVERAGE_THRESHOLD := 70

# Pytest common options
PYTEST_OPTS := -v --tb=short -ra

# =============================================================================
# INSTALLATION
# =============================================================================

install:
	@echo "Installing dev dependencies..."
	pip install -e "..[dev]"

# =============================================================================
# TEST COMMANDS
# =============================================================================

# Run all tests (excluding slow)
test:
	$(PYTEST) $(PYTEST_OPTS) -m "not slow"

# Run unit tests only (fast, no Spark required)
test-unit:
	$(PYTEST) $(PYTEST_OPTS) -m unit --ignore=tests/integration

# Run integration tests (requires Spark)
test-integration:
	$(PYTEST) $(PYTEST_OPTS) -m integration

# Run ML model tests
test-ml:
	$(PYTEST) $(PYTEST_OPTS) -m ml tests/ml/

# Run alerting tests
test-alerting:
	$(PYTEST) $(PYTEST_OPTS) tests/alerting/

# Run pipeline tests
test-pipelines:
	$(PYTEST) $(PYTEST_OPTS) tests/pipelines/

# Run dashboard tests
test-dashboards:
	$(PYTEST) $(PYTEST_OPTS) tests/dashboards/

# Run TVF tests
test-tvfs:
	$(PYTEST) $(PYTEST_OPTS) tests/tvfs/

# Run monitoring tests
test-monitoring:
	$(PYTEST) $(PYTEST_OPTS) tests/monitoring/

# Run ALL tests including slow
test-all:
	$(PYTEST) $(PYTEST_OPTS)

# Run tests in parallel
test-parallel:
	$(PYTEST) $(PYTEST_OPTS) -n auto -m "not slow"

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test.py"; \
		exit 1; \
	fi
	$(PYTEST) $(PYTEST_OPTS) $(FILE)

# Run tests matching pattern
test-match:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-match PATTERN='test_something'"; \
		exit 1; \
	fi
	$(PYTEST) $(PYTEST_OPTS) -k "$(PATTERN)"

# =============================================================================
# COVERAGE COMMANDS
# =============================================================================

# Run with HTML coverage report
coverage:
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing \
		-m "not slow" $(PYTEST_OPTS)
	@echo ""
	@echo "Coverage report generated: htmlcov/index.html"

# Run with XML coverage (for CI)
coverage-xml:
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=xml --cov-report=term-missing \
		-m "not slow" $(PYTEST_OPTS)

# Run coverage and fail if below threshold
coverage-check:
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing \
		--cov-fail-under=$(COVERAGE_THRESHOLD) -m "not slow" $(PYTEST_OPTS)

# Generate coverage badge (requires coverage-badge)
coverage-badge:
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=xml -m unit -q
	coverage-badge -o coverage.svg

# =============================================================================
# CODE QUALITY
# =============================================================================

# Run linters
lint:
	@echo "Running ruff..."
	ruff check $(SRC_DIR)
	@echo "Running mypy..."
	mypy $(SRC_DIR) --ignore-missing-imports

# Format code
format:
	@echo "Formatting with black..."
	black $(SRC_DIR) $(TEST_DIR)
	@echo "Sorting imports with ruff..."
	ruff check --fix --select I $(SRC_DIR) $(TEST_DIR)

# Check formatting without modifying
format-check:
	black --check $(SRC_DIR) $(TEST_DIR)
	ruff check --select I $(SRC_DIR) $(TEST_DIR)

# Run all checks
check: lint test-unit

# =============================================================================
# UTILITIES
# =============================================================================

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	rm -rf __pycache__ .pytest_cache htmlcov .coverage coverage.xml
	rm -rf .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage*" -delete 2>/dev/null || true
	@echo "Done."

# Watch mode - run tests on file changes (requires pytest-watch)
watch:
	ptw --runner "pytest -m unit -q --tb=short"

# Debug mode - stop on first failure and enter debugger
debug:
	$(PYTEST) -x --pdb -m unit

# Run last failed tests
rerun:
	$(PYTEST) --lf $(PYTEST_OPTS)

# Show test durations (slowest tests)
slow-tests:
	$(PYTEST) --durations=20 -m "not slow" -q

# Generate JUnit XML for CI
junit:
	$(PYTEST) --junitxml=test-results.xml -m "not slow" -q

# =============================================================================
# CI/CD TARGETS
# =============================================================================

# Full CI run
ci: lint coverage-check
	@echo "CI checks passed!"

# Pre-commit checks
pre-commit: format-check lint test-unit
	@echo "Pre-commit checks passed!"
