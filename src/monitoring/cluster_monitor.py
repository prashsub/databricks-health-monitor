# Databricks notebook source
"""
Cluster Utilization Monitor Configuration
=========================================

Lakehouse Monitor for fact_node_timeline table.
Tracks CPU, memory, and network utilization for right-sizing.
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

def get_cluster_custom_metrics():
    """Define custom metrics for cluster utilization monitoring."""
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Node counts
        create_aggregate_metric(
            "node_hour_count",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_nodes",
            "COUNT(DISTINCT instance_id)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_clusters",
            "COUNT(DISTINCT cluster_id)",
            "LONG"
        ),
        create_aggregate_metric(
            "driver_node_count",
            "SUM(CASE WHEN driver = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "worker_node_count",
            "SUM(CASE WHEN driver = FALSE OR driver IS NULL THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # CPU metrics
        create_aggregate_metric(
            "avg_cpu_user_pct",
            "AVG(cpu_user_percent)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "avg_cpu_system_pct",
            "AVG(cpu_system_percent)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "avg_cpu_wait_pct",
            "AVG(cpu_wait_percent)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_cpu_user_pct",
            "MAX(cpu_user_percent)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_cpu_total_pct",
            "MAX(cpu_user_percent + cpu_system_percent)",
            "DOUBLE"
        ),

        # Memory metrics
        create_aggregate_metric(
            "avg_memory_pct",
            "AVG(mem_used_percent)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_memory_pct",
            "MAX(mem_used_percent)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "avg_swap_pct",
            "AVG(mem_swap_percent)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_swap_pct",
            "MAX(mem_swap_percent)",
            "DOUBLE"
        ),

        # Network metrics
        create_aggregate_metric(
            "total_network_sent_gb",
            "SUM(network_sent_bytes) / (1024.0*1024.0*1024.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "total_network_received_gb",
            "SUM(network_received_bytes) / (1024.0*1024.0*1024.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "avg_network_sent_mb",
            "AVG(network_sent_bytes) / (1024.0*1024.0)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "avg_network_received_mb",
            "AVG(network_received_bytes) / (1024.0*1024.0)",
            "DOUBLE"
        ),

        # Utilization thresholds
        create_aggregate_metric(
            "underutilized_hours",
            "SUM(CASE WHEN cpu_user_percent < 20 AND mem_used_percent < 30 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "overutilized_hours",
            "SUM(CASE WHEN cpu_user_percent + cpu_system_percent > 80 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "high_io_wait_hours",
            "SUM(CASE WHEN cpu_wait_percent > 20 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "high_swap_hours",
            "SUM(CASE WHEN mem_swap_percent > 10 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "memory_pressure_hours",
            "SUM(CASE WHEN mem_used_percent > 90 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # ==========================================
        # WORKFLOW ADVISOR REPO METRICS (NEW)
        # Source: Workflow Advisor Repo - Right-sizing detection
        # ==========================================

        # P95 CPU utilization for peak analysis
        create_aggregate_metric(
            "p95_cpu_total_pct",
            "PERCENTILE(cpu_user_percent + cpu_system_percent, 0.95)",
            "DOUBLE"
        ),
        # P95 memory utilization
        create_aggregate_metric(
            "p95_memory_pct",
            "PERCENTILE(mem_used_percent, 0.95)",
            "DOUBLE"
        ),
        # CPU saturation detection (>90% indicates underprovisioning)
        create_aggregate_metric(
            "cpu_saturation_hours",
            "SUM(CASE WHEN cpu_user_percent + cpu_system_percent > 90 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        # CPU idle detection (<20% indicates overprovisioning)
        create_aggregate_metric(
            "cpu_idle_hours",
            "SUM(CASE WHEN cpu_user_percent + cpu_system_percent < 20 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        # Memory saturation (>85% indicates need for scale-up)
        create_aggregate_metric(
            "memory_saturation_hours",
            "SUM(CASE WHEN mem_used_percent > 85 THEN 1 ELSE 0 END)",
            "LONG"
        ),
        # Optimal utilization hours (30-80% CPU, 30-85% memory)
        create_aggregate_metric(
            "optimal_util_hours",
            """SUM(CASE
                WHEN (cpu_user_percent + cpu_system_percent) BETWEEN 30 AND 80
                 AND mem_used_percent BETWEEN 30 AND 85
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),
        # Underprovisioned hours (high saturation)
        create_aggregate_metric(
            "underprovisioned_hours",
            """SUM(CASE
                WHEN (cpu_user_percent + cpu_system_percent) > 90
                  OR mem_used_percent > 85
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),
        # Overprovisioned hours (low utilization)
        create_aggregate_metric(
            "overprovisioned_hours",
            """SUM(CASE
                WHEN (cpu_user_percent + cpu_system_percent) < 20
                 AND mem_used_percent < 30
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "avg_cpu_total_pct",
            "avg_cpu_user_pct + avg_cpu_system_pct"
        ),
        create_derived_metric(
            "underutilization_rate",
            "underutilized_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "overutilization_rate",
            "overutilized_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "io_bottleneck_rate",
            "high_io_wait_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "memory_pressure_rate",
            "memory_pressure_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "swap_usage_rate",
            "high_swap_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "total_network_gb",
            "total_network_sent_gb + total_network_received_gb"
        ),
        create_derived_metric(
            "avg_nodes_per_cluster",
            "distinct_nodes * 1.0 / NULLIF(distinct_clusters, 0)"
        ),

        # Workflow Advisor Repo derived metrics (NEW)
        create_derived_metric(
            "cpu_saturation_rate",
            "cpu_saturation_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "cpu_idle_rate",
            "cpu_idle_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "memory_saturation_rate",
            "memory_saturation_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "optimal_util_rate",
            "optimal_util_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "underprovisioned_rate",
            "underprovisioned_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        create_derived_metric(
            "overprovisioned_rate",
            "overprovisioned_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        # Efficiency score (optimal / total) - higher is better
        create_derived_metric(
            "efficiency_score",
            "optimal_util_hours * 100.0 / NULLIF(node_hour_count, 0)"
        ),
        # Right-sizing opportunity indicator
        create_derived_metric(
            "rightsizing_opportunity_pct",
            "(underprovisioned_hours + overprovisioned_hours) * 100.0 / NULLIF(node_hour_count, 0)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "cpu_utilization_drift",
            "{{current_df}}.avg_cpu_total_pct - {{base_df}}.avg_cpu_total_pct"
        ),
        create_drift_metric(
            "memory_utilization_drift",
            "{{current_df}}.avg_memory_pct - {{base_df}}.avg_memory_pct"
        ),
        create_drift_metric(
            "underutilization_drift",
            "{{current_df}}.underutilization_rate - {{base_df}}.underutilization_rate"
        ),
        create_drift_metric(
            "network_volume_drift_pct",
            "(({{current_df}}.total_network_gb - {{base_df}}.total_network_gb) / NULLIF({{base_df}}.total_network_gb, 0)) * 100"
        ),

        # Workflow Advisor Repo drift metrics (NEW)
        create_drift_metric(
            "efficiency_score_drift",
            "{{current_df}}.efficiency_score - {{base_df}}.efficiency_score"
        ),
        create_drift_metric(
            "rightsizing_opportunity_drift",
            "{{current_df}}.rightsizing_opportunity_pct - {{base_df}}.rightsizing_opportunity_pct"
        ),
        create_drift_metric(
            "p95_cpu_drift",
            "{{current_df}}.p95_cpu_total_pct - {{base_df}}.p95_cpu_total_pct"
        ),
    ]


def create_cluster_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """Create the cluster utilization monitor for fact_node_timeline."""
    table_name = f"{catalog}.{gold_schema}.fact_node_timeline"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    # Create monitor
    monitor = create_time_series_monitor(
        workspace_client=workspace_client,
        table_name=table_name,
        timestamp_col="start_time",
        granularities=["1 hour", "1 day"],
        custom_metrics=get_cluster_custom_metrics(),
        slicing_exprs=["workspace_id", "cluster_id", "node_type"],
        schedule_cron="0 0 * * * ?",  # Hourly
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
        monitor = create_cluster_monitor(workspace_client, catalog, gold_schema, spark)
        if monitor:
            dbutils.notebook.exit("SUCCESS: Cluster monitor created")
        else:
            dbutils.notebook.exit("SKIPPED: Monitor already exists")
    except Exception as e:
        dbutils.notebook.exit(f"FAILED: {str(e)}")

# COMMAND ----------

if __name__ == "__main__":
    main()
