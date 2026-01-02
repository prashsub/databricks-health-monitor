"""
Lakehouse Monitoring Utilities
==============================

Shared utilities for creating and managing Lakehouse Monitors.

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
# Comprehensive descriptions for all custom metrics to enable Genie understanding.
# Format: "Metric Name": "Business description. Technical: calculation details."

METRIC_DESCRIPTIONS = {
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
    "total_queries": "Total number of queries executed. Business: Query workload volume. Technical: COUNT(*) of all queries.",
    "avg_query_duration_seconds": "Average query duration in seconds. Business: Query performance baseline. Technical: AVG(duration_seconds).",
    "p50_duration_seconds": "Median query duration in seconds. Business: Typical query performance. Technical: PERCENTILE(duration_seconds, 0.50).",
    "p95_duration_seconds": "P95 query duration in seconds. Business: SLA threshold for slow queries. Technical: PERCENTILE(duration_seconds, 0.95).",
    "p99_duration_seconds": "P99 query duration in seconds. Business: Worst-case query performance. Technical: PERCENTILE(duration_seconds, 0.99).",
    "failed_queries": "Number of failed queries. Business: Query reliability issues. Technical: COUNT where status = FAILED.",
    "cancelled_queries": "Number of cancelled queries. Business: User intervention or timeout issues. Technical: COUNT where status = CANCELED.",
    "successful_queries": "Number of successful queries. Business: Query reliability numerator. Technical: COUNT where status = FINISHED.",
    "total_rows_read": "Total rows scanned by queries. Business: Data access volume indicator. Technical: SUM(rows_read).",
    "total_bytes_read": "Total bytes scanned by queries. Business: IO efficiency indicator. Technical: SUM(bytes_read).",
    "query_success_rate": "Query success rate percentage. Business: Query reliability KPI. Technical: successful / total * 100.",
    "query_failure_rate": "Query failure rate percentage. Business: Query reliability issue indicator. Technical: failed / total * 100.",
    "avg_rows_per_query": "Average rows per query. Business: Query scope indicator. Technical: total_rows / total_queries.",
    "query_duration_drift_pct": "Period-over-period query duration change. Business: Performance trend indicator. Technical: (current - baseline) / baseline * 100.",
    
    # ==========================================
    # CLUSTER MONITOR METRICS (fact_cluster_timeline)
    # ==========================================
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
    "total_events": "Total number of audit events. Business: Security activity volume. Technical: COUNT(*) of all audit events.",
    "distinct_users": "Number of unique users with activity. Business: User base active size. Technical: COUNT(DISTINCT user_id).",
    "failed_auth_count": "Number of failed authentication attempts. Business: Security incident indicator. Technical: COUNT of auth failures.",
    "sensitive_actions": "Number of sensitive/privileged actions. Business: Security audit priority events. Technical: COUNT of privileged operations.",
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
    # GOVERNANCE MONITOR METRICS (fact_governance_metrics)
    # ==========================================
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
        "profile_table": """Lakehouse Monitoring profile metrics for fact_node_timeline (cluster utilization data).

QUERY GUIDE:
- For table-level KPIs: WHERE column_name = ':table' AND log_type = 'INPUT'
- For overall metrics: WHERE slice_key IS NULL
- For dimensional analysis: WHERE slice_key = 'cluster_id' (or 'node_type', 'cluster_name', 'driver', 'workspace_id')
- Time filter: WHERE window.start >= 'date' AND window.end <= 'date'

AVAILABLE METRICS: node_hour_count, avg_cpu_total_pct, avg_memory_pct, underutilization_rate, overutilization_rate, efficiency_score, rightsizing_opportunity_pct

SLICING DIMENSIONS: workspace_id, cluster_id, node_type (instance type), cluster_name, driver (TRUE=driver node, FALSE=worker)

Business: Primary source for compute optimization and right-sizing dashboards.""",
        
        "drift_table": """Lakehouse Monitoring drift metrics for fact_node_timeline (cluster utilization data).

QUERY GUIDE:
- Filter: WHERE drift_type = 'CONSECUTIVE' AND column_name = ':table'

AVAILABLE DRIFT METRICS: cpu_utilization_drift, memory_utilization_drift, efficiency_score_drift, rightsizing_opportunity_drift

