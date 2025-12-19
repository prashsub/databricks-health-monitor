# Databricks notebook source
"""
Cost Monitor Configuration
==========================

Lakehouse Monitor for fact_usage table.
Tracks billing data quality, cost trends, and tag compliance.
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

def get_cost_custom_metrics():
    """Define custom metrics for cost monitoring."""
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Core cost metrics
        create_aggregate_metric(
            "total_daily_cost",
            "SUM(list_cost)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_daily_dbu",
            "SUM(usage_quantity)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "avg_cost_per_dbu",
            "AVG(list_price)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "record_count",
            "COUNT(*)",
            "LONG"
        ),

        # Completeness metrics
        create_aggregate_metric(
            "distinct_workspaces",
            "COUNT(DISTINCT workspace_id)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_skus",
            "COUNT(DISTINCT sku_name)",
            "LONG"
        ),
        create_aggregate_metric(
            "null_sku_count",
            "SUM(CASE WHEN sku_name IS NULL THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "null_price_count",
            "SUM(CASE WHEN list_price IS NULL THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Tag hygiene metrics (critical for cost attribution)
        create_aggregate_metric(
            "tagged_record_count",
            "SUM(CASE WHEN is_tagged = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "untagged_record_count",
            "SUM(CASE WHEN is_tagged = FALSE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "tagged_cost_total",
            "SUM(CASE WHEN is_tagged = TRUE THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "untagged_cost_total",
            "SUM(CASE WHEN is_tagged = FALSE THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),

        # SKU breakdown aggregates
        create_aggregate_metric(
            "jobs_compute_cost",
            "SUM(CASE WHEN sku_name LIKE '%JOBS%' THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "sql_compute_cost",
            "SUM(CASE WHEN sku_name LIKE '%SQL%' THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "all_purpose_cost",
            "SUM(CASE WHEN sku_name LIKE '%ALL_PURPOSE%' THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "serverless_cost",
            "SUM(CASE WHEN product_features_is_serverless = TRUE THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),

        # ==========================================
        # WORKFLOW ADVISOR BLOG METRICS (NEW)
        # Source: Workflow Advisor Blog - ALL_PURPOSE cluster inefficiency
        # ==========================================

        # Jobs running on ALL_PURPOSE clusters (inefficient pattern)
        create_aggregate_metric(
            "jobs_on_all_purpose_cost",
            """SUM(CASE
                WHEN sku_name LIKE '%ALL_PURPOSE%'
                 AND usage_metadata['job_id'] IS NOT NULL
                THEN list_cost ELSE 0
            END)""",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "jobs_on_all_purpose_count",
            """COUNT(DISTINCT CASE
                WHEN sku_name LIKE '%ALL_PURPOSE%'
                 AND usage_metadata['job_id'] IS NOT NULL
                THEN usage_metadata['job_id']
            END)""",
            "LONG"
        ),
        # Potential savings if jobs moved from ALL_PURPOSE to JOB clusters (~40% savings)
        create_aggregate_metric(
            "potential_job_cluster_savings",
            """SUM(CASE
                WHEN sku_name LIKE '%ALL_PURPOSE%'
                 AND usage_metadata['job_id'] IS NOT NULL
                THEN list_cost * 0.4
                ELSE 0
            END)""",
            "DOUBLE"
        ),
        # DLT pipeline cost tracking
        create_aggregate_metric(
            "dlt_cost",
            "SUM(CASE WHEN sku_name LIKE '%DLT%' THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),
        # Model serving cost tracking
        create_aggregate_metric(
            "model_serving_cost",
            "SUM(CASE WHEN sku_name LIKE '%MODEL_SERVING%' OR sku_name LIKE '%INFERENCE%' THEN list_cost ELSE 0 END)",
            "DOUBLE"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "null_sku_rate",
            "null_sku_count * 100.0 / NULLIF(record_count, 0)"
        ),
        create_derived_metric(
            "null_price_rate",
            "null_price_count * 100.0 / NULLIF(record_count, 0)"
        ),
        create_derived_metric(
            "tag_coverage_pct",
            "tagged_cost_total * 100.0 / NULLIF(total_daily_cost, 0)"
        ),
        create_derived_metric(
            "untagged_usage_pct",
            "untagged_cost_total * 100.0 / NULLIF(total_daily_cost, 0)"
        ),
        create_derived_metric(
            "serverless_ratio",
            "serverless_cost * 100.0 / NULLIF(total_daily_cost, 0)"
        ),
        create_derived_metric(
            "jobs_cost_share",
            "jobs_compute_cost * 100.0 / NULLIF(total_daily_cost, 0)"
        ),
        create_derived_metric(
            "sql_cost_share",
            "sql_compute_cost * 100.0 / NULLIF(total_daily_cost, 0)"
        ),

        # Workflow Advisor Blog derived metrics (NEW)
        create_derived_metric(
            "all_purpose_cost_ratio",
            "all_purpose_cost * 100.0 / NULLIF(total_daily_cost, 0)"
        ),
        create_derived_metric(
            "jobs_on_all_purpose_ratio",
            "jobs_on_all_purpose_cost * 100.0 / NULLIF(jobs_compute_cost + jobs_on_all_purpose_cost, 0)"
        ),
        create_derived_metric(
            "dlt_cost_share",
            "dlt_cost * 100.0 / NULLIF(total_daily_cost, 0)"
        ),
        create_derived_metric(
            "model_serving_cost_share",
            "model_serving_cost * 100.0 / NULLIF(total_daily_cost, 0)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "cost_drift_pct",
            "(({{current_df}}.total_daily_cost - {{base_df}}.total_daily_cost) / NULLIF({{base_df}}.total_daily_cost, 0)) * 100"
        ),
        create_drift_metric(
            "dbu_drift_pct",
            "(({{current_df}}.total_daily_dbu - {{base_df}}.total_daily_dbu) / NULLIF({{base_df}}.total_daily_dbu, 0)) * 100"
        ),
        create_drift_metric(
            "tag_coverage_drift",
            "{{current_df}}.tag_coverage_pct - {{base_df}}.tag_coverage_pct"
        ),
    ]


def create_cost_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """Create the cost monitor for fact_usage."""
    table_name = f"{catalog}.{gold_schema}.fact_usage"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    # Create monitor
    monitor = create_time_series_monitor(
        workspace_client=workspace_client,
        table_name=table_name,
        timestamp_col="usage_date",
        granularities=["1 day"],
        custom_metrics=get_cost_custom_metrics(),
        slicing_exprs=["workspace_id", "sku_name", "cloud"],
        schedule_cron="0 0 6 * * ?",  # Daily at 6 AM UTC
    )

    return monitor

# COMMAND ----------

def main():
    """Main entry point."""
    if not check_monitoring_available():
        print("Lakehouse Monitoring not available - skipping")
        dbutils.notebook.exit("SKIPPED: SDK not available")
        return

    workspace_client = WorkspaceClient()

    try:
        monitor = create_cost_monitor(workspace_client, catalog, gold_schema, spark)
        if monitor:
            dbutils.notebook.exit("SUCCESS: Cost monitor created")
        else:
            dbutils.notebook.exit("SKIPPED: Monitor already exists")
    except Exception as e:
        dbutils.notebook.exit(f"FAILED: {str(e)}")

# COMMAND ----------

if __name__ == "__main__":
    main()
