# Testing Architecture Design Document

## Overview

This document provides detailed technical specifications for the Databricks Health Monitor testing framework architecture. It covers the design decisions, component interactions, and implementation patterns that enable comprehensive local testing of Databricks notebooks and PySpark code.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Component Architecture](#component-architecture)
3. [Fixture System](#fixture-system)
4. [Mock Component Design](#mock-component-design)
5. [Test Data Management](#test-data-management)
6. [Execution Model](#execution-model)
7. [Performance Considerations](#performance-considerations)

---

## Design Principles

### 1. Dependency Inversion

Production code should depend on abstractions (interfaces), not concrete Databricks implementations. This allows tests to inject mock implementations.

```python
# Production code pattern
def process_data(spark, catalog_client=None):
    if catalog_client is None:
        catalog_client = DatabricksCatalogClient()  # Default to real
    return catalog_client.read_table("my_table")

# Test can inject mock
def test_process_data(spark, mock_catalog):
    result = process_data(spark, catalog_client=mock_catalog)
```

### 2. Test Isolation

Each test should:
- Create its own test data
- Not depend on external state
- Clean up after itself
- Be runnable in any order

### 3. Environment Parity

Local test environment should mirror Databricks runtime:
- Same PySpark version (3.5.x)
- Same Python version (3.10+)
- Same library versions for ML packages

### 4. Progressive Testing

Tests are organized in layers of increasing integration:

```
Layer 1: Unit (mocked)     → Fast, isolated, developer feedback
Layer 2: Component (Spark) → DataFrame operations, transformations
Layer 3: Integration (DB)  → Full workflow validation
```

---

## Component Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Test Runner (pytest)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Unit Tests  │  │ Component   │  │ Integration │              │
│  │ (No Spark)  │  │ Tests       │  │ Tests       │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                │                │                       │
│         ▼                ▼                ▼                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Fixture Layer                              │ │
│  │  ┌─────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ Spark   │ │ Mock        │ │ Sample   │ │ Assertion    │  │ │
│  │  │ Session │ │ Databricks  │ │ Data     │ │ Helpers      │  │ │
│  │  └─────────┘ └─────────────┘ └──────────┘ └──────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Mock Layer                                 │ │
│  │  ┌─────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ dbutils │ │ Unity       │ │ DLT      │ │ MLflow       │  │ │
│  │  │ Mock    │ │ Catalog     │ │ Mock     │ │ Mock         │  │ │
│  │  └─────────┘ └─────────────┘ └──────────┘ └──────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Source Code Under Test                         │
│  ┌─────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Alerting│ │ Pipelines   │ │ ML       │ │ Monitoring       │  │
│  └─────────┘ └─────────────┘ └──────────┘ └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Module Dependencies

```
tests/
├── conftest.py                 # Root fixtures, shared across all tests
│   ├── imports fixtures/       # Modular fixture packages
│   └── defines core fixtures   # spark, mock_dbutils, sample data
│
├── fixtures/
│   ├── spark_fixtures.py       # SparkSession management
│   │   └── depends on: pyspark
│   │
│   ├── databricks_mocks.py     # Databricks SDK mocks
│   │   └── depends on: unittest.mock
│   │
│   ├── dlt_mocks.py            # DLT framework mocks
│   │   └── depends on: spark_fixtures
│   │
│   ├── mlflow_mocks.py         # MLflow mocks
│   │   └── depends on: unittest.mock
│   │
│   ├── sample_data.py          # Test data factories
│   │   └── depends on: spark_fixtures, pandas, numpy
│   │
│   └── assertion_helpers.py    # Custom assertions
│       └── depends on: chispa, pyspark
```

---

## Fixture System

### Fixture Scopes

| Scope | Lifecycle | Use Case |
|-------|-----------|----------|
| `session` | Entire test run | SparkSession, expensive setup |
| `module` | Single test file | Module-specific data |
| `class` | Test class | Class-level shared state |
| `function` | Single test | Default, isolated state |

### Core Fixtures

#### SparkSession Fixture

```python
@pytest.fixture(scope="session")
def spark():
    """
    Create a session-scoped local SparkSession.

    Configuration optimized for testing:
    - 2 local cores for parallelism simulation
    - Reduced shuffle partitions (2 vs default 200)
    - Arrow optimization enabled
    - Limited driver memory (2g)
    """
    spark = (
        SparkSession.builder
        .master("local[2]")
        .appName("HealthMonitorTests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse-test")
        .config("spark.driver.extraJavaOptions", "-Xss4m")
        .getOrCreate()
    )

    # Set log level to reduce noise
    spark.sparkContext.setLogLevel("WARN")

    yield spark
    spark.stop()
```

#### Database Mock Fixture

```python
@pytest.fixture
def mock_dbutils():
    """Provide mock dbutils for widget parameter handling."""
    return MockDbutils(defaults={
        "catalog": "test_catalog",
        "gold_schema": "system_gold",
        "bronze_schema": "system_bronze",
        "feature_schema": "system_gold_features",
    })

@pytest.fixture
def patch_dbutils(mock_dbutils):
    """Inject mock dbutils into global namespace for notebook compatibility."""
    import builtins
    original = getattr(builtins, 'dbutils', None)
    builtins.dbutils = mock_dbutils
    yield mock_dbutils
    if original:
        builtins.dbutils = original
    else:
        delattr(builtins, 'dbutils')
```

### Sample Data Factory Pattern

```python
class SampleDataFactory:
    """Factory for generating realistic test data."""

    @staticmethod
    def create_usage_data(
        spark,
        num_days: int = 90,
        workspaces: List[str] = None,
        skus: List[str] = None,
        anomaly_rate: float = 0.05
    ) -> DataFrame:
        """
        Generate sample fact_usage data.

        Args:
            spark: SparkSession
            num_days: Number of days of data
            workspaces: List of workspace IDs
            skus: List of SKU names
            anomaly_rate: Fraction of records that are anomalies

        Returns:
            DataFrame matching fact_usage schema
        """
        ...

    @staticmethod
    def create_job_run_data(
        spark,
        num_jobs: int = 20,
        runs_per_day: int = 5,
        failure_rate: float = 0.30
    ) -> DataFrame:
        """Generate sample fact_job_run_timeline data."""
        ...
```

---

## Mock Component Design

### MockDbutils Class

```python
class MockDbutils:
    """
    Mock implementation of Databricks dbutils.

    Supports:
    - widgets.get/text for parameter handling
    - notebook.exit for return values
    - fs.ls/cp/rm for file operations (stubbed)
    - secrets.get for secret retrieval (stubbed)
    """

    def __init__(self, defaults: Dict[str, str] = None):
        self._widgets = defaults or {}
        self._exit_value = None
        self._secrets = {}

    class Widgets:
        def __init__(self, parent):
            self._parent = parent

        def get(self, name: str) -> str:
            if name not in self._parent._widgets:
                raise ValueError(f"Widget '{name}' not found")
            return self._parent._widgets[name]

        def text(self, name: str, default: str, label: str = ""):
            self._parent._widgets[name] = default

        def dropdown(self, name: str, default: str, choices: List[str], label: str = ""):
            self._parent._widgets[name] = default

    class Notebook:
        def __init__(self, parent):
            self._parent = parent

        def exit(self, value: str):
            self._parent._exit_value = value

        def run(self, path: str, timeout: int = 0, arguments: Dict = None) -> str:
            # Stub - return empty string
            return ""

    class Fs:
        def ls(self, path: str) -> List:
            return []

        def cp(self, src: str, dst: str, recurse: bool = False):
            pass

        def rm(self, path: str, recurse: bool = False):
            pass

    class Secrets:
        def __init__(self, parent):
            self._parent = parent

        def get(self, scope: str, key: str) -> str:
            return self._parent._secrets.get(f"{scope}/{key}", "mock-secret")

    @property
    def widgets(self):
        return self.Widgets(self)

    @property
    def notebook(self):
        return self.Notebook(self)

    @property
    def fs(self):
        return self.Fs()

    @property
    def secrets(self):
        return self.Secrets(self)
```

### DLT Mock Module

```python
"""
Mock Delta Live Tables (DLT) module for local testing.

This module provides mock implementations of DLT decorators and functions
that allow DLT pipeline code to run locally without the DLT runtime.
"""

import functools
from typing import Callable, Any, Dict, List
from pyspark.sql import DataFrame

# Storage for mock tables
_mock_tables: Dict[str, DataFrame] = {}
_mock_expectations: List[Dict] = []


def table(
    name: str = None,
    comment: str = None,
    partition_cols: List[str] = None,
    cluster_by: List[str] = None,
    table_properties: Dict[str, str] = None,
    **kwargs
) -> Callable:
    """
    Mock @dlt.table decorator.

    In production, this creates a DLT table. In tests, it:
    1. Executes the decorated function
    2. Stores the result in _mock_tables
    3. Returns the DataFrame for assertion
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **inner_kwargs):
            result = func(*args, **inner_kwargs)
            table_name = name or func.__name__
            _mock_tables[table_name] = result
            return result
        return wrapper
    return decorator


def view(name: str = None, comment: str = None, **kwargs) -> Callable:
    """Mock @dlt.view decorator."""
    return table(name=name, comment=comment, **kwargs)


def read_stream(name: str) -> DataFrame:
    """
    Mock dlt.read_stream function.

    In tests, this returns the mock table if available,
    or raises an error if not set up.
    """
    if name not in _mock_tables:
        raise ValueError(f"Mock table '{name}' not found. Set up with register_mock_table()")
    return _mock_tables[name]


def read(name: str) -> DataFrame:
    """Mock dlt.read function for batch reads."""
    return read_stream(name)


def expect(name: str, condition: str):
    """Mock dlt.expect for data quality expectations."""
    _mock_expectations.append({"name": name, "condition": condition})
    return lambda df: df  # Pass through


def expect_or_drop(name: str, condition: str):
    """Mock dlt.expect_or_drop - in tests, we don't actually drop."""
    return expect(name, condition)


def expect_or_fail(name: str, condition: str):
    """Mock dlt.expect_or_fail - in tests, we validate but don't fail."""
    return expect(name, condition)


def register_mock_table(name: str, df: DataFrame):
    """Register a mock table for dlt.read_stream to return."""
    _mock_tables[name] = df


def clear_mock_tables():
    """Clear all registered mock tables."""
    _mock_tables.clear()
    _mock_expectations.clear()


def get_expectations() -> List[Dict]:
    """Get list of expectations that were applied."""
    return _mock_expectations.copy()
```

### MLflow Mock Fixture

```python
@pytest.fixture
def mock_mlflow():
    """
    Comprehensive MLflow mocking for model training tests.

    Mocks:
    - Experiment management (set_experiment, create_experiment)
    - Run management (start_run, end_run, active_run)
    - Logging (log_params, log_metrics, log_artifact)
    - Model logging (sklearn.log_model, pyfunc.log_model)
    - Model registry (register_model)
    """
    with patch.multiple(
        'mlflow',
        set_registry_uri=MagicMock(),
        set_experiment=MagicMock(return_value=MagicMock(experiment_id="test_exp")),
        start_run=MagicMock(),
        log_params=MagicMock(),
        log_metrics=MagicMock(),
        log_artifact=MagicMock(),
        set_tags=MagicMock(),
        autolog=MagicMock(),
    ) as mocks:

        # Configure start_run to work as context manager
        run_context = MagicMock()
        run_context.info.run_id = "test_run_123"
        run_context.info.experiment_id = "test_exp"

        mocks['start_run'].return_value.__enter__ = MagicMock(return_value=run_context)
        mocks['start_run'].return_value.__exit__ = MagicMock(return_value=False)

        yield mocks
```

### Unity Catalog Mock

```python
class MockUnityCatalog:
    """
    Mock Unity Catalog for testing table operations.

    Provides:
    - Catalog/schema/table existence checks
    - Table metadata retrieval
    - Table listing
    """

    def __init__(self, spark):
        self.spark = spark
        self._catalogs = {"test_catalog": {}}
        self._current_catalog = "test_catalog"
        self._current_database = "default"

    def setCurrentCatalog(self, catalog: str):
        self._current_catalog = catalog

    def setCurrentDatabase(self, database: str):
        self._current_database = database

    def currentCatalog(self) -> str:
        return self._current_catalog

    def currentDatabase(self) -> str:
        return self._current_database

    def tableExists(self, table_name: str) -> bool:
        """Check if table exists (in temp views for testing)."""
        return table_name in [t.name for t in self.spark.catalog.listTables()]

    def listTables(self, database: str = None) -> List:
        """List tables in database."""
        return self.spark.catalog.listTables(database)

    def register_temp_table(self, name: str, df):
        """Register a DataFrame as a temp table for testing."""
        df.createOrReplaceTempView(name)
```

---

## Test Data Management

### Data Generation Strategies

#### 1. Deterministic Seeds

All random data generation uses fixed seeds for reproducibility:

```python
np.random.seed(42)  # Always use consistent seed
random.seed(42)
```

#### 2. Schema-Compliant Data

Test data must match production schemas exactly:

```python
FACT_USAGE_SCHEMA = StructType([
    StructField("record_id", StringType(), False),
    StructField("workspace_id", StringType(), False),
    StructField("usage_date", DateType(), False),
    StructField("sku_name", StringType(), False),
    StructField("usage_quantity", DoubleType(), False),
    StructField("usage_unit", StringType(), True),
    StructField("custom_tags", MapType(StringType(), StringType()), True),
    StructField("bronze_ingestion_timestamp", TimestampType(), False),
    StructField("gold_merge_timestamp", TimestampType(), False),
])

def create_usage_record(**overrides):
    """Create a single usage record with defaults."""
    defaults = {
        "record_id": str(uuid.uuid4()),
        "workspace_id": "ws_001",
        "usage_date": date.today(),
        "sku_name": "JOBS_COMPUTE",
        "usage_quantity": 100.0,
        "usage_unit": "DBU",
        "custom_tags": {},
        "bronze_ingestion_timestamp": datetime.now(),
        "gold_merge_timestamp": datetime.now(),
    }
    return {**defaults, **overrides}
```

#### 3. Edge Case Data

Explicit edge case generators for boundary testing:

```python
def create_edge_case_data(spark, case: str) -> DataFrame:
    """
    Generate specific edge case data for testing.

    Cases:
    - "null_values": Records with NULL in various columns
    - "empty": Empty DataFrame with correct schema
    - "single_record": Exactly one record
    - "duplicates": Records with duplicate keys
    - "unicode": Records with Unicode characters
    - "max_values": Records at numeric limits
    """
    ...
```

---

## Execution Model

### Test Discovery

pytest discovers tests following naming conventions:
- Files: `test_*.py` or `*_test.py`
- Classes: `Test*`
- Functions: `test_*`

### Marker-Based Filtering

```bash
# Run only unit tests
pytest -m unit

# Run only ML tests
pytest -m ml

# Run all except slow tests
pytest -m "not slow"

# Run integration tests that are also ML
pytest -m "integration and ml"
```

### Parallel Execution

Using pytest-xdist for parallel execution:

```bash
# Auto-detect CPU count
pytest -n auto

# Fixed worker count
pytest -n 4

# Run session-scoped fixtures in each worker
pytest -n auto --dist loadscope
```

### Test Order

Tests should be order-independent, but some guidelines:
1. Unit tests before integration tests (fail fast)
2. Lighter tests before heavier tests
3. Use `pytest-randomly` to detect order dependencies

---

## Performance Considerations

### SparkSession Reuse

Session scope for SparkSession means one JVM per test run:
- Startup: ~5-10 seconds (once)
- Per-test overhead: ~100ms

### DataFrame Caching

For expensive DataFrame operations, use caching:

```python
@pytest.fixture(scope="module")
def large_test_data(spark):
    df = create_large_dataset(spark)
    df.cache()
    df.count()  # Force cache materialization
    yield df
    df.unpersist()
```

### Lazy Evaluation Awareness

Remember Spark is lazy - time tests at action execution:

```python
def test_transformation_performance(spark, sample_data):
    start = time.time()
    result = my_transformation(sample_data)
    result.count()  # Force execution
    duration = time.time() - start
    assert duration < 5.0, f"Transformation too slow: {duration}s"
```

### Memory Management

Keep test data size reasonable:
- Unit tests: < 100 records
- Component tests: < 10,000 records
- Integration tests: < 100,000 records

---

## Appendix: Configuration Files

### pytest.ini / pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "-ra",
    "--strict-markers",
]
markers = [
    "unit: Unit tests that don't require Spark",
    "integration: Integration tests that require Spark",
    "slow: Slow tests that should be run separately",
    "ml: ML model tests",
    "tvf: Table-Valued Function tests",
    "feature: Feature engineering tests",
    "pipeline: Data pipeline tests",
    "alerting: Alert framework tests",
    "databricks: Tests requiring Databricks connectivity",
]
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]
```

### conftest.py Imports

```python
# tests/conftest.py
from tests.fixtures.spark_fixtures import spark, spark_session
from tests.fixtures.databricks_mocks import mock_dbutils, patch_dbutils, mock_catalog
from tests.fixtures.dlt_mocks import mock_dlt, register_mock_table
from tests.fixtures.mlflow_mocks import mock_mlflow
from tests.fixtures.sample_data import (
    sample_usage_data,
    sample_job_run_data,
    sample_query_history_data,
    sample_cost_features,
    sample_job_features,
)
from tests.fixtures.assertion_helpers import (
    assert_dataframe_equal,
    assert_schema_equal,
    assert_no_nulls,
)
```

---

*Document Version: 1.0*
*Last Updated: 2026-01-01*