Business: Alert source for compute efficiency changes."""
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
    custom_metrics: List = None
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
    
    Returns:
        dict with documentation status for each table
    """
    monitoring_schema = f"{gold_schema}_monitoring"
    profile_table = f"{catalog}.{monitoring_schema}.{table_name}_profile_metrics"
    drift_table = f"{catalog}.{monitoring_schema}.{table_name}_drift_metrics"
    
    results = {"profile_metrics": "NOT_FOUND", "drift_metrics": "NOT_FOUND"}
    
    print(f"  Documenting monitoring tables for {table_name}...")
    
    # Get table descriptions
    table_descs = MONITOR_TABLE_DESCRIPTIONS.get(table_name, {})
    profile_desc = table_descs.get("profile_table", f"Lakehouse Monitoring profile metrics for {table_name}. Use column_name=':table' for table-level aggregations.")
    drift_desc = table_descs.get("drift_table", f"Lakehouse Monitoring drift metrics for {table_name}. Contains period-over-period metric comparisons.")
    
    # Document profile_metrics table
    try:
        # Check if table exists
        spark.sql(f"DESCRIBE TABLE {profile_table}")
        
        # Add table comment
        escaped_desc = profile_desc.replace("'", "''")
        spark.sql(f"ALTER TABLE {profile_table} SET TBLPROPERTIES ('comment' = '{escaped_desc}')")
        print(f"    ✓ Added table comment to {table_name}_profile_metrics")
        
        # Add column comments for custom metrics
        columns_documented = 0
        for metric_name, description in METRIC_DESCRIPTIONS.items():
            try:
                escaped_col_desc = description.replace("'", "''")
                spark.sql(f"ALTER TABLE {profile_table} ALTER COLUMN {metric_name} COMMENT '{escaped_col_desc}'")
                columns_documented += 1
            except Exception:
                pass  # Column may not exist in this table
        
        print(f"    ✓ Documented {columns_documented} custom metric columns")
        results["profile_metrics"] = f"SUCCESS: {columns_documented} columns"
        
    except Exception as e:
        if "TABLE_OR_VIEW_NOT_FOUND" in str(e) or "does not exist" in str(e).lower():
            print(f"    ⚠ Table {profile_table} not found (monitor may still be initializing)")
            results["profile_metrics"] = "NOT_READY"
        else:
            print(f"    ✗ Error documenting profile_metrics: {str(e)[:80]}")
            results["profile_metrics"] = f"ERROR: {str(e)[:50]}"
    
    # Document drift_metrics table
    try:
        # Check if table exists
        spark.sql(f"DESCRIBE TABLE {drift_table}")
        
        # Add table comment
        escaped_desc = drift_desc.replace("'", "''")
        spark.sql(f"ALTER TABLE {drift_table} SET TBLPROPERTIES ('comment' = '{escaped_desc}')")
        print(f"    ✓ Added table comment to {table_name}_drift_metrics")
        
        # Add column comments for drift metrics
        columns_documented = 0
        for metric_name, description in METRIC_DESCRIPTIONS.items():
            if "drift" in metric_name.lower():
                try:
                    escaped_col_desc = description.replace("'", "''")
                    spark.sql(f"ALTER TABLE {drift_table} ALTER COLUMN {metric_name} COMMENT '{escaped_col_desc}'")
                    columns_documented += 1
                except Exception:
                    pass  # Column may not exist
        
        print(f"    ✓ Documented {columns_documented} drift metric columns")
        results["drift_metrics"] = f"SUCCESS: {columns_documented} columns"
        
    except Exception as e:
        if "TABLE_OR_VIEW_NOT_FOUND" in str(e) or "does not exist" in str(e).lower():
            print(f"    ⚠ Table {drift_table} not found (monitor may still be initializing)")
            results["drift_metrics"] = "NOT_READY"
        else:
            print(f"    ✗ Error documenting drift_metrics: {str(e)[:80]}")
            results["drift_metrics"] = f"ERROR: {str(e)[:50]}"
    
    return results


def document_all_monitor_tables(spark, catalog: str, gold_schema: str) -> dict:
    """
    Document all Lakehouse Monitoring output tables.
    
    Args:
        spark: SparkSession
        catalog: Catalog name
        gold_schema: Gold schema name
    
    Returns:
        dict with documentation status for each monitored table
    """
    # Tables with monitors
    monitored_tables = [
        "fact_usage",
        "fact_job_run_timeline",
        "fact_query_history",
        "fact_cluster_timeline",
        "fact_audit_logs",
        "fact_table_quality",
        "fact_governance_metrics",
        "fact_model_serving",
    ]
    
    print("=" * 60)
    print("Documenting Lakehouse Monitoring Tables for Genie")
    print("=" * 60)
    
    all_results = {}
    tables_documented = 0
    tables_not_ready = 0
    
    for table_name in monitored_tables:
        result = document_monitor_output_tables(spark, catalog, gold_schema, table_name)
        all_results[table_name] = result
        
        if "SUCCESS" in str(result.get("profile_metrics", "")):
            tables_documented += 1
        elif result.get("profile_metrics") == "NOT_READY":
            tables_not_ready += 1
    
    print("\n" + "=" * 60)
    print("Documentation Summary")
    print("=" * 60)
    print(f"  Tables documented: {tables_documented}")
    print(f"  Tables not ready:  {tables_not_ready}")
    print(f"  Tables with errors: {len(monitored_tables) - tables_documented - tables_not_ready}")
    
    if tables_not_ready > 0:
        print(f"\n  ⚠ Note: {tables_not_ready} tables are still initializing.")
        print("    Run documentation again after monitors complete initialization (~15 min).")
    
    return all_results
