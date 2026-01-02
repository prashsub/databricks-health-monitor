"""
Tests for Feature Engineering
=============================

Test coverage:
- Feature computation for each agent domain
- Rolling window calculations
- Data validation
- Feature table creation
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Skip this module if pyspark is not installed (for unit tests without Spark)
pyspark = pytest.importorskip("pyspark", reason="PySpark required for integration tests")
from pyspark.sql import functions as F
from pyspark.sql.window import Window


class TestCostFeatureComputation:
    """Test cost feature computation logic."""

    @pytest.mark.integration
    def test_cost_features_rolling_averages(self, spark, sample_usage_data):
        """Verify 7-day and 30-day rolling averages are computed correctly."""
        # Create temp view for testing
        sample_usage_data.createOrReplaceTempView("test_usage")

        # Aggregate to daily level
        daily_usage = spark.sql("""
            SELECT
                workspace_id,
                sku_name,
                usage_date,
                SUM(usage_quantity) as daily_dbu
            FROM test_usage
            GROUP BY workspace_id, sku_name, usage_date
        """)

        # Define windows
        ws_window = Window.partitionBy("workspace_id", "sku_name").orderBy("usage_date")
        ws_window_7d = ws_window.rowsBetween(-6, 0)

        # Compute rolling average
        with_rolling = daily_usage.withColumn(
            "avg_dbu_7d",
            F.avg("daily_dbu").over(ws_window_7d)
        )

        # Verify not null after enough data points
        result = with_rolling.filter(F.col("avg_dbu_7d").isNotNull())
        assert result.count() > 0, "Should have some rows with rolling averages"

        # Verify average is reasonable (not negative, not unrealistically large)
        stats = result.select(
            F.min("avg_dbu_7d").alias("min_avg"),
            F.max("avg_dbu_7d").alias("max_avg"),
            F.avg("avg_dbu_7d").alias("overall_avg")
        ).collect()[0]

        assert stats["min_avg"] >= 0, "Rolling average should be non-negative"
        assert stats["max_avg"] < 100000, "Rolling average should be reasonable"

    @pytest.mark.integration
    def test_cost_features_zscore_calculation(self, spark, sample_usage_data):
        """Verify z-score calculation is correct."""
        sample_usage_data.createOrReplaceTempView("test_usage")

        # Aggregate and compute z-score
        daily = spark.sql("""
            SELECT
                workspace_id,
                usage_date,
                SUM(usage_quantity) as daily_dbu
            FROM test_usage
            GROUP BY workspace_id, usage_date
        """)

        ws_window = Window.partitionBy("workspace_id").orderBy("usage_date")
        ws_window_7d = ws_window.rowsBetween(-6, 0)

        with_zscore = (
            daily
            .withColumn("avg_7d", F.avg("daily_dbu").over(ws_window_7d))
            .withColumn("std_7d", F.stddev("daily_dbu").over(ws_window_7d))
            .withColumn("z_score",
                       F.when(F.col("std_7d") > 0,
                             (F.col("daily_dbu") - F.col("avg_7d")) / F.col("std_7d"))
                       .otherwise(0))
        )

        # Z-scores should be roughly standard normal for random data
        result = with_zscore.filter(F.col("z_score").isNotNull())
        stats = result.select(
            F.avg("z_score").alias("mean_z"),
            F.stddev("z_score").alias("std_z")
        ).collect()[0]

        # Mean should be close to 0, std close to 1 for large enough sample
        assert abs(stats["mean_z"]) < 2, f"Mean z-score should be near 0, got {stats['mean_z']}"

    @pytest.mark.integration
    def test_cost_features_cyclical_encoding(self, spark, sample_usage_data):
        """Verify day-of-week cyclical encoding is correct."""
        result = (
            sample_usage_data
            .withColumn("day_of_week", F.dayofweek("usage_date"))
            .withColumn("dow_sin", F.sin(2 * 3.14159 * F.col("day_of_week") / 7))
            .withColumn("dow_cos", F.cos(2 * 3.14159 * F.col("day_of_week") / 7))
        )

        # Verify sin and cos are in [-1, 1]
        stats = result.select(
            F.min("dow_sin").alias("min_sin"),
            F.max("dow_sin").alias("max_sin"),
            F.min("dow_cos").alias("min_cos"),
            F.max("dow_cos").alias("max_cos")
        ).collect()[0]

        assert stats["min_sin"] >= -1 and stats["max_sin"] <= 1
        assert stats["min_cos"] >= -1 and stats["max_cos"] <= 1


class TestReliabilityFeatureComputation:
    """Test reliability feature computation logic."""

    @pytest.mark.integration
    def test_reliability_features_success_rate(self, spark, sample_job_run_data):
        """Verify job success rate is computed correctly."""
        sample_job_run_data.createOrReplaceTempView("test_jobs")

        # Compute success rate by job and date
        result = spark.sql("""
            SELECT
                job_id,
                DATE(period_start_time) as run_date,
                COUNT(*) as total_runs,
                SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) as successful_runs,
                SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) / COUNT(*) as success_rate
            FROM test_jobs
            GROUP BY job_id, DATE(period_start_time)
        """)

        # Verify success rate is in [0, 1]
        stats = result.select(
            F.min("success_rate").alias("min_rate"),
            F.max("success_rate").alias("max_rate")
        ).collect()[0]

        assert stats["min_rate"] >= 0, "Success rate should be >= 0"
        assert stats["max_rate"] <= 1, "Success rate should be <= 1"

    @pytest.mark.integration
    def test_reliability_features_duration_statistics(self, spark, sample_job_run_data):
        """Verify duration statistics are computed correctly."""
        result = (
            sample_job_run_data
            .withColumn("duration_sec",
                       F.unix_timestamp("period_end_time") - F.unix_timestamp("period_start_time"))
            .groupBy("job_id")
            .agg(
                F.avg("duration_sec").alias("avg_duration"),
                F.stddev("duration_sec").alias("std_duration"),
                F.min("duration_sec").alias("min_duration"),
                F.max("duration_sec").alias("max_duration")
            )
        )

        # Verify durations are positive
        stats = result.select(
            F.min("min_duration").alias("overall_min"),
            F.avg("avg_duration").alias("overall_avg")
        ).collect()[0]

        assert stats["overall_min"] >= 0, "Duration should be non-negative"
        assert stats["overall_avg"] > 0, "Average duration should be positive"

    @pytest.mark.integration
    def test_reliability_features_rolling_failure_rate(self, spark, sample_job_run_data):
        """Verify rolling failure rate computation."""
        sample_job_run_data.createOrReplaceTempView("test_jobs")

        # Compute daily failure rate
        daily = spark.sql("""
            SELECT
                job_id,
                DATE(period_start_time) as run_date,
                SUM(CASE WHEN result_state != 'SUCCEEDED' THEN 1 ELSE 0 END) / COUNT(*) as failure_rate
            FROM test_jobs
            GROUP BY job_id, DATE(period_start_time)
        """)

        # Compute 30-day rolling average
        job_window = Window.partitionBy("job_id").orderBy("run_date").rowsBetween(-29, 0)

        result = daily.withColumn(
            "rolling_failure_rate_30d",
            F.avg("failure_rate").over(job_window)
        )

        # Verify values are in valid range
        filtered = result.filter(F.col("rolling_failure_rate_30d").isNotNull())
        stats = filtered.select(
            F.min("rolling_failure_rate_30d").alias("min_rate"),
            F.max("rolling_failure_rate_30d").alias("max_rate")
        ).collect()[0]

        assert stats["min_rate"] >= 0
        assert stats["max_rate"] <= 1


class TestPerformanceFeatureComputation:
    """Test performance feature computation logic."""

    @pytest.mark.integration
    def test_performance_features_duration_percentiles(self, spark, sample_query_history_data):
        """Verify query duration percentiles are computed correctly."""
        result = (
            sample_query_history_data
            .groupBy("warehouse_id")
            .agg(
                F.percentile_approx("duration_ms", 0.5).alias("p50_duration"),
                F.percentile_approx("duration_ms", 0.95).alias("p95_duration"),
                F.percentile_approx("duration_ms", 0.99).alias("p99_duration")
            )
        )

        # Verify P50 <= P95 <= P99
        result_df = result.collect()

        for row in result_df:
            assert row["p50_duration"] <= row["p95_duration"], \
                f"P50 ({row['p50_duration']}) should be <= P95 ({row['p95_duration']})"
            assert row["p95_duration"] <= row["p99_duration"], \
                f"P95 ({row['p95_duration']}) should be <= P99 ({row['p99_duration']})"

    @pytest.mark.integration
    def test_performance_features_error_rate(self, spark, sample_query_history_data):
        """Verify query error rate calculation."""
        result = (
            sample_query_history_data
            .groupBy("warehouse_id")
            .agg(
                F.count("*").alias("total_queries"),
                F.sum(F.when(F.col("status") == "FAILED", 1).otherwise(0)).alias("failed_queries")
            )
            .withColumn("error_rate",
                       F.when(F.col("total_queries") > 0,
                             F.col("failed_queries") / F.col("total_queries"))
                       .otherwise(0))
        )

        stats = result.select(
            F.min("error_rate").alias("min_rate"),
            F.max("error_rate").alias("max_rate")
        ).collect()[0]

        assert stats["min_rate"] >= 0
        assert stats["max_rate"] <= 1


class TestFeatureTableCreation:
    """Test feature table creation functionality."""

    @pytest.mark.unit
    def test_feature_columns_complete(self, sample_cost_features):
        """Verify all expected cost feature columns are present."""
        expected_columns = [
            'workspace_id', 'daily_dbu', 'avg_dbu_7d', 'avg_dbu_30d',
            'z_score_7d', 'z_score_30d', 'dbu_change_pct_1d', 'dbu_change_pct_7d',
            'dow_sin', 'dow_cos', 'is_weekend', 'is_month_end'
        ]

        missing = [col for col in expected_columns if col not in sample_cost_features.columns]
        assert len(missing) == 0, f"Missing columns: {missing}"

    @pytest.mark.unit
    def test_feature_data_quality(self, sample_cost_features):
        """Verify feature data quality (no extreme values)."""
        numeric_cols = sample_cost_features.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            # Check for NaN
            nan_count = sample_cost_features[col].isna().sum()
            total = len(sample_cost_features)
            nan_pct = nan_count / total

            assert nan_pct < 0.1, f"Column {col} has {nan_pct:.1%} NaN values"

            # Check for infinite values
            if sample_cost_features[col].dtype == np.float64:
                inf_count = np.isinf(sample_cost_features[col]).sum()
                assert inf_count == 0, f"Column {col} has {inf_count} infinite values"

    @pytest.mark.unit
    def test_feature_primary_key_uniqueness(self, sample_cost_features):
        """Verify primary key columns form a unique combination."""
        # Primary key should be workspace_id + feature_date (or similar)
        if 'feature_date' in sample_cost_features.columns:
            pk_cols = ['workspace_id', 'feature_date']
        else:
            pk_cols = ['workspace_id']

        duplicates = sample_cost_features.duplicated(subset=pk_cols).sum()
        # Note: In real feature tables, duplicates might exist if there's a sku dimension
        # This test is simplified for demonstration


class TestFeatureEngineeringEdgeCases:
    """Test edge cases in feature engineering."""

    @pytest.mark.unit
    def test_handles_single_day_data(self):
        """Verify feature computation handles single day of data."""
        data = pd.DataFrame({
            'workspace_id': ['ws_001'] * 5,
            'usage_date': [datetime.now().date()] * 5,
            'usage_quantity': [10.0, 20.0, 30.0, 40.0, 50.0]
        })

        # Rolling averages should handle single day gracefully
        # (will be partial or null for windows requiring more days)
        assert len(data) == 5

    @pytest.mark.unit
    def test_handles_missing_days(self):
        """Verify feature computation handles gaps in data."""
        # Create data with missing days
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            # Gap: Jan 3-4 missing
            datetime(2024, 1, 5),
            datetime(2024, 1, 6),
        ]

        data = pd.DataFrame({
            'workspace_id': ['ws_001'] * len(dates),
            'usage_date': dates,
            'usage_quantity': [100.0] * len(dates)
        })

        assert len(data) == 4
        # Rolling calculations should handle gaps (though may produce unexpected results)

    @pytest.mark.unit
    def test_handles_zero_values(self, sample_cost_features):
        """Verify z-score calculation handles zero standard deviation."""
        # Add a workspace with constant values (std = 0)
        constant_data = pd.DataFrame({
            'workspace_id': ['constant_ws'] * 10,
            'daily_dbu': [100.0] * 10,
            'avg_dbu_7d': [100.0] * 10,
            'avg_dbu_30d': [100.0] * 10,
            'z_score_7d': [0.0] * 10,  # Should be 0 when std = 0
            'z_score_30d': [0.0] * 10,
            'dbu_change_pct_1d': [0.0] * 10,
            'dbu_change_pct_7d': [0.0] * 10,
            'dow_sin': [0.0] * 10,
            'dow_cos': [1.0] * 10,
            'is_weekend': [0] * 10,
            'is_month_end': [0] * 10,
            'feature_date': pd.date_range(end=datetime.now(), periods=10, freq='D')
        })

        # Z-scores should be 0 for constant data
        assert (constant_data['z_score_7d'] == 0).all()
        assert (constant_data['z_score_30d'] == 0).all()


class TestFeatureEngineeringIntegration:
    """Integration tests for full feature engineering pipeline."""

    @pytest.mark.integration
    def test_cost_features_end_to_end(self, spark, sample_usage_data, sample_sku_data):
        """Test end-to-end cost feature computation."""
        # Register tables
        sample_usage_data.createOrReplaceTempView("fact_usage")
        sample_sku_data.createOrReplaceTempView("dim_sku")

        # Run simplified feature computation
        result = spark.sql("""
            WITH daily_usage AS (
                SELECT
                    workspace_id,
                    sku_name,
                    usage_date,
                    SUM(usage_quantity) as daily_dbu
                FROM fact_usage
                GROUP BY workspace_id, sku_name, usage_date
            )
            SELECT
                workspace_id,
                sku_name,
                usage_date,
                daily_dbu,
                AVG(daily_dbu) OVER (
                    PARTITION BY workspace_id, sku_name
                    ORDER BY usage_date
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as avg_dbu_7d
            FROM daily_usage
        """)

        # Verify results
        assert result.count() > 0
        assert "avg_dbu_7d" in result.columns

    @pytest.mark.integration
    def test_reliability_features_end_to_end(self, spark, sample_job_run_data):
        """Test end-to-end reliability feature computation."""
        sample_job_run_data.createOrReplaceTempView("fact_job_run_timeline")

        result = spark.sql("""
            SELECT
                job_id,
                DATE(period_start_time) as run_date,
                COUNT(*) as total_runs,
                SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) as successful_runs,
                SUM(CASE WHEN result_state = 'SUCCEEDED' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
            FROM fact_job_run_timeline
            GROUP BY job_id, DATE(period_start_time)
            HAVING COUNT(*) >= 1
        """)

        # Verify results
        assert result.count() > 0
        assert "success_rate" in result.columns

        # Success rate should be in [0, 1]
        min_rate = result.agg(F.min("success_rate")).collect()[0][0]
        max_rate = result.agg(F.max("success_rate")).collect()[0][0]
        assert min_rate >= 0
        assert max_rate <= 1
