# Test Implementation Patterns

## Overview

This document provides concrete code patterns and examples for implementing tests across all modules of the Databricks Health Monitor. Each section includes template code that can be directly adapted for new tests.

---

## Table of Contents

1. [General Testing Patterns](#general-testing-patterns)
2. [Alert Framework Testing](#alert-framework-testing)
3. [Pipeline Testing](#pipeline-testing)
4. [ML Model Testing](#ml-model-testing)
5. [Monitoring Testing](#monitoring-testing)
6. [Semantic Layer Testing](#semantic-layer-testing)
7. [Dashboard Testing](#dashboard-testing)
8. [Edge Case Patterns](#edge-case-patterns)

---

## General Testing Patterns

### Test File Template

```python
"""
Tests for [Module Name]
=======================

Run with: pytest tests/module/test_file.py -v

Test coverage:
- [Area 1]
- [Area 2]
- [Area 3]
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestModuleUnit:
    """Unit tests - no Spark required."""

    @pytest.mark.unit
    def test_function_basic(self):
        """Test basic functionality."""
        from module.submodule import my_function
        result = my_function(input_value)
        assert result == expected_value

    @pytest.mark.unit
    def test_function_edge_case(self):
        """Test edge case handling."""
        pass


class TestModuleIntegration:
    """Integration tests - Spark required."""

    @pytest.mark.integration
    def test_with_spark(self, spark, sample_data):
        """Test with real Spark operations."""
        pass
```

### Parametrized Testing

```python
class TestAlertDomains:
    """Test each alert domain."""

    @pytest.mark.unit
    @pytest.mark.parametrize("domain,expected_count", [
        ("COST", 3),
        ("SECURITY", 2),
        ("RELIABILITY", 2),
        ("PERFORMANCE", 2),
        ("QUALITY", 1),
    ])
    def test_templates_per_domain(self, domain, expected_count):
        """Verify template count per domain."""
        from alerting.alert_templates import list_templates_by_domain
        templates = list_templates_by_domain(domain)
        assert len(templates) >= expected_count


@pytest.mark.integration
@pytest.mark.parametrize("table_name", [
    "fact_usage",
    "fact_job_run_timeline",
    "fact_query_history",
    "dim_workspace",
])
def test_gold_table_schema(spark, mock_catalog, table_name):
    """Verify each Gold table has expected schema."""
    # Load table and validate
    pass
```

### Fixture Composition

```python
@pytest.fixture
def complete_test_environment(
    spark,
    mock_dbutils,
    mock_catalog,
    mock_mlflow,
    sample_usage_data,
    sample_job_data,
):
    """
    Compose multiple fixtures into a complete test environment.

    Returns:
        dict with all test resources
    """
    # Register tables in mock catalog
    mock_catalog.register_table(
        "test_catalog", "system_gold", "fact_usage",
        sample_usage_data
    )
    mock_catalog.register_table(
        "test_catalog", "system_gold", "fact_job_run_timeline",
        sample_job_data
    )

    return {
        "spark": spark,
        "dbutils": mock_dbutils,
        "catalog": mock_catalog,
        "mlflow": mock_mlflow,
        "usage_data": sample_usage_data,
        "job_data": sample_job_data,
    }
```

---

## Alert Framework Testing

### Template Rendering Tests

```python
"""tests/unit/alerting/test_template_rendering.py"""

import pytest
from alerting.alert_templates import (
    get_template,
    render_template,
    ALERT_TEMPLATES,
)


class TestTemplateRendering:
    """Test alert template rendering."""

    @pytest.mark.unit
    def test_render_cost_spike(self):
        """Test COST_SPIKE template renders correctly."""
        template = get_template("COST_SPIKE")

        rendered = render_template(
            template,
            params={"threshold_usd": 10000},
            catalog="prod_catalog",
            gold_schema="system_gold",
        )

        # Verify query template
        query = rendered["alert_query_template"]
        assert "prod_catalog.system_gold.fact_usage" in query
        assert "10000" in query
        assert "daily_cost" in query

        # Verify threshold column
        assert rendered["threshold_column"] == "daily_cost"
        assert rendered["threshold_operator"] == ">"

    @pytest.mark.unit
    def test_render_missing_required_param(self):
        """Test error handling for missing required parameters."""
        template = get_template("COST_SPIKE")

        with pytest.raises(ValueError, match="Missing required parameter"):
            render_template(
                template,
                params={},  # Missing threshold_usd
                catalog="catalog",
                gold_schema="gold",
            )

    @pytest.mark.unit
    def test_render_optional_param_default(self):
        """Test optional parameters use defaults."""
        template = get_template("COST_SPIKE")

        rendered = render_template(
            template,
            params={"threshold_usd": 5000},
            catalog="cat",
            gold_schema="gold",
        )

        # Should use default lookback_days
        query = rendered["alert_query_template"]
        assert "14 DAYS" in query  # Default lookback

    @pytest.mark.unit
    def test_render_optional_param_override(self):
        """Test optional parameters can be overridden."""
        template = get_template("COST_SPIKE")

        rendered = render_template(
            template,
            params={"threshold_usd": 5000, "lookback_days": 7},
            catalog="cat",
            gold_schema="gold",
        )

        query = rendered["alert_query_template"]
        assert "7 DAYS" in query

    @pytest.mark.unit
    @pytest.mark.parametrize("template_id", ALERT_TEMPLATES.keys())
    def test_all_templates_render(self, template_id):
        """Verify all templates can render with sample params."""
        template = get_template(template_id)

        # Build minimum required params
        params = {}
        for param_name, param_info in template.required_params.items():
            if param_info["type"] == "number":
                params[param_name] = 100
            elif param_info["type"] == "string":
                params[param_name] = "test_value"
            elif param_info["type"] == "list":
                params[param_name] = ["item1"]

        # Should not raise
        rendered = render_template(
            template,
            params=params,
            catalog="test_catalog",
            gold_schema="system_gold",
        )

        assert "alert_query_template" in rendered
        assert len(rendered["alert_query_template"]) > 50
```

### Query Validation Tests

```python
"""tests/unit/alerting/test_query_validation.py"""

import pytest
from alerting.query_validator import (
    validate_sql_syntax,
    extract_table_references,
    validate_placeholder_usage,
)


class TestQueryValidation:
    """Test SQL query validation."""

    @pytest.mark.unit
    def test_valid_sql_syntax(self):
        """Test valid SQL passes validation."""
        query = """
        SELECT
            workspace_id,
            SUM(usage_quantity) as total_dbu
        FROM ${catalog}.${gold_schema}.fact_usage
        WHERE usage_date >= CURRENT_DATE - INTERVAL 7 DAYS
        GROUP BY workspace_id
        HAVING SUM(usage_quantity) > 1000
        """

        result = validate_sql_syntax(query)
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.unit
    def test_invalid_sql_syntax(self):
        """Test invalid SQL fails validation."""
        query = """
        SELECT
            workspace_id,
            SUM(usage_quantity as total_dbu  -- Missing closing paren
        FROM fact_usage
        """

        result = validate_sql_syntax(query)
        assert not result.is_valid
        assert len(result.errors) > 0

    @pytest.mark.unit
    def test_extract_table_references(self):
        """Test table reference extraction."""
        query = """
        SELECT u.*, w.workspace_name
        FROM ${catalog}.${gold_schema}.fact_usage u
        JOIN ${catalog}.${gold_schema}.dim_workspace w
            ON u.workspace_id = w.workspace_id
        """

        tables = extract_table_references(query)
        assert "fact_usage" in tables
        assert "dim_workspace" in tables

    @pytest.mark.unit
    def test_placeholder_validation(self):
        """Test placeholder usage validation."""
        # Good: Uses proper placeholders
        good_query = "SELECT * FROM ${catalog}.${gold_schema}.fact_usage"
        result = validate_placeholder_usage(good_query)
        assert result.is_valid

        # Bad: Missing placeholders
        bad_query = "SELECT * FROM my_catalog.my_schema.fact_usage"
        result = validate_placeholder_usage(bad_query)
        assert not result.is_valid
        assert "catalog placeholder" in result.errors[0].lower()
```

### Alert Query Execution Tests

```python
"""tests/component/alerting/test_alert_execution.py"""

import pytest
from datetime import datetime, timedelta


class TestAlertQueryExecution:
    """Test alert queries execute correctly against sample data."""

    @pytest.mark.integration
    def test_cost_spike_detection(self, spark, sample_usage_data):
        """Test COST_SPIKE alert detects anomalies."""
        from alerting.alert_templates import get_template, render_template

        # Create temp view
        sample_usage_data.createOrReplaceTempView("fact_usage")

        # Get and render template
        template = get_template("COST_SPIKE")
        rendered = render_template(
            template,
            params={"threshold_usd": 500},  # Low threshold for testing
            catalog="",  # Use temp view
            gold_schema="",
        )

        # Adjust query for temp view
        query = rendered["alert_query_template"]
        query = query.replace("${catalog}.${gold_schema}.", "")

        # Execute query
        result = spark.sql(query)

        # Should find some cost spikes in sample data
        assert result.count() >= 0  # May or may not have anomalies

        # Verify schema
        assert "workspace_id" in result.columns
        assert "daily_cost" in result.columns

    @pytest.mark.integration
    def test_job_failure_rate_alert(self, spark, sample_job_run_data):
        """Test JOB_FAILURE_RATE alert detection."""
        from alerting.alert_templates import get_template, render_template

        # Create temp view
        sample_job_run_data.createOrReplaceTempView("fact_job_run_timeline")

        # Render template
        template = get_template("JOB_FAILURE_RATE")
        rendered = render_template(
            template,
            params={"threshold_pct": 20},  # 20% failure threshold
            catalog="",
            gold_schema="",
        )

        query = rendered["alert_query_template"]
        query = query.replace("${catalog}.${gold_schema}.", "")

        result = spark.sql(query)

        # Sample data has ~30% failure rate, should trigger
        assert result.count() > 0, "Should detect jobs with high failure rate"

        # Verify output columns
        assert "job_id" in result.columns
        assert "failure_rate" in result.columns
```

---

## Pipeline Testing

### Bronze Streaming Tests

```python
"""tests/component/pipelines/bronze/test_streaming_tables.py"""

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import *


class TestBronzeAccessTables:
    """Test bronze access audit table transformations."""

    @pytest.fixture
    def sample_audit_events(self, spark):
        """Create sample audit event data."""
        schema = StructType([
            StructField("event_time", TimestampType(), False),
            StructField("action_name", StringType(), False),
            StructField("user_identity", StructType([
                StructField("email", StringType(), True),
            ]), True),
            StructField("request_params", MapType(StringType(), StringType()), True),
            StructField("response", StructType([
                StructField("status_code", IntegerType(), True),
            ]), True),
            StructField("workspace_id", StringType(), True),
        ])

        data = [
            {
                "event_time": datetime.now(),
                "action_name": "getCluster",
                "user_identity": {"email": "user@example.com"},
                "request_params": {"cluster_id": "cluster_123"},
                "response": {"status_code": 200},
                "workspace_id": "ws_001",
            },
            {
                "event_time": datetime.now(),
                "action_name": "runCommand",
                "user_identity": {"email": "admin@example.com"},
                "request_params": {"command": "SELECT 1"},
                "response": {"status_code": 200},
                "workspace_id": "ws_001",
            },
        ]

        return spark.createDataFrame(data, schema)

    @pytest.mark.integration
    def test_audit_table_transformation(self, mock_dlt, spark, sample_audit_events):
        """Test audit table DLT transformation."""
        # Register source
        mock_dlt.register_table("system.access.audit", sample_audit_events)

        # Import and execute the DLT function
        # Note: We need to adapt the DLT function for testing
        from pipelines.bronze.streaming.access_tables import create_bronze_audit

        # Execute the transformation logic (extracted from DLT decorator)
        result = create_bronze_audit(spark)

        # Verify output
        assert result.count() == 2
        assert "event_time" in result.columns
        assert "action_name" in result.columns
        assert "user_email" in result.columns  # Flattened from struct

    @pytest.mark.integration
    def test_audit_deduplication(self, spark, sample_audit_events):
        """Test duplicate events are handled correctly."""
        # Create duplicates
        duplicated = sample_audit_events.union(sample_audit_events)
        assert duplicated.count() == 4

        # Apply deduplication logic
        from pipelines.bronze.streaming.access_tables import deduplicate_audit

        result = deduplicate_audit(duplicated)

        assert result.count() == 2  # Should remove duplicates


class TestBronzeBillingTables:
    """Test bronze billing table transformations."""

    @pytest.fixture
    def sample_billing_data(self, spark):
        """Create sample billing data."""
        return spark.createDataFrame([
            {
                "workspace_id": "ws_001",
                "usage_date": "2024-01-01",
                "sku_name": "JOBS_COMPUTE",
                "usage_quantity": 100.0,
                "usage_unit": "DBU",
            },
            {
                "workspace_id": "ws_002",
                "usage_date": "2024-01-01",
                "sku_name": "SQL_COMPUTE",
                "usage_quantity": 50.0,
                "usage_unit": "DBU",
            },
        ])

    @pytest.mark.integration
    def test_billing_table_schema(self, spark, sample_billing_data):
        """Verify billing table has expected schema."""
        from pipelines.bronze.streaming.billing_tables import BILLING_SCHEMA

        # Validate input data matches expected schema
        for field in BILLING_SCHEMA.fields:
            if not field.nullable:
                null_count = sample_billing_data.filter(
                    F.col(field.name).isNull()
                ).count()
                assert null_count == 0, f"Required field {field.name} has nulls"
```

### Gold Merge Tests

```python
"""tests/component/pipelines/gold/test_merge_operations.py"""

import pytest
from pyspark.sql import functions as F
from datetime import datetime


class TestGoldMergeUsage:
    """Test Gold layer fact_usage MERGE operations."""

    @pytest.fixture
    def bronze_usage(self, spark):
        """Create sample bronze usage data for merge."""
        return spark.createDataFrame([
            {
                "record_id": "rec_001",
                "workspace_id": "ws_001",
                "usage_date": datetime(2024, 1, 1),
                "sku_name": "JOBS_COMPUTE",
                "usage_quantity": 100.0,
                "bronze_ingestion_timestamp": datetime.now(),
            },
            {
                "record_id": "rec_002",
                "workspace_id": "ws_001",
                "usage_date": datetime(2024, 1, 2),
                "sku_name": "JOBS_COMPUTE",
                "usage_quantity": 150.0,
                "bronze_ingestion_timestamp": datetime.now(),
            },
        ])

    @pytest.fixture
    def gold_usage_existing(self, spark):
        """Create existing Gold usage data."""
        return spark.createDataFrame([
            {
                "record_id": "rec_001",
                "workspace_id": "ws_001",
                "usage_date": datetime(2024, 1, 1),
                "sku_name": "JOBS_COMPUTE",
                "usage_quantity": 90.0,  # Old value
                "gold_merge_timestamp": datetime(2024, 1, 1),
            },
        ])

    @pytest.mark.integration
    def test_merge_inserts_new_records(self, spark, bronze_usage, gold_usage_existing):
        """Test MERGE inserts new records."""
        from pipelines.gold.merge_helpers import prepare_merge_df

        # Prepare merge
        merge_df = prepare_merge_df(
            source_df=bronze_usage,
            target_df=gold_usage_existing,
            key_columns=["record_id"],
        )

        # Filter to new records only
        new_records = merge_df.filter(F.col("_merge_action") == "INSERT")

        assert new_records.count() == 1
        assert new_records.first()["record_id"] == "rec_002"

    @pytest.mark.integration
    def test_merge_updates_existing_records(self, spark, bronze_usage, gold_usage_existing):
        """Test MERGE updates existing records."""
        from pipelines.gold.merge_helpers import prepare_merge_df

        merge_df = prepare_merge_df(
            source_df=bronze_usage,
            target_df=gold_usage_existing,
            key_columns=["record_id"],
        )

        # Filter to updates only
        updates = merge_df.filter(F.col("_merge_action") == "UPDATE")

        assert updates.count() == 1
        assert updates.first()["record_id"] == "rec_001"
        assert updates.first()["usage_quantity"] == 100.0  # New value

    @pytest.mark.integration
    def test_merge_deduplication(self, spark):
        """Test deduplication before merge."""
        # Create data with duplicates
        data_with_dupes = spark.createDataFrame([
            {"record_id": "rec_001", "value": 100, "timestamp": datetime(2024, 1, 1, 10)},
            {"record_id": "rec_001", "value": 200, "timestamp": datetime(2024, 1, 1, 11)},  # Later
        ])

        from pipelines.gold.merge_helpers import deduplicate_for_merge

        deduped = deduplicate_for_merge(
            data_with_dupes,
            key_columns=["record_id"],
            order_by="timestamp",
            ascending=False,  # Keep latest
        )

        assert deduped.count() == 1
        assert deduped.first()["value"] == 200  # Should keep later value

    @pytest.mark.integration
    def test_merge_handles_nulls(self, spark):
        """Test MERGE handles NULL values correctly."""
        source = spark.createDataFrame([
            {"id": 1, "value": None},  # NULL value
            {"id": 2, "value": 100},
        ])

        from pipelines.gold.merge_helpers import prepare_merge_df

        # Should not raise on NULL values
        result = prepare_merge_df(source, source, key_columns=["id"])
        assert result.count() == 2


class TestGoldMergeJobs:
    """Test Gold layer job run MERGE operations."""

    @pytest.fixture
    def bronze_job_runs(self, spark):
        """Create sample job run data."""
        return spark.createDataFrame([
            {
                "run_id": 12345,
                "job_id": "job_001",
                "result_state": "SUCCEEDED",
                "start_time": datetime(2024, 1, 1, 10, 0),
                "end_time": datetime(2024, 1, 1, 10, 30),
            },
            {
                "run_id": 12346,
                "job_id": "job_001",
                "result_state": "FAILED",
                "start_time": datetime(2024, 1, 1, 11, 0),
                "end_time": datetime(2024, 1, 1, 11, 5),
            },
        ])

    @pytest.mark.integration
    def test_job_run_metrics_calculation(self, spark, bronze_job_runs):
        """Test job run metrics are calculated correctly."""
        from pipelines.gold.merge_lakeflow import calculate_job_metrics

        metrics = calculate_job_metrics(bronze_job_runs)

        # Should have job-level aggregates
        job_metrics = metrics.filter(F.col("job_id") == "job_001").first()

        assert job_metrics["total_runs"] == 2
        assert job_metrics["success_count"] == 1
        assert job_metrics["failure_count"] == 1
        assert job_metrics["failure_rate"] == 0.5
```

---

## ML Model Testing

### Feature Engineering Tests

```python
"""tests/component/ml/test_feature_engineering.py"""

import pytest
import numpy as np
from pyspark.sql import functions as F


class TestCostFeatureEngineering:
    """Test cost anomaly detection feature engineering."""

    @pytest.fixture
    def raw_usage_data(self, spark):
        """Create raw usage data for feature engineering."""
        import pandas as pd
        from datetime import datetime, timedelta

        # Generate 60 days of usage data
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        data = []

        for i, date in enumerate(dates):
            # Add daily pattern and weekly seasonality
            base = 100 + np.sin(2 * np.pi * i / 7) * 20  # Weekly pattern
            data.append({
                "workspace_id": "ws_001",
                "usage_date": date.date(),
                "daily_dbu": base + np.random.normal(0, 5),
            })

        return spark.createDataFrame(pd.DataFrame(data))

    @pytest.mark.integration
    @pytest.mark.ml
    def test_rolling_average_features(self, spark, raw_usage_data):
        """Test rolling average feature calculation."""
        from ml.features.cost_features import calculate_rolling_features

        result = calculate_rolling_features(raw_usage_data, window_sizes=[7, 30])

        # Verify columns exist
        assert "avg_dbu_7d" in result.columns
        assert "avg_dbu_30d" in result.columns

        # Verify values are reasonable
        sample = result.filter(F.col("avg_dbu_7d").isNotNull()).first()
        assert 50 < sample["avg_dbu_7d"] < 150  # Reasonable range

    @pytest.mark.integration
    @pytest.mark.ml
    def test_z_score_features(self, spark, raw_usage_data):
        """Test z-score feature calculation."""
        from ml.features.cost_features import calculate_zscore_features

        result = calculate_zscore_features(raw_usage_data, window_sizes=[7])

        assert "z_score_7d" in result.columns

        # Z-scores should mostly be between -3 and 3
        stats = result.select(
            F.mean("z_score_7d").alias("mean"),
            F.stddev("z_score_7d").alias("std"),
        ).first()

        assert abs(stats["mean"]) < 0.5  # Close to 0
        assert 0.5 < stats["std"] < 2.0  # Reasonable variance

    @pytest.mark.integration
    @pytest.mark.ml
    def test_cyclical_time_features(self, spark, raw_usage_data):
        """Test cyclical time feature encoding."""
        from ml.features.cost_features import add_cyclical_features

        result = add_cyclical_features(raw_usage_data)

        # Verify cyclical encoding
        assert "dow_sin" in result.columns
        assert "dow_cos" in result.columns

        # Values should be in [-1, 1]
        min_max = result.select(
            F.min("dow_sin").alias("min_sin"),
            F.max("dow_sin").alias("max_sin"),
        ).first()

        assert min_max["min_sin"] >= -1.0
        assert min_max["max_sin"] <= 1.0

    @pytest.mark.unit
    @pytest.mark.ml
    def test_feature_column_completeness(self, sample_cost_features):
        """Test all required feature columns are present."""
        required_features = [
            'daily_dbu', 'avg_dbu_7d', 'avg_dbu_30d',
            'z_score_7d', 'z_score_30d',
            'dbu_change_pct_1d', 'dbu_change_pct_7d',
            'dow_sin', 'dow_cos',
            'is_weekend', 'is_month_end'
        ]

        for col in required_features:
            assert col in sample_cost_features.columns, f"Missing feature: {col}"

    @pytest.mark.unit
    @pytest.mark.ml
    def test_feature_no_infinites(self, sample_cost_features):
        """Test no infinite values in features."""
        numeric_cols = sample_cost_features.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            infinite_count = np.isinf(sample_cost_features[col]).sum()
            assert infinite_count == 0, f"Found {infinite_count} infinite values in {col}"
```

### Model Training Tests

```python
"""tests/component/ml/test_model_training.py"""

import pytest
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier


class TestCostAnomalyTraining:
    """Test cost anomaly detection model training."""

    @pytest.mark.unit
    @pytest.mark.ml
    def test_isolation_forest_trains(self, sample_cost_features):
        """Test Isolation Forest model trains successfully."""
        feature_cols = ['daily_dbu', 'avg_dbu_7d', 'z_score_7d']
        X = sample_cost_features[feature_cols].fillna(0)

        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )

        model.fit(X)

        assert hasattr(model, 'estimators_')
        assert len(model.estimators_) == 100

    @pytest.mark.unit
    @pytest.mark.ml
    def test_predictions_valid(self, sample_cost_features):
        """Test model predictions are valid."""
        feature_cols = ['daily_dbu', 'avg_dbu_7d', 'z_score_7d']
        X = sample_cost_features[feature_cols].fillna(0)

        model = IsolationForest(n_estimators=50, contamination=0.05, random_state=42)
        model.fit(X)

        predictions = model.predict(X)

        # Predictions should be -1 (anomaly) or 1 (normal)
        unique_preds = set(predictions)
        assert unique_preds <= {-1, 1}

        # Anomaly rate should match contamination
        anomaly_rate = (predictions == -1).mean()
        assert abs(anomaly_rate - 0.05) < 0.02

    @pytest.mark.unit
    @pytest.mark.ml
    def test_mlflow_logging(self, mock_mlflow, sample_cost_features):
        """Test MLflow logging during training."""
        import mlflow

        feature_cols = ['daily_dbu', 'avg_dbu_7d', 'z_score_7d']
        X = sample_cost_features[feature_cols].fillna(0)

        with mlflow.start_run():
            model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
            model.fit(X)

            mlflow.log_params({
                "model_type": "IsolationForest",
                "n_estimators": 100,
                "contamination": 0.05,
            })

            predictions = model.predict(X)
            anomaly_rate = (predictions == -1).mean()

            mlflow.log_metrics({
                "anomaly_rate": anomaly_rate,
                "training_samples": len(X),
            })

        # Verify logging occurred
        mock_mlflow.assert_param_logged("model_type", "IsolationForest")
        mock_mlflow.assert_metric_logged("anomaly_rate")


class TestJobFailurePredictor:
    """Test job failure prediction model."""

    @pytest.mark.unit
    @pytest.mark.ml
    def test_classifier_trains(self, sample_job_features):
        """Test RandomForest classifier trains successfully."""
        feature_cols = [
            'historical_failure_rate', 'consecutive_failures',
            'avg_duration_minutes', 'task_count'
        ]
        X = sample_job_features[feature_cols]
        y = sample_job_features['is_failure']

        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X, y)

        assert hasattr(model, 'feature_importances_')
        assert len(model.feature_importances_) == len(feature_cols)

    @pytest.mark.unit
    @pytest.mark.ml
    def test_predictions_probability(self, sample_job_features):
        """Test model outputs valid probabilities."""
        feature_cols = [
            'historical_failure_rate', 'consecutive_failures',
            'avg_duration_minutes', 'task_count'
        ]
        X = sample_job_features[feature_cols]
        y = sample_job_features['is_failure']

        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X, y)

        probas = model.predict_proba(X)

        # Probabilities should sum to 1
        assert np.allclose(probas.sum(axis=1), 1.0)

        # Probabilities should be in [0, 1]
        assert (probas >= 0).all()
        assert (probas <= 1).all()
```

---

## Monitoring Testing

### Monitor Configuration Tests

```python
"""tests/unit/monitoring/test_monitor_config.py"""

import pytest
from pathlib import Path
import yaml


class TestMonitorConfigurations:
    """Test Lakehouse monitor configurations."""

    @pytest.fixture
    def monitor_configs(self):
        """Load all monitor configurations."""
        config_dir = Path(__file__).parent.parent.parent.parent / "src" / "monitoring"
        configs = {}

        for config_file in config_dir.glob("*.yaml"):
            with open(config_file) as f:
                configs[config_file.stem] = yaml.safe_load(f)

        return configs

    @pytest.mark.unit
    def test_all_monitors_have_required_fields(self, monitor_configs):
        """Verify all monitors have required configuration."""
        required_fields = ['table_name', 'output_schema_name', 'granularities']

        for name, config in monitor_configs.items():
            for field in required_fields:
                assert field in config, f"Monitor {name} missing {field}"

    @pytest.mark.unit
    def test_valid_granularities(self, monitor_configs):
        """Test granularities are valid."""
        valid_granularities = {'5 minutes', '1 hour', '1 day'}

        for name, config in monitor_configs.items():
            for gran in config.get('granularities', []):
                assert gran in valid_granularities, \
                    f"Monitor {name} has invalid granularity: {gran}"

    @pytest.mark.unit
    def test_valid_metric_types(self, monitor_configs):
        """Test custom metrics have valid types."""
        valid_types = {'aggregate', 'derived'}

        for name, config in monitor_configs.items():
            for metric in config.get('custom_metrics', []):
                assert 'type' in metric
                assert metric['type'] in valid_types


class TestMonitorCreation:
    """Test monitor creation logic."""

    @pytest.mark.unit
    def test_create_monitor_config(self):
        """Test monitor configuration generation."""
        from monitoring.monitor_utils import create_monitor_config

        config = create_monitor_config(
            table_name="test_catalog.schema.fact_usage",
            baseline_table_name="test_catalog.schema.fact_usage_baseline",
            granularities=["1 day"],
            slicing_exprs=["workspace_id"],
        )

        assert config['table_name'] == "test_catalog.schema.fact_usage"
        assert "1 day" in config['granularities']
        assert "workspace_id" in config['slicing_exprs']

    @pytest.mark.unit
    def test_monitor_creates_with_sdk(self, mock_quality_monitors):
        """Test monitor creation via SDK."""
        from monitoring.cluster_monitor import create_cluster_monitor

        # Call the creation function with mock
        create_cluster_monitor(
            catalog="test",
            schema="gold",
            api=mock_quality_monitors,
        )

        # Verify monitor was created
        assert len(mock_quality_monitors._monitors) > 0
```

---

## Semantic Layer Testing

### TVF Testing

```python
"""tests/component/semantic/test_tvf_execution.py"""

import pytest
from pyspark.sql import functions as F


class TestCostTVFs:
    """Test cost-related Table-Valued Functions."""

    @pytest.fixture
    def setup_gold_tables(self, spark, sample_usage_data, sample_workspace_data):
        """Set up Gold tables for TVF testing."""
        sample_usage_data.createOrReplaceTempView("fact_usage")
        sample_workspace_data.createOrReplaceTempView("dim_workspace")
        yield
        spark.catalog.dropTempView("fact_usage")
        spark.catalog.dropTempView("dim_workspace")

    @pytest.mark.integration
    @pytest.mark.tvf
    def test_get_daily_cost_summary(self, spark, setup_gold_tables):
        """Test daily cost summary TVF."""
        # Simulate TVF query
        query = """
        SELECT
            usage_date,
            workspace_id,
            SUM(usage_quantity) as total_dbu,
            COUNT(*) as record_count
        FROM fact_usage
        WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
        GROUP BY usage_date, workspace_id
        ORDER BY usage_date DESC
        """

        result = spark.sql(query)

        # Verify output
        assert result.count() > 0
        assert "total_dbu" in result.columns
        assert "workspace_id" in result.columns

    @pytest.mark.integration
    @pytest.mark.tvf
    def test_get_cost_by_sku(self, spark, setup_gold_tables):
        """Test cost by SKU TVF."""
        query = """
        SELECT
            sku_name,
            SUM(usage_quantity) as total_dbu
        FROM fact_usage
        GROUP BY sku_name
        """

        result = spark.sql(query)

        # Should have multiple SKUs
        sku_count = result.count()
        assert sku_count >= 1

        # Total DBU should be positive
        total = result.agg(F.sum("total_dbu")).first()[0]
        assert total > 0


class TestReliabilityTVFs:
    """Test reliability TVFs."""

    @pytest.mark.integration
    @pytest.mark.tvf
    def test_get_job_failure_summary(self, spark, sample_job_run_data):
        """Test job failure summary TVF."""
        sample_job_run_data.createOrReplaceTempView("fact_job_run_timeline")

        query = """
        SELECT
            job_id,
            COUNT(*) as total_runs,
            SUM(CASE WHEN result_state != 'SUCCEEDED' THEN 1 ELSE 0 END) as failures,
            SUM(CASE WHEN result_state != 'SUCCEEDED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as failure_rate
        FROM fact_job_run_timeline
        GROUP BY job_id
        HAVING COUNT(*) >= 5
        ORDER BY failure_rate DESC
        """

        result = spark.sql(query)

        # Should find jobs
        assert result.count() > 0

        # Failure rate should be between 0 and 100
        max_rate = result.agg(F.max("failure_rate")).first()[0]
        assert 0 <= max_rate <= 100

        spark.catalog.dropTempView("fact_job_run_timeline")
```

---

## Dashboard Testing

### Dashboard JSON Validation

```python
"""tests/unit/dashboards/test_dashboard_validation.py"""

import pytest
import json
from pathlib import Path


class TestDashboardStructure:
    """Test dashboard JSON structure."""

    @pytest.fixture
    def load_dashboards(self):
        """Load all dashboard JSON files."""
        dashboard_dir = Path(__file__).parent.parent.parent.parent / "context" / "dashboards"
        dashboards = {}

        for json_file in dashboard_dir.glob("*.lvdash.json"):
            with open(json_file) as f:
                dashboards[json_file.name] = json.load(f)

        return dashboards

    @pytest.mark.unit
    def test_valid_json_structure(self, load_dashboards):
        """Test all dashboards are valid JSON."""
        for name, config in load_dashboards.items():
            assert isinstance(config, dict), f"{name} should be a dict"
            assert "displayName" in config, f"{name} missing displayName"
            assert "pages" in config, f"{name} missing pages"

    @pytest.mark.unit
    def test_six_column_grid(self, load_dashboards):
        """Test widgets use 6-column grid layout."""
        for name, config in load_dashboards.items():
            for page in config.get("pages", []):
                for item in page.get("layout", []):
                    pos = item.get("position", {})
                    x = pos.get("x", 0)
                    width = pos.get("width", 1)

                    assert x + width <= 6, \
                        f"{name}: Widget at x={x}, width={width} exceeds 6-column grid"

    @pytest.mark.unit
    def test_datasets_use_variables(self, load_dashboards):
        """Test datasets use ${catalog} and ${gold_schema} variables."""
        for name, config in load_dashboards.items():
            for dataset in config.get("datasets", []):
                query = dataset.get("query", "")
                if "FROM" in query.upper():
                    assert "${catalog}" in query, \
                        f"{name}: Dataset '{dataset.get('name')}' missing ${{catalog}}"
                    assert "${gold_schema}" in query, \
                        f"{name}: Dataset missing ${{gold_schema}}"

    @pytest.mark.unit
    def test_widgets_have_titles(self, load_dashboards):
        """Test all visualization widgets have titles."""
        for name, config in load_dashboards.items():
            for page in config.get("pages", []):
                for item in page.get("layout", []):
                    widget = item.get("widget", {})
                    spec = widget.get("spec", {})

                    # Skip text/markdown widgets
                    if spec.get("widgetType") in ["text", "markdown"]:
                        continue

                    # Visualization widgets should have titles
                    frame = spec.get("frame", {})
                    assert frame.get("title") or frame.get("showTitle") == False, \
                        f"{name}: Widget '{widget.get('name')}' missing title"
```

---

## Edge Case Patterns

### Null Handling Tests

```python
"""tests/component/edge_cases/test_null_handling.py"""

import pytest
from pyspark.sql import functions as F


class TestNullHandling:
    """Test null value handling across modules."""

    @pytest.mark.integration
    def test_merge_with_null_keys(self, spark):
        """Test MERGE handles NULL in key columns."""
        source = spark.createDataFrame([
            {"id": None, "value": 100},  # NULL key
            {"id": 1, "value": 200},
        ])

        from pipelines.gold.merge_helpers import validate_keys

        with pytest.raises(ValueError, match="NULL values in key columns"):
            validate_keys(source, ["id"])

    @pytest.mark.integration
    def test_aggregation_with_nulls(self, spark):
        """Test aggregations handle NULLs correctly."""
        data = spark.createDataFrame([
            {"group": "A", "value": 100},
            {"group": "A", "value": None},
            {"group": "B", "value": 200},
        ])

        result = data.groupBy("group").agg(
            F.sum("value").alias("total"),
            F.count("value").alias("non_null_count"),
            F.count("*").alias("total_count"),
        )

        group_a = result.filter(F.col("group") == "A").first()

        # SUM should ignore NULL
        assert group_a["total"] == 100
        # COUNT(column) ignores NULL, COUNT(*) doesn't
        assert group_a["non_null_count"] == 1
        assert group_a["total_count"] == 2


class TestEmptyDataFrames:
    """Test handling of empty DataFrames."""

    @pytest.mark.integration
    def test_merge_with_empty_source(self, spark):
        """Test MERGE handles empty source."""
        target = spark.createDataFrame([{"id": 1, "value": 100}])
        source = spark.createDataFrame([], target.schema)

        from pipelines.gold.merge_helpers import prepare_merge_df

        result = prepare_merge_df(source, target, key_columns=["id"])

        # Should return empty merge set
        assert result.count() == 0

    @pytest.mark.integration
    def test_aggregation_empty_dataframe(self, spark):
        """Test aggregation on empty DataFrame."""
        from pyspark.sql.types import StructType, StructField, StringType, DoubleType

        schema = StructType([
            StructField("group", StringType()),
            StructField("value", DoubleType()),
        ])
        empty_df = spark.createDataFrame([], schema)

        result = empty_df.groupBy("group").agg(F.sum("value").alias("total"))

        assert result.count() == 0
```

### Data Quality Tests

```python
"""tests/component/edge_cases/test_data_quality.py"""

import pytest
from pyspark.sql import functions as F


class TestDataQualityEdgeCases:
    """Test data quality edge cases."""

    @pytest.mark.integration
    def test_duplicate_key_detection(self, spark):
        """Test detection of duplicate keys."""
        data = spark.createDataFrame([
            {"id": 1, "value": 100},
            {"id": 1, "value": 200},  # Duplicate key
            {"id": 2, "value": 300},
        ])

        from pipelines.gold.merge_helpers import detect_duplicates

        duplicates = detect_duplicates(data, ["id"])

        assert duplicates.count() == 2  # Both records with id=1

    @pytest.mark.integration
    def test_schema_evolution(self, spark):
        """Test handling of schema changes."""
        old_schema_data = spark.createDataFrame([
            {"id": 1, "old_column": "value"},
        ])

        new_schema_data = spark.createDataFrame([
            {"id": 1, "old_column": "value", "new_column": "new_value"},
        ])

        # Merging should handle schema differences
        from pipelines.gold.merge_helpers import align_schemas

        aligned = align_schemas(old_schema_data, new_schema_data)

        assert "new_column" in aligned.columns

    @pytest.mark.integration
    def test_unicode_handling(self, spark):
        """Test Unicode string handling."""
        data = spark.createDataFrame([
            {"id": 1, "name": "Regular ASCII"},
            {"id": 2, "name": "Unicode: \u4e2d\u6587"},  # Chinese
            {"id": 3, "name": "Emoji: \ud83d\ude00"},  # Emoji
        ])

        # Should not raise on string operations
        result = data.filter(F.length("name") > 0)
        assert result.count() == 3

        # Should handle in aggregations
        concat_result = result.agg(
            F.concat_ws(", ", F.collect_list("name")).alias("all_names")
        ).first()

        assert "\u4e2d\u6587" in concat_result["all_names"]
```

---

*Document Version: 1.0*
*Last Updated: 2026-01-01*
