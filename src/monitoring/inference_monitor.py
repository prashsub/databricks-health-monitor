# Databricks notebook source
"""
ML Inference Monitor Configuration
==================================

Lakehouse Monitor for ML model predictions.
Tracks prediction quality, drift, and anomaly detection performance.

Agent Domain: 🤖 ML / 💰 Cost (for cost anomaly model)
Reference: Phase 3 Addendum 3.4 - ML Inference Monitors
"""

# COMMAND ----------

from monitor_utils import (
    check_monitoring_available,
    delete_monitor_if_exists,
    create_time_series_monitor,
    create_aggregate_metric,
    create_derived_metric,
    create_drift_metric,
    MONITORING_AVAILABLE
)

if MONITORING_AVAILABLE:
    from databricks.sdk import WorkspaceClient

# COMMAND ----------

# Widget parameters
dbutils.widgets.text("catalog", "health_monitor", "Target Catalog")
dbutils.widgets.text("gold_schema", "gold", "Gold Schema")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")

# COMMAND ----------

def get_cost_anomaly_inference_metrics():
    """
    Define custom metrics for cost anomaly inference monitoring.
    
    Tracks:
    - Prediction accuracy (MAE, MAPE)
    - Anomaly detection rates
    - Model confidence distribution
    - Prediction drift patterns
    """
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Prediction volume
        create_aggregate_metric(
            "prediction_count",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_workspaces",
            "COUNT(DISTINCT workspace_id)",
            "LONG"
        ),

        # Accuracy metrics (MAE, MAPE)
        create_aggregate_metric(
            "mean_absolute_error",
            "AVG(ABS(daily_cost - expected_cost))",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "mean_squared_error",
            "AVG(POWER(daily_cost - expected_cost, 2))",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "mean_actual_cost",
            "AVG(daily_cost)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "mean_expected_cost",
            "AVG(expected_cost)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_actual_cost",
            "SUM(daily_cost)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_expected_cost",
            "SUM(expected_cost)",
            "DOUBLE"
        ),

        # Anomaly detection metrics
        create_aggregate_metric(
            "anomaly_count",
            "SUM(CASE WHEN is_anomaly = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "non_anomaly_count",
            "SUM(CASE WHEN is_anomaly = FALSE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "high_confidence_anomaly_count",
            "SUM(CASE WHEN anomaly_score > 0.9 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "medium_confidence_anomaly_count",
            "SUM(CASE WHEN anomaly_score BETWEEN 0.7 AND 0.9 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "low_confidence_anomaly_count",
            "SUM(CASE WHEN anomaly_score BETWEEN 0.5 AND 0.7 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Anomaly score distribution
        create_aggregate_metric(
            "avg_anomaly_score",
            "AVG(anomaly_score)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_anomaly_score",
            "MAX(anomaly_score)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "min_anomaly_score",
            "MIN(anomaly_score)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p50_anomaly_score",
            "PERCENTILE(anomaly_score, 0.50)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p90_anomaly_score",
            "PERCENTILE(anomaly_score, 0.90)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p99_anomaly_score",
            "PERCENTILE(anomaly_score, 0.99)",
            "DOUBLE"
        ),

        # Deviation distribution
        create_aggregate_metric(
            "avg_deviation_pct",
            "AVG(ABS(daily_cost - expected_cost) * 100.0 / NULLIF(expected_cost, 0))",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_deviation_pct",
            "MAX(ABS(daily_cost - expected_cost) * 100.0 / NULLIF(expected_cost, 0))",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "predictions_within_10pct",
            "SUM(CASE WHEN ABS(daily_cost - expected_cost) <= expected_cost * 0.1 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "predictions_within_20pct",
            "SUM(CASE WHEN ABS(daily_cost - expected_cost) <= expected_cost * 0.2 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "mean_absolute_percentage_error",
            "mean_absolute_error * 100.0 / NULLIF(mean_actual_cost, 0)"
        ),
        create_derived_metric(
            "anomaly_rate",
            "anomaly_count * 100.0 / NULLIF(prediction_count, 0)"
        ),
        create_derived_metric(
            "high_confidence_anomaly_rate",
            "high_confidence_anomaly_count * 100.0 / NULLIF(prediction_count, 0)"
        ),
        create_derived_metric(
            "prediction_accuracy_10pct",
            "predictions_within_10pct * 100.0 / NULLIF(prediction_count, 0)"
        ),
        create_derived_metric(
            "prediction_accuracy_20pct",
            "predictions_within_20pct * 100.0 / NULLIF(prediction_count, 0)"
        ),
        create_derived_metric(
            "cost_forecast_bias",
            "(total_expected_cost - total_actual_cost) / NULLIF(total_actual_cost, 0) * 100"
        ),
        create_derived_metric(
            "root_mean_squared_error",
            "SQRT(mean_squared_error)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "mae_drift",
            "{{current_df}}.mean_absolute_error - {{base_df}}.mean_absolute_error"
        ),
        create_drift_metric(
            "mape_drift",
            "{{current_df}}.mean_absolute_percentage_error - {{base_df}}.mean_absolute_percentage_error"
        ),
        create_drift_metric(
            "anomaly_rate_drift",
            "{{current_df}}.anomaly_rate - {{base_df}}.anomaly_rate"
        ),
        create_drift_metric(
            "avg_score_drift",
            "{{current_df}}.avg_anomaly_score - {{base_df}}.avg_anomaly_score"
        ),
        create_drift_metric(
            "accuracy_drift",
            "{{current_df}}.prediction_accuracy_10pct - {{base_df}}.prediction_accuracy_10pct"
        ),
        create_drift_metric(
            "bias_drift",
            "{{current_df}}.cost_forecast_bias - {{base_df}}.cost_forecast_bias"
        ),
    ]


