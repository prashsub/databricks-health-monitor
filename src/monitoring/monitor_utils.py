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
