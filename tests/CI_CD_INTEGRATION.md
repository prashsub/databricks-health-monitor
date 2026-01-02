# CI/CD Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the testing framework with CI/CD pipelines, including GitHub Actions, Azure DevOps, and Databricks Workflows.

---

## Table of Contents

1. [Local Development Workflow](#local-development-workflow)
2. [Pre-commit Hooks](#pre-commit-hooks)
3. [GitHub Actions](#github-actions)
4. [Azure DevOps](#azure-devops)
5. [Databricks Integration Tests](#databricks-integration-tests)
6. [Coverage Requirements](#coverage-requirements)
7. [Test Reports](#test-reports)

---

## Local Development Workflow

### Installation

```bash
# Install project with dev dependencies
pip install -e ".[dev]"

# Or using uv
uv sync --extra dev
```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest -m unit

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/alerting/test_alert_templates.py

# Run specific test class
pytest tests/alerting/test_alert_templates.py::TestAlertTemplates

# Run specific test
pytest tests/alerting/test_alert_templates.py::TestAlertTemplates::test_templates_exist

# Run with coverage
pytest --cov=src --cov-report=html

# Run tests in parallel
pytest -n auto

# Run slow tests separately
pytest -m slow --timeout=300
```

### Makefile Commands

Create a `tests/Makefile` for common operations:

```makefile
# tests/Makefile

.PHONY: test test-unit test-integration test-ml test-all coverage lint clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-ml       - Run ML model tests"
	@echo "  make test-all      - Run all tests including slow"
	@echo "  make coverage      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make clean         - Clean test artifacts"

# Run all tests (excluding slow)
test:
	pytest -m "not slow" -v

# Run unit tests only (fast)
test-unit:
	pytest -m unit -v --tb=short

# Run integration tests
test-integration:
	pytest -m integration -v

# Run ML tests
test-ml:
	pytest -m ml -v

# Run all tests including slow
test-all:
	pytest -v

# Run with coverage
coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=70
	@echo "Coverage report: htmlcov/index.html"

# Run linters
lint:
	ruff check ../src
	black --check ../src
	mypy ../src

# Clean artifacts
clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Format code
format:
	black ../src ../tests
	ruff check --fix ../src ../tests
```

### Test Run Script

Create `tests/run_tests.py` for programmatic test execution:

```python
#!/usr/bin/env python3
"""
Test Runner Script
==================

Provides programmatic access to test execution with various configurations.

Usage:
    python tests/run_tests.py --unit
    python tests/run_tests.py --integration
    python tests/run_tests.py --coverage
    python tests/run_tests.py --module alerting
"""

import argparse
import sys
import subprocess
from pathlib import Path


def run_tests(args):
    """Run tests with specified configuration."""
    cmd = ["pytest"]

    # Add markers
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.ml:
        cmd.extend(["-m", "ml"])

    # Add specific module
    if args.module:
        module_path = Path(__file__).parent / args.module
        if module_path.exists():
            cmd.append(str(module_path))
        else:
            print(f"Error: Module path not found: {module_path}")
            return 1

    # Add coverage
    if args.coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
        ])
        if args.fail_under:
            cmd.append(f"--cov-fail-under={args.fail_under}")

    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])

    # Add JUnit output for CI
    if args.junit:
        cmd.extend(["--junitxml=test-results.xml"])

    # Print command
    if args.dry_run:
        print(" ".join(cmd))
        return 0

    # Execute
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main():
    parser = argparse.ArgumentParser(description="Run tests")

    # Test type selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unit", action="store_true", help="Run unit tests only")
    group.add_argument("--integration", action="store_true", help="Run integration tests")
    group.add_argument("--ml", action="store_true", help="Run ML model tests")

    # Options
    parser.add_argument("--module", "-m", help="Run tests for specific module")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage")
    parser.add_argument("--fail-under", type=int, default=70, help="Coverage threshold")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run in parallel")
    parser.add_argument("--junit", action="store_true", help="Generate JUnit XML")
    parser.add_argument("--dry-run", action="store_true", help="Print command only")

    args = parser.parse_args()
    sys.exit(run_tests(args))


if __name__ == "__main__":
    main()
```

---

## Pre-commit Hooks

### Configuration

Create `.pre-commit-config.yaml` in project root:

```yaml
# .pre-commit-config.yaml

repos:
  # Code formatting
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.10

  # Linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix]

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML]
        args: [--ignore-missing-imports]

  # Unit tests (fast only)
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest -m unit -q --tb=short
        language: system
        pass_filenames: false
        always_run: true
        stages: [push]  # Only on push, not every commit

  # YAML validation
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
        args: [--unsafe]  # Allow custom YAML tags
      - id: check-json
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
        args: [--maxkb=1000]
```

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

---

## GitHub Actions

### Main Test Workflow

Create `.github/workflows/tests.yml`:

```yaml
# .github/workflows/tests.yml

name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.10"

jobs:
  # Quick unit tests
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run unit tests
        run: pytest -m unit -v --junitxml=test-results-unit.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-unit
          path: test-results-unit.xml

  # Integration tests with Spark
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests  # Only run if unit tests pass
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Set up Java (for Spark)
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '11'

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run integration tests
        run: pytest -m integration -v --junitxml=test-results-integration.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-integration
          path: test-results-integration.xml

  # Coverage report
  coverage:
    name: Coverage
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-report=html --cov-fail-under=70

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Upload coverage HTML report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/

  # Publish test summary
  test-summary:
    name: Test Summary
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    if: always()
    steps:
      - name: Download unit test results
        uses: actions/download-artifact@v4
        with:
          name: test-results-unit

      - name: Download integration test results
        uses: actions/download-artifact@v4
        with:
          name: test-results-integration

      - name: Publish Test Results
        uses: EnricoMi/publish-unit-test-result-action@v2
        with:
          files: |
            test-results-unit.xml
            test-results-integration.xml
```

### ML Model Tests Workflow

Create `.github/workflows/ml-tests.yml`:

```yaml
# .github/workflows/ml-tests.yml

name: ML Model Tests

on:
  push:
    branches: [main]
    paths:
      - 'src/ml/**'
      - 'tests/ml/**'
  pull_request:
    paths:
      - 'src/ml/**'
      - 'tests/ml/**'

jobs:
  ml-tests:
    name: ML Model Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run ML tests
        run: pytest -m ml -v --junitxml=test-results-ml.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-ml
          path: test-results-ml.xml
```

---

## Azure DevOps

### Pipeline Configuration

Create `azure-pipelines.yml`:

```yaml
# azure-pipelines.yml

trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - src/**
      - tests/**

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.10'

stages:
  - stage: Test
    displayName: 'Run Tests'
    jobs:
      - job: UnitTests
        displayName: 'Unit Tests'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'
            displayName: 'Use Python $(pythonVersion)'

          - script: |
              python -m pip install --upgrade pip
              pip install -e ".[dev]"
            displayName: 'Install dependencies'

          - script: |
              pytest -m unit -v --junitxml=test-results-unit.xml
            displayName: 'Run unit tests'

          - task: PublishTestResults@2
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: 'test-results-unit.xml'
              testRunTitle: 'Unit Tests'
            condition: always()

      - job: IntegrationTests
        displayName: 'Integration Tests'
        dependsOn: UnitTests
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - task: JavaToolInstaller@0
            inputs:
              versionSpec: '11'
              jdkArchitectureOption: 'x64'
              jdkSourceOption: 'PreInstalled'

          - script: |
              pip install -e ".[dev]"
            displayName: 'Install dependencies'

          - script: |
              pytest -m integration -v --junitxml=test-results-integration.xml
            displayName: 'Run integration tests'

          - task: PublishTestResults@2
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: 'test-results-integration.xml'
              testRunTitle: 'Integration Tests'
            condition: always()

      - job: Coverage
        displayName: 'Code Coverage'
        dependsOn:
          - UnitTests
          - IntegrationTests
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - task: JavaToolInstaller@0
            inputs:
              versionSpec: '11'
              jdkArchitectureOption: 'x64'

          - script: |
              pip install -e ".[dev]"
            displayName: 'Install dependencies'

          - script: |
              pytest --cov=src --cov-report=xml --cov-fail-under=70
            displayName: 'Run coverage'

          - task: PublishCodeCoverageResults@1
            inputs:
              codeCoverageTool: 'Cobertura'
              summaryFileLocation: 'coverage.xml'
```

---

## Databricks Integration Tests

### Using Databricks Connect

For full integration tests against Databricks:

```python
"""tests/integration/conftest.py"""

import pytest
import os
from databricks.connect import DatabricksSession


@pytest.fixture(scope="session")
def databricks_spark():
    """
    Create Databricks Connect session for integration tests.

    Requires environment variables:
    - DATABRICKS_HOST
    - DATABRICKS_TOKEN (or DATABRICKS_CLUSTER_ID)
    """
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    cluster_id = os.environ.get("DATABRICKS_CLUSTER_ID")

    if not host:
        pytest.skip("DATABRICKS_HOST not set")

    spark = DatabricksSession.builder.remote(
        host=host,
        token=token,
        cluster_id=cluster_id,
    ).getOrCreate()

    yield spark

    spark.stop()


@pytest.fixture
def ephemeral_schema(databricks_spark):
    """
    Create ephemeral schema for test isolation.

    Schema is automatically cleaned up after tests.
    """
    import uuid
    schema_name = f"test_schema_{uuid.uuid4().hex[:8]}"
    catalog = os.environ.get("TEST_CATALOG", "main")

    databricks_spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema_name}")

    yield f"{catalog}.{schema_name}"

    # Cleanup
    databricks_spark.sql(f"DROP SCHEMA IF EXISTS {catalog}.{schema_name} CASCADE")
```

### Integration Test Example

```python
"""tests/integration/test_full_pipeline.py"""

import pytest


@pytest.mark.databricks
class TestFullPipeline:
    """Full pipeline integration tests on Databricks."""

    def test_bronze_to_gold_flow(self, databricks_spark, ephemeral_schema):
        """Test complete Bronze to Gold data flow."""
        # Create test data in ephemeral schema
        databricks_spark.sql(f"""
            CREATE TABLE {ephemeral_schema}.test_bronze AS
            SELECT 1 as id, 'test' as value
        """)

        # Run transformation
        # ... your pipeline code ...

        # Verify output
        result = databricks_spark.sql(f"""
            SELECT * FROM {ephemeral_schema}.test_gold
        """)

        assert result.count() > 0
```

### GitHub Actions for Databricks Tests

```yaml
# .github/workflows/databricks-integration.yml

name: Databricks Integration Tests

on:
  workflow_dispatch:  # Manual trigger
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  integration:
    name: Databricks Integration
    runs-on: ubuntu-latest
    environment: databricks-test
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install databricks-connect

      - name: Run Databricks integration tests
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
          DATABRICKS_CLUSTER_ID: ${{ secrets.DATABRICKS_CLUSTER_ID }}
          TEST_CATALOG: ${{ vars.TEST_CATALOG }}
        run: |
          pytest -m databricks -v --junitxml=test-results-databricks.xml
```

---

## Coverage Requirements

### Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/.venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
show_missing = true
fail_under = 70

[tool.coverage.html]
directory = "htmlcov"
```

### Module-Level Coverage Targets

```python
# tests/coverage_config.py

# Define coverage targets per module
COVERAGE_TARGETS = {
    "alerting": 90,
    "pipelines": 80,
    "ml": 80,
    "monitoring": 70,
    "semantic": 70,
    "dashboards": 60,
}

def check_coverage_targets(coverage_data):
    """Check if coverage meets module-level targets."""
    failures = []
    for module, target in COVERAGE_TARGETS.items():
        actual = coverage_data.get(module, 0)
        if actual < target:
            failures.append(f"{module}: {actual}% < {target}%")
    return failures
```

---

## Test Reports

### JUnit XML Reports

Generated automatically with `--junitxml` flag:

```xml
<!-- test-results.xml -->
<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="42">
    <testcase classname="tests.alerting.test_alert_templates.TestAlertTemplates"
              name="test_templates_exist" time="0.003"/>
    <!-- ... -->
</testsuite>
```

### HTML Coverage Reports

Access at `htmlcov/index.html` after running:

```bash
pytest --cov=src --cov-report=html
```

### Custom Test Reporter

```python
# tests/reporter.py

"""Custom test reporter for CI/CD integration."""

import json
from datetime import datetime
from pathlib import Path


class TestReporter:
    """Generate custom test reports."""

    def __init__(self, output_dir: Path = Path("test-reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def generate_summary(self, junit_file: Path) -> dict:
        """Parse JUnit XML and generate summary."""
        import xml.etree.ElementTree as ET

        tree = ET.parse(junit_file)
        root = tree.getroot()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total": int(root.get("tests", 0)),
            "passed": 0,
            "failed": int(root.get("failures", 0)),
            "errors": int(root.get("errors", 0)),
            "skipped": int(root.get("skipped", 0)),
            "duration": float(root.get("time", 0)),
            "failures": [],
        }

        summary["passed"] = summary["total"] - summary["failed"] - summary["errors"] - summary["skipped"]

        for testcase in root.findall(".//testcase"):
            failure = testcase.find("failure")
            if failure is not None:
                summary["failures"].append({
                    "test": f"{testcase.get('classname')}.{testcase.get('name')}",
                    "message": failure.get("message", ""),
                })

        return summary

    def write_markdown_report(self, summary: dict, output_file: Path):
        """Write Markdown test report."""
        status = "PASSED" if summary["failed"] == 0 else "FAILED"

        content = f"""# Test Results

**Status**: {status}
**Timestamp**: {summary['timestamp']}

## Summary

| Metric | Count |
|--------|-------|
| Total Tests | {summary['total']} |
| Passed | {summary['passed']} |
| Failed | {summary['failed']} |
| Errors | {summary['errors']} |
| Skipped | {summary['skipped']} |
| Duration | {summary['duration']:.2f}s |

"""

        if summary["failures"]:
            content += "## Failures\n\n"
            for failure in summary["failures"]:
                content += f"- **{failure['test']}**: {failure['message']}\n"

        output_file.write_text(content)

    def write_json_report(self, summary: dict, output_file: Path):
        """Write JSON test report."""
        output_file.write_text(json.dumps(summary, indent=2))
```

---

## Quick Reference Commands

```bash
# Local Development
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m ml                # ML tests
pytest --cov=src            # With coverage
pytest -n auto              # Parallel execution

# Pre-commit
pre-commit run --all-files  # Run all hooks
pre-commit install          # Install hooks

# CI/CD
pytest --junitxml=results.xml  # JUnit output
pytest --cov-report=xml        # Cobertura coverage

# Debugging
pytest -v --tb=long         # Verbose with full traceback
pytest -x                   # Stop on first failure
pytest --pdb                # Debug on failure
pytest --lf                 # Run last failed tests
```

---

*Document Version: 1.0*
*Last Updated: 2026-01-01*