def create_cost_anomaly_inference_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """
    Create inference monitor for cost anomaly predictions.
    
    Monitors the ML model that detects cost anomalies to ensure
    prediction quality and detect model drift.
    """
    table_name = f"{catalog}.{gold_schema}.cost_anomaly_predictions"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    try:
        # Create monitor (pass spark to create monitoring schema if needed)
        monitor = create_time_series_monitor(
            workspace_client=workspace_client,
            table_name=table_name,
            timestamp_col="prediction_date",
            granularities=["1 day"],
            custom_metrics=get_cost_anomaly_inference_metrics(),
            slicing_exprs=["workspace_id"],
            schedule_cron="0 0 8 * * ?",  # Daily at 8 AM UTC (after predictions run)
            spark=spark,  # Pass spark to create monitoring schema
        )
        return monitor
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"  Note: Predictions table {table_name} does not exist yet.")
            print("  This monitor will be created when ML inference runs.")
            return None
        raise


# COMMAND ----------

def get_failure_predictor_inference_metrics():
    """
    Define custom metrics for job failure predictor inference monitoring.
    
    Tracks classification accuracy, precision, recall, and prediction distribution.
    """
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        create_aggregate_metric(
            "prediction_count",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_jobs",
            "COUNT(DISTINCT job_id)",
            "LONG"
        ),

        # Prediction distribution
        create_aggregate_metric(
            "predicted_failures",
            "SUM(CASE WHEN predicted_will_fail = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "predicted_success",
            "SUM(CASE WHEN predicted_will_fail = FALSE THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Confidence distribution
        create_aggregate_metric(
            "avg_confidence",
            "AVG(prediction_confidence)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "high_confidence_predictions",
            "SUM(CASE WHEN prediction_confidence > 0.8 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Actual outcome (if available)
        create_aggregate_metric(
            "actual_failures",
            "SUM(CASE WHEN actual_failed = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "true_positives",
            "SUM(CASE WHEN predicted_will_fail = TRUE AND actual_failed = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "false_positives",
            "SUM(CASE WHEN predicted_will_fail = TRUE AND actual_failed = FALSE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "true_negatives",
            "SUM(CASE WHEN predicted_will_fail = FALSE AND actual_failed = FALSE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "false_negatives",
            "SUM(CASE WHEN predicted_will_fail = FALSE AND actual_failed = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # ==========================================
        # DERIVED METRICS - Classification Metrics
        # ==========================================

        create_derived_metric(
            "predicted_failure_rate",
            "predicted_failures * 100.0 / NULLIF(prediction_count, 0)"
        ),
        create_derived_metric(
            "actual_failure_rate",
            "actual_failures * 100.0 / NULLIF(prediction_count, 0)"
        ),
        create_derived_metric(
            "precision",
            "true_positives * 100.0 / NULLIF(true_positives + false_positives, 0)"
        ),
        create_derived_metric(
            "recall",
            "true_positives * 100.0 / NULLIF(true_positives + false_negatives, 0)"
        ),
        create_derived_metric(
            "accuracy",
            "(true_positives + true_negatives) * 100.0 / NULLIF(prediction_count, 0)"
        ),
        create_derived_metric(
            "high_confidence_rate",
            "high_confidence_predictions * 100.0 / NULLIF(prediction_count, 0)"
        ),

        # ==========================================
        # DRIFT METRICS
        # ==========================================

        create_drift_metric(
            "accuracy_drift",
            "{{current_df}}.accuracy - {{base_df}}.accuracy"
        ),
        create_drift_metric(
            "precision_drift",
            "{{current_df}}.precision - {{base_df}}.precision"
        ),
        create_drift_metric(
            "predicted_failure_rate_drift",
            "{{current_df}}.predicted_failure_rate - {{base_df}}.predicted_failure_rate"
        ),
    ]


def create_failure_predictor_inference_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """
    Create inference monitor for job failure predictions.
    
    Monitors the ML model that predicts job failures to track
    classification performance over time.
    """
    table_name = f"{catalog}.{gold_schema}.failure_predictions"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    try:
        # Create monitor (pass spark to create monitoring schema if needed)
        monitor = create_time_series_monitor(
            workspace_client=workspace_client,
            table_name=table_name,
            timestamp_col="prediction_date",
            granularities=["1 day"],
            custom_metrics=get_failure_predictor_inference_metrics(),
            slicing_exprs=["workspace_id"],
            schedule_cron="0 0 8 * * ?",
            spark=spark,  # Pass spark to create monitoring schema
        )
        return monitor
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"  Note: Predictions table {table_name} does not exist yet.")
            return None
        raise


# COMMAND ----------

def create_inference_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """
    Create all inference monitors for ML models.
    
    Returns dict of monitor results.
    """
    results = {}

    # Cost Anomaly Inference Monitor
    cost_table = f"{catalog}.{gold_schema}.cost_anomaly_predictions"
    print(f"\n  [1/2] Cost Anomaly Inference Monitor")
    print(f"        Table: {cost_table}")
    try:
        monitor = create_cost_anomaly_inference_monitor(workspace_client, catalog, gold_schema, spark)
        if monitor:
            print(f"        [✓] Created successfully")
            results["cost_anomaly"] = "OK"
        else:
            print(f"        [⊘] Table not available yet (ML predictions pending)")
            results["cost_anomaly"] = "SKIP"
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            print(f"        [⊘] Table does not exist yet")
            results["cost_anomaly"] = "SKIP"
        else:
            print(f"        [✗] Error: {error_msg[:80]}")
            results["cost_anomaly"] = "FAIL"

    # Failure Predictor Inference Monitor
    failure_table = f"{catalog}.{gold_schema}.failure_predictions"
    print(f"\n  [2/2] Failure Predictor Inference Monitor")
    print(f"        Table: {failure_table}")
    try:
        monitor = create_failure_predictor_inference_monitor(workspace_client, catalog, gold_schema, spark)
        if monitor:
            print(f"        [✓] Created successfully")
            results["failure_predictor"] = "OK"
        else:
            print(f"        [⊘] Table not available yet (ML predictions pending)")
            results["failure_predictor"] = "SKIP"
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            print(f"        [⊘] Table does not exist yet")
            results["failure_predictor"] = "SKIP"
        else:
            print(f"        [✗] Error: {error_msg[:80]}")
            results["failure_predictor"] = "FAIL"

    return results


# COMMAND ----------

def main():
    """Main entry point."""
    print("=" * 70)
    print("ML INFERENCE MONITOR SETUP")
    print("=" * 70)
    print(f"  Catalog: {catalog}")
    print(f"  Schema: {gold_schema}")
    print("-" * 70)
    
    if not check_monitoring_available():
        print("[⊘ SKIPPED] Lakehouse Monitoring SDK not available")
        dbutils.notebook.exit("SKIPPED: SDK not available")
        return

    workspace_client = WorkspaceClient()

    try:
        results = create_inference_monitor(workspace_client, catalog, gold_schema, spark)

        ok_count = sum(1 for v in results.values() if v == "OK")
        skip_count = sum(1 for v in results.values() if v == "SKIP")
        fail_count = sum(1 for v in results.values() if v == "FAIL")

        print("\n" + "-" * 70)
        print("SUMMARY:")
        print(f"  ✓ Created: {ok_count}")
        print(f"  ⊘ Skipped: {skip_count} (tables not available yet)")
        print(f"  ✗ Failed:  {fail_count}")
        print("-" * 70)

        if ok_count > 0:
            dbutils.notebook.exit(f"SUCCESS: {ok_count} inference monitors created")
        elif skip_count > 0 and fail_count == 0:
            dbutils.notebook.exit(f"SKIPPED: ML prediction tables not available")
        else:
            raise RuntimeError(f"{fail_count} monitors failed to create")
    except Exception as e:
        print(f"[✗ FAILED] Unexpected error: {str(e)}")
        raise  # Let job show failure status

# COMMAND ----------

if __name__ == "__main__":
    main()



