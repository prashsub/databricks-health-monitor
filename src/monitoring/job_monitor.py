# Databricks notebook source
"""
Job Reliability Monitor Configuration
=====================================

Lakehouse Monitor for fact_job_run_timeline table.
Tracks job success rates, failures, and duration patterns.
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

def get_job_custom_metrics():
    """Define custom metrics for job reliability monitoring."""
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Core reliability metrics
        create_aggregate_metric(
            "total_runs",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "success_count",
            "SUM(CASE WHEN is_success = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "failure_count",
            "SUM(CASE WHEN result_state IN ('FAILED', 'ERROR') THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "timeout_count",
            "SUM(CASE WHEN result_state = 'TIMED_OUT' OR termination_code = 'TIMED_OUT' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "cancelled_count",
            "SUM(CASE WHEN result_state = 'CANCELED' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Duration metrics
        create_aggregate_metric(
            "avg_duration_minutes",
            "AVG(run_duration_minutes)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_duration_minutes",
            "SUM(run_duration_minutes)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_duration_minutes",
            "MAX(run_duration_minutes)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "min_duration_minutes",
            "MIN(run_duration_minutes)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p50_duration_minutes",
            "PERCENTILE(run_duration_minutes, 0.50)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p95_duration_minutes",
            "PERCENTILE(run_duration_minutes, 0.95)",
            "DOUBLE"
        ),
        # P99 duration for SLA monitoring (NEW)
        create_aggregate_metric(
            "p99_duration_minutes",
            "PERCENTILE(run_duration_minutes, 0.99)",
            "DOUBLE"
        ),

        # ==========================================
        # DASHBOARD PATTERN METRICS (NEW)
        # Source: Dashboard P90 outlier detection pattern
        # ==========================================

        # P90 duration for outlier baseline
        create_aggregate_metric(
            "p90_duration_minutes",
            "PERCENTILE(run_duration_minutes, 0.90)",
            "DOUBLE"
        ),
        # Duration standard deviation for regression detection
        create_aggregate_metric(
            "stddev_duration_minutes",
            "STDDEV(run_duration_minutes)",
            "DOUBLE"
        ),
        # Duration coefficient of variation (stddev / mean)
        # Note: Computed as derived metric since AGGREGATE can't reference other metrics

        # Outcome category breakdown (NEW)
        create_aggregate_metric(
            "skipped_count",
            "SUM(CASE WHEN result_state = 'SKIPPED' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "upstream_failed_count",
            "SUM(CASE WHEN result_state = 'UPSTREAM_FAILED' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        # Long running jobs (>1 hour)
        create_aggregate_metric(
            "long_running_count",
            "SUM(CASE WHEN run_duration_minutes > 60 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        # Very long running jobs (>4 hours)
        create_aggregate_metric(
            "very_long_running_count",
            "SUM(CASE WHEN run_duration_minutes > 240 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Job/run counts
        create_aggregate_metric(
            "distinct_jobs",
            "COUNT(DISTINCT job_id)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_runs",
            "COUNT(DISTINCT run_id)",
            "LONG"
        ),

        # Trigger type breakdown
        create_aggregate_metric(
            "scheduled_runs",
            "SUM(CASE WHEN trigger_type = 'SCHEDULE' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "manual_runs",
            "SUM(CASE WHEN trigger_type = 'MANUAL' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "retry_runs",
            "SUM(CASE WHEN trigger_type = 'RETRY' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Termination code breakdown
        create_aggregate_metric(
            "user_cancelled_count",
            "SUM(CASE WHEN termination_code = 'USER_CANCELED' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "internal_error_count",
            "SUM(CASE WHEN termination_code = 'INTERNAL_ERROR' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "driver_error_count",
            "SUM(CASE WHEN termination_code = 'DRIVER_ERROR' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "success_rate",
            "success_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "failure_rate",
            "failure_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "timeout_rate",
            "timeout_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "cancellation_rate",
            "cancelled_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "repair_rate",
            "retry_runs * 100.0 / NULLIF(distinct_runs, 0)"
        ),
        create_derived_metric(
            "scheduled_ratio",
            "scheduled_runs * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "avg_runs_per_job",
            "total_runs * 1.0 / NULLIF(distinct_jobs, 0)"
        ),

        # Dashboard pattern derived metrics (NEW)
        create_derived_metric(
            "duration_cv",
            "stddev_duration_minutes / NULLIF(avg_duration_minutes, 0)"
        ),
        create_derived_metric(
            "skipped_rate",
            "skipped_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "upstream_failed_rate",
            "upstream_failed_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "long_running_rate",
            "long_running_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        create_derived_metric(
            "very_long_running_rate",
            "very_long_running_count * 100.0 / NULLIF(total_runs, 0)"
        ),
        # P90 to P50 ratio (indicates distribution skewness)
        create_derived_metric(
            "duration_skew_ratio",
            "p90_duration_minutes / NULLIF(p50_duration_minutes, 0)"
        ),
        # P99 to P95 ratio (tail behavior)
        create_derived_metric(
            "tail_ratio",
            "p99_duration_minutes / NULLIF(p95_duration_minutes, 0)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "success_rate_drift",
            "{{current_df}}.success_rate - {{base_df}}.success_rate"
        ),
        create_drift_metric(
            "failure_count_drift",
            "{{current_df}}.failure_count - {{base_df}}.failure_count"
        ),
        create_drift_metric(
            "run_count_drift_pct",
            "(({{current_df}}.total_runs - {{base_df}}.total_runs) / NULLIF({{base_df}}.total_runs, 0)) * 100"
        ),
        create_drift_metric(
            "duration_drift_pct",
            "(({{current_df}}.avg_duration_minutes - {{base_df}}.avg_duration_minutes) / NULLIF({{base_df}}.avg_duration_minutes, 0)) * 100"
        ),

        # Dashboard pattern drift metrics (NEW)
        create_drift_metric(
            "p99_duration_drift_pct",
            "(({{current_df}}.p99_duration_minutes - {{base_df}}.p99_duration_minutes) / NULLIF({{base_df}}.p99_duration_minutes, 0)) * 100"
        ),
        create_drift_metric(
            "p90_duration_drift_pct",
            "(({{current_df}}.p90_duration_minutes - {{base_df}}.p90_duration_minutes) / NULLIF({{base_df}}.p90_duration_minutes, 0)) * 100"
        ),
        create_drift_metric(
            "duration_cv_drift",
            "{{current_df}}.duration_cv - {{base_df}}.duration_cv"
        ),
        create_drift_metric(
            "long_running_drift",
            "{{current_df}}.long_running_count - {{base_df}}.long_running_count"
        ),
    ]


def create_job_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """Create the job reliability monitor for fact_job_run_timeline."""
    table_name = f"{catalog}.{gold_schema}.fact_job_run_timeline"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    # Create monitor (pass spark to create monitoring schema if needed)
    monitor = create_time_series_monitor(
        workspace_client=workspace_client,
        table_name=table_name,
        timestamp_col="run_date",
        granularities=["1 hour", "1 day"],
        custom_metrics=get_job_custom_metrics(),
        slicing_exprs=["workspace_id", "result_state", "trigger_type"],
        schedule_cron="0 0 * * * ?",  # Hourly
        spark=spark,  # Pass spark to create monitoring schema
    )

    return monitor

# COMMAND ----------

def main():
    """Main entry point."""
    table_name = f"{catalog}.{gold_schema}.fact_job_run_timeline"
    custom_metrics = get_job_custom_metrics()
    num_metrics = len(custom_metrics)
    
    print("=" * 70)
    print("JOB RELIABILITY MONITOR SETUP")
    print("=" * 70)
    print(f"  Target Table:    {table_name}")
    print(f"  Catalog:         {catalog}")
    print(f"  Schema:          {gold_schema}")
    print(f"  Custom Metrics:  {num_metrics}")
    print(f"  Timestamp Col:   run_date")
    print(f"  Granularity:     1 hour, 1 day")
    print(f"  Slicing:         workspace_id, result_state, trigger_type")
    print(f"  Schedule:        Hourly")
    print("-" * 70)
    
    if not check_monitoring_available():
        print("[⊘ SKIPPED] Lakehouse Monitoring SDK not available")
        dbutils.notebook.exit("SKIPPED: SDK not available")
        return

    print("[1/3] Initializing WorkspaceClient...")
    workspace_client = WorkspaceClient()
    print("      WorkspaceClient ready")

    try:
        print("[2/3] Checking for existing monitor...")
        monitor = create_job_monitor(workspace_client, catalog, gold_schema, spark)
        
        print("[3/3] Verifying monitor status...")
        if monitor:
            print("-" * 70)
            print("[✓ SUCCESS] Job reliability monitor created!")
            print(f"  Custom Metrics:  {num_metrics} configured")
            dbutils.notebook.exit(f"SUCCESS: Job monitor created with {num_metrics} metrics")
        else:
            print("-" * 70)
            print("[⊘ SKIPPED] Monitor already exists - no action needed")
            dbutils.notebook.exit("SKIPPED: Job monitor already exists")
    except Exception as e:
        print("-" * 70)
        print(f"[✗ FAILED] Error creating job monitor")
        print(f"  Error Type:  {type(e).__name__}")
        print(f"  Error:       {str(e)}")
        raise  # Let job show failure status

# COMMAND ----------

# Call main() directly - __name__ check doesn't work in Databricks job notebooks
main()
