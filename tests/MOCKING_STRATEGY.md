# Mocking Strategy Guide

## Overview

This guide provides comprehensive patterns for mocking Databricks-specific components when running tests locally. Proper mocking enables fast, reliable tests without requiring Databricks cluster access.

---

## Table of Contents

1. [Mocking Philosophy](#mocking-philosophy)
2. [dbutils Mocking](#dbutils-mocking)
3. [DLT Framework Mocking](#dlt-framework-mocking)
4. [Unity Catalog Mocking](#unity-catalog-mocking)
5. [MLflow Mocking](#mlflow-mocking)
6. [Databricks SDK Mocking](#databricks-sdk-mocking)
7. [Lakehouse Monitoring Mocking](#lakehouse-monitoring-mocking)
8. [Best Practices](#best-practices)

---

## Mocking Philosophy

### When to Mock

| Scenario | Mock? | Rationale |
|----------|-------|-----------|
| External API calls | Yes | Speed, reliability, cost |
| Databricks runtime features | Yes | Not available locally |
| Database reads/writes | Depends | Mock for unit tests, real for integration |
| File system operations | Depends | Mock for unit, temp files for integration |
| Time-dependent code | Yes | Deterministic tests |

### When NOT to Mock

| Scenario | Rationale |
|----------|-----------|
| Core business logic | That's what we're testing! |
| Simple data transformations | Use real Spark locally |
| Pure Python functions | No external dependencies |

### Mock Fidelity Levels

1. **Stub**: Returns fixed values (simplest)
2. **Spy**: Records calls, returns real values
3. **Mock**: Returns configured values, verifies calls
4. **Fake**: Simplified working implementation

---

## dbutils Mocking

### Overview

`dbutils` is Databricks' utility object providing widgets, notebooks, filesystem, and secrets access. It's not available locally and must be mocked.

### Complete MockDbutils Implementation

```python
"""
tests/fixtures/databricks_mocks.py

Comprehensive dbutils mock for local testing.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from unittest.mock import MagicMock


@dataclass
class FileInfo:
    """Mock file info returned by dbutils.fs.ls()"""
    path: str
    name: str
    size: int
    modificationTime: int = 0
    isDir: bool = False
    isFile: bool = True


class MockWidgets:
    """Mock implementation of dbutils.widgets"""

    def __init__(self, defaults: Dict[str, str] = None):
        self._values: Dict[str, str] = defaults or {}
        self._definitions: Dict[str, Dict] = {}

    def get(self, name: str) -> str:
        """Get widget value. Raises ValueError if not found."""
        if name not in self._values:
            raise ValueError(
                f"InputWidget named '{name}' does not exist. "
                f"Available widgets: {list(self._values.keys())}"
            )
        return self._values[name]

    def text(self, name: str, defaultValue: str, label: str = "") -> None:
        """Create text widget with default value."""
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "text",
            "default": defaultValue,
            "label": label
        }

    def dropdown(
        self,
        name: str,
        defaultValue: str,
        choices: List[str],
        label: str = ""
    ) -> None:
        """Create dropdown widget."""
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "dropdown",
            "default": defaultValue,
            "choices": choices,
            "label": label
        }

    def combobox(
        self,
        name: str,
        defaultValue: str,
        choices: List[str],
        label: str = ""
    ) -> None:
        """Create combobox widget."""
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "combobox",
            "default": defaultValue,
            "choices": choices,
            "label": label
        }

    def multiselect(
        self,
        name: str,
        defaultValue: str,
        choices: List[str],
        label: str = ""
    ) -> None:
        """Create multiselect widget."""
        self._values[name] = defaultValue
        self._definitions[name] = {
            "type": "multiselect",
            "default": defaultValue,
            "choices": choices,
            "label": label
        }

    def remove(self, name: str) -> None:
        """Remove a widget."""
        self._values.pop(name, None)
        self._definitions.pop(name, None)

    def removeAll(self) -> None:
        """Remove all widgets."""
        self._values.clear()
        self._definitions.clear()

    # Test helper methods
    def set_value(self, name: str, value: str) -> None:
        """Test helper: Set widget value without creating definition."""
        self._values[name] = value

    def get_all_values(self) -> Dict[str, str]:
        """Test helper: Get all widget values."""
        return self._values.copy()


class MockNotebook:
    """Mock implementation of dbutils.notebook"""

    def __init__(self):
        self._exit_value: Optional[str] = None
        self._run_results: Dict[str, str] = {}

    def exit(self, value: str) -> None:
        """Exit notebook with return value."""
        self._exit_value = value

    def run(
        self,
        path: str,
        timeout_seconds: int = 0,
        arguments: Dict[str, str] = None
    ) -> str:
        """
        Run another notebook.

        In tests, returns pre-configured result or empty string.
        """
        return self._run_results.get(path, "")

    def getContext(self) -> MagicMock:
        """Get notebook context (mocked)."""
        context = MagicMock()
        context.notebookPath.return_value = "/Workspace/test_notebook"
        context.currentRunId.return_value = "run_12345"
        return context

    # Test helper methods
    def set_run_result(self, path: str, result: str) -> None:
        """Test helper: Configure result for notebook.run()."""
        self._run_results[path] = result

    def get_exit_value(self) -> Optional[str]:
        """Test helper: Get the exit value."""
        return self._exit_value


class MockFs:
    """Mock implementation of dbutils.fs"""

    def __init__(self):
        self._files: Dict[str, bytes] = {}
        self._directories: set = set()

    def ls(self, path: str) -> List[FileInfo]:
        """List files in directory."""
        results = []
        for file_path in self._files:
            if file_path.startswith(path):
                name = file_path[len(path):].lstrip("/").split("/")[0]
                results.append(FileInfo(
                    path=f"{path}/{name}",
                    name=name,
                    size=len(self._files[file_path])
                ))
        return results

    def head(self, path: str, max_bytes: int = 65536) -> str:
        """Read first bytes of file."""
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        return self._files[path][:max_bytes].decode('utf-8')

    def cp(self, src: str, dst: str, recurse: bool = False) -> bool:
        """Copy file or directory."""
        if src in self._files:
            self._files[dst] = self._files[src]
        return True

    def mv(self, src: str, dst: str, recurse: bool = False) -> bool:
        """Move file or directory."""
        if src in self._files:
            self._files[dst] = self._files[src]
            del self._files[src]
        return True

    def rm(self, path: str, recurse: bool = False) -> bool:
        """Remove file or directory."""
        if path in self._files:
            del self._files[path]
        return True

    def mkdirs(self, path: str) -> bool:
        """Create directory."""
        self._directories.add(path)
        return True

    def put(self, path: str, contents: str, overwrite: bool = False) -> bool:
        """Write contents to file."""
        if path in self._files and not overwrite:
            raise FileExistsError(f"File exists: {path}")
        self._files[path] = contents.encode('utf-8')
        return True

    # Test helper methods
    def add_file(self, path: str, contents: bytes) -> None:
        """Test helper: Add a mock file."""
        self._files[path] = contents

    def clear(self) -> None:
        """Test helper: Clear all files."""
        self._files.clear()
        self._directories.clear()


class MockSecrets:
    """Mock implementation of dbutils.secrets"""

    def __init__(self):
        self._secrets: Dict[str, str] = {}

    def get(self, scope: str, key: str) -> str:
        """Get secret value."""
        full_key = f"{scope}/{key}"
        if full_key not in self._secrets:
            raise ValueError(f"Secret '{key}' not found in scope '{scope}'")
        return self._secrets[full_key]

    def getBytes(self, scope: str, key: str) -> bytes:
        """Get secret as bytes."""
        return self.get(scope, key).encode('utf-8')

    def list(self, scope: str) -> List[Dict]:
        """List secrets in scope."""
        results = []
        for key in self._secrets:
            if key.startswith(f"{scope}/"):
                secret_key = key.split("/", 1)[1]
                results.append({"key": secret_key})
        return results

    def listScopes(self) -> List[Dict]:
        """List all scopes."""
        scopes = set()
        for key in self._secrets:
            scope = key.split("/")[0]
            scopes.add(scope)
        return [{"name": s} for s in scopes]

    # Test helper methods
    def set_secret(self, scope: str, key: str, value: str) -> None:
        """Test helper: Set a secret value."""
        self._secrets[f"{scope}/{key}"] = value


class MockDbutils:
    """
    Complete mock implementation of Databricks dbutils.

    Usage in tests:
        @pytest.fixture
        def mock_dbutils():
            return MockDbutils(defaults={
                "catalog": "test_catalog",
                "schema": "test_schema",
            })

        def test_notebook(mock_dbutils, patch_dbutils):
            # mock_dbutils is now available as dbutils
            value = dbutils.widgets.get("catalog")
            assert value == "test_catalog"
    """

    def __init__(self, defaults: Dict[str, str] = None):
        self._widgets = MockWidgets(defaults)
        self._notebook = MockNotebook()
        self._fs = MockFs()
        self._secrets = MockSecrets()

    @property
    def widgets(self) -> MockWidgets:
        return self._widgets

    @property
    def notebook(self) -> MockNotebook:
        return self._notebook

    @property
    def fs(self) -> MockFs:
        return self._fs

    @property
    def secrets(self) -> MockSecrets:
        return self._secrets
```

### Usage Examples

```python
# tests/test_example.py

import pytest

def test_widget_access(mock_dbutils, patch_dbutils):
    """Test that notebook can access widget values."""
    # Widget is already set to "test_catalog" by fixture
    catalog = dbutils.widgets.get("catalog")
    assert catalog == "test_catalog"

def test_custom_widget_value(mock_dbutils, patch_dbutils):
    """Test with custom widget value."""
    mock_dbutils.widgets.set_value("custom_param", "custom_value")
    assert dbutils.widgets.get("custom_param") == "custom_value"

def test_notebook_exit(mock_dbutils, patch_dbutils):
    """Test notebook exit capture."""
    dbutils.notebook.exit("SUCCESS")
    assert mock_dbutils.notebook.get_exit_value() == "SUCCESS"

def test_secret_access(mock_dbutils, patch_dbutils):
    """Test secret retrieval."""
    mock_dbutils.secrets.set_secret("my_scope", "api_key", "secret123")
    value = dbutils.secrets.get("my_scope", "api_key")
    assert value == "secret123"
```

---

## DLT Framework Mocking

### Overview

Delta Live Tables (DLT) provides decorators (`@dlt.table`, `@dlt.view`) and functions (`dlt.read_stream`, `dlt.expect`) that require the DLT runtime. Our mock allows DLT pipeline code to run locally.

### Mock DLT Module

```python
"""
tests/fixtures/dlt_mocks.py

Mock Delta Live Tables framework for local testing.
"""

import functools
from typing import Callable, Any, Dict, List, Optional, Union
from pyspark.sql import DataFrame, SparkSession
import sys

# Storage for mock state
_mock_tables: Dict[str, DataFrame] = {}
_mock_expectations: List[Dict[str, Any]] = []
_mock_spark: Optional[SparkSession] = None


def set_spark(spark: SparkSession) -> None:
    """Set the SparkSession for DLT operations."""
    global _mock_spark
    _mock_spark = spark


def table(
    name: Optional[str] = None,
    comment: Optional[str] = None,
    spark_conf: Optional[Dict[str, str]] = None,
    table_properties: Optional[Dict[str, str]] = None,
    path: Optional[str] = None,
    partition_cols: Optional[List[str]] = None,
    cluster_by: Optional[List[str]] = None,
    schema: Optional[str] = None,
    temporary: bool = False,
) -> Callable:
    """
    Mock @dlt.table decorator.

    Captures the decorated function's output for testing.
    """
    def decorator(func: Callable[..., DataFrame]) -> Callable[..., DataFrame]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> DataFrame:
            result = func(*args, **kwargs)
            table_name = name or func.__name__
            _mock_tables[table_name] = result
            return result

        # Store metadata for inspection
        wrapper._dlt_table_name = name or func.__name__
        wrapper._dlt_comment = comment
        wrapper._dlt_properties = table_properties or {}

        return wrapper
    return decorator


def view(
    name: Optional[str] = None,
    comment: Optional[str] = None,
) -> Callable:
    """Mock @dlt.view decorator - same behavior as table for testing."""
    return table(name=name, comment=comment)


def read_stream(name: str) -> DataFrame:
    """
    Mock dlt.read_stream() - returns registered mock table.

    Raises ValueError if table not registered.
    """
    if name not in _mock_tables:
        raise ValueError(
            f"DLT table '{name}' not found. "
            f"Register with dlt_mock.register_table(). "
            f"Available: {list(_mock_tables.keys())}"
        )
    return _mock_tables[name]


def read(name: str) -> DataFrame:
    """Mock dlt.read() for batch reads."""
    return read_stream(name)


def apply_changes(
    target: str,
    source: str,
    keys: List[str],
    sequence_by: str,
    stored_as_scd_type: int = 1,
    **kwargs
) -> None:
    """
    Mock dlt.apply_changes() for CDC operations.

    In tests, this is a no-op since we handle CDC differently.
    """
    pass


# Expectation Functions

class ExpectationChain:
    """Chainable expectation for DataFrame operations."""

    def __init__(self, expectations: List[Dict[str, Any]]):
        self._expectations = expectations

    def __call__(self, df: DataFrame) -> DataFrame:
        """Apply expectations to DataFrame (pass-through in tests)."""
        return df


def expect(name: str, condition: str) -> ExpectationChain:
    """
    Mock dlt.expect() - data quality expectation.

    Records expectation for verification, returns pass-through.
    """
    expectation = {
        "name": name,
        "condition": condition,
        "action": "warn",
    }
    _mock_expectations.append(expectation)
    return ExpectationChain([expectation])


def expect_or_drop(name: str, condition: str) -> ExpectationChain:
    """Mock dlt.expect_or_drop() - records expectation with drop action."""
    expectation = {
        "name": name,
        "condition": condition,
        "action": "drop",
    }
    _mock_expectations.append(expectation)
    return ExpectationChain([expectation])


def expect_or_fail(name: str, condition: str) -> ExpectationChain:
    """Mock dlt.expect_or_fail() - records expectation with fail action."""
    expectation = {
        "name": name,
        "condition": condition,
        "action": "fail",
    }
    _mock_expectations.append(expectation)
    return ExpectationChain([expectation])


def expect_all(expectations: Dict[str, str]) -> ExpectationChain:
    """Mock dlt.expect_all() - multiple expectations."""
    recorded = []
    for name, condition in expectations.items():
        exp = {"name": name, "condition": condition, "action": "warn"}
        _mock_expectations.append(exp)
        recorded.append(exp)
    return ExpectationChain(recorded)


def expect_all_or_drop(expectations: Dict[str, str]) -> ExpectationChain:
    """Mock dlt.expect_all_or_drop()."""
    recorded = []
    for name, condition in expectations.items():
        exp = {"name": name, "condition": condition, "action": "drop"}
        _mock_expectations.append(exp)
        recorded.append(exp)
    return ExpectationChain(recorded)


def expect_all_or_fail(expectations: Dict[str, str]) -> ExpectationChain:
    """Mock dlt.expect_all_or_fail()."""
    recorded = []
    for name, condition in expectations.items():
        exp = {"name": name, "condition": condition, "action": "fail"}
        _mock_expectations.append(exp)
        recorded.append(exp)
    return ExpectationChain(recorded)


# Test Helper Functions

def register_table(name: str, df: DataFrame) -> None:
    """Register a mock table for read_stream/read."""
    _mock_tables[name] = df


def get_table(name: str) -> Optional[DataFrame]:
    """Get a registered mock table."""
    return _mock_tables.get(name)


def get_all_tables() -> Dict[str, DataFrame]:
    """Get all registered tables."""
    return _mock_tables.copy()


def get_expectations() -> List[Dict[str, Any]]:
    """Get all recorded expectations."""
    return _mock_expectations.copy()


def clear() -> None:
    """Clear all mock state."""
    _mock_tables.clear()
    _mock_expectations.clear()


def verify_expectation(name: str) -> Optional[Dict[str, Any]]:
    """Verify an expectation was applied."""
    for exp in _mock_expectations:
        if exp["name"] == name:
            return exp
    return None


# Pytest Fixture

import pytest

@pytest.fixture
def mock_dlt(spark, monkeypatch):
    """
    Fixture that patches 'dlt' module with mock implementation.

    Usage:
        def test_my_pipeline(mock_dlt, spark):
            # Register source tables
            mock_dlt.register_table("source_table", source_df)

            # Import and run pipeline
            from src.pipelines.bronze import my_pipeline
            result = my_pipeline.process()

            # Verify output
            assert mock_dlt.get_table("target_table").count() > 0
    """
    # Set spark for the mock
    set_spark(spark)
    clear()

    # Create module mock
    mock_module = type(sys)('dlt')
    mock_module.table = table
    mock_module.view = view
    mock_module.read_stream = read_stream
    mock_module.read = read
    mock_module.apply_changes = apply_changes
    mock_module.expect = expect
    mock_module.expect_or_drop = expect_or_drop
    mock_module.expect_or_fail = expect_or_fail
    mock_module.expect_all = expect_all
    mock_module.expect_all_or_drop = expect_all_or_drop
    mock_module.expect_all_or_fail = expect_all_or_fail

    # Add to sys.modules
    monkeypatch.setitem(sys.modules, 'dlt', mock_module)

    # Create helper interface
    class DLTHelper:
        register_table = staticmethod(register_table)
        get_table = staticmethod(get_table)
        get_all_tables = staticmethod(get_all_tables)
        get_expectations = staticmethod(get_expectations)
        verify_expectation = staticmethod(verify_expectation)
        clear = staticmethod(clear)

    yield DLTHelper

    # Cleanup
    clear()
```

### Usage Examples

```python
# tests/component/pipelines/test_bronze_streaming.py

def test_access_audit_streaming(mock_dlt, spark, sample_audit_data):
    """Test bronze access audit streaming pipeline."""
    # Arrange: Register source data
    mock_dlt.register_table("system.access.audit", sample_audit_data)

    # Act: Import and execute the DLT pipeline function
    from src.pipelines.bronze.streaming.access_tables import bronze_audit

    # The @dlt.table decorator captures output
    result = bronze_audit()

    # Assert: Verify output
    output_df = mock_dlt.get_table("bronze_audit")
    assert output_df is not None
    assert output_df.count() > 0
    assert "action_name" in output_df.columns


def test_data_quality_expectations(mock_dlt, spark):
    """Test that DLT expectations are properly applied."""
    # Create test data with some invalid records
    data = [
        {"id": 1, "value": 100},
        {"id": 2, "value": None},  # Should trigger expectation
    ]
    df = spark.createDataFrame(data)
    mock_dlt.register_table("source", df)

    # Run pipeline that applies expectations
    from src.pipelines.bronze.streaming import quality_checks

    # Verify expectation was recorded
    exp = mock_dlt.verify_expectation("valid_value")
    assert exp is not None
    assert exp["action"] == "drop"
```

---

## Unity Catalog Mocking

### Overview

Unity Catalog provides three-level namespace (catalog.schema.table), access control, and data governance. Mock provides namespace resolution without actual catalog.

### Mock Implementation

```python
"""
tests/fixtures/unity_catalog_mocks.py

Mock Unity Catalog for local testing.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType
import pytest


@dataclass
class TableInfo:
    """Metadata for a mock table."""
    name: str
    catalog: str
    schema: str
    table_type: str = "MANAGED"
    data_source_format: str = "DELTA"
    columns: List[Dict] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    owner: str = "test_user"

    @property
    def full_name(self) -> str:
        return f"{self.catalog}.{self.schema}.{self.name}"


@dataclass
class SchemaInfo:
    """Metadata for a mock schema."""
    name: str
    catalog: str
    owner: str = "test_user"
    comment: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.catalog}.{self.name}"


class MockUnityCatalog:
    """
    Mock Unity Catalog for testing catalog/schema/table operations.

    Provides:
    - Catalog and schema management
    - Table registration and lookup
    - Three-level namespace resolution
    """

    def __init__(self, spark: SparkSession):
        self.spark = spark
        self._catalogs: Dict[str, Dict[str, SchemaInfo]] = {}
        self._tables: Dict[str, TableInfo] = {}
        self._table_data: Dict[str, DataFrame] = {}
        self._current_catalog = "main"
        self._current_schema = "default"

        # Initialize default catalog/schema
        self.create_catalog("main")
        self.create_schema("main", "default")

    # Catalog operations

    def create_catalog(self, name: str) -> None:
        """Create a catalog."""
        if name not in self._catalogs:
            self._catalogs[name] = {}

    def list_catalogs(self) -> List[str]:
        """List all catalogs."""
        return list(self._catalogs.keys())

    def catalog_exists(self, name: str) -> bool:
        """Check if catalog exists."""
        return name in self._catalogs

    # Schema operations

    def create_schema(
        self,
        catalog: str,
        name: str,
        comment: str = ""
    ) -> SchemaInfo:
        """Create a schema in catalog."""
        if catalog not in self._catalogs:
            self.create_catalog(catalog)

        schema_info = SchemaInfo(name=name, catalog=catalog, comment=comment)
        self._catalogs[catalog][name] = schema_info
        return schema_info

    def list_schemas(self, catalog: str) -> List[SchemaInfo]:
        """List schemas in catalog."""
        return list(self._catalogs.get(catalog, {}).values())

    def schema_exists(self, catalog: str, name: str) -> bool:
        """Check if schema exists."""
        return name in self._catalogs.get(catalog, {})

    # Table operations

    def register_table(
        self,
        catalog: str,
        schema: str,
        name: str,
        df: DataFrame,
        properties: Dict[str, str] = None
    ) -> TableInfo:
        """
        Register a DataFrame as a mock table.

        Also creates the table as a temp view for SQL access.
        """
        # Ensure catalog/schema exist
        self.create_schema(catalog, schema)

        # Create table info
        table_info = TableInfo(
            name=name,
            catalog=catalog,
            schema=schema,
            properties=properties or {},
            columns=[
                {"name": f.name, "type": str(f.dataType)}
                for f in df.schema.fields
            ]
        )

        full_name = table_info.full_name
        self._tables[full_name] = table_info
        self._table_data[full_name] = df

        # Register as temp view for SQL access
        # Use underscore notation for temp view name
        temp_view_name = full_name.replace(".", "_")
        df.createOrReplaceTempView(temp_view_name)

        return table_info

    def get_table(self, full_name: str) -> Optional[DataFrame]:
        """Get table data by full name."""
        return self._table_data.get(full_name)

    def get_table_by_parts(
        self,
        catalog: str,
        schema: str,
        name: str
    ) -> Optional[DataFrame]:
        """Get table data by catalog.schema.name parts."""
        full_name = f"{catalog}.{schema}.{name}"
        return self.get_table(full_name)

    def table_exists(self, full_name: str) -> bool:
        """Check if table exists."""
        return full_name in self._tables

    def list_tables(self, catalog: str, schema: str) -> List[TableInfo]:
        """List tables in schema."""
        prefix = f"{catalog}.{schema}."
        return [
            info for name, info in self._tables.items()
            if name.startswith(prefix)
        ]

    def drop_table(self, full_name: str) -> bool:
        """Drop a table."""
        if full_name in self._tables:
            del self._tables[full_name]
            del self._table_data[full_name]
            return True
        return False

    # Current context

    def setCurrentCatalog(self, catalog: str) -> None:
        """Set current catalog."""
        self._current_catalog = catalog

    def setCurrentDatabase(self, schema: str) -> None:
        """Set current schema/database."""
        self._current_schema = schema

    def currentCatalog(self) -> str:
        """Get current catalog."""
        return self._current_catalog

    def currentDatabase(self) -> str:
        """Get current schema."""
        return self._current_schema

    # SQL table name resolution

    def resolve_table_name(self, name: str) -> str:
        """
        Resolve table name to full three-level name.

        - "table" -> "current_catalog.current_schema.table"
        - "schema.table" -> "current_catalog.schema.table"
        - "catalog.schema.table" -> "catalog.schema.table"
        """
        parts = name.split(".")
        if len(parts) == 1:
            return f"{self._current_catalog}.{self._current_schema}.{name}"
        elif len(parts) == 2:
            return f"{self._current_catalog}.{parts[0]}.{parts[1]}"
        else:
            return name

    def clear(self) -> None:
        """Clear all mock data."""
        self._tables.clear()
        self._table_data.clear()
        # Reset to defaults
        self._catalogs = {"main": {"default": SchemaInfo("default", "main")}}
        self._current_catalog = "main"
        self._current_schema = "default"


# Pytest Fixture

@pytest.fixture
def mock_catalog(spark):
    """
    Fixture providing mock Unity Catalog.

    Usage:
        def test_table_ops(mock_catalog, spark):
            # Register a table
            df = spark.createDataFrame([{"id": 1}])
            mock_catalog.register_table(
                "my_catalog", "my_schema", "my_table", df
            )

            # Verify table exists
            assert mock_catalog.table_exists("my_catalog.my_schema.my_table")

            # Get table data
            result = mock_catalog.get_table("my_catalog.my_schema.my_table")
            assert result.count() == 1
    """
    catalog = MockUnityCatalog(spark)
    yield catalog
    catalog.clear()
```

### Usage Examples

```python
def test_gold_merge_with_catalog(mock_catalog, spark):
    """Test Gold layer merge with Unity Catalog mock."""
    # Setup: Register source and target tables
    source_df = spark.createDataFrame([
        {"id": 1, "value": "new"},
    ])
    target_df = spark.createDataFrame([
        {"id": 1, "value": "old"},
    ])

    mock_catalog.register_table(
        "main", "bronze", "source_table", source_df
    )
    mock_catalog.register_table(
        "main", "gold", "target_table", target_df
    )

    # Test merge logic
    # ... your merge code here ...

    # Verify result
    result = mock_catalog.get_table("main.gold.target_table")
    assert result.filter("value = 'new'").count() == 1
```

---

## MLflow Mocking

### Overview

MLflow provides experiment tracking, model logging, and registry. Mocking prevents actual experiment creation while verifying logging calls.

### Comprehensive MLflow Mock

```python
"""
tests/fixtures/mlflow_mocks.py

Comprehensive MLflow mocking for ML pipeline tests.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class MockRunInfo:
    """Mock MLflow run info."""
    run_id: str = "test_run_123"
    experiment_id: str = "test_exp_456"
    run_name: str = "test_run"
    status: str = "RUNNING"
    artifact_uri: str = "/tmp/mlflow/artifacts"


@dataclass
class MockRun:
    """Mock MLflow run."""
    info: MockRunInfo = field(default_factory=MockRunInfo)
    data: Dict[str, Any] = field(default_factory=dict)


class MockMLflowClient:
    """Mock MLflow tracking client."""

    def __init__(self):
        self.logged_params: Dict[str, Any] = {}
        self.logged_metrics: Dict[str, float] = {}
        self.logged_tags: Dict[str, str] = {}
        self.logged_artifacts: List[str] = []
        self.logged_models: List[Dict] = []
        self.registered_models: List[Dict] = []

    def log_param(self, run_id: str, key: str, value: Any) -> None:
        self.logged_params[key] = value

    def log_metric(self, run_id: str, key: str, value: float, **kwargs) -> None:
        self.logged_metrics[key] = value

    def set_tag(self, run_id: str, key: str, value: str) -> None:
        self.logged_tags[key] = value

    def log_artifact(self, run_id: str, local_path: str, **kwargs) -> None:
        self.logged_artifacts.append(local_path)


@pytest.fixture
def mock_mlflow():
    """
    Comprehensive MLflow mock fixture.

    Tracks all logging calls for assertion in tests.
    """
    client = MockMLflowClient()
    mock_run = MockRun()

    patches = {}

    with patch('mlflow.set_tracking_uri') as mock_tracking_uri, \
         patch('mlflow.set_registry_uri') as mock_registry_uri, \
         patch('mlflow.set_experiment') as mock_set_exp, \
         patch('mlflow.start_run') as mock_start_run, \
         patch('mlflow.end_run') as mock_end_run, \
         patch('mlflow.active_run') as mock_active_run, \
         patch('mlflow.log_params') as mock_log_params, \
         patch('mlflow.log_metrics') as mock_log_metrics, \
         patch('mlflow.log_param') as mock_log_param, \
         patch('mlflow.log_metric') as mock_log_metric, \
         patch('mlflow.set_tag') as mock_set_tag, \
         patch('mlflow.set_tags') as mock_set_tags, \
         patch('mlflow.log_artifact') as mock_log_artifact, \
         patch('mlflow.log_artifacts') as mock_log_artifacts, \
         patch('mlflow.sklearn.log_model') as mock_sklearn_log, \
         patch('mlflow.pyfunc.log_model') as mock_pyfunc_log, \
         patch('mlflow.register_model') as mock_register, \
         patch('mlflow.autolog') as mock_autolog:

        # Configure start_run as context manager
        mock_start_run.return_value.__enter__ = MagicMock(return_value=mock_run)
        mock_start_run.return_value.__exit__ = MagicMock(return_value=False)

        # Configure active_run
        mock_active_run.return_value = mock_run

        # Configure set_experiment
        mock_exp = MagicMock()
        mock_exp.experiment_id = mock_run.info.experiment_id
        mock_set_exp.return_value = mock_exp

        # Track calls
        def track_params(params):
            client.logged_params.update(params)
        mock_log_params.side_effect = track_params

        def track_metrics(metrics, step=None):
            client.logged_metrics.update(metrics)
        mock_log_metrics.side_effect = track_metrics

        def track_param(key, value):
            client.logged_params[key] = value
        mock_log_param.side_effect = track_param

        def track_metric(key, value, step=None):
            client.logged_metrics[key] = value
        mock_log_metric.side_effect = track_metric

        def track_tags(tags):
            client.logged_tags.update(tags)
        mock_set_tags.side_effect = track_tags

        def track_sklearn(model, artifact_path, **kwargs):
            client.logged_models.append({
                "type": "sklearn",
                "artifact_path": artifact_path,
                "kwargs": kwargs
            })
        mock_sklearn_log.side_effect = track_sklearn

        def track_register(model_uri, name, **kwargs):
            client.registered_models.append({
                "uri": model_uri,
                "name": name,
            })
            return MagicMock(version="1")
        mock_register.side_effect = track_register

        # Create helper interface
        class MLflowHelper:
            @property
            def logged_params(self) -> Dict[str, Any]:
                return client.logged_params

            @property
            def logged_metrics(self) -> Dict[str, float]:
                return client.logged_metrics

            @property
            def logged_tags(self) -> Dict[str, str]:
                return client.logged_tags

            @property
            def logged_models(self) -> List[Dict]:
                return client.logged_models

            @property
            def registered_models(self) -> List[Dict]:
                return client.registered_models

            def assert_param_logged(self, key: str, expected: Any = None):
                assert key in client.logged_params, \
                    f"Param '{key}' not logged. Logged: {list(client.logged_params.keys())}"
                if expected is not None:
                    assert client.logged_params[key] == expected, \
                        f"Param '{key}' = {client.logged_params[key]}, expected {expected}"

            def assert_metric_logged(self, key: str, min_val: float = None, max_val: float = None):
                assert key in client.logged_metrics, \
                    f"Metric '{key}' not logged. Logged: {list(client.logged_metrics.keys())}"
                if min_val is not None:
                    assert client.logged_metrics[key] >= min_val
                if max_val is not None:
                    assert client.logged_metrics[key] <= max_val

            def assert_model_logged(self, artifact_path: str = None):
                assert len(client.logged_models) > 0, "No models logged"
                if artifact_path:
                    paths = [m["artifact_path"] for m in client.logged_models]
                    assert artifact_path in paths, \
                        f"Model with path '{artifact_path}' not found. Paths: {paths}"

            def assert_model_registered(self, name: str = None):
                assert len(client.registered_models) > 0, "No models registered"
                if name:
                    names = [m["name"] for m in client.registered_models]
                    assert name in names, \
                        f"Model '{name}' not registered. Names: {names}"

        yield MLflowHelper()
```

### Usage Examples

```python
def test_cost_anomaly_training(mock_mlflow, sample_cost_features):
    """Test that cost anomaly model logs correctly to MLflow."""
    from src.ml.cost.train_cost_anomaly_detector import train_model

    # Train model
    model = train_model(sample_cost_features)

    # Verify MLflow logging
    mock_mlflow.assert_param_logged("model_type", "IsolationForest")
    mock_mlflow.assert_param_logged("n_estimators")
    mock_mlflow.assert_param_logged("contamination")

    mock_mlflow.assert_metric_logged("anomaly_rate", min_val=0, max_val=1)
    mock_mlflow.assert_metric_logged("training_samples")

    mock_mlflow.assert_model_logged("model")


def test_model_registration(mock_mlflow, sample_cost_features):
    """Test model is registered to Unity Catalog."""
    from src.ml.cost.train_cost_anomaly_detector import train_and_register

    # Train and register
    train_and_register(sample_cost_features, register=True)

    # Verify registration
    mock_mlflow.assert_model_registered("cost_anomaly_detector")
```

---

## Databricks SDK Mocking

### Overview

The Databricks SDK provides Python APIs for workspace operations, job management, and resource access. Mock for testing orchestration code.

```python
"""
tests/fixtures/sdk_mocks.py

Mock Databricks SDK client.
"""

from unittest.mock import MagicMock
from dataclasses import dataclass
from typing import List, Optional
import pytest


@dataclass
class MockJob:
    job_id: int
    name: str
    settings: dict


@dataclass
class MockCluster:
    cluster_id: str
    cluster_name: str
    state: str = "RUNNING"


class MockJobsAPI:
    """Mock for WorkspaceClient.jobs"""

    def __init__(self):
        self._jobs: List[MockJob] = []
        self._runs: dict = {}

    def list(self):
        return iter(self._jobs)

    def get(self, job_id: int):
        for job in self._jobs:
            if job.job_id == job_id:
                return job
        raise ValueError(f"Job {job_id} not found")

    def run_now(self, job_id: int, **kwargs):
        run_id = len(self._runs) + 1
        self._runs[run_id] = {"job_id": job_id, "state": "RUNNING"}
        result = MagicMock()
        result.result.return_value = MagicMock(
            state=MagicMock(result_state="SUCCESS")
        )
        return result

    # Test helpers
    def add_job(self, job_id: int, name: str, settings: dict = None):
        self._jobs.append(MockJob(job_id, name, settings or {}))


class MockClustersAPI:
    """Mock for WorkspaceClient.clusters"""

    def __init__(self):
        self._clusters: List[MockCluster] = []

    def list(self):
        return iter(self._clusters)

    def get(self, cluster_id: str):
        for cluster in self._clusters:
            if cluster.cluster_id == cluster_id:
                return cluster
        raise ValueError(f"Cluster {cluster_id} not found")


class MockWorkspaceClient:
    """Mock Databricks WorkspaceClient."""

    def __init__(self, host: str = None, token: str = None):
        self.jobs = MockJobsAPI()
        self.clusters = MockClustersAPI()
        self.workspace = MagicMock()
        self.sql = MagicMock()


@pytest.fixture
def mock_workspace_client():
    """Fixture providing mock WorkspaceClient."""
    return MockWorkspaceClient()
```

---

## Lakehouse Monitoring Mocking

```python
"""
tests/fixtures/monitoring_mocks.py

Mock Lakehouse Monitoring API.
"""

from unittest.mock import MagicMock
from typing import Dict, List, Optional
import pytest


class MockMonitorInfo:
    """Mock monitor info returned by get_monitor."""

    def __init__(
        self,
        table_name: str,
        status: str = "ACTIVE",
        output_schema_name: str = None,
    ):
        self.table_name = table_name
        self.status = status
        self.output_schema_name = output_schema_name or f"{table_name}_monitor"


class MockQualityMonitorsAPI:
    """Mock for lakeview.quality_monitors API."""

    def __init__(self):
        self._monitors: Dict[str, MockMonitorInfo] = {}

    def create(self, table_name: str, **kwargs) -> MockMonitorInfo:
        monitor = MockMonitorInfo(table_name, **kwargs)
        self._monitors[table_name] = monitor
        return monitor

    def get(self, table_name: str) -> MockMonitorInfo:
        if table_name not in self._monitors:
            raise ValueError(f"Monitor for {table_name} not found")
        return self._monitors[table_name]

    def update(self, table_name: str, **kwargs) -> MockMonitorInfo:
        if table_name not in self._monitors:
            raise ValueError(f"Monitor for {table_name} not found")
        # Update monitor settings
        return self._monitors[table_name]

    def delete(self, table_name: str) -> None:
        if table_name in self._monitors:
            del self._monitors[table_name]

    def run_refresh(self, table_name: str) -> dict:
        return {"status": "QUEUED"}


@pytest.fixture
def mock_quality_monitors():
    """Fixture providing mock quality monitors API."""
    return MockQualityMonitorsAPI()
```

---

## Best Practices

### 1. Mock at the Boundary

Mock external dependencies, not internal logic:

```python
# Good: Mock external API
with patch('databricks.sdk.WorkspaceClient') as mock_client:
    mock_client.return_value.jobs.list.return_value = [...]
    result = my_function()

# Bad: Mock internal functions
with patch('my_module.internal_helper'):  # Don't do this
    ...
```

### 2. Use Fixtures for Reusability

```python
# Good: Reusable fixture
@pytest.fixture
def sample_data(spark):
    return spark.createDataFrame([...])

def test_one(sample_data):
    ...

def test_two(sample_data):
    ...

# Bad: Duplicate setup
def test_one(spark):
    data = spark.createDataFrame([...])  # Repeated
    ...
```

### 3. Verify Mock Interactions

```python
def test_logging(mock_mlflow):
    run_training()

    # Good: Verify expected interactions
    mock_mlflow.assert_param_logged("model_type")
    mock_mlflow.assert_metric_logged("accuracy")

    # Better: Verify specific values
    mock_mlflow.assert_param_logged("n_estimators", 100)
```

### 4. Document Mock Limitations

```python
class MockDLT:
    """
    Mock DLT framework.

    Limitations:
    - Does not simulate streaming behavior
    - Expectations are recorded but not enforced
    - No checkpointing support
    """
```

### 5. Keep Mocks Simple

```python
# Good: Simple, focused mock
class MockDbutils:
    def __init__(self):
        self._widgets = {}

    class Widgets:
        def get(self, name): ...
        def text(self, name, default, label): ...

# Bad: Over-engineered mock with unused features
class MockDbutils:
    def __init__(self, config_file, validation_mode, ...):
        self._load_config(config_file)
        self._setup_validation(validation_mode)
        ...
```

---

*Document Version: 1.0*
*Last Updated: 2026-01-01*
