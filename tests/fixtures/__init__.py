"""
Test Fixtures Package
=====================

This package provides comprehensive fixtures for testing Databricks notebooks
and PySpark code locally without requiring Databricks cluster access.

Modules:
- spark_fixtures: SparkSession management
- databricks_mocks: dbutils, Unity Catalog mocks
- dlt_mocks: Delta Live Tables mock framework
- mlflow_mocks: MLflow experiment and model registry mocks
- sample_data: Test data factories
- assertion_helpers: Custom assertion utilities
"""

from tests.fixtures.spark_fixtures import spark, spark_session
from tests.fixtures.databricks_mocks import (
    MockDbutils,
    MockWidgets,
    MockNotebook,
    MockFs,
    MockSecrets,
    mock_dbutils,
    patch_dbutils,
)
from tests.fixtures.sample_data import (
    sample_usage_data,
    sample_job_run_data,
    sample_query_history_data,
    sample_cost_features,
    sample_job_features,
    SampleDataFactory,
)
from tests.fixtures.assertion_helpers import (
    assert_dataframe_equal,
    assert_schema_equal,
    assert_column_exists,
    assert_no_nulls,
    assert_row_count,
    assert_column_values_in_range,
)

__all__ = [
    # Spark
    "spark",
    "spark_session",
    # Databricks mocks
    "MockDbutils",
    "MockWidgets",
    "MockNotebook",
    "MockFs",
    "MockSecrets",
    "mock_dbutils",
    "patch_dbutils",
    # Sample data
    "sample_usage_data",
    "sample_job_run_data",
    "sample_query_history_data",
    "sample_cost_features",
    "sample_job_features",
    "SampleDataFactory",
    # Assertions
    "assert_dataframe_equal",
    "assert_schema_equal",
    "assert_column_exists",
    "assert_no_nulls",
    "assert_row_count",
    "assert_column_values_in_range",
]
