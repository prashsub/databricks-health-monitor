"""
TRAINING MATERIAL: Lakehouse Monitoring Utilities Pattern
=========================================================

Shared utilities for creating and managing Databricks Lakehouse Monitors.

WHAT IS LAKEHOUSE MONITORING:
-----------------------------

┌─────────────────────────────────────────────────────────────────────────┐
│  LAKEHOUSE MONITORING                                                    │
│  ─────────────────────                                                  │
│  Automated data quality tracking for Delta tables.                      │
│                                                                         │
│  When you create a monitor on fact_usage:                               │
│                                                                         │
│  fact_usage (your table)                                                │
│      ↓ Lakehouse Monitoring                                             │
│  fact_usage_profile_metrics  ← Statistics, custom metrics               │
│  fact_usage_drift_metrics    ← Period-over-period comparisons           │
│                                                                         │
│  Runs on schedule (e.g., daily) to track:                               │
│  - Distribution statistics (mean, std, nulls)                           │
│  - Your custom metrics (total_cost, failure_rate)                       │
│  - Drift detection (did cost increase 50%?)                             │
└─────────────────────────────────────────────────────────────────────────┘

CUSTOM METRIC TYPES:
--------------------

1. AGGREGATE - Simple aggregations
   MonitorMetric(type=MonitorMetricType.AGGREGATE, expression="SUM(cost)")
   → Stored in _profile_metrics as column

2. DERIVED - Calculated from aggregates
   MonitorMetric(type=MonitorMetricType.DERIVED, expression="failure_count/total_runs")
   → References other metrics

3. DRIFT - Change detection
   MonitorMetric(type=MonitorMetricType.DRIFT)
   → Stored in _drift_metrics, compares periods

WHY input_columns=[":table"]:
-----------------------------
┌─────────────────────────────────────────────────────────────────────────┐
│  ❌ WRONG: Per-column metrics                                            │
│     input_columns=["cost_value"]                                        │
│     → Metric stored with column_name='cost_value'                       │
│     → Different row for each column!                                    │
│     → DERIVED can't reference AGGREGATE metrics in different rows!      │
│                                                                         │
│  ✅ CORRECT: Table-level metrics                                         │
│     input_columns=[":table"]                                            │
│     → All metrics stored with column_name=':table'                      │
│     → Same row for related metrics!                                     │
│     → DERIVED can reference AGGREGATE metrics                           │
└─────────────────────────────────────────────────────────────────────────┘

SLICING FOR DIMENSIONAL ANALYSIS:
---------------------------------
slicing_exprs=["workspace_id", "sku_name"]

Enables queries like:
  "Show cost by workspace"
  → WHERE slice_key='workspace_id' AND slice_value='prod'

ASYNC TABLE CREATION:
---------------------
Monitors create output tables ASYNCHRONOUSLY (~15 minutes).

┌─────────────────────────────────────────────────────────────────────────┐
│  create_monitor()  →  Returns immediately                               │
│                       Tables don't exist yet!                           │
│                                                                         │
│  wait_for_tables()  →  Poll until tables exist                          │
│                        (or timeout)                                     │
│                                                                         │
│  document_tables()  →  Add descriptions for Genie                       │
│                        (must wait for tables first!)                    │
└─────────────────────────────────────────────────────────────────────────┘

CLEANUP PATTERN:
----------------
Deleting a monitor does NOT delete its output tables.
Must explicitly drop _profile_metrics and _drift_metrics tables.

NOTE: This is a pure Python module (NOT a Databricks notebook).
Do NOT add '# Databricks notebook source' header - notebooks cannot be imported.
"""

import time
from typing import List, Optional

# Graceful import for SDK monitoring classes
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.catalog import (
        MonitorTimeSeries,
        MonitorSnapshot,
        MonitorMetric,
        MonitorMetricType,
        MonitorCronSchedule
    )
    from databricks.sdk.errors import ResourceAlreadyExists, ResourceDoesNotExist
    import pyspark.sql.types as T
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    print("Lakehouse Monitoring classes not available in this SDK version")


def check_monitoring_available() -> bool:
    """Check if Lakehouse Monitoring SDK is available."""
    return MONITORING_AVAILABLE


def delete_monitor_if_exists(
    workspace_client,
    table_name: str,
    spark=None
) -> bool:
    """
    Delete existing monitor and its output tables.

    This is necessary because:
    1. Deleting a monitor doesn't delete its output tables
    2. Schema conflicts occur when recreating monitors
    """
    try:
        # Check if monitor exists
        existing = workspace_client.quality_monitors.get(table_name=table_name)
        print(f"      Found existing monitor (created: {getattr(existing, 'create_time', 'unknown')})")

        # Delete monitor definition
        print(f"      Deleting monitor definition...")
        workspace_client.quality_monitors.delete(table_name=table_name)
        print(f"      ✓ Monitor definition deleted")

        # Parse table name and drop output tables
        parts = table_name.split(".")
        if len(parts) == 3:
            catalog, schema, table = parts
            monitoring_schema = f"{schema}_monitoring"

            if spark:
                # Drop profile_metrics table
                profile_table = f"{catalog}.{monitoring_schema}.{table}_profile_metrics"
                print(f"      Dropping {profile_table}...")
                spark.sql(f"DROP TABLE IF EXISTS {profile_table}")
                print(f"      ✓ Dropped profile_metrics")

                # Drop drift_metrics table
                drift_table = f"{catalog}.{monitoring_schema}.{table}_drift_metrics"
                print(f"      Dropping {drift_table}...")
                spark.sql(f"DROP TABLE IF EXISTS {drift_table}")
                print(f"      ✓ Dropped drift_metrics")

        print(f"      Cleanup complete")
        return True

    except ResourceDoesNotExist:
        print(f"      No existing monitor found - clean slate")
        return False  # No monitor to delete
    except Exception as e:
        print(f"  [⚠] Error cleaning up monitor: {type(e).__name__}: {str(e)[:80]}")
        return False


def create_time_series_monitor(
    workspace_client,
    table_name: str,
    timestamp_col: str,
    granularities: List[str],
    custom_metrics: List,
    slicing_exprs: Optional[List[str]] = None,
    assets_dir: Optional[str] = None,
    output_schema: Optional[str] = None,
    schedule_cron: Optional[str] = None,
    spark=None
):
    """
    Create a time series monitor with custom metrics.

    Args:
        workspace_client: Databricks WorkspaceClient
        table_name: Full table name (catalog.schema.table)
        timestamp_col: Column to use for time series
        granularities: List of granularities (e.g., ["1 day", "1 hour"])
        custom_metrics: List of MonitorMetric objects
        slicing_exprs: Optional columns for dimensional analysis
        assets_dir: Optional assets directory path
        output_schema: Optional output schema name
        schedule_cron: Optional cron schedule expression
        spark: SparkSession for creating monitoring schema if needed
    """
    if not MONITORING_AVAILABLE:
        raise RuntimeError("Lakehouse Monitoring SDK not available")

    # Parse table name for defaults
    parts = table_name.split(".")
    if len(parts) == 3:
        catalog, schema, table = parts
    else:
        raise ValueError(f"Invalid table name format: {table_name}")

    # Set defaults
    if assets_dir is None:
        assets_dir = f"/Workspace/Shared/health_monitor/monitoring/{catalog}/{schema}"
    if output_schema is None:
        output_schema = f"{catalog}.{schema}_monitoring"

    # Create monitoring schema if it doesn't exist
    # This is required by Lakehouse Monitoring to store profile_metrics and drift_metrics tables
    if spark is not None:
        monitoring_schema_name = output_schema.split(".")[-1] if "." in output_schema else output_schema
        monitoring_catalog = output_schema.split(".")[0] if "." in output_schema else catalog
        print(f"      Ensuring monitoring schema exists: {output_schema}")
        try:
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {monitoring_catalog}.{monitoring_schema_name}")
            print(f"      ✓ Monitoring schema ready")
        except Exception as e:
            print(f"      ⚠ Warning: Could not create monitoring schema: {str(e)[:80]}")

    print(f"      Building monitor configuration...")
    print(f"        Table:       {table_name}")
    print(f"        Timestamp:   {timestamp_col}")
    print(f"        Granularity: {', '.join(granularities)}")
    print(f"        Metrics:     {len(custom_metrics)} custom metrics")
    if slicing_exprs:
        print(f"        Slicing:     {', '.join(slicing_exprs)}")
    if schedule_cron:
        print(f"        Schedule:    {schedule_cron}")

    try:
        # Build monitor configuration
        config = {
            "table_name": table_name,
            "assets_dir": assets_dir,
            "output_schema_name": output_schema,
            "time_series": MonitorTimeSeries(
                timestamp_col=timestamp_col,
                granularities=granularities
            ),
            "custom_metrics": custom_metrics,
        }

        if slicing_exprs:
            config["slicing_exprs"] = slicing_exprs

        if schedule_cron:
            config["schedule"] = MonitorCronSchedule(
                quartz_cron_expression=schedule_cron,
                timezone_id="UTC"
            )

        # Create monitor
        print(f"      Calling quality_monitors.create()...")
        monitor = workspace_client.quality_monitors.create(**config)

        print(f"      ✓ Monitor created successfully")
        print(f"        Table:       {monitor.table_name if hasattr(monitor, 'table_name') else table_name}")
        print(f"        Status:      {monitor.status if hasattr(monitor, 'status') else 'CREATED'}")
        if hasattr(monitor, 'dashboard_id') and monitor.dashboard_id:
            print(f"        Dashboard:   {monitor.dashboard_id}")
        if hasattr(monitor, 'monitor_version') and monitor.monitor_version:
            print(f"        Version:     {monitor.monitor_version}")

        return monitor

    except ResourceAlreadyExists:
        print(f"      ⊘ Monitor already exists - no action needed")
        return None
    except Exception as e:
        print(f"      ✗ Failed to create monitor")
        print(f"        Error Type:  {type(e).__name__}")
        print(f"        Error:       {str(e)[:120]}")
        raise


def wait_for_monitor_tables(minutes: int = 15):
    """Wait for monitor output tables to be created asynchronously."""
    wait_seconds = minutes * 60
    print(f"Waiting {minutes} minutes for monitor tables to be created...")

    for elapsed in range(0, wait_seconds, 60):
        progress_pct = (elapsed / wait_seconds) * 100
        remaining = (wait_seconds - elapsed) // 60
        print(f"  Progress: {progress_pct:.0f}% | Remaining: {remaining}m")
        time.sleep(60)

    print("  Wait completed - tables should be ready")


def create_aggregate_metric(name: str, definition: str, output_type: str = "DOUBLE"):
    """
    Helper to create an AGGREGATE custom metric.

    Args:
        name: Metric name
        definition: SQL aggregation expression
        output_type: Output data type (DOUBLE, LONG)
    """
    if not MONITORING_AVAILABLE:
        raise RuntimeError("Lakehouse Monitoring SDK not available")

    if output_type == "DOUBLE":
        data_type = T.StructField("output", T.DoubleType()).json()
    elif output_type == "LONG":
        data_type = T.StructField("output", T.LongType()).json()
    else:
        raise ValueError(f"Unknown output type: {output_type}")

    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
        name=name,
        input_columns=[":table"],  # Always use :table for business KPIs
        definition=definition,
        output_data_type=data_type
    )


