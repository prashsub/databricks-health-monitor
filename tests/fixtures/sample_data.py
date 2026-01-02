"""
Sample Data Fixtures
====================

Provides factory functions and pytest fixtures for generating
realistic test data that matches production schemas.

All data generation uses fixed random seeds for reproducibility.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
import uuid


# Set global random seed for reproducibility
np.random.seed(42)


class SampleDataFactory:
    """
    Factory class for generating test data.

    Provides methods to create DataFrames matching production schemas
    with configurable parameters for different test scenarios.
    """

    @staticmethod
    def create_usage_data(
        spark,
        num_days: int = 90,
        workspaces: List[str] = None,
        skus: List[str] = None,
        anomaly_rate: float = 0.05,
        seed: int = 42,
    ):
        """
        Generate sample fact_usage data.

        Args:
            spark: SparkSession
            num_days: Number of days of data to generate
            workspaces: List of workspace IDs (default: 3 workspaces)
            skus: List of SKU names (default: 4 SKUs)
            anomaly_rate: Fraction of records that are anomalies
            seed: Random seed for reproducibility

        Returns:
            DataFrame matching fact_usage schema
        """
        np.random.seed(seed)

        if workspaces is None:
            workspaces = ['ws_001', 'ws_002', 'ws_003']
        if skus is None:
            skus = ['JOBS_COMPUTE', 'SQL_COMPUTE', 'DLT_COMPUTE', 'ALL_PURPOSE_COMPUTE']

        dates = pd.date_range(end=datetime.now().date(), periods=num_days, freq='D')
        data = []

        for dt in dates:
            for ws in workspaces:
                for sku in skus:
                    # Base usage with some randomness
                    base_usage = np.random.uniform(10, 100)

                    # Add weekly seasonality (higher on weekdays)
                    if dt.weekday() < 5:
                        base_usage *= 1.5

                    # Add some anomalies
                    if np.random.random() < anomaly_rate:
                        base_usage *= np.random.uniform(3, 10)

                    data.append({
                        'record_id': f"{dt.strftime('%Y%m%d')}_{ws}_{sku}",
                        'workspace_id': ws,
                        'usage_date': dt.date(),
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

    @staticmethod
    def create_job_run_data(
        spark,
        num_jobs: int = 20,
        num_days: int = 30,
        runs_per_day_range: tuple = (2, 6),
        failure_rate: float = 0.30,
        seed: int = 42,
    ):
        """
        Generate sample fact_job_run_timeline data.

        Args:
            spark: SparkSession
            num_jobs: Number of unique jobs
            num_days: Number of days of data
            runs_per_day_range: (min, max) runs per job per day
            failure_rate: Approximate failure rate
            seed: Random seed

        Returns:
            DataFrame matching fact_job_run_timeline schema
        """
        np.random.seed(seed)

        start_date = datetime.now() - timedelta(days=num_days)
        jobs = [f'job_{i}' for i in range(1, num_jobs + 1)]

        # Weight result states by failure rate
        success_weight = 1 - failure_rate
        failure_weight = failure_rate / 3  # Split among FAILED, ERROR, TIMED_OUT
        result_states = ['SUCCEEDED', 'FAILED', 'ERROR', 'TIMED_OUT']
        weights = [success_weight, failure_weight, failure_weight, failure_weight]

        data = []
        for job_id in jobs:
            runs_per_day = np.random.randint(*runs_per_day_range)

            for day_offset in range(num_days):
                run_date = start_date + timedelta(days=day_offset)

                for _ in range(runs_per_day):
                    duration_minutes = np.random.uniform(5, 120)
                    period_start = run_date + timedelta(hours=np.random.randint(0, 24))
                    period_end = period_start + timedelta(minutes=duration_minutes)

                    result_state = np.random.choice(result_states, p=weights)

                    data.append({
                        'record_id': f"{job_id}_{period_start.strftime('%Y%m%d%H%M%S')}_{np.random.randint(1000, 9999)}",
                        'workspace_id': f'ws_{np.random.randint(1, 4):03d}',
                        'job_id': job_id,
                        'run_id': np.random.randint(100000, 999999),
                        'period_start_time': period_start,
                        'period_end_time': period_end,
                        'result_state': result_state,
                        'termination_code': 'SUCCESS' if result_state == 'SUCCEEDED' else 'FAILED',
                        'error_message': None if result_state == 'SUCCEEDED' else 'Sample error message',
                        'compute_ids_json': f'["{job_id}_cluster"]',
                        'run_page_url': f'https://databricks.com/jobs/{job_id}/runs/{np.random.randint(1000, 9999)}',
                        'bronze_ingestion_timestamp': datetime.now(),
                        'gold_merge_timestamp': datetime.now(),
                    })

        df = pd.DataFrame(data)
        return spark.createDataFrame(df)

    @staticmethod
    def create_query_history_data(
        spark,
        num_queries: int = 1000,
        warehouses: List[str] = None,
        users: List[str] = None,
        seed: int = 42,
    ):
        """
        Generate sample fact_query_history data.

        Args:
            spark: SparkSession
            num_queries: Number of queries to generate
            warehouses: List of warehouse IDs
            users: List of user emails
            seed: Random seed

        Returns:
            DataFrame matching fact_query_history schema
        """
        np.random.seed(seed)

        if warehouses is None:
            warehouses = ['warehouse_1', 'warehouse_2', 'warehouse_3']
        if users is None:
            users = ['user1@company.com', 'user2@company.com', 'user3@company.com']

        statement_types = ['SELECT', 'INSERT', 'MERGE', 'CREATE', 'DROP']
        statement_weights = [0.6, 0.2, 0.1, 0.05, 0.05]

        data = []
        for i in range(num_queries):
            # Exponential distribution for duration (most fast, some slow)
            duration_ms = np.random.exponential(10000)
            start_time = datetime.now() - timedelta(hours=np.random.randint(0, 720))

            data.append({
                'record_id': f'query_{i}',
                'workspace_id': f'ws_{np.random.randint(1, 4):03d}',
                'statement_id': f'stmt_{uuid.uuid4().hex[:12]}',
                'warehouse_id': np.random.choice(warehouses),
                'executed_by': np.random.choice(users),
                'statement_type': np.random.choice(statement_types, p=statement_weights),
                'statement_text': f'SELECT * FROM table_{np.random.randint(1, 100)}',
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

    @staticmethod
    def create_cost_features(
        num_samples: int = 500,
        seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generate sample cost features for ML model testing.

        Args:
            num_samples: Number of samples to generate
            seed: Random seed

        Returns:
            pandas DataFrame with cost features
        """
        np.random.seed(seed)

        data = {
            'feature_date': pd.date_range(end=datetime.now(), periods=num_samples, freq='D'),
            'workspace_id': [f'ws_{i % 3 + 1:03d}' for i in range(num_samples)],
            'daily_dbu': np.random.exponential(50, num_samples),
            'avg_dbu_7d': np.random.exponential(50, num_samples),
            'avg_dbu_30d': np.random.exponential(50, num_samples),
            'z_score_7d': np.random.normal(0, 1, num_samples),
            'z_score_30d': np.random.normal(0, 1, num_samples),
            'dbu_change_pct_1d': np.random.normal(0, 10, num_samples),
            'dbu_change_pct_7d': np.random.normal(0, 20, num_samples),
            'dow_sin': np.sin(2 * np.pi * np.arange(num_samples) / 7),
            'dow_cos': np.cos(2 * np.pi * np.arange(num_samples) / 7),
            'is_weekend': [1 if i % 7 >= 5 else 0 for i in range(num_samples)],
            'is_month_end': [1 if (i + 1) % 30 == 0 else 0 for i in range(num_samples)],
        }

        return pd.DataFrame(data)

    @staticmethod
    def create_job_features(
        num_samples: int = 500,
        failure_rate: float = 0.25,
        seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generate sample job features for failure prediction.

        Args:
            num_samples: Number of samples
            failure_rate: Target failure rate in labels
            seed: Random seed

        Returns:
            pandas DataFrame with job features
        """
        np.random.seed(seed)

        data = {
            'job_id': [f'job_{i % 50}' for i in range(num_samples)],
            'historical_failure_rate': np.random.uniform(0, 0.5, num_samples),
            'recent_failure_rate_7d': np.random.uniform(0, 0.5, num_samples),
            'consecutive_failures': np.random.randint(0, 5, num_samples),
            'avg_duration_minutes': np.random.exponential(30, num_samples),
            'duration_std_dev': np.random.exponential(10, num_samples),
            'task_count': np.random.randint(1, 10, num_samples),
            'worker_count': np.random.randint(1, 20, num_samples),
            'hour_of_day': np.random.randint(0, 24, num_samples),
            'day_of_week': np.random.randint(0, 7, num_samples),
            'is_failure': np.random.choice(
                [0, 1],
                num_samples,
                p=[1 - failure_rate, failure_rate]
            ),
        }

        return pd.DataFrame(data)

    @staticmethod
    def create_sku_dimension(spark):
        """Create sample dim_sku data."""
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
        return spark.createDataFrame(pd.DataFrame(data))

    @staticmethod
    def create_workspace_dimension(spark):
        """Create sample dim_workspace data."""
        data = [
            {'workspace_id': 'ws_001', 'workspace_name': 'Production',
             'cloud': 'AWS', 'region': 'us-west-2', 'is_current': True},
            {'workspace_id': 'ws_002', 'workspace_name': 'Development',
             'cloud': 'AWS', 'region': 'us-east-1', 'is_current': True},
            {'workspace_id': 'ws_003', 'workspace_name': 'Staging',
             'cloud': 'AWS', 'region': 'us-west-2', 'is_current': True},
        ]
        return spark.createDataFrame(pd.DataFrame(data))


# =============================================================================
# PYTEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_usage_data(spark):
    """
    Create sample fact_usage data for cost-related tests.

    Generates 90 days of usage data across 3 workspaces and 4 SKUs.
    Includes weekly seasonality and ~5% anomalies.
    """
    return SampleDataFactory.create_usage_data(spark)


@pytest.fixture
def sample_job_run_data(spark):
    """
    Create sample fact_job_run_timeline data for reliability tests.

    Generates 30 days of job runs for 20 jobs with ~30% failure rate.
    """
    return SampleDataFactory.create_job_run_data(spark)


@pytest.fixture
def sample_query_history_data(spark):
    """
    Create sample fact_query_history data for performance tests.

    Generates 1000 sample queries with exponential duration distribution.
    """
    return SampleDataFactory.create_query_history_data(spark)


@pytest.fixture
def sample_sku_data(spark):
    """Create sample dim_sku data for pricing lookups."""
    return SampleDataFactory.create_sku_dimension(spark)


@pytest.fixture
def sample_workspace_data(spark):
    """Create sample dim_workspace data."""
    return SampleDataFactory.create_workspace_dimension(spark)


@pytest.fixture
def sample_cost_features():
    """
    Create sample cost features DataFrame for ML model testing.

    Returns pandas DataFrame with 500 samples of cost features.
    """
    return SampleDataFactory.create_cost_features()


@pytest.fixture
def sample_job_features():
    """
    Create sample job features for failure prediction testing.

    Returns pandas DataFrame with 500 samples.
    """
    return SampleDataFactory.create_job_features()


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


@pytest.fixture
def sample_data_factory():
    """Provide direct access to SampleDataFactory."""
    return SampleDataFactory
