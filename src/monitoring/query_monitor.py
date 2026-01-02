# Databricks notebook source
"""
Query Performance Monitor Configuration
=======================================

Lakehouse Monitor for fact_query_history table.
Tracks query latency, efficiency, and warehouse utilization.
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

def get_query_custom_metrics():
    """Define custom metrics for query performance monitoring."""
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Volume metrics
        create_aggregate_metric(
            "query_count",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "successful_queries",
            "SUM(CASE WHEN execution_status = 'FINISHED' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "failed_queries",
            "SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "cancelled_queries",
            "SUM(CASE WHEN execution_status = 'CANCELED' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Duration metrics
        create_aggregate_metric(
            "avg_duration_sec",
            "AVG(total_duration_ms / 1000.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_duration_sec",
            "SUM(total_duration_ms / 1000.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p50_duration_sec",
            "PERCENTILE(total_duration_ms / 1000.0, 0.50)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p95_duration_sec",
            "PERCENTILE(total_duration_ms / 1000.0, 0.95)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p99_duration_sec",
            "PERCENTILE(total_duration_ms / 1000.0, 0.99)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_duration_sec",
            "MAX(total_duration_ms / 1000.0)",
            "DOUBLE"
        ),

        # Queue metrics (warehouse capacity)
        create_aggregate_metric(
            "avg_queue_time_sec",
            "AVG(waiting_at_capacity_duration_ms / 1000.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_queue_time_sec",
            "SUM(waiting_at_capacity_duration_ms / 1000.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "high_queue_count",
            "SUM(CASE WHEN waiting_at_capacity_duration_ms > total_duration_ms * 0.1 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Slow query tracking
        create_aggregate_metric(
            "slow_query_count",
            "SUM(CASE WHEN total_duration_ms > 300000 THEN 1 ELSE 0 END)",  # > 5 min
            "LONG"
        ),
        create_aggregate_metric(
            "very_slow_query_count",
            "SUM(CASE WHEN total_duration_ms > 900000 THEN 1 ELSE 0 END)",  # > 15 min
            "LONG"
        ),

        # ==========================================
        # DBSQL WAREHOUSE ADVISOR BLOG METRICS (NEW)
        # Source: DBSQL Warehouse Advisor v5 Blog - 60s SLA threshold
        # ==========================================

        # SLA breach tracking (60-second threshold from blog)
        create_aggregate_metric(
            "sla_breach_count",
            "SUM(CASE WHEN total_duration_ms > 60000 THEN 1 ELSE 0 END)",  # > 60 seconds
            "LONG"
        ),
        # Query efficiency classification
        create_aggregate_metric(
            "efficient_query_count",
            """SUM(CASE
                WHEN spilled_local_bytes = 0
                 AND waiting_at_capacity_duration_ms <= total_duration_ms * 0.1
                 AND total_duration_ms <= 60000
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),
        # High queue time queries (>10% of duration spent in queue)
        create_aggregate_metric(
            "high_queue_severe_count",
            "SUM(CASE WHEN waiting_at_capacity_duration_ms > total_duration_ms * 0.3 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        # Query complexity metrics
        create_aggregate_metric(
            "complex_query_count",
            "SUM(CASE WHEN LENGTH(COALESCE(statement_text, '')) > 5000 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Data volume metrics
        create_aggregate_metric(
            "total_bytes_read_tb",
            "SUM(read_bytes) / (1024.0*1024.0*1024.0*1024.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_rows_read_b",
            "SUM(read_rows) / 1000000000.0",  # Billions
            "DOUBLE"
        ),
        create_aggregate_metric(
            "avg_bytes_per_query",
            "AVG(read_bytes)",
            "DOUBLE"
        ),

        # Spill metrics (memory pressure indicator)
        create_aggregate_metric(
            "queries_with_spill",
            "SUM(CASE WHEN spilled_local_bytes > 0 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "total_spilled_bytes",
            "SUM(spilled_local_bytes)",
            "DOUBLE"
        ),

        # Cache metrics
        create_aggregate_metric(
            "cache_hit_count",
            "SUM(CASE WHEN from_result_cache = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Compilation metrics
        create_aggregate_metric(
            "avg_compilation_sec",
            "AVG(compilation_duration_ms / 1000.0)",
            "DOUBLE"
        ),

        # Distinct entities
        create_aggregate_metric(
            "distinct_users",
            "COUNT(DISTINCT executed_by)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_warehouses",
            "COUNT(DISTINCT compute_warehouse_id)",
            "LONG"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "query_success_rate",
            "successful_queries * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "query_failure_rate",
            "failed_queries * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "high_queue_rate",
            "high_queue_count * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "slow_query_rate",
            "slow_query_count * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "spill_rate",
            "queries_with_spill * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "cache_hit_rate",
            "cache_hit_count * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "avg_queries_per_user",
            "query_count * 1.0 / NULLIF(distinct_users, 0)"
        ),

        # DBSQL Warehouse Advisor Blog derived metrics (NEW)
        create_derived_metric(
            "sla_breach_rate",
            "sla_breach_count * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "efficiency_rate",
            "efficient_query_count * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "severe_queue_rate",
            "high_queue_severe_count * 100.0 / NULLIF(query_count, 0)"
        ),
        create_derived_metric(
            "complex_query_rate",
            "complex_query_count * 100.0 / NULLIF(query_count, 0)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "p95_duration_drift_pct",
            "(({{current_df}}.p95_duration_sec - {{base_df}}.p95_duration_sec) / NULLIF({{base_df}}.p95_duration_sec, 0)) * 100"
        ),
        create_drift_metric(
            "query_volume_drift_pct",
            "(({{current_df}}.query_count - {{base_df}}.query_count) / NULLIF({{base_df}}.query_count, 0)) * 100"
        ),
        create_drift_metric(
            "failure_rate_drift",
            "{{current_df}}.query_failure_rate - {{base_df}}.query_failure_rate"
        ),
        create_drift_metric(
            "spill_rate_drift",
            "{{current_df}}.spill_rate - {{base_df}}.spill_rate"
        ),

        # DBSQL Warehouse Advisor Blog drift metrics (NEW)
        create_drift_metric(
            "sla_breach_rate_drift",
            "{{current_df}}.sla_breach_rate - {{base_df}}.sla_breach_rate"
        ),
        create_drift_metric(
            "efficiency_rate_drift",
            "{{current_df}}.efficiency_rate - {{base_df}}.efficiency_rate"
        ),
        create_drift_metric(
            "p99_duration_drift_pct",
            "(({{current_df}}.p99_duration_sec - {{base_df}}.p99_duration_sec) / NULLIF({{base_df}}.p99_duration_sec, 0)) * 100"
        ),
    ]


def create_query_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """Create the query performance monitor for fact_query_history."""
    table_name = f"{catalog}.{gold_schema}.fact_query_history"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    # Create monitor (pass spark to create monitoring schema if needed)
    # Slicing enables dimensional analysis in Genie queries:
    #   - workspace_id: "Query performance by workspace"
    #   - compute_warehouse_id: "Which warehouse is slowest?"
    #   - execution_status: "Failed vs successful queries"
    #   - statement_type: "SELECT vs INSERT performance"
    #   - executed_by: "Queries by user"
    monitor = create_time_series_monitor(
        workspace_client=workspace_client,
        table_name=table_name,
        timestamp_col="start_time",
        granularities=["1 hour", "1 day"],
        custom_metrics=get_query_custom_metrics(),
        slicing_exprs=[
            "workspace_id",
            "compute_warehouse_id",
            "execution_status",
            "statement_type",
            "executed_by"
        ],
        schedule_cron="0 0 * * * ?",  # Hourly
        spark=spark,  # Pass spark to create monitoring schema
    )

    return monitor

# COMMAND ----------

def main():
    """Main entry point."""
    table_name = f"{catalog}.{gold_schema}.fact_query_history"
    custom_metrics = get_query_custom_metrics()
    num_metrics = len(custom_metrics)
    
    print("=" * 70)
    print("QUERY PERFORMANCE MONITOR SETUP")
    print("=" * 70)
    print(f"  Target Table:    {table_name}")
    print(f"  Catalog:         {catalog}")
    print(f"  Schema:          {gold_schema}")
    print(f"  Custom Metrics:  {num_metrics}")
    print(f"  Timestamp Col:   start_time")
    print(f"  Granularity:     1 hour, 1 day")
    print(f"  Slicing:         workspace_id, compute_warehouse_id, execution_status, statement_type, executed_by")
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
        monitor = create_query_monitor(workspace_client, catalog, gold_schema, spark)
        
        print("[3/3] Verifying monitor status...")
        if monitor:
            print("-" * 70)
            print("[✓ SUCCESS] Query performance monitor created!")
            print(f"  Custom Metrics:  {num_metrics} configured")
            dbutils.notebook.exit(f"SUCCESS: Query monitor created with {num_metrics} metrics")
        else:
            print("-" * 70)
            print("[⊘ SKIPPED] Monitor already exists - no action needed")
            dbutils.notebook.exit("SKIPPED: Query monitor already exists")
    except Exception as e:
        print("-" * 70)
        print(f"[✗ FAILED] Error creating query monitor")
        print(f"  Error Type:  {type(e).__name__}")
        print(f"  Error:       {str(e)}")
        raise  # Let job show failure status

# COMMAND ----------

# Call main() directly - __name__ check doesn't work in Databricks job notebooks
main()