def create_derived_metric(name: str, definition: str):
    """
    Helper to create a DERIVED custom metric.

    Args:
        name: Metric name
        definition: SQL expression referencing other metrics
    """
    if not MONITORING_AVAILABLE:
        raise RuntimeError("Lakehouse Monitoring SDK not available")

    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
        name=name,
        input_columns=[":table"],  # Must match AGGREGATE metrics
        definition=definition,
        output_data_type=T.StructField("output", T.DoubleType()).json()
    )


def create_drift_metric(name: str, definition: str):
    """
    Helper to create a DRIFT custom metric.

    Args:
        name: Metric name
        definition: SQL expression with {{current_df}} and {{base_df}}
    """
    if not MONITORING_AVAILABLE:
        raise RuntimeError("Lakehouse Monitoring SDK not available")

    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_DRIFT,
        name=name,
        input_columns=[":table"],  # Must match AGGREGATE metrics
        definition=definition,
        output_data_type=T.StructField("output", T.DoubleType()).json()
    )


# ============================================================================
# METRIC DOCUMENTATION REGISTRY
# ============================================================================
# Comprehensive descriptions for all custom metrics AND standard Lakehouse Monitoring
# columns to enable Genie understanding.
# Format: "Metric Name": "Business description. Technical: calculation details."

