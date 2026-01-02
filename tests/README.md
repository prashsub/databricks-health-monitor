# Databricks Health Monitor - Testing Framework

A comprehensive testing framework for validating Databricks notebooks and PySpark code locally before deployment.

## Quick Start

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all unit tests (fast, no Spark)
make test-unit

# Run all tests with Spark
make test

# Run with coverage
make coverage
```

## Documentation

| Document | Description |
|----------|-------------|
| [TESTING_FRAMEWORK_PLAN.md](TESTING_FRAMEWORK_PLAN.md) | Master plan and roadmap |
| [TESTING_ARCHITECTURE.md](TESTING_ARCHITECTURE.md) | Technical architecture details |
| [MOCKING_STRATEGY.md](MOCKING_STRATEGY.md) | Databricks component mocking patterns |
| [IMPLEMENTATION_PATTERNS.md](IMPLEMENTATION_PATTERNS.md) | Code examples and templates |
| [CI_CD_INTEGRATION.md](CI_CD_INTEGRATION.md) | CI/CD pipeline configuration |

## Directory Structure

```
tests/
├── TESTING_FRAMEWORK_PLAN.md   # Master planning document
├── TESTING_ARCHITECTURE.md     # Architecture design
├── MOCKING_STRATEGY.md         # Mocking patterns
├── IMPLEMENTATION_PATTERNS.md  # Code examples
├── CI_CD_INTEGRATION.md        # CI/CD guide
├── README.md                   # This file
├── Makefile                    # Test commands
├── run_tests.py                # Python test runner
├── conftest.py                 # Shared pytest fixtures
│
├── fixtures/                   # Reusable test fixtures
│   ├── __init__.py
│   ├── spark_fixtures.py       # SparkSession management
│   ├── databricks_mocks.py     # dbutils, Unity Catalog mocks
│   ├── sample_data.py          # Test data factories
│   └── assertion_helpers.py    # Custom assertions
│
├── alerting/                   # Alert framework tests
├── dashboards/                 # Dashboard JSON tests
├── genie/                      # Genie space tests
├── metric_views/               # Metric view tests
├── ml/                         # ML model tests
├── monitoring/                 # Lakehouse monitoring tests
├── pipelines/                  # Pipeline tests
└── tvfs/                       # TVF syntax tests
```

## Test Categories

| Marker | Description | Command |
|--------|-------------|---------|
| `unit` | Pure Python, no Spark | `pytest -m unit` |
| `integration` | Requires local Spark | `pytest -m integration` |
| `ml` | ML model tests | `pytest -m ml` |
| `slow` | Long-running tests | `pytest -m slow` |
| `tvf` | TVF validation | `pytest -m tvf` |

## Common Commands

```bash
# Using Makefile
make test-unit          # Fast unit tests
make test-integration   # Spark integration tests
make test-ml            # ML model tests
make coverage           # HTML coverage report
make lint               # Run linters
make check              # Lint + unit tests

# Using Python script
python tests/run_tests.py --unit
python tests/run_tests.py --coverage
python tests/run_tests.py --module alerting
python tests/run_tests.py --parallel

# Using pytest directly
pytest -m unit -v
pytest tests/alerting/ -v
pytest -k "test_cost" -v
pytest --cov=src --cov-report=html
```

## Key Fixtures

### Spark Session
```python
def test_with_spark(spark):
    df = spark.createDataFrame([{"id": 1}])
    assert df.count() == 1
```

### Mock dbutils
```python
def test_widget_access(mock_dbutils, patch_dbutils):
    value = dbutils.widgets.get("catalog")
    assert value == "test_catalog"
```

### Sample Data
```python
def test_with_data(spark, sample_usage_data):
    assert sample_usage_data.count() > 0
```

### MLflow Mock
```python
def test_model_training(mock_mlflow, sample_cost_features):
    # Train model
    train_model(sample_cost_features)

    # Verify logging
    mock_mlflow.assert_param_logged("model_type")
```

## Coverage Requirements

| Module | Target |
|--------|--------|
| Overall | 70% |
| Alerting | 90% |
| Pipelines | 80% |
| ML | 80% |
| Monitoring | 70% |

## Running in CI

```yaml
# GitHub Actions
- name: Run tests
  run: pytest -m "not slow" --junitxml=results.xml

# With coverage
- name: Run coverage
  run: pytest --cov=src --cov-fail-under=70
```

## Troubleshooting

### PySpark not found
```bash
pip install pyspark>=3.5.0
```

### Java not installed (required for Spark)
```bash
# macOS
brew install openjdk@11

# Ubuntu
sudo apt-get install openjdk-11-jdk
```

### Slow test discovery
```bash
# Run only unit tests (no Spark initialization)
pytest -m unit --collect-only
```
