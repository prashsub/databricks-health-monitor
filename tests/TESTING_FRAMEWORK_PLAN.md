# Databricks Health Monitor - Testing Framework Plan

## Executive Summary

This document outlines a comprehensive testing framework for the Databricks Health Monitor platform, enabling developers to validate code locally before deploying to Databricks. The framework follows industry best practices and Databricks-recommended patterns for testing notebooks and PySpark code.

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Testing Layers](#testing-layers)
3. [Codebase Analysis](#codebase-analysis)
4. [Framework Architecture](#framework-architecture)
5. [Mocking Strategy](#mocking-strategy)
6. [Test Categories](#test-categories)
7. [Implementation Roadmap](#implementation-roadmap)
8. [CI/CD Integration](#cicd-integration)
9. [Coverage Requirements](#coverage-requirements)

---

## Testing Philosophy

### Core Principles

1. **Local-First Development**: All tests should run locally without Databricks cluster access
2. **Fast Feedback Loops**: Unit tests should complete in seconds, not minutes
3. **Isolation**: Each test should be independent and not rely on external state
4. **Determinism**: Tests should produce consistent results across runs
5. **Production Parity**: Test data should mirror production structures without using real data

### Testing Pyramid

```
                    /\
                   /  \
                  / E2E \           (5%) - Databricks Integration
                 /------\
                / Integ. \          (15%) - Component + Spark Integration
               /----------\
              /    Unit    \        (80%) - Pure Python + Mocked Spark
             /--------------\
```

---

## Testing Layers

### Layer 1: Unit Tests (Local, No Spark)
- **Purpose**: Test individual functions and business logic
- **Scope**: Pure Python code, mocked Spark/Databricks dependencies
- **Speed**: < 100ms per test
- **Markers**: `@pytest.mark.unit`

### Layer 2: Component Tests (Local Spark)
- **Purpose**: Test PySpark transformations and DataFrame operations
- **Scope**: Multiple functions working together with local SparkSession
- **Speed**: < 5s per test
- **Markers**: `@pytest.mark.integration`

### Layer 3: Integration Tests (Databricks Connect)
- **Purpose**: Validate complete workflows against Databricks
- **Scope**: Full pipeline execution with ephemeral test schemas
- **Speed**: Variable (depends on cluster)
- **Markers**: `@pytest.mark.databricks`
- **Note**: Optional, requires Databricks connectivity

---

## Codebase Analysis

### Modules Requiring Testing

| Module | Files | Priority | Testing Approach |
|--------|-------|----------|------------------|
| `alerting/` | 11 | HIGH | Unit tests for templates, query validation |
| `pipelines/bronze/` | 10 | HIGH | Component tests with sample data |
| `pipelines/gold/` | 12 | HIGH | Component tests for merge operations |
| `ml/` | 50+ | HIGH | Unit tests for training, mock MLflow |
| `monitoring/` | 13 | MEDIUM | Unit tests for monitor configuration |
| `semantic/` | 6 | MEDIUM | SQL syntax validation |
| `dashboards/` | 4 | LOW | JSON structure validation |
| `genie/` | 3 | LOW | Configuration validation |

### Existing Test Coverage

Currently, the codebase has:
- 18 test files
- ~466 lines of test fixtures in `conftest.py`
- Coverage for: alerting, ML (partial), dashboards, TVFs, monitoring

### Gap Analysis

| Area | Current Coverage | Target | Gap |
|------|-----------------|--------|-----|
| Alert Templates | 80% | 90% | Query execution mocking |
| Pipeline Bronze | 10% | 80% | DLT streaming mocks |
| Pipeline Gold | 10% | 80% | MERGE operation tests |
| ML Models | 20% | 80% | Feature engineering, training |
| Monitoring | 30% | 70% | Monitor creation logic |
| Semantic Layer | 60% | 80% | Execution validation |

---

## Framework Architecture

### Directory Structure

```
tests/
├── TESTING_FRAMEWORK_PLAN.md     # This document
├── TESTING_ARCHITECTURE.md       # Detailed architecture
├── MOCKING_STRATEGY.md           # Mocking patterns guide
├── IMPLEMENTATION_PATTERNS.md    # Code patterns and examples
├── CI_CD_INTEGRATION.md          # Pipeline configuration
│
├── conftest.py                   # Shared fixtures (enhanced)
├── fixtures/                     # Additional fixture modules
│   ├── __init__.py
│   ├── spark_fixtures.py         # SparkSession, DataFrame helpers
│   ├── databricks_mocks.py       # dbutils, DLT, Unity Catalog mocks
│   ├── mlflow_mocks.py           # MLflow mocking utilities
│   ├── sample_data.py            # Factory functions for test data
│   └── assertion_helpers.py      # Custom assertion utilities
│
├── unit/                         # Pure unit tests (no Spark)
│   ├── __init__.py
│   ├── alerting/
│   ├── ml/
│   └── monitoring/
│
├── component/                    # Component tests (local Spark)
│   ├── __init__.py
│   ├── pipelines/
│   │   ├── bronze/
│   │   └── gold/
│   ├── ml/
│   └── semantic/
│
├── integration/                  # Databricks integration tests
│   ├── __init__.py
│   ├── conftest.py               # Databricks-specific fixtures
│   └── test_full_pipeline.py
│
├── alerting/                     # Existing tests (to be reorganized)
├── dashboards/
├── genie/
├── metric_views/
├── ml/
├── monitoring/
└── tvfs/
```

### Key Components

#### 1. Enhanced conftest.py
- Session-scoped SparkSession
- Mock dbutils with widget support
- Sample data factories
- DLT runtime mocks
- Unity Catalog mocks

#### 2. Fixture Modules
- `spark_fixtures.py`: DataFrame creation, schema validation
- `databricks_mocks.py`: Comprehensive Databricks SDK mocks
- `mlflow_mocks.py`: Experiment and model registry mocks
- `sample_data.py`: Realistic test data generators

#### 3. Assertion Helpers
- DataFrame equality comparison
- Schema validation
- Null/missing value checks
- Metric range validation

---

## Mocking Strategy

### Databricks Components to Mock

| Component | Mock Strategy | Complexity |
|-----------|--------------|------------|
| `dbutils` | Custom MockDbutils class | LOW |
| SparkSession | Local PySpark session | LOW |
| Unity Catalog | Mock catalog/schema resolution | MEDIUM |
| DLT | Custom DLT mock module | HIGH |
| MLflow | pytest-mock patches | MEDIUM |
| Databricks SDK | Mock API responses | MEDIUM |
| Lakehouse Monitor | Mock API client | MEDIUM |

### DLT Mocking Approach

```python
# Mock DLT decorators to return identity functions
class MockDLT:
    @staticmethod
    def table(name=None, **kwargs):
        def decorator(func):
            return func
        return decorator

    @staticmethod
    def view(name=None, **kwargs):
        def decorator(func):
            return func
        return decorator

    @staticmethod
    def read_stream(name):
        # Return mock DataFrame
        pass
```

### Unity Catalog Mocking

```python
class MockCatalog:
    def __init__(self):
        self._tables = {}
        self._schemas = {}

    def table(self, full_name):
        return self._tables.get(full_name)

    def setCurrentCatalog(self, catalog):
        pass

    def setCurrentDatabase(self, schema):
        pass
```

---

## Test Categories

### 1. Alert Framework Tests

**Scope**: Template rendering, query validation, alert creation

```python
@pytest.mark.unit
class TestAlertTemplates:
    def test_template_rendering(self)
    def test_parameter_validation(self)
    def test_query_syntax_validation(self)
    def test_alert_id_generation(self)

@pytest.mark.integration
class TestAlertExecution:
    def test_alert_query_runs(self, spark, sample_data)
    def test_threshold_detection(self)
```

### 2. Pipeline Tests

**Scope**: Bronze ingestion, Gold transformations, MERGE operations

```python
@pytest.mark.integration
class TestBronzeStreaming:
    def test_schema_inference(self)
    def test_deduplication(self)
    def test_incremental_load(self)

@pytest.mark.integration
class TestGoldMerge:
    def test_merge_new_records(self)
    def test_merge_updates(self)
    def test_merge_deduplication(self)
    def test_foreign_key_integrity(self)
```

### 3. ML Model Tests

**Scope**: Feature engineering, model training, predictions

```python
@pytest.mark.unit
class TestFeatureEngineering:
    def test_feature_columns_present(self)
    def test_feature_data_types(self)
    def test_no_infinite_values(self)

@pytest.mark.ml
class TestModelTraining:
    def test_model_trains_successfully(self)
    def test_predictions_valid(self)
    def test_mlflow_logging(self, mock_mlflow)
```

### 4. Monitoring Tests

**Scope**: Monitor configuration, metric aggregation

```python
@pytest.mark.unit
class TestMonitorConfig:
    def test_monitor_definition_valid(self)
    def test_metric_aggregation_logic(self)
    def test_threshold_evaluation(self)
```

### 5. Semantic Layer Tests

**Scope**: TVF syntax, metric view YAML, query execution

```python
@pytest.mark.unit
class TestTVFSyntax:
    def test_parameter_ordering(self)
    def test_no_date_type_parameters(self)
    def test_division_null_safety(self)

@pytest.mark.integration
class TestTVFExecution:
    def test_tvf_returns_expected_columns(self, spark)
    def test_tvf_handles_edge_cases(self)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Documentation + Core Fixtures)
- [ ] Create detailed architecture document
- [ ] Create mocking strategy guide
- [ ] Create implementation patterns document
- [ ] Enhanced conftest.py with all fixtures
- [ ] DLT mock module
- [ ] Unity Catalog mock module

### Phase 2: Unit Tests
- [ ] Alert framework unit tests
- [ ] ML feature validation tests
- [ ] Monitoring configuration tests
- [ ] Pipeline helper function tests

### Phase 3: Component Tests
- [ ] Bronze pipeline transformation tests
- [ ] Gold MERGE operation tests
- [ ] ML training pipeline tests
- [ ] Semantic layer execution tests

### Phase 4: Integration Support
- [ ] Databricks Connect configuration
- [ ] Ephemeral schema fixtures
- [ ] Full pipeline integration tests
- [ ] CI/CD pipeline configuration

---

## CI/CD Integration

### Local Development

```bash
# Run all unit tests (fast)
pytest -m unit -v

# Run with coverage
pytest -m unit --cov=src --cov-report=html

# Run specific module
pytest tests/alerting/ -v

# Run with parallel execution
pytest -m unit -n auto
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest -m unit --tb=short -q
        language: system
        pass_filenames: false
        always_run: true
```

### GitHub Actions / CI Pipeline

```yaml
# Example workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install .[dev]
      - name: Run unit tests
        run: pytest -m unit --cov=src
      - name: Run integration tests
        run: pytest -m integration
```

---

## Coverage Requirements

### Minimum Coverage Targets

| Category | Target | Rationale |
|----------|--------|-----------|
| Overall | 70% | Industry standard baseline |
| Alert Templates | 90% | Critical business logic |
| Pipeline Transforms | 80% | Core data processing |
| ML Training | 80% | Model quality assurance |
| Monitoring | 70% | Configuration validation |
| Semantic Layer | 70% | Query correctness |

### Excluded from Coverage

- `__init__.py` files
- CLI scripts and notebooks
- Third-party integrations
- Generated code

### Coverage Commands

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-fail-under=70

# View coverage by module
pytest --cov=src --cov-report=term-missing
```

---

## Appendix: References

### Databricks Testing Documentation
- [Unit Testing for Notebooks](https://docs.databricks.com/aws/en/notebooks/testing)
- [Testing Notebooks](https://docs.databricks.com/aws/en/notebooks/test-notebooks)
- [Integration Testing with pytest](https://community.databricks.com/t5/technical-blog/integration-testing-for-lakeflow-jobs-with-pytest-and-databricks/ba-p/141683)

### Tools and Libraries
- [pytest](https://docs.pytest.org/) - Testing framework
- [chispa](https://github.com/MrPowers/chispa) - PySpark testing utilities
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin
- [pytest-xdist](https://pytest-xdist.readthedocs.io/) - Parallel execution
- [databricks-labs-pytester](https://github.com/databrickslabs/pytester) - Databricks test fixtures

---

*Document Version: 1.0*
*Last Updated: 2026-01-01*
*Author: Data Engineering Team*
