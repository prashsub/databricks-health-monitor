# Databricks notebook source
"""
Governance and Lineage Monitor Configuration
============================================

Lakehouse Monitor for fact_table_lineage table.
Tracks data lineage events, table activity, and governance patterns.

Agent Domain: 🔒 Security / ✅ Quality
Source: Governance Hub Dashboard patterns
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

def get_governance_custom_metrics():
    """
    Define custom metrics for governance and lineage monitoring.
    
    Based on Governance Hub Dashboard patterns:
    - Active vs inactive table tracking
    - Read/write ratio analysis
    - User data consumption patterns
    - Sensitive data access monitoring
    """
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Event volume metrics
        create_aggregate_metric(
            "total_lineage_events",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_users",
            "COUNT(DISTINCT created_by)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_workspaces",
            "COUNT(DISTINCT workspace_id)",
            "LONG"
        ),

        # Table activity metrics
        create_aggregate_metric(
            "active_tables_count",
            "COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name))",
            "LONG"
        ),
        create_aggregate_metric(
            "active_source_tables",
            "COUNT(DISTINCT source_table_full_name)",
            "LONG"
        ),
        create_aggregate_metric(
            "active_target_tables",
            "COUNT(DISTINCT target_table_full_name)",
            "LONG"
        ),

        # Read/Write breakdown (from Governance Hub pattern)
        create_aggregate_metric(
            "read_event_count",
            "SUM(CASE WHEN source_table_full_name IS NOT NULL THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "write_event_count",
            "SUM(CASE WHEN target_table_full_name IS NOT NULL THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Entity type breakdown
        create_aggregate_metric(
            "table_entity_events",
            "SUM(CASE WHEN entity_type = 'TABLE' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "notebook_entity_events",
            "SUM(CASE WHEN entity_type = 'NOTEBOOK' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "pipeline_entity_events",
            "SUM(CASE WHEN entity_type = 'PIPELINE' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "job_entity_events",
            "SUM(CASE WHEN entity_type = 'JOB' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "query_entity_events",
            "SUM(CASE WHEN entity_type = 'QUERY' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Data consumption patterns
        create_aggregate_metric(
            "unique_data_consumers",
            "COUNT(DISTINCT CASE WHEN source_table_full_name IS NOT NULL THEN created_by END)",
            "LONG"
        ),
        create_aggregate_metric(
            "unique_data_producers",
            "COUNT(DISTINCT CASE WHEN target_table_full_name IS NOT NULL THEN created_by END)",
            "LONG"
        ),

        # Sensitive data tracking (from Governance Hub patterns)
        create_aggregate_metric(
            "sensitive_table_access_count",
            """SUM(CASE
                WHEN source_table_full_name LIKE '%pii%'
                  OR source_table_full_name LIKE '%sensitive%'
                  OR source_table_full_name LIKE '%confidential%'
                  OR target_table_full_name LIKE '%pii%'
                  OR target_table_full_name LIKE '%sensitive%'
                THEN 1 ELSE 0
            END)""",
            "LONG"
        ),

        # Gold layer access tracking
        create_aggregate_metric(
            "gold_layer_reads",
            "SUM(CASE WHEN source_table_full_name LIKE '%gold%' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "gold_layer_writes",
            "SUM(CASE WHEN target_table_full_name LIKE '%gold%' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "silver_layer_reads",
            "SUM(CASE WHEN source_table_full_name LIKE '%silver%' THEN 1 ELSE 0 END)",
            "LONG"
        ),
        create_aggregate_metric(
            "bronze_layer_reads",
            "SUM(CASE WHEN source_table_full_name LIKE '%bronze%' THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # Cross-catalog access (potential governance concern)
        create_aggregate_metric(
            "distinct_source_catalogs",
            "COUNT(DISTINCT source_table_catalog)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_target_catalogs",
            "COUNT(DISTINCT target_table_catalog)",
            "LONG"
        ),

        # Off-hours lineage events
        create_aggregate_metric(
            "off_hours_events",
            "SUM(CASE WHEN HOUR(event_time) < 6 OR HOUR(event_time) > 22 THEN 1 ELSE 0 END)",
            "LONG"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "read_write_ratio",
            "read_event_count * 1.0 / NULLIF(write_event_count, 0)"
        ),
        create_derived_metric(
            "avg_events_per_user",
            "total_lineage_events * 1.0 / NULLIF(distinct_users, 0)"
        ),
        create_derived_metric(
            "avg_tables_per_user",
            "active_tables_count * 1.0 / NULLIF(distinct_users, 0)"
        ),
        create_derived_metric(
            "consumer_producer_ratio",
            "unique_data_consumers * 1.0 / NULLIF(unique_data_producers, 0)"
        ),
        create_derived_metric(
            "sensitive_access_rate",
            "sensitive_table_access_count * 100.0 / NULLIF(total_lineage_events, 0)"
        ),
        create_derived_metric(
            "off_hours_rate",
            "off_hours_events * 100.0 / NULLIF(total_lineage_events, 0)"
        ),
        create_derived_metric(
            "gold_layer_access_rate",
            "(gold_layer_reads + gold_layer_writes) * 100.0 / NULLIF(total_lineage_events, 0)"
        ),
        create_derived_metric(
            "notebook_activity_rate",
            "notebook_entity_events * 100.0 / NULLIF(total_lineage_events, 0)"
        ),
        create_derived_metric(
            "pipeline_activity_rate",
            "pipeline_entity_events * 100.0 / NULLIF(total_lineage_events, 0)"
        ),
        create_derived_metric(
            "cross_catalog_complexity",
            "(distinct_source_catalogs + distinct_target_catalogs) * 1.0 / 2"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "active_tables_drift",
            "{{current_df}}.active_tables_count - {{base_df}}.active_tables_count"
        ),
        create_drift_metric(
            "lineage_volume_drift_pct",
            "(({{current_df}}.total_lineage_events - {{base_df}}.total_lineage_events) / NULLIF({{base_df}}.total_lineage_events, 0)) * 100"
        ),
        create_drift_metric(
            "read_write_ratio_drift",
            "{{current_df}}.read_write_ratio - {{base_df}}.read_write_ratio"
        ),
        create_drift_metric(
            "sensitive_access_drift",
            "{{current_df}}.sensitive_table_access_count - {{base_df}}.sensitive_table_access_count"
        ),
        create_drift_metric(
            "user_count_drift",
            "{{current_df}}.distinct_users - {{base_df}}.distinct_users"
        ),
        create_drift_metric(
            "off_hours_rate_drift",
            "{{current_df}}.off_hours_rate - {{base_df}}.off_hours_rate"
        ),
    ]


def create_governance_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """
    Create the governance monitor for fact_table_lineage.
    
    Tracks data lineage events for governance and security analysis.
    Based on Governance Hub Dashboard patterns.
    """
    table_name = f"{catalog}.{gold_schema}.fact_table_lineage"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    try:
        # Create monitor (pass spark to create monitoring schema if needed)
        monitor = create_time_series_monitor(
            workspace_client=workspace_client,
            table_name=table_name,
            timestamp_col="event_date",
            granularities=["1 day"],
            custom_metrics=get_governance_custom_metrics(),
            slicing_exprs=["workspace_id", "entity_type"],
            schedule_cron="0 0 6 * * ?",  # Daily at 6 AM UTC
            spark=spark,  # Pass spark to create monitoring schema
        )
        return monitor
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"  Note: Lineage table {table_name} does not exist yet.")
            print("  This monitor will be created when the table is available.")
            return None
        raise


# COMMAND ----------

def main():
    """Main entry point."""
    table_name = f"{catalog}.{gold_schema}.fact_table_lineage"
    
    print("=" * 70)
    print("GOVERNANCE & LINEAGE MONITOR SETUP")
    print("=" * 70)
    print(f"  Target Table: {table_name}")
    print(f"  Catalog: {catalog}")
    print(f"  Schema: {gold_schema}")
    print("-" * 70)
    
    if not check_monitoring_available():
        print("[⊘ SKIPPED] Lakehouse Monitoring SDK not available")
        dbutils.notebook.exit("[SKIP] SDK not available")
        return

    workspace_client = WorkspaceClient()

    try:
        monitor = create_governance_monitor(workspace_client, catalog, gold_schema, spark)
        if monitor:
            print("-" * 70)
            print("[✓ SUCCESS] Governance & lineage monitor created successfully!")
            dbutils.notebook.exit("[OK] Governance monitor created")
        else:
            print("-" * 70)
            print("[⊘ SKIPPED] Table not available yet")
            dbutils.notebook.exit("[SKIP] Table not available")
    except Exception as e:
        error_msg = str(e)
        print("-" * 70)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            print(f"[⊘ SKIPPED] Table does not exist yet")
            dbutils.notebook.exit("[SKIP] Table not exists")
        else:
            print(f"[✗ FAILED] Error creating governance monitor")
            print(f"  Error: {error_msg}")
            dbutils.notebook.exit(f"[FAIL] {error_msg[:100]}")

# COMMAND ----------

if __name__ == "__main__":
    main()



