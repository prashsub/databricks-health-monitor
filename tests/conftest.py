"""
Pytest Configuration and Fixtures
==================================

This module provides shared fixtures for testing Databricks notebooks and
PySpark code locally without requiring a Databricks cluster.

Key fixtures:
- spark: Local SparkSession for testing
- mock_dbutils: Mock dbutils for widget parameters
- sample_gold_tables: Pre-populated DataFrames mimicking Gold layer
- mock_mlflow: MLflow mocking for model tests
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# =============================================================================
# SPARK SESSION FIXTURE
# =============================================================================

@pytest.fixture(scope="session")
def spark():
    """
    Create a local SparkSession for testing.

    Uses 'local[2]' to simulate parallelism while keeping tests fast.
    Session is shared across all tests in the session.
    """
    try:
        from pyspark.sql import SparkSession

        spark = (
            SparkSession.builder
            .master("local[2]")
            .appName("HealthMonitorTests")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.default.parallelism", "2")
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .config("spark.driver.memory", "2g")
            .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse-test")
            .getOrCreate()
        )

        yield spark

        spark.stop()
    except ImportError:
        pytest.skip("PySpark not installed")


# =============================================================================
# DBUTILS MOCK FIXTURE
# =============================================================================

class MockDbutils:
    """
    Mock implementation of Databricks dbutils.

    Provides widgets for parameter handling in notebooks.
    """

    def __init__(self):
        self._widgets = {}
        self._exit_value = None

        # Default widget values for testing
        self._widgets = {
            "catalog": "test_catalog",
            "gold_schema": "system_gold",
            "feature_schema": "system_gold_ml",
            "bronze_schema": "system_bronze",
        }

    class Widgets:
        def __init__(self, parent):
            self._parent = parent

        def get(self, name: str) -> str:
            if name not in self._parent._widgets:
                raise ValueError(f"Widget '{name}' not found")
            return self._parent._widgets[name]

        def text(self, name: str, default: str, label: str = ""):
            self._parent._widgets[name] = default

    class Notebook:
        def __init__(self, parent):
            self._parent = parent

        def exit(self, value: str):
            self._parent._exit_value = value

    @property
    def widgets(self):
        return self.Widgets(self)

    @property
    def notebook(self):
        return self.Notebook(self)


@pytest.fixture
def mock_dbutils():
    """Provide a mock dbutils instance."""
    return MockDbutils()


@pytest.fixture
def patch_dbutils(mock_dbutils):
    """
    Patch dbutils into builtins for notebook execution.

    This allows notebooks to use dbutils.widgets.get() without modification.
    """
    import builtins
    original = getattr(builtins, 'dbutils', None)
    builtins.dbutils = mock_dbutils
    yield mock_dbutils
    if original is not None:
        builtins.dbutils = original
    else:
        delattr(builtins, 'dbutils')


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_usage_data(spark):
    """
    Create sample fact_usage data for cost-related tests.

    Mimics the Gold layer fact_usage table structure.
    """
    # Generate 90 days of usage data
    dates = pd.date_range(end=datetime.now().date(), periods=90, freq='D')

    data = []
    workspaces = ['ws_001', 'ws_002', 'ws_003']
    skus = ['JOBS_COMPUTE', 'SQL_COMPUTE', 'DLT_COMPUTE', 'ALL_PURPOSE_COMPUTE']

    for date in dates:
        for ws in workspaces:
            for sku in skus:
                # Base usage with some randomness
                base_usage = np.random.uniform(10, 100)

                # Add weekly seasonality (higher on weekdays)
                if date.weekday() < 5:
                    base_usage *= 1.5

                # Add some anomalies (~5%)
                if np.random.random() < 0.05:
                    base_usage *= np.random.uniform(3, 10)

                data.append({
                    'record_id': f"{date.strftime('%Y%m%d')}_{ws}_{sku}",
                    'workspace_id': ws,
                    'usage_date': date.date(),
                    'sku_name': sku,
                    'usage_quantity': round(base_usage, 2),
                    'usage_unit': 'DBU',
                    'usage_metadata_cluster_id': f"cluster_{np.random.randint(1, 10)}",
                    'usage_metadata_job_id': f"job_{np.random.randint(1, 50)}",
                    'usage_metadata_warehouse_id': f"warehouse_{np.random.randint(1, 5)}",
                    'custom_tags': {'team': 'data_eng', 'env': 'prod'},
                    'is_tagged': True,
                    'tag_count': 2,
                    'bronze_ingestion_timestamp': datetime.now(),
                    'gold_merge_timestamp': datetime.now(),
                })

    df = pd.DataFrame(data)
    return spark.createDataFrame(df)


@pytest.fixture
def sample_job_run_data(spark):
    """
    Create sample fact_job_run_timeline data for reliability tests.

    Mimics the Gold layer fact_job_run_timeline table structure.
    """
    # Generate 30 days of job runs
    start_date = datetime.now() - timedelta(days=30)

    data = []
    jobs = [f'job_{i}' for i in range(1, 21)]
    result_states = ['SUCCEEDED', 'SUCCEEDED', 'SUCCEEDED', 'SUCCEEDED',
                     'FAILED', 'ERROR', 'TIMED_OUT']  # ~30% failure rate

    for job_id in jobs:
        # Each job runs 2-5 times per day
        runs_per_day = np.random.randint(2, 6)

        for day_offset in range(30):
            run_date = start_date + timedelta(days=day_offset)

            for run_num in range(runs_per_day):
                duration_minutes = np.random.uniform(5, 120)
                period_start = run_date + timedelta(hours=np.random.randint(0, 24))
                period_end = period_start + timedelta(minutes=duration_minutes)

                result_state = np.random.choice(result_states)

                data.append({
                    'record_id': f"{job_id}_{period_start.strftime('%Y%m%d%H%M%S')}",
                    'workspace_id': f'ws_{np.random.randint(1, 4):03d}',
                    'job_id': job_id,
                    'run_id': np.random.randint(100000, 999999),
                    'period_start_time': period_start,
                    'period_end_time': period_end,
                    'result_state': result_state,
                    'termination_code': 'SUCCESS' if result_state == 'SUCCEEDED' else 'FAILED',
                    'error_message': None if result_state == 'SUCCEEDED' else 'Sample error',
                    'compute_ids_json': f'["{job_id}_cluster"]',
                    'run_page_url': f'https://databricks.com/jobs/{job_id}/runs/123',
                    'bronze_ingestion_timestamp': datetime.now(),
                    'gold_merge_timestamp': datetime.now(),
                })

    df = pd.DataFrame(data)
    return spark.createDataFrame(df)


@pytest.fixture
def sample_query_history_data(spark):
    """
    Create sample fact_query_history data for performance tests.
    """
    data = []
    warehouses = ['warehouse_1', 'warehouse_2', 'warehouse_3']
    users = ['user1@company.com', 'user2@company.com', 'user3@company.com']
    statement_types = ['SELECT', 'INSERT', 'MERGE', 'CREATE']

    for i in range(1000):
        duration_ms = np.random.exponential(10000)  # Most queries fast, some slow
        start_time = datetime.now() - timedelta(hours=np.random.randint(0, 720))

        data.append({
            'record_id': f'query_{i}',
            'workspace_id': f'ws_{np.random.randint(1, 4):03d}',
            'statement_id': f'stmt_{i}',
            'warehouse_id': np.random.choice(warehouses),
            'executed_by': np.random.choice(users),
            'statement_type': np.random.choice(statement_types),
            'start_time': start_time,
            'end_time': start_time + timedelta(milliseconds=duration_ms),
            'duration_ms': int(duration_ms),
            'read_bytes': np.random.randint(1000, 10000000),
            'read_rows': np.random.randint(100, 1000000),
            'produced_rows': np.random.randint(1, 10000),
            'spilled_local_bytes': np.random.randint(0, 1000000),
            'status': 'FINISHED',
            'error_message': None,
            'bronze_ingestion_timestamp': datetime.now(),
            'gold_merge_timestamp': datetime.now(),
        })

    df = pd.DataFrame(data)
    return spark.createDataFrame(df)


@pytest.fixture
def sample_sku_data(spark):
    """Create sample dim_sku data for pricing lookups."""
    data = [
        {'sku_name': 'JOBS_COMPUTE', 'sku_id': 'sku_001', 'list_price': 0.15,
         'pricing_unit': 'DBU', 'is_current': True},
        {'sku_name': 'SQL_COMPUTE', 'sku_id': 'sku_002', 'list_price': 0.22,
         'pricing_unit': 'DBU', 'is_current': True},
        {'sku_name': 'DLT_COMPUTE', 'sku_id': 'sku_003', 'list_price': 0.20,
         'pricing_unit': 'DBU', 'is_current': True},
        {'sku_name': 'ALL_PURPOSE_COMPUTE', 'sku_id': 'sku_004', 'list_price': 0.40,
         'pricing_unit': 'DBU', 'is_current': True},
    ]
    df = pd.DataFrame(data)
    return spark.createDataFrame(df)


@pytest.fixture
def sample_workspace_data(spark):
    """Create sample dim_workspace data."""
    data = [
        {'workspace_id': 'ws_001', 'workspace_name': 'Production',
         'cloud': 'AWS', 'region': 'us-west-2', 'is_current': True},
        {'workspace_id': 'ws_002', 'workspace_name': 'Development',
         'cloud': 'AWS', 'region': 'us-east-1', 'is_current': True},
        {'workspace_id': 'ws_003', 'workspace_name': 'Staging',
         'cloud': 'AWS', 'region': 'us-west-2', 'is_current': True},
    ]
    df = pd.DataFrame(data)
    return spark.createDataFrame(df)


# =============================================================================
# MLFLOW MOCKING FIXTURES
# =============================================================================

@pytest.fixture
def mock_mlflow():
    """
    Create a mock MLflow client for testing model training.

    Avoids actual MLflow calls during unit tests.
    """
    with patch('mlflow.set_registry_uri') as mock_registry, \
         patch('mlflow.set_experiment') as mock_experiment, \
         patch('mlflow.start_run') as mock_run, \
         patch('mlflow.log_params') as mock_params, \
         patch('mlflow.log_metrics') as mock_metrics, \
         patch('mlflow.set_tags') as mock_tags, \
         patch('mlflow.sklearn.log_model') as mock_log_model, \
         patch('mlflow.log_input') as mock_log_input, \
         patch('mlflow.autolog') as mock_autolog:

        # Configure mock experiment
        mock_exp = MagicMock()
        mock_exp.experiment_id = "test_experiment_id"
        mock_experiment.return_value = mock_exp

        # Configure mock run
        mock_run_context = MagicMock()
        mock_run_context.info.run_id = "test_run_id"
        mock_run.return_value.__enter__ = MagicMock(return_value=mock_run_context)
        mock_run.return_value.__exit__ = MagicMock(return_value=False)

        yield {
            'set_registry_uri': mock_registry,
            'set_experiment': mock_experiment,
            'start_run': mock_run,
            'log_params': mock_params,
            'log_metrics': mock_metrics,
            'set_tags': mock_tags,
            'log_model': mock_log_model,
            'log_input': mock_log_input,
            'autolog': mock_autolog,
        }


# =============================================================================
# FEATURE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_cost_features():
    """
    Create sample cost features DataFrame for ML model testing.

    These features match the expected schema from create_feature_tables.py
    """
    np.random.seed(42)
    n_samples = 500

    data = {
        'feature_date': pd.date_range(end=datetime.now(), periods=n_samples, freq='D'),
        'workspace_id': [f'ws_{i % 3 + 1:03d}' for i in range(n_samples)],
        'daily_dbu': np.random.exponential(50, n_samples),
        'avg_dbu_7d': np.random.exponential(50, n_samples),
        'avg_dbu_30d': np.random.exponential(50, n_samples),
        'z_score_7d': np.random.normal(0, 1, n_samples),
        'z_score_30d': np.random.normal(0, 1, n_samples),
        'dbu_change_pct_1d': np.random.normal(0, 10, n_samples),
        'dbu_change_pct_7d': np.random.normal(0, 20, n_samples),
        'dow_sin': np.sin(2 * np.pi * np.arange(n_samples) / 7),
        'dow_cos': np.cos(2 * np.pi * np.arange(n_samples) / 7),
        'is_weekend': [1 if i % 7 >= 5 else 0 for i in range(n_samples)],
        'is_month_end': [1 if (i + 1) % 30 == 0 else 0 for i in range(n_samples)],
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_job_features():
    """Create sample job features for failure prediction testing."""
    np.random.seed(42)
    n_samples = 500

    data = {
        'job_id': [f'job_{i % 50}' for i in range(n_samples)],
        'historical_failure_rate': np.random.uniform(0, 0.5, n_samples),
        'recent_failure_rate_7d': np.random.uniform(0, 0.5, n_samples),
        'consecutive_failures': np.random.randint(0, 5, n_samples),
        'avg_duration_minutes': np.random.exponential(30, n_samples),
        'duration_std_dev': np.random.exponential(10, n_samples),
        'task_count': np.random.randint(1, 10, n_samples),
        'worker_count': np.random.randint(1, 20, n_samples),
        'hour_of_day': np.random.randint(0, 24, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'is_failure': np.random.choice([0, 0, 0, 1], n_samples),  # 25% failure rate
    }

    return pd.DataFrame(data)


# =============================================================================
# SQL TESTING UTILITIES
# =============================================================================

@pytest.fixture
def create_temp_tables(spark, sample_usage_data, sample_job_run_data,
                       sample_sku_data, sample_workspace_data):
    """
    Create temporary views for SQL-based tests.

    This allows testing TVFs and SQL queries against realistic data.
    """
    sample_usage_data.createOrReplaceTempView("fact_usage")
    sample_job_run_data.createOrReplaceTempView("fact_job_run_timeline")
    sample_sku_data.createOrReplaceTempView("dim_sku")
    sample_workspace_data.createOrReplaceTempView("dim_workspace")

    yield

    # Cleanup
    spark.catalog.dropTempView("fact_usage")
    spark.catalog.dropTempView("fact_job_run_timeline")
    spark.catalog.dropTempView("dim_sku")
    spark.catalog.dropTempView("dim_workspace")


# =============================================================================
# ASSERTION HELPERS
# =============================================================================

def assert_dataframe_equal(df1, df2, check_order=False):
    """
    Assert two PySpark DataFrames are equal.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        check_order: Whether row order matters
    """
    from chispa import assert_df_equality
    assert_df_equality(df1, df2, ignore_row_order=not check_order)


def assert_schema_equal(df1, df2):
    """Assert two DataFrames have the same schema."""
    assert df1.schema == df2.schema, f"Schemas differ:\n{df1.schema}\nvs\n{df2.schema}"


def assert_column_exists(df, column_name):
    """Assert a column exists in the DataFrame."""
    assert column_name in df.columns, f"Column '{column_name}' not found in {df.columns}"


def assert_no_nulls(df, column_name):
    """Assert no null values in a column."""
    null_count = df.filter(df[column_name].isNull()).count()
    assert null_count == 0, f"Found {null_count} nulls in column '{column_name}'"
