# Databricks notebook source
"""
Data Quality Monitor Configuration
==================================

Lakehouse Monitor for data quality tracking.
Tracks quality scores, rule violations, and data freshness.

Agent Domain: ✅ Quality
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

def get_quality_custom_metrics():
    """
    Define custom metrics for data quality monitoring.
    
    Tracks:
    - Quality scores and trends
    - Rule evaluation results
    - Violation counts by severity
    - Data freshness patterns
    """
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================

        # Volume metrics
        create_aggregate_metric(
            "total_evaluations",
            "COUNT(*)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_tables",
            "COUNT(DISTINCT table_name)",
            "LONG"
        ),
        create_aggregate_metric(
            "distinct_catalogs",
            "COUNT(DISTINCT catalog_name)",
            "LONG"
        ),

        # Quality score metrics
        create_aggregate_metric(
            "avg_quality_score",
            "AVG(quality_score)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "min_quality_score",
            "MIN(quality_score)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "max_quality_score",
            "MAX(quality_score)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p50_quality_score",
            "PERCENTILE(quality_score, 0.50)",
            "DOUBLE"
        ),
        create_aggregate_metric(
            "p25_quality_score",
            "PERCENTILE(quality_score, 0.25)",
            "DOUBLE"
        ),

        # Rule evaluation metrics
        create_aggregate_metric(
            "total_rules_evaluated",
            "SUM(COALESCE(rules_count, 0))",
            "LONG"
        ),
        create_aggregate_metric(
            "total_rules_passed",
            "SUM(COALESCE(rules_passed, 0))",
            "LONG"
        ),
        create_aggregate_metric(
            "total_rules_failed",
            "SUM(COALESCE(rules_count, 0) - COALESCE(rules_passed, 0))",
            "LONG"
        ),

        # Violation severity breakdown
        create_aggregate_metric(
            "critical_violation_count",
            "SUM(COALESCE(critical_violations, 0))",
            "LONG"
        ),
        create_aggregate_metric(
            "warning_violation_count",
            "SUM(COALESCE(warning_violations, 0))",
            "LONG"
        ),
        create_aggregate_metric(
            "info_violation_count",
            "SUM(COALESCE(info_violations, 0))",
            "LONG"
        ),

        # Tables with issues
        create_aggregate_metric(
            "tables_with_violations",
            "COUNT(DISTINCT CASE WHEN COALESCE(rules_passed, 0) < COALESCE(rules_count, 0) THEN table_name END)",
            "LONG"
        ),
        create_aggregate_metric(
            "tables_with_critical",
            "COUNT(DISTINCT CASE WHEN COALESCE(critical_violations, 0) > 0 THEN table_name END)",
            "LONG"
        ),
        create_aggregate_metric(
            "tables_fully_passing",
            "COUNT(DISTINCT CASE WHEN COALESCE(rules_passed, 0) = COALESCE(rules_count, 0) AND COALESCE(rules_count, 0) > 0 THEN table_name END)",
            "LONG"
        ),

        # Quality score distribution
        create_aggregate_metric(
            "tables_score_above_90",
            "COUNT(DISTINCT CASE WHEN quality_score >= 0.9 THEN table_name END)",
            "LONG"
        ),
        create_aggregate_metric(
            "tables_score_below_80",
            "COUNT(DISTINCT CASE WHEN quality_score < 0.8 THEN table_name END)",
            "LONG"
        ),
        create_aggregate_metric(
            "tables_score_below_70",
            "COUNT(DISTINCT CASE WHEN quality_score < 0.7 THEN table_name END)",
            "LONG"
        ),

        # Row count metrics (data freshness)
        create_aggregate_metric(
            "total_rows_scanned",
            "SUM(COALESCE(row_count, 0))",
            "LONG"
        ),
        create_aggregate_metric(
            "avg_row_count",
            "AVG(COALESCE(row_count, 0))",
            "DOUBLE"
        ),

        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================

        create_derived_metric(
            "rule_pass_rate",
            "total_rules_passed * 100.0 / NULLIF(total_rules_evaluated, 0)"
        ),
        create_derived_metric(
            "rule_fail_rate",
            "total_rules_failed * 100.0 / NULLIF(total_rules_evaluated, 0)"
        ),
        create_derived_metric(
            "violation_rate",
            "tables_with_violations * 100.0 / NULLIF(distinct_tables, 0)"
        ),
        create_derived_metric(
            "critical_violation_rate",
            "tables_with_critical * 100.0 / NULLIF(distinct_tables, 0)"
        ),
        create_derived_metric(
            "fully_passing_rate",
            "tables_fully_passing * 100.0 / NULLIF(distinct_tables, 0)"
        ),
        create_derived_metric(
            "high_quality_rate",
            "tables_score_above_90 * 100.0 / NULLIF(distinct_tables, 0)"
        ),
        create_derived_metric(
            "low_quality_rate",
            "tables_score_below_80 * 100.0 / NULLIF(distinct_tables, 0)"
        ),
        create_derived_metric(
            "avg_violations_per_table",
            "(critical_violation_count + warning_violation_count) * 1.0 / NULLIF(distinct_tables, 0)"
        ),
        create_derived_metric(
            "avg_rules_per_table",
            "total_rules_evaluated * 1.0 / NULLIF(total_evaluations, 0)"
        ),

        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================

        create_drift_metric(
            "quality_score_drift",
            "{{current_df}}.avg_quality_score - {{base_df}}.avg_quality_score"
        ),
        create_drift_metric(
            "rule_pass_rate_drift",
            "{{current_df}}.rule_pass_rate - {{base_df}}.rule_pass_rate"
        ),
        create_drift_metric(
            "critical_violation_drift",
            "{{current_df}}.critical_violation_count - {{base_df}}.critical_violation_count"
        ),
        create_drift_metric(
            "violation_rate_drift",
            "{{current_df}}.violation_rate - {{base_df}}.violation_rate"
        ),
        create_drift_metric(
            "tables_evaluated_drift_pct",
            "(({{current_df}}.distinct_tables - {{base_df}}.distinct_tables) / NULLIF({{base_df}}.distinct_tables, 0)) * 100"
        ),
    ]


def create_quality_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """
    Create the data quality monitor for quality monitoring tables.
    
    Note: This monitor tracks the output of DLT expectations or
    custom data quality frameworks. The table name may need to be
    adjusted based on your specific quality tracking implementation.
    """
    # Quality results table (from Lakehouse Monitoring or custom DQ framework)
    table_name = f"{catalog}.{gold_schema}.fact_data_quality_results"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    try:
        # Create monitor (pass spark to create monitoring schema if needed)
        monitor = create_time_series_monitor(
            workspace_client=workspace_client,
            table_name=table_name,
            timestamp_col="evaluation_time",
            granularities=["1 day"],
            custom_metrics=get_quality_custom_metrics(),
            slicing_exprs=["catalog_name", "schema_name"],
            schedule_cron="0 0 7 * * ?",  # Daily at 7 AM UTC
            spark=spark,  # Pass spark to create monitoring schema
        )
        return monitor
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"  Note: Quality table {table_name} does not exist yet.")
            print("  This monitor will be created when the table is available.")
            return None
        raise


# COMMAND ----------

def main():
    """Main entry point."""
    table_name = f"{catalog}.{gold_schema}.fact_data_quality_results"
    
    print("=" * 70)
    print("DATA QUALITY MONITOR SETUP")
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
        monitor = create_quality_monitor(workspace_client, catalog, gold_schema, spark)
        if monitor:
            print("-" * 70)
            print("[✓ SUCCESS] Data quality monitor created successfully!")
            dbutils.notebook.exit("[OK] Quality monitor created")
        else:
            print("-" * 70)
            print("[⊘ SKIPPED] Table not available yet (DQX integration pending)")
            dbutils.notebook.exit("[SKIP] Table not available")
    except Exception as e:
        error_msg = str(e)
        print("-" * 70)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            print(f"[⊘ SKIPPED] Table does not exist yet")
            print(f"  Note: This table will be created when DQX integration is enabled")
            dbutils.notebook.exit("[SKIP] Table not exists")
        else:
            print(f"[✗ FAILED] Error creating quality monitor")
            print(f"  Error: {error_msg}")
            dbutils.notebook.exit(f"[FAIL] {error_msg[:100]}")

# COMMAND ----------

if __name__ == "__main__":
    main()