METRIC_DESCRIPTIONS = {
    # ==========================================
    # STANDARD LAKEHOUSE MONITORING SYSTEM COLUMNS
    # These columns appear in ALL monitoring tables
    # ==========================================
    
    # -- Profile Metrics Standard Columns --
    "window": "Time window for the metric aggregation. Contains start and end timestamps. Use window.start for time-series analysis. Technical: Struct with start/end fields.",
    "granularity": "Time granularity for the metric (e.g., '1 day', '1 hour'). Business: Determines the aggregation period. Technical: String matching monitor configuration.",
    "monitor_version": "Version of the Lakehouse Monitor that produced these metrics. Business: Track schema changes. Technical: Integer incremented on monitor updates.",
    "logging_table_commit_version": "Delta table commit version when metrics were computed. Business: Data lineage tracking. Technical: Delta log version number.",
    "slice_key": "The dimension column used for slicing (NULL for overall metrics). Business: Use to filter by dimension type. Technical: Column name from slicing_exprs. Example: 'workspace_id', 'sku_name'.",
    "slice_value": "The value of the slice dimension (NULL for overall metrics). Business: Specific dimension value being analyzed. Technical: Actual value from the slice_key column.",
    "column_name": "The column being profiled. CRITICAL: Use ':table' for custom/table-level metrics. Business: Filter column_name=':table' for business KPIs. Technical: ':table' = aggregate metrics, other values = column-level stats.",
    "log_type": "Whether metrics are for INPUT or OUTPUT data. CRITICAL: Use 'INPUT' for source data metrics. Business: Filter log_type='INPUT' for most queries. Technical: INPUT=source table, OUTPUT=predictions/results.",
    "data_type": "Data type of the profiled column. Business: Understand column types. Technical: Spark SQL data type string.",
    "count": "Number of rows in the time window. Business: Data volume indicator. Technical: COUNT(*) for the window.",
    "num_nulls": "Count of NULL values in the column. Business: Data completeness indicator. Technical: COUNT where column IS NULL.",
    "avg": "Average value for numeric columns. Business: Central tendency measure. Technical: AVG(column_value).",
    "quantiles": "Distribution quantiles (0.05, 0.25, 0.5, 0.75, 0.95). Business: Value distribution understanding. Technical: PERCENTILE array.",
    "min": "Minimum value in the column. Business: Lower bound of data range. Technical: MIN(column_value).",
    "max": "Maximum value in the column. Business: Upper bound of data range. Technical: MAX(column_value).",
    "stddev": "Standard deviation for numeric columns. Business: Data spread/variability measure. Technical: STDDEV(column_value).",
    "num_zeros": "Count of zero values in the column. Business: Zero-value frequency. Technical: COUNT where column = 0.",
    "num_nan": "Count of NaN (Not a Number) values. Business: Data quality issue indicator. Technical: COUNT where isnan(column).",
    "min_length": "Minimum string length for string columns. Business: Shortest string size. Technical: MIN(LENGTH(column)).",
    "max_length": "Maximum string length for string columns. Business: Longest string size. Technical: MAX(LENGTH(column)).",
    "avg_length": "Average string length for string columns. Business: Typical string size. Technical: AVG(LENGTH(column)).",
    "non_null_columns": "Count of non-null columns in struct types. Business: Struct completeness. Technical: COUNT of non-null struct fields.",
    "frequent_items": "Most common values in the column. Business: Top value distribution. Technical: Array of frequent value/count pairs.",
    "median": "Median value (50th percentile). Business: Central value measure. Technical: PERCENTILE(column, 0.5).",
    "distinct_count": "Number of unique values. Business: Cardinality measure. Technical: COUNT(DISTINCT column).",
    "percent_nan": "Percentage of NaN values. Business: NaN frequency as percentage. Technical: num_nan / count * 100.",
    "percent_null": "Percentage of NULL values. Business: NULL frequency as percentage. Technical: num_nulls / count * 100.",
    "percent_zeros": "Percentage of zero values. Business: Zero frequency as percentage. Technical: num_zeros / count * 100.",
    "percent_distinct": "Percentage of distinct values (uniqueness). Business: Column uniqueness measure. Technical: distinct_count / count * 100.",
    
    # -- Drift Metrics Standard Columns --
    "window_cmp": "Comparison (baseline) time window for drift calculation. Business: The period being compared against. Technical: Struct with start/end fields.",
    "drift_type": "Type of drift calculation. CRITICAL: Use 'CONSECUTIVE' for period-over-period comparison. Business: Filter drift_type='CONSECUTIVE'. Technical: CONSECUTIVE=compare to previous period, BASELINE=compare to fixed baseline.",
    "count_delta": "Change in row count between periods. Business: Volume growth/decline indicator. Technical: current_count - baseline_count.",
    "avg_delta": "Change in average value between periods. Business: Central tendency shift. Technical: current_avg - baseline_avg.",
    "percent_null_delta": "Change in NULL percentage between periods. Business: Data completeness trend. Technical: current_pct_null - baseline_pct_null.",
    "percent_zeros_delta": "Change in zero percentage between periods. Business: Zero frequency trend. Technical: current_pct_zeros - baseline_pct_zeros.",
    "percent_distinct_delta": "Change in uniqueness between periods. Business: Cardinality trend. Technical: current_pct_distinct - baseline_pct_distinct.",
    "non_null_columns_delta": "Change in non-null column count for structs. Business: Struct completeness trend. Technical: current - baseline non_null_columns.",
    "js_distance": "Jensen-Shannon divergence between distributions. Business: Distribution similarity measure (0=identical, 1=completely different). Technical: Statistical distance metric.",
    "ks_test": "Kolmogorov-Smirnov test p-value for distribution change. Business: Statistical significance of distribution shift. Technical: Lower p-value = more significant change.",
    "wasserstein_distance": "Wasserstein (Earth Mover's) distance between distributions. Business: Cost to transform one distribution to another. Technical: Optimal transport distance metric.",
    "population_stability_index": "PSI for monitoring distribution stability. Business: <0.1=stable, 0.1-0.25=moderate change, >0.25=significant drift. Technical: Sum of (actual-expected)*ln(actual/expected).",
    "chi_squared_test": "Chi-squared test p-value for categorical distribution change. Business: Statistical significance for categorical columns. Technical: Lower p-value = significant change.",
    "tv_distance": "Total Variation distance between distributions. Business: Maximum difference between probability distributions. Technical: 0.5 * sum(|P-Q|).",
    "l_infinity_distance": "L-infinity (maximum) distance between distributions. Business: Largest single-point probability difference. Technical: max(|P-Q|).",
    
    # ==========================================
    # CUSTOM DRIFT METRICS FOR SPECIFIC MONITORS
    # ==========================================
    # Node Timeline specific drift metrics
    "network_volume_drift_pct": "Percentage change in network traffic volume. Business: Network utilization trend. Technical: (current - baseline) / baseline * 100.",
    "efficiency_score_drift": "Change in cluster efficiency score. Business: Right-sizing improvement indicator. Technical: current - baseline efficiency_score.",
    "rightsizing_opportunity_drift": "Change in rightsizing opportunity count. Business: Optimization trend. Technical: current - baseline rightsizing_opportunity_count.",
    "p95_cpu_drift": "Change in P95 CPU utilization. Business: Peak CPU demand trend. Technical: current - baseline P95 CPU.",
    "rightsizing_opportunity_pct": "Percentage of periods with right-sizing opportunities. Business: Optimization scope indicator. Technical: rightsizing_opportunities / total_periods * 100.",
    
    # Security/Audit specific drift metrics (additional)
    "user_count_drift": "Change in active user count between periods. Business: User engagement trend. Technical: current - baseline distinct_users.",
    "failure_rate_drift": "Change in failure rate between periods. Business: Reliability trend indicator. Technical: current - baseline failure_rate.",
    
    # Query specific drift metrics (additional)
    "query_volume_drift_pct": "Percentage change in query volume. Business: Workload growth indicator. Technical: (current - baseline) / baseline * 100.",
    "query_duration_drift_pct": "Percentage change in average query duration. Business: Performance trend. Technical: (current - baseline) / baseline * 100.",
    

    # ==========================================
    # COST MONITOR METRICS (fact_usage)
    # ==========================================
    # Core cost metrics
    "total_daily_cost": "Total daily cost in list prices. Business: Primary FinOps metric for budgeting and forecasting. Technical: SUM(list_cost), aggregated per time window.",
    "total_daily_dbu": "Total Databricks Units consumed. Business: Usage volume independent of pricing. Technical: SUM(usage_quantity), key for capacity planning.",
    "avg_cost_per_dbu": "Average cost per DBU. Business: Unit economics indicator for pricing efficiency. Technical: AVG(list_price), varies by SKU.",
    "record_count": "Count of billing records processed. Business: Data completeness indicator. Technical: COUNT(*), should match source system.",
    
    # Completeness metrics
    "distinct_workspaces": "Number of unique workspaces with billing activity. Business: Platform utilization breadth. Technical: COUNT(DISTINCT workspace_id).",
    "distinct_skus": "Number of unique SKUs billed. Business: Product mix indicator. Technical: COUNT(DISTINCT sku_name).",
    "null_sku_count": "Records with missing SKU names. Business: Data quality issue requiring investigation. Technical: COUNT where sku_name IS NULL.",
    "null_price_count": "Records with missing prices. Business: Billing data quality indicator. Technical: COUNT where list_price IS NULL.",
    
    # Tag hygiene metrics
    "tagged_record_count": "Records with cost allocation tags. Business: FinOps maturity indicator. Technical: COUNT where is_tagged = TRUE.",
    "untagged_record_count": "Records missing cost allocation tags. Business: Unattributable spend requiring attention. Technical: COUNT where is_tagged = FALSE.",
    "tagged_cost_total": "Total cost for tagged resources. Business: Attributable spend amount. Technical: SUM(list_cost) where is_tagged = TRUE.",
    "untagged_cost_total": "Total cost for untagged resources. Business: Unattributable spend requiring investigation. Technical: SUM(list_cost) where is_tagged = FALSE.",
    
    # SKU breakdown
    "jobs_compute_cost": "Cost from Jobs compute SKUs. Business: Workflow automation spend. Technical: SUM(list_cost) for JOBS SKUs.",
    "sql_compute_cost": "Cost from SQL warehouse SKUs. Business: Analytics workload spend. Technical: SUM(list_cost) for SQL SKUs.",
    "all_purpose_cost": "Cost from all-purpose cluster SKUs. Business: Interactive compute spend, often higher cost. Technical: SUM(list_cost) for ALL_PURPOSE SKUs.",
    "serverless_cost": "Cost from serverless compute. Business: Modern compute pattern adoption. Technical: SUM(list_cost) where is_serverless = TRUE.",
    
    # Workflow advisor metrics
    "jobs_on_all_purpose_cost": "Cost of jobs running on all-purpose clusters. Business: Inefficient pattern causing ~40% overspend. Technical: Jobs running on ALL_PURPOSE instead of JOB clusters.",
    "jobs_on_all_purpose_count": "Number of jobs running on all-purpose clusters. Business: Optimization candidates for JOB cluster migration. Technical: COUNT DISTINCT job_ids on ALL_PURPOSE.",
    "potential_job_cluster_savings": "Potential savings from migrating to job clusters. Business: Actionable optimization opportunity. Technical: Estimated 40% savings on jobs currently using ALL_PURPOSE.",
    "dlt_cost": "Delta Live Tables pipeline cost. Business: Data pipeline infrastructure spend. Technical: SUM(list_cost) for DLT SKUs.",
    "model_serving_cost": "Model serving and inference cost. Business: ML production serving spend. Technical: SUM(list_cost) for MODEL_SERVING and INFERENCE SKUs.",
    
    # Derived cost metrics
    "null_sku_rate": "Percentage of records with missing SKUs. Business: Data quality score (target: <1%). Technical: null_sku_count / record_count * 100.",
    "null_price_rate": "Percentage of records with missing prices. Business: Billing completeness score (target: 0%). Technical: null_price_count / record_count * 100.",
    "tag_coverage_pct": "Percentage of cost covered by tags. Business: FinOps maturity KPI (target: >90%). Technical: tagged_cost / total_cost * 100.",
    "untagged_usage_pct": "Percentage of cost without tags. Business: Cost attribution gap requiring attention. Technical: untagged_cost / total_cost * 100.",
    "serverless_ratio": "Percentage of cost on serverless compute. Business: Modern architecture adoption rate. Technical: serverless_cost / total_cost * 100.",
    "jobs_cost_share": "Percentage of total cost from Jobs. Business: Workflow automation cost proportion. Technical: jobs_cost / total_cost * 100.",
    "sql_cost_share": "Percentage of total cost from SQL. Business: Analytics workload cost proportion. Technical: sql_cost / total_cost * 100.",
    "all_purpose_cost_ratio": "Percentage of cost on all-purpose clusters. Business: Interactive compute overhead. Technical: all_purpose_cost / total_cost * 100.",
    "jobs_on_all_purpose_ratio": "Percentage of job cost on all-purpose clusters. Business: Optimization priority score. Technical: jobs_on_all_purpose_cost / total_jobs_cost * 100.",
    "dlt_cost_share": "Percentage of cost from DLT pipelines. Business: Data engineering pipeline spend proportion. Technical: dlt_cost / total_cost * 100.",
    "model_serving_cost_share": "Percentage of cost from model serving. Business: ML inference spend proportion. Technical: model_serving_cost / total_cost * 100.",
    
    # Cost drift metrics
    "cost_drift_pct": "Period-over-period cost change percentage. Business: Budget variance indicator requiring review if >10%. Technical: (current - baseline) / baseline * 100.",
    "dbu_drift_pct": "Period-over-period DBU change percentage. Business: Usage trend independent of pricing. Technical: (current - baseline) / baseline * 100.",
    "tag_coverage_drift": "Change in tag coverage between periods. Business: FinOps maturity trend. Technical: current_coverage - baseline_coverage.",
    
    # ==========================================
    # JOB MONITOR METRICS (fact_job_run_timeline)
    # ==========================================
    # Core reliability metrics
    "total_runs": "Total number of job runs. Business: Workload volume indicator. Technical: COUNT(*) of all job executions.",
    "success_count": "Number of successful job runs. Business: Reliability numerator. Technical: COUNT where is_success = TRUE.",
    "failure_count": "Number of failed job runs. Business: Reliability issues requiring investigation. Technical: COUNT where result_state IN (FAILED, ERROR).",
    "timeout_count": "Number of timed out job runs. Business: Resource constraint or configuration issues. Technical: COUNT where result_state = TIMED_OUT.",
    "cancelled_count": "Number of cancelled job runs. Business: Manual interventions or dependency issues. Technical: COUNT where result_state = CANCELED.",
    
    # Duration metrics
    "avg_duration_minutes": "Average job duration in minutes. Business: Baseline performance indicator. Technical: AVG(run_duration_minutes).",
    "total_duration_minutes": "Total job duration in minutes. Business: Compute time consumption. Technical: SUM(run_duration_minutes).",
    "max_duration_minutes": "Maximum job duration in minutes. Business: Worst-case performance indicator. Technical: MAX(run_duration_minutes).",
    "min_duration_minutes": "Minimum job duration in minutes. Business: Best-case performance indicator. Technical: MIN(run_duration_minutes).",
    "p50_duration_minutes": "Median (P50) job duration in minutes. Business: Typical performance indicator. Technical: PERCENTILE(run_duration_minutes, 0.50).",
    "p90_duration_minutes": "P90 job duration in minutes. Business: Outlier threshold for SLA monitoring. Technical: PERCENTILE(run_duration_minutes, 0.90).",
    "p95_duration_minutes": "P95 job duration in minutes. Business: Performance SLA target threshold. Technical: PERCENTILE(run_duration_minutes, 0.95).",
    "p99_duration_minutes": "P99 job duration in minutes. Business: Critical SLA threshold for worst-case scenarios. Technical: PERCENTILE(run_duration_minutes, 0.99).",
    "stddev_duration_minutes": "Standard deviation of job duration. Business: Performance consistency indicator. Technical: STDDEV(run_duration_minutes).",
    
    # Outcome breakdown
    "skipped_count": "Number of skipped job runs. Business: Dependency or condition issues. Technical: COUNT where result_state = SKIPPED.",
    "upstream_failed_count": "Number of runs failed due to upstream. Business: Dependency chain failures. Technical: COUNT where result_state = UPSTREAM_FAILED.",
    "long_running_count": "Jobs running longer than 1 hour. Business: Potential optimization candidates. Technical: COUNT where duration > 60 minutes.",
    "very_long_running_count": "Jobs running longer than 4 hours. Business: Resource-intensive jobs requiring review. Technical: COUNT where duration > 240 minutes.",
    
    # Job counts
    "distinct_jobs": "Number of unique jobs executed. Business: Workload diversity indicator. Technical: COUNT(DISTINCT job_id).",
    "distinct_runs": "Number of unique run IDs. Business: Execution count including retries. Technical: COUNT(DISTINCT run_id).",
    
    # Trigger breakdown
    "scheduled_runs": "Number of scheduled job runs. Business: Automated workload proportion. Technical: COUNT where trigger_type = SCHEDULE.",
    "manual_runs": "Number of manually triggered runs. Business: Ad-hoc workload proportion. Technical: COUNT where trigger_type = MANUAL.",
    "retry_runs": "Number of retry job runs. Business: Recovery activity indicator. Technical: COUNT where trigger_type = RETRY.",
    
    # Termination breakdown
    "user_cancelled_count": "Jobs cancelled by users. Business: Manual intervention frequency. Technical: COUNT where termination_code = USER_CANCELED.",
    "internal_error_count": "Jobs failed due to internal errors. Business: Platform stability issues. Technical: COUNT where termination_code = INTERNAL_ERROR.",
    "driver_error_count": "Jobs failed due to driver errors. Business: Code or configuration issues. Technical: COUNT where termination_code = DRIVER_ERROR.",
    
    # Derived job metrics
    "success_rate": "Job success rate percentage. Business: Primary reliability KPI (target: >95%). Technical: success_count / total_runs * 100.",
    "failure_rate": "Job failure rate percentage. Business: Reliability issue indicator. Technical: failure_count / total_runs * 100.",
    "timeout_rate": "Job timeout rate percentage. Business: Resource constraint indicator. Technical: timeout_count / total_runs * 100.",
    "cancellation_rate": "Job cancellation rate percentage. Business: Intervention frequency indicator. Technical: cancelled_count / total_runs * 100.",
    "repair_rate": "Job repair/retry rate percentage. Business: Recovery activity level. Technical: retry_runs / distinct_runs * 100.",
    "scheduled_ratio": "Percentage of scheduled runs. Business: Automation maturity indicator. Technical: scheduled_runs / total_runs * 100.",
    "avg_runs_per_job": "Average runs per unique job. Business: Execution frequency indicator. Technical: total_runs / distinct_jobs.",
    "duration_cv": "Coefficient of variation for duration. Business: Performance consistency score (lower is better). Technical: stddev / avg duration.",
    "skipped_rate": "Skipped run rate percentage. Business: Dependency issue frequency. Technical: skipped_count / total_runs * 100.",
    "upstream_failed_rate": "Upstream failure rate percentage. Business: Dependency chain health indicator. Technical: upstream_failed / total_runs * 100.",
    "long_running_rate": "Long running job rate percentage. Business: Optimization opportunity scope. Technical: long_running_count / total_runs * 100.",
    "very_long_running_rate": "Very long running job rate percentage. Business: Resource-intensive workload proportion. Technical: very_long_running_count / total_runs * 100.",
    "duration_skew_ratio": "P90 to P50 duration ratio. Business: Performance distribution skewness (1 = perfect, >2 = skewed). Technical: p90_duration / p50_duration.",
    "tail_ratio": "P99 to P95 duration ratio. Business: Tail latency indicator for worst-case scenarios. Technical: p99_duration / p95_duration.",
    
    # Job drift metrics
    "success_rate_drift": "Change in success rate between periods. Business: Reliability trend indicator (negative = degrading). Technical: current - baseline success_rate.",
    "failure_count_drift": "Change in failure count between periods. Business: Problem emergence indicator. Technical: current - baseline failure_count.",
    "run_count_drift_pct": "Percentage change in run count. Business: Workload volume trend. Technical: (current - baseline) / baseline * 100.",
    "duration_drift_pct": "Percentage change in average duration. Business: Performance regression indicator. Technical: (current - baseline) / baseline * 100.",
    "p99_duration_drift_pct": "Percentage change in P99 duration. Business: SLA compliance trend. Technical: (current - baseline) / baseline * 100.",
    "p90_duration_drift_pct": "Percentage change in P90 duration. Business: Outlier trend indicator. Technical: (current - baseline) / baseline * 100.",
    "duration_cv_drift": "Change in duration coefficient of variation. Business: Consistency trend indicator. Technical: current - baseline CV.",
    "long_running_drift": "Change in long running job count. Business: Performance degradation indicator. Technical: current - baseline count.",
    
    # ==========================================
    # QUERY MONITOR METRICS (fact_query_history)
    # ==========================================
    # Core volume metrics
    "query_count": "Total number of queries executed. Business: Query workload volume. Technical: COUNT(*) of all queries.",
    "total_queries": "Total number of queries executed. Business: Query workload volume. Technical: COUNT(*) of all queries.",
    "successful_queries": "Number of successful queries. Business: Query reliability numerator. Technical: COUNT where execution_status = FINISHED.",
    "failed_queries": "Number of failed queries. Business: Query reliability issues. Technical: COUNT where execution_status = FAILED.",
    "cancelled_queries": "Number of cancelled queries. Business: User intervention or timeout issues. Technical: COUNT where execution_status = CANCELED.",
    
    # Duration metrics (seconds)
    "avg_duration_sec": "Average query duration in seconds. Business: Query performance baseline. Technical: AVG(total_duration_ms / 1000).",
    "total_duration_sec": "Total query duration in seconds. Business: Total compute time. Technical: SUM(total_duration_ms / 1000).",
    "p50_duration_sec": "Median (P50) query duration in seconds. Business: Typical query performance. Technical: PERCENTILE(duration, 0.50).",
    "p95_duration_sec": "P95 query duration in seconds. Business: SLA threshold for slow queries. Technical: PERCENTILE(duration, 0.95).",
    "p99_duration_sec": "P99 query duration in seconds. Business: Worst-case query performance. Technical: PERCENTILE(duration, 0.99).",
    "max_duration_sec": "Maximum query duration in seconds. Business: Longest query execution. Technical: MAX(total_duration_ms / 1000).",
    "avg_query_duration_seconds": "Average query duration in seconds. Business: Query performance baseline. Technical: AVG(duration_seconds).",
    "p50_duration_seconds": "Median query duration in seconds. Business: Typical query performance. Technical: PERCENTILE(duration_seconds, 0.50).",
    "p95_duration_seconds": "P95 query duration in seconds. Business: SLA threshold for slow queries. Technical: PERCENTILE(duration_seconds, 0.95).",
    "p99_duration_seconds": "P99 query duration in seconds. Business: Worst-case query performance. Technical: PERCENTILE(duration_seconds, 0.99).",
    
    # Queue metrics (warehouse capacity)
    "avg_queue_time_sec": "Average queue waiting time in seconds. Business: Warehouse capacity indicator. Technical: AVG(waiting_at_capacity_duration_ms / 1000).",
    "total_queue_time_sec": "Total queue waiting time in seconds. Business: Aggregate capacity constraint. Technical: SUM(waiting_at_capacity_duration_ms / 1000).",
    "high_queue_count": "Queries with high queue time (>10% of duration). Business: Capacity-constrained queries. Technical: COUNT where queue_time > 10% of total_duration.",
    "high_queue_severe_count": "Queries with severe queue time (>30% of duration). Business: Critical capacity issues. Technical: COUNT where queue_time > 30% of total_duration.",
    
    # Slow query tracking
    "slow_query_count": "Queries longer than 5 minutes. Business: Long-running query count. Technical: COUNT where duration > 300 seconds.",
    "very_slow_query_count": "Queries longer than 15 minutes. Business: Very long-running query count. Technical: COUNT where duration > 900 seconds.",
    
    # SLA and efficiency metrics (DBSQL Warehouse Advisor)
    "sla_breach_count": "Queries exceeding 60-second SLA threshold. Business: SLA compliance tracking. Technical: COUNT where duration > 60 seconds.",
    "efficient_query_count": "Queries meeting efficiency criteria (no spill, low queue, under SLA). Business: Optimally performing queries. Technical: COUNT meeting all efficiency criteria.",
    "complex_query_count": "Queries with complex SQL (>5000 chars). Business: Query complexity tracking. Technical: COUNT where statement_text length > 5000.",
    
    # Data volume metrics
    "total_bytes_read_tb": "Total bytes scanned in terabytes. Business: Data read volume at scale. Technical: SUM(read_bytes) / TB.",
    "total_rows_read_b": "Total rows scanned in billions. Business: Row scan volume at scale. Technical: SUM(read_rows) / billion.",
    "avg_bytes_per_query": "Average bytes per query. Business: Query scan size indicator. Technical: AVG(read_bytes).",
    "total_rows_read": "Total rows scanned by queries. Business: Data access volume indicator. Technical: SUM(rows_read).",
    "total_bytes_read": "Total bytes scanned by queries. Business: IO efficiency indicator. Technical: SUM(bytes_read).",
    
    # Spill metrics (memory pressure)
    "queries_with_spill": "Queries that spilled to disk. Business: Memory pressure indicator. Technical: COUNT where spilled_local_bytes > 0.",
    "total_spilled_bytes": "Total bytes spilled to disk. Business: Memory constraint severity. Technical: SUM(spilled_local_bytes).",
    
    # Cache metrics
    "cache_hit_count": "Queries served from cache. Business: Cache effectiveness. Technical: COUNT where from_result_cache = TRUE.",
    
    # Compilation metrics
    "avg_compilation_sec": "Average query compilation time in seconds. Business: Query parsing overhead. Technical: AVG(compilation_duration_ms / 1000).",
    
    # Distinct entities
    "distinct_warehouses": "Number of unique warehouses used. Business: Warehouse utilization breadth. Technical: COUNT(DISTINCT compute_warehouse_id).",
    
    # Derived query metrics
    "query_success_rate": "Query success rate percentage. Business: Query reliability KPI (target: >99%). Technical: successful / total * 100.",
    "query_failure_rate": "Query failure rate percentage. Business: Query reliability issue indicator. Technical: failed / total * 100.",
    "high_queue_rate": "Percentage of queries with high queue time. Business: Capacity constraint indicator. Technical: high_queue_count / total * 100.",
    "slow_query_rate": "Percentage of slow queries (>5 min). Business: Performance issue scope. Technical: slow_query_count / total * 100.",
    "spill_rate": "Percentage of queries with disk spill. Business: Memory pressure frequency. Technical: queries_with_spill / total * 100.",
    "cache_hit_rate": "Percentage of queries served from cache. Business: Cache effectiveness KPI. Technical: cache_hit_count / total * 100.",
    "avg_queries_per_user": "Average queries per user. Business: User activity level. Technical: query_count / distinct_users.",
    "sla_breach_rate": "Percentage of queries breaching 60s SLA. Business: SLA compliance KPI (target: <5%). Technical: sla_breach_count / total * 100.",
    "efficiency_rate": "Percentage of efficient queries (no spill, low queue, under SLA). Business: Query efficiency KPI. Technical: efficient_query_count / total * 100.",
    "severe_queue_rate": "Percentage of queries with severe queue time. Business: Critical capacity issues frequency. Technical: high_queue_severe_count / total * 100.",
    "complex_query_rate": "Percentage of complex queries. Business: Query complexity distribution. Technical: complex_query_count / total * 100.",
    "avg_rows_per_query": "Average rows per query. Business: Query scope indicator. Technical: total_rows / total_queries.",
    
    # Query drift metrics
    "p95_duration_drift_pct": "Period-over-period change in P95 query duration. Business: Performance trend indicator. Technical: (current - baseline) / baseline * 100.",
    "p99_duration_drift_pct": "Period-over-period change in P99 query duration. Business: Tail latency trend. Technical: (current - baseline) / baseline * 100.",
    "query_volume_drift_pct": "Period-over-period change in query volume. Business: Workload growth indicator. Technical: (current - baseline) / baseline * 100.",
    "failure_rate_drift": "Change in query failure rate between periods. Business: Reliability trend indicator. Technical: current - baseline failure_rate.",
    "spill_rate_drift": "Change in spill rate between periods. Business: Memory pressure trend. Technical: current - baseline spill_rate.",
    "sla_breach_rate_drift": "Change in SLA breach rate between periods. Business: SLA compliance trend. Technical: current - baseline sla_breach_rate.",
    "efficiency_rate_drift": "Change in efficiency rate between periods. Business: Query optimization trend. Technical: current - baseline efficiency_rate.",
    "query_duration_drift_pct": "Period-over-period query duration change. Business: Performance trend indicator. Technical: (current - baseline) / baseline * 100.",
    
    # ==========================================
    # CLUSTER/NODE MONITOR METRICS (fact_node_timeline)
    # ==========================================
    # Node counts
    "node_hour_count": "Total node-hours of compute time. Business: Compute resource consumption. Technical: COUNT(*) of node telemetry records.",
    "distinct_nodes": "Number of unique cluster nodes. Business: Node count for sizing. Technical: COUNT(DISTINCT instance_id).",
    "distinct_clusters": "Number of unique clusters. Business: Compute infrastructure breadth. Technical: COUNT(DISTINCT cluster_id).",
    "driver_node_count": "Number of driver node records. Business: Control plane utilization. Technical: COUNT where driver = TRUE.",
    "worker_node_count": "Number of worker node records. Business: Compute node utilization. Technical: COUNT where driver = FALSE.",
    
    # CPU metrics
    "avg_cpu_user_pct": "Average CPU user percentage. Business: Workload CPU consumption. Technical: AVG(cpu_user_percent).",
    "avg_cpu_system_pct": "Average CPU system percentage. Business: System overhead indicator. Technical: AVG(cpu_system_percent).",
    "avg_cpu_wait_pct": "Average CPU I/O wait percentage. Business: Storage bottleneck indicator. Technical: AVG(cpu_wait_percent).",
    "max_cpu_user_pct": "Maximum CPU user percentage. Business: Peak CPU demand. Technical: MAX(cpu_user_percent).",
    "max_cpu_total_pct": "Maximum total CPU percentage. Business: Peak CPU utilization. Technical: MAX(cpu_user + cpu_system).",
    "avg_cpu_total_pct": "Average total CPU percentage. Business: Overall CPU utilization. Technical: avg_cpu_user + avg_cpu_system.",
    "p95_cpu_total_pct": "P95 total CPU percentage. Business: Peak CPU for sizing. Technical: PERCENTILE(cpu_total, 0.95).",
    
    # Memory metrics
    "avg_memory_pct": "Average memory utilization percentage. Business: Memory consumption indicator. Technical: AVG(mem_used_percent).",
    "max_memory_pct": "Maximum memory utilization percentage. Business: Peak memory demand. Technical: MAX(mem_used_percent).",
    "avg_swap_pct": "Average swap usage percentage. Business: Memory pressure indicator. Technical: AVG(mem_swap_percent).",
    "max_swap_pct": "Maximum swap usage percentage. Business: Severe memory pressure. Technical: MAX(mem_swap_percent).",
    "p95_memory_pct": "P95 memory utilization percentage. Business: Peak memory for sizing. Technical: PERCENTILE(mem_used, 0.95).",
    
    # Network metrics
    "total_network_sent_gb": "Total network bytes sent in GB. Business: Egress volume. Technical: SUM(network_sent_bytes) / GB.",
    "total_network_received_gb": "Total network bytes received in GB. Business: Ingress volume. Technical: SUM(network_received_bytes) / GB.",
    "avg_network_sent_mb": "Average network bytes sent in MB. Business: Per-record egress. Technical: AVG(network_sent_bytes) / MB.",
    "avg_network_received_mb": "Average network bytes received in MB. Business: Per-record ingress. Technical: AVG(network_received_bytes) / MB.",
    "total_network_gb": "Total network traffic in GB. Business: Overall network utilization. Technical: sent_gb + received_gb.",
    
    # Utilization threshold metrics
    "underutilized_hours": "Hours with low utilization (<20% CPU, <30% memory). Business: Waste indicator. Technical: COUNT of underutilized periods.",
    "overutilized_hours": "Hours with high utilization (>80% CPU). Business: Capacity constraint indicator. Technical: COUNT where CPU > 80%.",
    "high_io_wait_hours": "Hours with high I/O wait (>20%). Business: Storage bottleneck indicator. Technical: COUNT where io_wait > 20%.",
    "high_swap_hours": "Hours with high swap usage (>10%). Business: Memory pressure indicator. Technical: COUNT where swap > 10%.",
    "memory_pressure_hours": "Hours with memory pressure (>90%). Business: Memory constraint indicator. Technical: COUNT where memory > 90%.",
    
    # Right-sizing metrics (Workflow Advisor)
    "cpu_saturation_hours": "Hours with CPU saturation (>90%). Business: Underprovisioned indicator. Technical: COUNT where CPU > 90%.",
    "cpu_idle_hours": "Hours with CPU idle (<20%). Business: Overprovisioned indicator. Technical: COUNT where CPU < 20%.",
    "memory_saturation_hours": "Hours with memory saturation (>85%). Business: Memory underprovisioned indicator. Technical: COUNT where memory > 85%.",
    "optimal_util_hours": "Hours with optimal utilization (30-80% CPU, 30-85% memory). Business: Right-sized periods. Technical: COUNT in optimal range.",
    "underprovisioned_hours": "Hours underprovisioned (high saturation). Business: Scale-up candidates. Technical: COUNT where CPU > 90% or memory > 85%.",
    "overprovisioned_hours": "Hours overprovisioned (low utilization). Business: Scale-down candidates. Technical: COUNT where CPU < 20% and memory < 30%.",
    
    # Derived utilization rates
    "underutilization_rate": "Percentage of underutilized hours. Business: Waste proportion (target: <20%). Technical: underutilized / total * 100.",
    "overutilization_rate": "Percentage of overutilized hours. Business: Capacity constraint proportion. Technical: overutilized / total * 100.",
    "io_bottleneck_rate": "Percentage of I/O bottleneck hours. Business: Storage constraint proportion. Technical: high_io_wait / total * 100.",
    "memory_pressure_rate": "Percentage of memory pressure hours. Business: Memory constraint proportion. Technical: memory_pressure / total * 100.",
    "swap_usage_rate": "Percentage of high swap usage hours. Business: Memory overflow proportion. Technical: high_swap / total * 100.",
    "avg_nodes_per_cluster": "Average nodes per cluster. Business: Cluster sizing indicator. Technical: distinct_nodes / distinct_clusters.",
    
    # Right-sizing rates
    "cpu_saturation_rate": "Percentage of CPU saturated hours. Business: Underprovisioning frequency. Technical: cpu_saturation / total * 100.",
    "cpu_idle_rate": "Percentage of CPU idle hours. Business: Overprovisioning frequency. Technical: cpu_idle / total * 100.",
    "memory_saturation_rate": "Percentage of memory saturated hours. Business: Memory constraint frequency. Technical: memory_saturation / total * 100.",
    "optimal_util_rate": "Percentage of optimally utilized hours. Business: Right-sizing success rate (target: >60%). Technical: optimal / total * 100.",
    "underprovisioned_rate": "Percentage of underprovisioned hours. Business: Scale-up opportunity. Technical: underprovisioned / total * 100.",
    "overprovisioned_rate": "Percentage of overprovisioned hours. Business: Scale-down opportunity. Technical: overprovisioned / total * 100.",
    "efficiency_score": "Cluster efficiency score (0-100). Business: Overall right-sizing KPI. Technical: optimal_util_rate.",
    
    # Drift metrics
    "cpu_utilization_drift": "Change in average CPU utilization. Business: CPU trend indicator. Technical: current - baseline avg_cpu_total.",
    "memory_utilization_drift": "Change in average memory utilization. Business: Memory trend indicator. Technical: current - baseline avg_memory.",
    "efficiency_drift": "Change in efficiency score. Business: Right-sizing improvement indicator. Technical: current - baseline efficiency_score.",
    "underutilization_drift": "Change in underutilization rate. Business: Waste reduction indicator. Technical: current - baseline underutilization_rate.",
    "overutilization_drift": "Change in overutilization rate. Business: Capacity improvement indicator. Technical: current - baseline overutilization_rate.",
    "node_count_drift": "Change in node count. Business: Infrastructure growth indicator. Technical: current - baseline distinct_nodes.",
    
    # Legacy cluster metrics (for backwards compatibility)
    "total_clusters": "Total number of unique clusters. Business: Compute infrastructure breadth. Technical: COUNT(DISTINCT cluster_id).",
    "total_cluster_hours": "Total cluster running hours. Business: Compute resource consumption. Technical: SUM(cluster_hours).",
    "avg_cluster_uptime_hours": "Average cluster uptime in hours. Business: Cluster utilization duration. Technical: AVG(uptime_hours).",
    "idle_cluster_hours": "Total hours clusters were idle. Business: Wasted compute time (optimization target). Technical: SUM(idle_hours).",
    "active_cluster_hours": "Total hours clusters were active. Business: Productive compute time. Technical: SUM(active_hours).",
    "cluster_utilization_pct": "Cluster utilization percentage. Business: Compute efficiency KPI (target: >60%). Technical: active_hours / total_hours * 100.",
    "idle_cost_estimate": "Estimated cost of idle cluster time. Business: FinOps optimization opportunity. Technical: idle_hours * avg_cost_per_hour.",
    "autoscale_events": "Number of autoscale events. Business: Elastic scaling activity. Technical: COUNT of scale up/down events.",
    "cluster_start_count": "Number of cluster starts. Business: Cluster lifecycle activity. Technical: COUNT of start events.",
    "cluster_terminate_count": "Number of cluster terminations. Business: Cluster lifecycle completions. Technical: COUNT of terminate events.",
    
    # ==========================================
    # SECURITY MONITOR METRICS (fact_audit_logs)
    # ==========================================
    # Event volume metrics
    "total_events": "Total number of audit events. Business: Security activity volume. Technical: COUNT(*) of all audit events.",
    "distinct_services": "Number of unique services accessed. Business: Service breadth. Technical: COUNT(DISTINCT service_name).",
    "distinct_actions": "Number of unique action types. Business: Action diversity. Technical: COUNT(DISTINCT action_name).",
    "distinct_ips": "Number of unique source IP addresses. Business: Access point diversity. Technical: COUNT(DISTINCT source_ip_address).",
    
    # Sensitive and failed action metrics
    "sensitive_action_count": "Number of sensitive/privileged actions. Business: Security audit priority events. Technical: COUNT where is_sensitive_action = TRUE.",
    "failed_action_count": "Number of failed actions. Business: Security issue indicator. Technical: COUNT where is_failed_action = TRUE.",
    "sensitive_actions": "Number of sensitive/privileged actions. Business: Security audit priority events. Technical: COUNT of privileged operations.",
    
    # Permission and secret metrics
    "permission_change_count": "Number of permission change events. Business: Access control changes requiring audit. Technical: COUNT where action LIKE '%grant%' or '%revoke%'.",
    "secret_access_count": "Number of secret access events. Business: Credential access requiring audit. Technical: COUNT where action LIKE '%Secret%'.",
    
    # Audit level breakdown
    "account_level_events": "Events at account level. Business: Cross-workspace activity. Technical: COUNT where audit_level = ACCOUNT_LEVEL.",
    "workspace_level_events": "Events at workspace level. Business: Workspace-specific activity. Technical: COUNT where audit_level = WORKSPACE_LEVEL.",
    
    # Error tracking
    "client_error_count": "HTTP 4xx client errors. Business: Bad request or permission issues. Technical: COUNT where response_status_code 400-499.",
    "server_error_count": "HTTP 5xx server errors. Business: Platform stability issues. Technical: COUNT where response_status_code >= 500.",
    "unauthorized_count": "401/403 unauthorized responses. Business: Access denied events requiring investigation. Technical: COUNT where response_status_code 401 or 403.",
    
    # Off-hours and weekend activity
    "weekend_events": "Events on weekends (Saturday/Sunday). Business: Non-business hours activity. Technical: COUNT where DAYOFWEEK IN (1, 7).",
    
    # User type classification (Audit Logs Repo)
    "human_user_events": "Events from human users (excludes system/service accounts). Business: Real user activity. Technical: COUNT where email LIKE '%@%' and NOT service principal.",
    "service_principal_events": "Events from service principals. Business: Automated/programmatic activity. Technical: COUNT where user is service principal.",
    "system_account_events": "Events from system accounts. Business: Platform internal activity. Technical: COUNT where user LIKE 'System-%' or 'DBX_%'.",
    "human_off_hours_events": "Human user events during off-hours. Business: Critical security indicator for human activity outside business hours. Technical: Human events where HOUR < 7 or HOUR >= 19.",
    "distinct_human_users": "Number of unique human users. Business: Human user base size. Technical: COUNT(DISTINCT human user emails).",
    "distinct_service_principals": "Number of unique service principals. Business: Automation account count. Technical: COUNT(DISTINCT service principal IDs).",
    
    # Service breakdown
    "clusters_service_events": "Events from clusters service. Business: Compute management activity. Technical: COUNT where service_name = 'clusters'.",
    "sql_service_events": "Events from SQL service. Business: SQL warehouse activity. Technical: COUNT where service_name = 'databrickssql'.",
    "workspace_service_events": "Events from workspace service. Business: Workspace management activity. Technical: COUNT where service_name = 'workspace'.",
    "unitycatalog_service_events": "Events from Unity Catalog service. Business: Governance and catalog activity. Technical: COUNT where service_name = 'unityCatalog'.",
    
    # Derived security metrics
    "sensitive_action_rate": "Percentage of sensitive actions. Business: Security exposure indicator (target: <5%). Technical: sensitive_action_count / total_events * 100.",
    "weekend_rate": "Percentage of weekend activity. Business: Non-business hours proportion. Technical: weekend_events / total_events * 100.",
    "unauthorized_rate": "Percentage of unauthorized responses. Business: Access denial rate (high = security concern). Technical: unauthorized_count / total_events * 100.",
    "account_level_ratio": "Percentage of account-level events. Business: Cross-workspace activity proportion. Technical: account_level_events / total_events * 100.",
    "human_user_ratio": "Percentage of human user events. Business: Human vs automation activity balance. Technical: human_user_events / total_events * 100.",
    "service_principal_ratio": "Percentage of service principal events. Business: Automation activity proportion. Technical: service_principal_events / total_events * 100.",
    "system_account_ratio": "Percentage of system account events. Business: Platform internal activity proportion. Technical: system_account_events / total_events * 100.",
    "human_off_hours_rate": "Percentage of human events during off-hours. Business: Critical security KPI (target: <10%). Technical: human_off_hours_events / human_user_events * 100.",
    "avg_events_per_human": "Average events per human user. Business: Human user activity level. Technical: human_user_events / distinct_human_users.",
    "avg_events_per_sp": "Average events per service principal. Business: Automation activity level. Technical: service_principal_events / distinct_service_principals.",
    
    # Security drift metrics
    "event_volume_drift_pct": "Percentage change in event volume. Business: Activity trend indicator. Technical: (current - baseline) / baseline * 100.",
    "sensitive_action_drift": "Change in sensitive action count. Business: Security posture change requiring investigation. Technical: current - baseline sensitive_action_count.",
    "off_hours_drift": "Change in off-hours rate. Business: Unusual activity trend. Technical: current - baseline off_hours_rate.",
    "human_off_hours_drift": "Change in human off-hours rate. Business: Critical security trend (increase = concern). Technical: current - baseline human_off_hours_rate.",
    "human_user_count_drift": "Change in human user count. Business: User base growth indicator. Technical: current - baseline distinct_human_users.",
    "service_principal_volume_drift_pct": "Percentage change in service principal events. Business: Automation activity trend. Technical: (current - baseline) / baseline * 100.",
    
    # Legacy security metrics (for backward compatibility)
    "failed_auth_count": "Number of failed authentication attempts. Business: Security incident indicator. Technical: COUNT of auth failures.",
    "data_access_events": "Number of data access events. Business: Data consumption activity. Technical: COUNT of SELECT/READ operations.",
    "admin_actions": "Number of administrative actions. Business: Privileged activity for audit. Technical: COUNT of ADMIN operations.",
    "failed_auth_rate": "Failed authentication rate percentage. Business: Security risk indicator. Technical: failed_auth / total_auth * 100.",
    "admin_action_rate": "Admin action rate percentage. Business: Privileged activity proportion. Technical: admin_actions / total_events * 100.",
    "events_per_user": "Average events per user. Business: User activity level. Technical: total_events / distinct_users.",
    "auth_failure_drift": "Change in failed auth attempts. Business: Security posture trend. Technical: current - baseline failed_auth.",
    
    # ==========================================
    # QUALITY MONITOR METRICS (fact_table_quality)
    # ==========================================
    "total_tables": "Total number of monitored tables. Business: Data estate coverage. Technical: COUNT(DISTINCT table_name).",
    "tables_with_issues": "Tables with quality issues. Business: Data quality problem scope. Technical: COUNT of tables with quality_score < threshold.",
    "avg_quality_score": "Average data quality score. Business: Overall data quality KPI (0-100). Technical: AVG(quality_score).",
    "null_violation_count": "Count of NULL constraint violations. Business: Data completeness issues. Technical: COUNT of NULL violations.",
    "schema_drift_count": "Count of schema changes detected. Business: Schema stability indicator. Technical: COUNT of schema changes.",
    "freshness_violations": "Count of data freshness violations. Business: Data currency issues. Technical: COUNT where data_age > SLA.",
    "quality_score_below_threshold": "Tables with score below threshold. Business: Quality attention required. Technical: COUNT where quality_score < 80.",
    "quality_issue_rate": "Percentage of tables with issues. Business: Quality coverage indicator. Technical: tables_with_issues / total_tables * 100.",
    "avg_freshness_hours": "Average data freshness in hours. Business: Data currency indicator. Technical: AVG(hours_since_update).",
    "quality_drift": "Change in average quality score. Business: Quality trend indicator. Technical: current - baseline avg_quality_score.",
    
    # ==========================================
    # GOVERNANCE MONITOR METRICS (fact_table_lineage)
    # ==========================================
    # Event volume metrics
    "total_lineage_events": "Total number of lineage events. Business: Data activity volume. Technical: COUNT(*) of all lineage records.",
    "distinct_users": "Number of unique users with activity. Business: Active user count. Technical: COUNT(DISTINCT user/created_by).",
    
    # Table activity metrics
    "active_tables_count": "Number of unique tables with activity. Business: Data estate utilization. Technical: COUNT(DISTINCT source + target tables).",
    "active_source_tables": "Number of unique source tables. Business: Data read breadth. Technical: COUNT(DISTINCT source_table_full_name).",
    "active_target_tables": "Number of unique target tables. Business: Data write breadth. Technical: COUNT(DISTINCT target_table_full_name).",
    
    # Read/Write breakdown
    "read_event_count": "Number of data read events. Business: Data consumption volume. Technical: COUNT where source_table IS NOT NULL.",
    "write_event_count": "Number of data write events. Business: Data production volume. Technical: COUNT where target_table IS NOT NULL.",
    
    # Entity type breakdown
    "table_entity_events": "Lineage events from TABLE operations. Business: Direct table activity. Technical: COUNT where entity_type = TABLE.",
    "notebook_entity_events": "Lineage events from NOTEBOOK operations. Business: Interactive analysis activity. Technical: COUNT where entity_type = NOTEBOOK.",
    "pipeline_entity_events": "Lineage events from PIPELINE operations. Business: ETL pipeline activity. Technical: COUNT where entity_type = PIPELINE.",
    "job_entity_events": "Lineage events from JOB operations. Business: Scheduled job activity. Technical: COUNT where entity_type = JOB.",
    "query_entity_events": "Lineage events from QUERY operations. Business: SQL query activity. Technical: COUNT where entity_type = QUERY.",
    
    # Data consumption patterns
    "unique_data_consumers": "Number of unique users reading data. Business: Data consumer count. Technical: COUNT(DISTINCT created_by where source IS NOT NULL).",
    "unique_data_producers": "Number of unique users writing data. Business: Data producer count. Technical: COUNT(DISTINCT created_by where target IS NOT NULL).",
    
    # Sensitive data tracking
    "sensitive_table_access_count": "Access events to potentially sensitive tables. Business: Security monitoring indicator. Technical: COUNT where table_name LIKE '%pii%' or '%sensitive%'.",
    
    # Layer access tracking
    "gold_layer_reads": "Read events from Gold layer tables. Business: Analytics consumption. Technical: COUNT where source LIKE '%gold%'.",
    "gold_layer_writes": "Write events to Gold layer tables. Business: Gold layer production. Technical: COUNT where target LIKE '%gold%'.",
    "silver_layer_reads": "Read events from Silver layer tables. Business: Intermediate data consumption. Technical: COUNT where source LIKE '%silver%'.",
    "bronze_layer_reads": "Read events from Bronze layer tables. Business: Raw data consumption. Technical: COUNT where source LIKE '%bronze%'.",
    
    # Cross-catalog tracking
    "distinct_source_catalogs": "Number of unique source catalogs. Business: Cross-catalog data access. Technical: COUNT(DISTINCT source_table_catalog).",
    "distinct_target_catalogs": "Number of unique target catalogs. Business: Cross-catalog data writes. Technical: COUNT(DISTINCT target_table_catalog).",
    
    # Off-hours activity
    "off_hours_events": "Lineage events during off-hours (before 6AM or after 10PM). Business: Unusual activity indicator. Technical: COUNT where HOUR < 6 or HOUR > 22.",
    
    # Derived governance metrics
    "read_write_ratio": "Ratio of read to write events. Business: Consumption vs production balance. Technical: read_event_count / write_event_count.",
    "avg_events_per_user": "Average lineage events per user. Business: User activity level. Technical: total_events / distinct_users.",
    "avg_tables_per_user": "Average tables accessed per user. Business: User data breadth. Technical: active_tables / distinct_users.",
    "consumer_producer_ratio": "Ratio of consumers to producers. Business: Data consumption pattern. Technical: consumers / producers.",
    "sensitive_access_rate": "Percentage of access to sensitive tables. Business: Security exposure indicator. Technical: sensitive_access / total * 100.",
    "off_hours_rate": "Percentage of off-hours activity. Business: Unusual activity indicator. Technical: off_hours_events / total * 100.",
    "gold_layer_access_rate": "Percentage of Gold layer access. Business: Analytics utilization. Technical: (gold_reads + gold_writes) / total * 100.",
    "notebook_activity_rate": "Percentage of notebook-driven activity. Business: Interactive analysis proportion. Technical: notebook_events / total * 100.",
    "pipeline_activity_rate": "Percentage of pipeline-driven activity. Business: ETL automation proportion. Technical: pipeline_events / total * 100.",
    "cross_catalog_complexity": "Average number of catalogs involved. Business: Data governance complexity. Technical: (source_catalogs + target_catalogs) / 2.",
    
    # Governance drift metrics
    "active_tables_drift": "Change in active table count between periods. Business: Data estate growth indicator. Technical: current - baseline active_tables_count.",
    "lineage_volume_drift_pct": "Percentage change in lineage events. Business: Activity growth indicator. Technical: (current - baseline) / baseline * 100.",
    "read_write_ratio_drift": "Change in read/write ratio between periods. Business: Consumption pattern shift. Technical: current - baseline read_write_ratio.",
    "sensitive_access_drift": "Change in sensitive table access count. Business: Security posture change. Technical: current - baseline sensitive_access_count.",
    "user_count_drift": "Change in active user count between periods. Business: User engagement trend. Technical: current - baseline distinct_users.",
    "off_hours_rate_drift": "Change in off-hours activity rate. Business: Unusual activity trend. Technical: current - baseline off_hours_rate.",
    
    # Legacy governance metrics (for fact_governance_metrics if it exists)
    "total_assets": "Total governed data assets. Business: Governance coverage scope. Technical: COUNT(DISTINCT asset_id).",
    "documented_assets": "Assets with documentation. Business: Documentation coverage. Technical: COUNT where has_documentation = TRUE.",
    "tagged_assets": "Assets with governance tags. Business: Tagging coverage. Technical: COUNT where is_tagged = TRUE.",
    "access_controlled_assets": "Assets with explicit access controls. Business: Security coverage. Technical: COUNT where has_acl = TRUE.",
    "lineage_tracked_assets": "Assets with lineage tracking. Business: Data provenance coverage. Technical: COUNT where has_lineage = TRUE.",
    "documentation_rate": "Documentation coverage percentage. Business: Governance maturity indicator. Technical: documented / total * 100.",
    "tagging_rate": "Tagging coverage percentage. Business: Metadata quality indicator. Technical: tagged / total * 100.",
    "access_control_rate": "Access control coverage percentage. Business: Security governance indicator. Technical: controlled / total * 100.",
    "lineage_coverage_rate": "Lineage coverage percentage. Business: Data provenance maturity. Technical: tracked / total * 100.",
    "governance_score": "Composite governance score (0-100). Business: Overall governance maturity KPI. Technical: Weighted average of coverage rates.",
    "governance_drift": "Change in governance score. Business: Governance improvement trend. Technical: current - baseline governance_score.",
    
    # ==========================================
    # INFERENCE MONITOR METRICS (fact_model_serving)
    # ==========================================
    "total_requests": "Total inference requests. Business: ML serving volume. Technical: COUNT(*) of all requests.",
    "successful_requests": "Successful inference requests. Business: ML reliability numerator. Technical: COUNT where status = SUCCESS.",
    "failed_requests": "Failed inference requests. Business: ML reliability issues. Technical: COUNT where status = FAILED.",
    "avg_latency_ms": "Average inference latency in milliseconds. Business: ML performance baseline. Technical: AVG(latency_ms).",
    "p50_latency_ms": "Median inference latency. Business: Typical ML performance. Technical: PERCENTILE(latency_ms, 0.50).",
    "p95_latency_ms": "P95 inference latency. Business: ML SLA threshold. Technical: PERCENTILE(latency_ms, 0.95).",
    "p99_latency_ms": "P99 inference latency. Business: Worst-case ML performance. Technical: PERCENTILE(latency_ms, 0.99).",
    "total_tokens": "Total tokens processed. Business: LLM usage volume (for LLMs). Technical: SUM(token_count).",
    "request_success_rate": "Inference success rate percentage. Business: ML reliability KPI (target: >99%). Technical: successful / total * 100.",
    "error_rate": "Inference error rate percentage. Business: ML reliability issue indicator. Technical: failed / total * 100.",
    "avg_tokens_per_request": "Average tokens per request. Business: Request complexity indicator. Technical: total_tokens / total_requests.",
    "throughput_per_second": "Requests per second. Business: ML serving capacity utilization. Technical: total_requests / time_window_seconds.",
    "latency_drift_pct": "Period-over-period latency change. Business: ML performance trend. Technical: (current - baseline) / baseline * 100.",
    "error_rate_drift": "Change in error rate. Business: ML reliability trend. Technical: current - baseline error_rate.",
}

# ============================================================================
# LAKEHOUSE MONITORING QUERY GUIDE
# ============================================================================
# This guide explains how to query Lakehouse Monitoring output tables.
# Essential for Genie natural language query understanding.

MONITORING_QUERY_GUIDE = """
LAKEHOUSE MONITORING QUERY GUIDE FOR GENIE
==========================================

Lakehouse Monitoring creates two output tables per monitored table:
- {table}_profile_metrics: Contains AGGREGATE and DERIVED custom metrics
- {table}_drift_metrics: Contains DRIFT metrics comparing periods

CRITICAL QUERY PATTERNS:
========================

1. PROFILE_METRICS TABLE - Business KPIs
----------------------------------------
Filter for table-level KPIs (custom metrics):
  WHERE column_name = ':table'
  AND log_type = 'INPUT'

Filter for time window:
  WHERE window.start >= '2024-01-01'
  AND window.end <= '2024-12-31'

Get overall metrics (no slicing):
  WHERE slice_key IS NULL OR slice_key = 'No Slice'
  -- Alternative: COALESCE(slice_key, 'No Slice') = 'No Slice'

Get metrics by dimension (sliced):
  WHERE slice_key = 'workspace_id'
  AND slice_value = 'your_workspace_id'

Example - Get daily cost metrics:
  SELECT window.start, total_daily_cost, tag_coverage_pct
  FROM fact_usage_profile_metrics
  WHERE column_name = ':table'
    AND log_type = 'INPUT'
    AND slice_key IS NULL
  ORDER BY window.start DESC

Example - Get cost by workspace:
  SELECT slice_value AS workspace_id, total_daily_cost
  FROM fact_usage_profile_metrics
  WHERE column_name = ':table'
    AND log_type = 'INPUT'
    AND slice_key = 'workspace_id'
  ORDER BY total_daily_cost DESC


2. DRIFT_METRICS TABLE - Period Comparisons
-------------------------------------------
Filter for consecutive period comparison:
  WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'

Filter by time window:
  WHERE window.start >= '2024-01-01'

Get overall drift (no slicing):
  WHERE slice_key IS NULL OR slice_key = 'No Slice'

Get drift by dimension:
  WHERE slice_key = 'workspace_id'
  AND slice_value = 'your_workspace_id'

Example - Get cost drift over time:
  SELECT window.start, cost_drift_pct, dbu_drift_pct
  FROM fact_usage_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND slice_key IS NULL
  ORDER BY window.start


3. SLICING DIMENSIONS BY MONITOR
--------------------------------
Cost Monitor (fact_usage):
  - workspace_id: Cost by workspace
  - sku_name: Cost by SKU type
  - cloud: AWS vs Azure vs GCP
  - is_tagged: Tagged vs untagged spend
  - product_features_is_serverless: Serverless vs classic

Job Monitor (fact_job_run_timeline):
  - workspace_id: Jobs by workspace
  - result_state: SUCCESS, FAILED, ERROR, CANCELED
  - trigger_type: SCHEDULE, MANUAL, RETRY
  - job_name: By specific job
  - termination_code: USER_CANCELED, DRIVER_ERROR, etc.

Query Monitor (fact_query_history):
  - workspace_id: Queries by workspace
  - compute_warehouse_id: By warehouse
  - execution_status: FINISHED, FAILED, CANCELED
  - statement_type: SELECT, INSERT, UPDATE, etc.
  - executed_by: By user

Cluster Monitor (fact_node_timeline):
  - workspace_id: Clusters by workspace
  - cluster_id: By specific cluster
  - node_type: Instance type
  - cluster_name: By named cluster
  - driver: TRUE/FALSE for driver vs worker

Security Monitor (fact_audit_logs):
  - workspace_id: Events by workspace
  - service_name: clusters, databrickssql, workspace, unityCatalog
  - audit_level: ACCOUNT_LEVEL, WORKSPACE_LEVEL
  - action_name: By specific action
  - user_identity_email: By user


4. KEY COLUMNS EXPLAINED
------------------------
window.start: Start of the time window (use for time series)
window.end: End of the time window
column_name: ':table' for custom metrics, column name for built-in stats
log_type: 'INPUT' for source data metrics
slice_key: The dimension being sliced (NULL for overall)
slice_value: The value of the slice dimension
drift_type: 'CONSECUTIVE' for period-over-period


5. EXAMPLE GENIE QUERIES
------------------------
"What is the total cost this month?"
→ Query fact_usage_profile_metrics, filter column_name=':table', sum total_daily_cost

"Show cost breakdown by workspace"
→ Query fact_usage_profile_metrics, filter slice_key='workspace_id'

"Which jobs failed yesterday?"
→ Query fact_job_run_timeline_profile_metrics, filter slice_key='result_state', 
   slice_value='FAILED'

"How has cost changed compared to last period?"
→ Query fact_usage_drift_metrics, select cost_drift_pct

"Show query performance by warehouse"
→ Query fact_query_history_profile_metrics, filter slice_key='compute_warehouse_id'
"""

# Table-level descriptions for monitoring output tables
# These descriptions are added as table comments for Genie understanding
MONITOR_TABLE_DESCRIPTIONS = {
    "fact_usage": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_usage (billing/cost data). 

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL (or COALESCE(slice_key, 'No Slice') = 'No Slice')
- For dimensional analysis: WHERE slice_key = 'workspace_id' (or 'sku_name', 'cloud', 'is_tagged', 'product_features_is_serverless')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: total_daily_cost, total_daily_dbu, tag_coverage_pct, serverless_ratio, jobs_cost_share, sql_cost_share, all_purpose_cost_ratio, dlt_cost_share, model_serving_cost_share

SLICING DIMENSIONS: workspace_id (by workspace), sku_name (by SKU), cloud (AWS/Azure/GCP), is_tagged (tagged vs untagged), product_features_is_serverless (serverless vs classic)

Business: Primary source for FinOps dashboards tracking spend, efficiency, and cost attribution.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_usage (billing/cost data).

QUERY GUIDE:
- Filter for period comparison: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'
- For overall drift: WHERE slice_key IS NULL
- For dimensional drift: WHERE slice_key = 'workspace_id' AND slice_value = 'value'
- Time filter: WHERE window.start >= 'date'

AVAILABLE DRIFT METRICS: cost_drift_pct (% change in cost), dbu_drift_pct (% change in DBU), tag_coverage_drift (change in tag coverage %)

Business: Alert source for budget variance and FinOps trend monitoring. Positive drift = cost increase."""
    },
    "fact_job_run_timeline": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_job_run_timeline (job execution data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- For dimensional analysis: WHERE slice_key = 'result_state' (or 'trigger_type', 'job_name', 'termination_code', 'workspace_id')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: total_runs, success_count, failure_count, success_rate, failure_rate, avg_duration_minutes, p95_duration_minutes, p99_duration_minutes, timeout_rate, cancellation_rate

SLICING DIMENSIONS: workspace_id, result_state (SUCCESS/FAILED/ERROR/CANCELED), trigger_type (SCHEDULE/MANUAL/RETRY), job_name, termination_code

Business: Primary source for reliability dashboards tracking job health and SLA compliance.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_job_run_timeline (job execution data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'
- For overall drift: WHERE slice_key IS NULL
- For dimensional drift: WHERE slice_key = 'result_state' AND slice_value = 'FAILED'

AVAILABLE DRIFT METRICS: success_rate_drift (change in success %), failure_count_drift (change in failures), duration_drift_pct (% change in duration), p99_duration_drift_pct

Business: Alert source for reliability degradation. Negative success_rate_drift = degradation."""
    },
    "fact_query_history": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_query_history (SQL query execution data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- For dimensional analysis: WHERE slice_key = 'compute_warehouse_id' (or 'execution_status', 'statement_type', 'executed_by', 'workspace_id')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: query_count, successful_queries, failed_queries, query_success_rate, avg_duration_sec, p95_duration_sec, p99_duration_sec, sla_breach_rate, cache_hit_rate, spill_rate

SLICING DIMENSIONS: workspace_id, compute_warehouse_id (by warehouse), execution_status (FINISHED/FAILED/CANCELED), statement_type (SELECT/INSERT/etc), executed_by (by user)

Business: Primary source for query performance dashboards and warehouse sizing.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_query_history (SQL query execution data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'
- For overall drift: WHERE slice_key IS NULL
- For warehouse drift: WHERE slice_key = 'compute_warehouse_id'

AVAILABLE DRIFT METRICS: p95_duration_drift_pct, query_volume_drift_pct, failure_rate_drift, sla_breach_rate_drift

Business: Alert source for query performance degradation."""
    },
    "fact_node_timeline": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_node_timeline (cluster node utilization data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- For dimensional analysis: WHERE slice_key = 'cluster_id' (or 'node_type', 'driver', 'workspace_id')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: total_node_hours, active_clusters, avg_cpu_pct, avg_memory_pct, cpu_underutilized_rate, cpu_overutilized_rate, memory_underutilized_rate, memory_overutilized_rate, underutilized_rate, overutilized_rate, rightsizing_opportunity_count

SLICING DIMENSIONS: workspace_id, cluster_id, node_type (instance type), driver (TRUE=driver node, FALSE=worker)

Business: Primary source for compute optimization and right-sizing dashboards.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_node_timeline (cluster node utilization data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'
- For overall drift: WHERE slice_key IS NULL
- For cluster drift: WHERE slice_key = 'cluster_id'

AVAILABLE DRIFT METRICS: cpu_drift, memory_drift, utilization_drift

Business: Alert source for compute efficiency changes."""
    },
    "fact_table_lineage": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_table_lineage (data lineage tracking).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- For dimensional analysis: WHERE slice_key = 'entity_type' (or 'created_by', 'source_table_catalog', 'workspace_id')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: lineage_record_count, distinct_source_tables, distinct_target_tables, distinct_users, cross_catalog_count, cross_catalog_rate, same_catalog_rate

SLICING DIMENSIONS: workspace_id, entity_type (TABLE/VIEW), created_by (user email), source_table_catalog

Business: Primary source for data governance and lineage visibility dashboards.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_table_lineage (data lineage tracking).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'
- For overall drift: WHERE slice_key IS NULL

AVAILABLE DRIFT METRICS: lineage_volume_drift, cross_catalog_drift

Business: Alert source for lineage pattern changes."""
    },
    "fact_cluster_timeline": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_cluster_timeline (cluster utilization data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- For dimensional analysis: WHERE slice_key = 'cluster_id' (or 'node_type', 'cluster_name', 'driver', 'workspace_id')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: node_hour_count, avg_cpu_total_pct, avg_memory_pct, underutilization_rate, overutilization_rate, efficiency_score, rightsizing_opportunity_pct

SLICING DIMENSIONS: workspace_id, cluster_id, node_type (instance type), cluster_name, driver (TRUE=driver node, FALSE=worker)

Business: Primary source for compute optimization and right-sizing dashboards.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_cluster_timeline (cluster utilization data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'

AVAILABLE DRIFT METRICS: cpu_utilization_drift, memory_utilization_drift, efficiency_score_drift, rightsizing_opportunity_drift

Business: Alert source for compute efficiency changes."""
    },
    "fact_audit_logs": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_audit_logs (security audit data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- For dimensional analysis: WHERE slice_key = 'service_name' (or 'audit_level', 'action_name', 'user_identity_email', 'workspace_id')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: total_events, distinct_users, sensitive_action_count, failed_action_count, unauthorized_count, off_hours_rate, human_user_ratio, service_principal_ratio

SLICING DIMENSIONS: workspace_id, service_name (clusters/databrickssql/workspace/unityCatalog), audit_level (ACCOUNT_LEVEL/WORKSPACE_LEVEL), action_name, user_identity_email

Business: Primary source for security dashboards and compliance reporting.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_audit_logs (security audit data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'
- For user drift: WHERE slice_key = 'user_identity_email'

AVAILABLE DRIFT METRICS: event_volume_drift_pct, sensitive_action_drift, failure_rate_drift, off_hours_drift, user_count_drift

Business: Alert source for security anomaly detection. Spike in sensitive_action_drift = investigation needed."""
    },
    "fact_table_quality": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_table_quality (data quality metrics).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: total_tables, tables_with_issues, avg_quality_score, null_violation_count, schema_drift_count, freshness_violations, quality_issue_rate

Business: Primary source for data quality dashboards.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_table_quality (data quality metrics).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'

AVAILABLE DRIFT METRICS: quality_drift (change in avg_quality_score)

Business: Alert source for data quality degradation. Negative quality_drift = quality declining."""
    },
    "fact_governance_metrics": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_governance_metrics (governance coverage data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: total_assets, documented_assets, tagged_assets, documentation_rate, tagging_rate, access_control_rate, lineage_coverage_rate, governance_score

Business: Primary source for governance maturity dashboards.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_governance_metrics (governance coverage data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'

AVAILABLE DRIFT METRICS: governance_drift (change in governance_score)

Business: Alert source for governance improvement tracking. Positive governance_drift = improving."""
    },
    "fact_model_serving": {
        "profile_table": """Lakehouse Monitoring profile metrics for fact_model_serving (ML inference data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: total_requests, successful_requests, failed_requests, request_success_rate, error_rate, avg_latency_ms, p50_latency_ms, p95_latency_ms, p99_latency_ms, throughput_per_second

Business: Primary source for ML performance dashboards.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_model_serving (ML inference data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'

AVAILABLE DRIFT METRICS: latency_drift_pct (% change in latency), error_rate_drift (change in error %)

Business: Alert source for ML model degradation. Positive latency_drift_pct = latency increasing."""
    },
}


def document_monitor_output_tables(
    spark,
    catalog: str,
    gold_schema: str,
    table_name: str,
    custom_metrics: List = None,
    verbose: bool = False
) -> dict:
    """
    Add detailed table and column descriptions to Lakehouse Monitoring output tables.
    
    This enables Genie and LLMs to understand the monitoring metrics for natural language queries.
    
    Args:
        spark: SparkSession
        catalog: Catalog name
        gold_schema: Gold schema name (monitoring schema will be {gold_schema}_monitoring)
        table_name: Base table name (e.g., 'fact_usage')
        custom_metrics: Optional list of MonitorMetric objects to document
        verbose: If True, print detailed debugging output for each column
    
    Returns:
        dict with documentation status for each table
    """
    monitoring_schema = f"{gold_schema}_monitoring"
    profile_table = f"{catalog}.{monitoring_schema}.{table_name}_profile_metrics"
    drift_table = f"{catalog}.{monitoring_schema}.{table_name}_drift_metrics"
    
    results = {
        "profile_metrics": "NOT_FOUND", 
        "drift_metrics": "NOT_FOUND",
        "profile_columns_total": 0,
        "profile_columns_documented": 0,
        "drift_columns_total": 0,
        "drift_columns_documented": 0,
    }
    
    print(f"  Documenting: {table_name}")
    
    # Get table descriptions
    table_descs = MONITOR_TABLE_DESCRIPTIONS.get(table_name, {})
    profile_desc = table_descs.get("profile_table", f"Lakehouse Monitoring profile metrics for {table_name}. Use column_name=':table' for table-level aggregations.")
    drift_desc = table_descs.get("drift_table", f"Lakehouse Monitoring drift metrics for {table_name}. Contains period-over-period metric comparisons.")
    
    # Document profile_metrics table
    try:
        # Get actual columns in the table
        df_schema = spark.sql(f"DESCRIBE TABLE {profile_table}")
        actual_columns = [row.col_name for row in df_schema.collect() if not row.col_name.startswith("#")]
        results["profile_columns_total"] = len(actual_columns)
        
        print(f"    Profile table: {profile_table}")
        print(f"    Total columns: {len(actual_columns)}")
        
        if verbose:
            # Show all columns in the table
            print(f"    Columns in table: {', '.join(actual_columns[:10])}{'...' if len(actual_columns) > 10 else ''}")
        
        # Add table comment
        escaped_desc = profile_desc.replace("'", "''")
        spark.sql(f"ALTER TABLE {profile_table} SET TBLPROPERTIES ('comment' = '{escaped_desc}')")
        print(f"    ✓ Table comment added")
        
        # Add column comments for custom metrics that EXIST in this table
        columns_documented = 0
        columns_skipped = 0
        columns_missing_desc = []
        
        for col_name in actual_columns:
            if col_name in METRIC_DESCRIPTIONS:
                description = METRIC_DESCRIPTIONS[col_name]
                try:
                    escaped_col_desc = description.replace("'", "''")
                    spark.sql(f"ALTER TABLE {profile_table} ALTER COLUMN `{col_name}` COMMENT '{escaped_col_desc}'")
                    columns_documented += 1
                    if verbose:
                        print(f"      ✓ {col_name}")
                except Exception as col_err:
                    columns_skipped += 1
                    if verbose:
                        print(f"      ✗ {col_name}: {str(col_err)[:50]}")
            else:
                # Column exists but no description in registry
                # These are typically system columns like window, slice_key, etc.
                if col_name not in ['window', 'granularity', 'slice_key', 'slice_value', 
                                    'column_name', 'log_type', 'table_name', 'model_id',
                                    '__databricks_internal_id']:
                    columns_missing_desc.append(col_name)
        
        results["profile_columns_documented"] = columns_documented
        print(f"    ✓ Documented {columns_documented} custom metric columns")
        
        if columns_skipped > 0:
            print(f"    ⚠ Skipped {columns_skipped} columns (errors)")
        
        if verbose and columns_missing_desc:
            print(f"    ⚠ Missing descriptions for: {', '.join(columns_missing_desc[:5])}{'...' if len(columns_missing_desc) > 5 else ''}")
        
        results["profile_metrics"] = f"SUCCESS: {columns_documented}/{len(actual_columns)} columns"
        
    except Exception as e:
        error_str = str(e)
        if "TABLE_OR_VIEW_NOT_FOUND" in error_str or "does not exist" in error_str.lower():
            print(f"    ⏳ Profile table not found (monitor initializing)")
            results["profile_metrics"] = "NOT_READY"
        else:
            print(f"    ✗ Error: {error_str[:80]}")
            results["profile_metrics"] = f"ERROR: {error_str[:50]}"
    
    # Document drift_metrics table
    try:
        # Get actual columns in the table
        df_schema = spark.sql(f"DESCRIBE TABLE {drift_table}")
        actual_columns = [row.col_name for row in df_schema.collect() if not row.col_name.startswith("#")]
        results["drift_columns_total"] = len(actual_columns)
        
        print(f"    Drift table: {drift_table}")
        print(f"    Total columns: {len(actual_columns)}")
        
        if verbose:
            print(f"    Columns in table: {', '.join(actual_columns[:10])}{'...' if len(actual_columns) > 10 else ''}")
        
        # Add table comment
        escaped_desc = drift_desc.replace("'", "''")
        spark.sql(f"ALTER TABLE {drift_table} SET TBLPROPERTIES ('comment' = '{escaped_desc}')")
        print(f"    ✓ Table comment added")
        
        # Add column comments for drift metrics that EXIST in this table
        columns_documented = 0
        columns_skipped = 0
        
        for col_name in actual_columns:
            if col_name in METRIC_DESCRIPTIONS:
                description = METRIC_DESCRIPTIONS[col_name]
                try:
                    escaped_col_desc = description.replace("'", "''")
                    spark.sql(f"ALTER TABLE {drift_table} ALTER COLUMN `{col_name}` COMMENT '{escaped_col_desc}'")
                    columns_documented += 1
                    if verbose:
                        print(f"      ✓ {col_name}")
                except Exception as col_err:
                    columns_skipped += 1
                    if verbose:
                        print(f"      ✗ {col_name}: {str(col_err)[:50]}")
        
        results["drift_columns_documented"] = columns_documented
        print(f"    ✓ Documented {columns_documented} drift metric columns")
        
        if columns_skipped > 0:
            print(f"    ⚠ Skipped {columns_skipped} columns (errors)")
        
        results["drift_metrics"] = f"SUCCESS: {columns_documented}/{len(actual_columns)} columns"
        
    except Exception as e:
        error_str = str(e)
        if "TABLE_OR_VIEW_NOT_FOUND" in error_str or "does not exist" in error_str.lower():
            print(f"    ⏳ Drift table not found (monitor initializing)")
            results["drift_metrics"] = "NOT_READY"
        else:
            print(f"    ✗ Error: {error_str[:80]}")
            results["drift_metrics"] = f"ERROR: {error_str[:50]}"
    
    return results


def document_all_monitor_tables(spark, catalog: str, gold_schema: str, verbose: bool = False) -> dict:
    """
    Document all Lakehouse Monitoring output tables.
    
    Args:
        spark: SparkSession
        catalog: Catalog name
        gold_schema: Gold schema name
        verbose: If True, print detailed debugging output
    
    Returns:
        dict with documentation status for each monitored table
    """
    # Tables with ACTUAL monitors (must match the monitor notebooks)
    # These are the Gold layer tables being monitored:
    monitored_tables = [
        "fact_usage",              # cost_monitor.py
        "fact_job_run_timeline",   # job_monitor.py
        "fact_query_history",      # query_monitor.py
        "fact_node_timeline",      # cluster_monitor.py (NOT fact_cluster_timeline!)
        "fact_audit_logs",         # security_monitor.py
        "fact_table_quality",      # quality_monitor.py (may not exist yet)
        "fact_table_lineage",      # governance_monitor.py (NOT fact_governance_metrics!)
        # Inference monitors are in ML schema - handled separately
    ]
    
    print("=" * 60)
    print("Documenting Lakehouse Monitoring Tables for Genie")
    print("=" * 60)
    print(f"  Catalog: {catalog}")
    print(f"  Gold Schema: {gold_schema}")
    print(f"  Monitoring Schema: {gold_schema}_monitoring")
    print(f"  Tables to document: {len(monitored_tables)}")
    print("-" * 60)
    
    all_results = {}
    tables_documented = 0
    tables_not_ready = 0
    tables_with_errors = 0
    
    for table_name in monitored_tables:
        print(f"\n[{monitored_tables.index(table_name) + 1}/{len(monitored_tables)}] {table_name}")
        result = document_monitor_output_tables(spark, catalog, gold_schema, table_name, verbose=verbose)
        all_results[table_name] = result
        
        # Count by status
        profile_status = result.get("profile_metrics", "")
        if "SUCCESS" in str(profile_status):
            tables_documented += 1
        elif profile_status == "NOT_READY":
            tables_not_ready += 1
        else:
            tables_with_errors += 1
    
    print("\n" + "=" * 60)
    print("DOCUMENTATION SUMMARY")
    print("=" * 60)
    print(f"  ✓ Tables documented:  {tables_documented}")
    print(f"  ⏳ Tables not ready:   {tables_not_ready}")
    print(f"  ✗ Tables with errors: {tables_with_errors}")
    
    if tables_not_ready > 0:
        print(f"\n  ⚠ Note: {tables_not_ready} tables are still initializing.")
        print("    Run documentation again after monitors complete initialization (~15 min).")
    
    if verbose:
        print("\n" + "-" * 60)
        print("DETAILED RESULTS:")
        for table_name, result in all_results.items():
            print(f"\n  {table_name}:")
            for key, value in result.items():
                icon = "✓" if "SUCCESS" in str(value) else ("⏳" if value == "NOT_READY" else "✗")
                print(f"    [{icon}] {key}: {value}")
    
    return all_results
