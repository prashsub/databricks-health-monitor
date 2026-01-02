# Appendix A - Code Examples

## Complete Monitor Notebook Template

```python
# Databricks notebook source
"""
{Domain} Monitor Configuration
==============================

Lakehouse Monitor for {table_name} table.
{Description of what this monitor tracks.}
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

def get_custom_metrics():
    """Define custom metrics for {domain} monitoring."""
    return [
        # ==========================================
        # AGGREGATE METRICS - Base Measurements
        # ==========================================
        
        create_aggregate_metric("record_count", "COUNT(*)", "LONG"),
        create_aggregate_metric("total_value", "SUM(value_column)", "DOUBLE"),
        create_aggregate_metric(
            "conditional_count",
            "SUM(CASE WHEN condition = TRUE THEN 1 ELSE 0 END)",
            "LONG"
        ),
        
        # ==========================================
        # DERIVED METRICS - Business Ratios
        # ==========================================
        
        create_derived_metric(
            "rate_metric",
            "conditional_count * 100.0 / NULLIF(record_count, 0)"
        ),
        
        # ==========================================
        # DRIFT METRICS - Period Comparison
        # ==========================================
        
        create_drift_metric(
            "value_drift_pct",
            "(({{current_df}}.total_value - {{base_df}}.total_value) / NULLIF({{base_df}}.total_value, 0)) * 100"
        ),
    ]


def create_monitor(workspace_client, catalog: str, gold_schema: str, spark=None):
    """Create the monitor for {table_name}."""
    table_name = f"{catalog}.{gold_schema}.{source_table}"

    # Clean up existing monitor
    delete_monitor_if_exists(workspace_client, table_name, spark)

    # Create monitor
    monitor = create_time_series_monitor(
        workspace_client=workspace_client,
        table_name=table_name,
        timestamp_col="timestamp_column",
        granularities=["1 day"],  # or ["1 hour", "1 day"]
        custom_metrics=get_custom_metrics(),
        slicing_exprs=["dimension1", "dimension2"],
        schedule_cron="0 0 6 * * ?",  # Daily at 6 AM
        spark=spark,
    )

    return monitor

# COMMAND ----------

def main():
    """Main entry point."""
    table_name = f"{catalog}.{gold_schema}.{source_table}"
    custom_metrics = get_custom_metrics()
    num_metrics = len(custom_metrics)
    
    print("=" * 70)
    print("{DOMAIN} MONITOR SETUP")
    print("=" * 70)
    print(f"  Target Table:    {table_name}")
    print(f"  Custom Metrics:  {num_metrics}")
    print("-" * 70)
    
    if not check_monitoring_available():
        print("[⊘ SKIPPED] Lakehouse Monitoring SDK not available")
        dbutils.notebook.exit("SKIPPED: SDK not available")
        return

    print("[1/3] Initializing WorkspaceClient...")
    workspace_client = WorkspaceClient()

    try:
        print("[2/3] Creating monitor...")
        monitor = create_monitor(workspace_client, catalog, gold_schema, spark)
        
        print("[3/3] Verifying monitor status...")
        if monitor:
            print("-" * 70)
            print("[✓ SUCCESS] Monitor created!")
            print(f"  Custom Metrics:  {num_metrics} configured")
            dbutils.notebook.exit(f"SUCCESS: Monitor created with {num_metrics} metrics")
        else:
            print("[⊘ SKIPPED] Monitor already exists")
            dbutils.notebook.exit("SKIPPED: Monitor already exists")
    except Exception as e:
        print(f"[✗ FAILED] Error: {str(e)}")
        raise

# COMMAND ----------

main()
```

## Monitor Utils Module (Pure Python)

```python
"""
Lakehouse Monitoring Utilities
==============================

Shared utilities for creating and managing Lakehouse Monitors.

NOTE: This is a pure Python module (NOT a Databricks notebook).
Do NOT add '# Databricks notebook source' header.
"""

import time
from typing import List, Optional

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.catalog import (
        MonitorTimeSeries,
        MonitorMetric,
        MonitorMetricType,
        MonitorCronSchedule
    )
    from databricks.sdk.errors import ResourceAlreadyExists, ResourceDoesNotExist
    import pyspark.sql.types as T
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


def check_monitoring_available() -> bool:
    """Check if Lakehouse Monitoring SDK is available."""
    return MONITORING_AVAILABLE


def delete_monitor_if_exists(workspace_client, table_name: str, spark=None) -> bool:
    """Delete existing monitor and its output tables."""
    try:
        existing = workspace_client.quality_monitors.get(table_name=table_name)
        print(f"      Found existing monitor")

        workspace_client.quality_monitors.delete(table_name=table_name)
        print(f"      ✓ Monitor deleted")

        # Drop output tables
        parts = table_name.split(".")
        if len(parts) == 3 and spark:
            catalog, schema, table = parts
            monitoring_schema = f"{schema}_monitoring"
            spark.sql(f"DROP TABLE IF EXISTS {catalog}.{monitoring_schema}.{table}_profile_metrics")
            spark.sql(f"DROP TABLE IF EXISTS {catalog}.{monitoring_schema}.{table}_drift_metrics")
            print(f"      ✓ Output tables dropped")

        return True
    except ResourceDoesNotExist:
        print(f"      No existing monitor")
        return False


def create_time_series_monitor(
    workspace_client,
    table_name: str,
    timestamp_col: str,
    granularities: List[str],
    custom_metrics: List,
    slicing_exprs: Optional[List[str]] = None,
    schedule_cron: Optional[str] = None,
    spark=None
):
    """Create a time series monitor with custom metrics."""
    parts = table_name.split(".")
    catalog, schema, table = parts
    
    output_schema = f"{catalog}.{schema}_monitoring"

    # Create monitoring schema
    if spark:
        monitoring_schema_name = f"{schema}_monitoring"
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{monitoring_schema_name}")

    config = {
        "table_name": table_name,
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

    try:
        monitor = workspace_client.quality_monitors.create(**config)
        print(f"      ✓ Monitor created")
        return monitor
    except ResourceAlreadyExists:
        print(f"      ⊘ Monitor already exists")
        return None


def create_aggregate_metric(name: str, definition: str, output_type: str = "DOUBLE"):
    """Create an AGGREGATE custom metric."""
    if output_type == "DOUBLE":
        data_type = T.StructField("output", T.DoubleType()).json()
    elif output_type == "LONG":
        data_type = T.StructField("output", T.LongType()).json()
    else:
        raise ValueError(f"Unknown type: {output_type}")

    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
        name=name,
        input_columns=[":table"],
        definition=definition,
        output_data_type=data_type
    )


def create_derived_metric(name: str, definition: str):
    """Create a DERIVED custom metric."""
    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
        name=name,
        input_columns=[":table"],
        definition=definition,
        output_data_type=T.StructField("output", T.DoubleType()).json()
    )


def create_drift_metric(name: str, definition: str):
    """Create a DRIFT custom metric."""
    return MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_DRIFT,
        name=name,
        input_columns=[":table"],
        definition=definition,
        output_data_type=T.StructField("output", T.DoubleType()).json()
    )
```

## Asset Bundle Job Definition

```yaml
# resources/monitoring/lakehouse_monitors_job.yml

resources:
  jobs:
    lakehouse_monitoring_setup_job:
      name: "[${bundle.target}] Health Monitor - Lakehouse Monitoring Setup"
      description: "Creates all Lakehouse Monitors for Gold layer tables."

      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - "databricks-sdk>=0.28.0"

      tasks:
        - task_key: create_cost_monitor
          environment_key: default
          notebook_task:
            notebook_path: ../../src/monitoring/cost_monitor.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}

        - task_key: create_job_monitor
          environment_key: default
          depends_on:
            - task_key: create_cost_monitor
          notebook_task:
            notebook_path: ../../src/monitoring/job_monitor.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}

        # ... more tasks

      timeout_seconds: 3600
      
      tags:
        project: health_monitor
        layer: monitoring
        job_type: setup
```

## Documentation Function

```python
def document_monitor_output_tables(
    spark,
    catalog: str,
    gold_schema: str,
    table_name: str
) -> dict:
    """Add descriptions to monitoring output tables for Genie."""
    monitoring_schema = f"{gold_schema}_monitoring"
    profile_table = f"{catalog}.{monitoring_schema}.{table_name}_profile_metrics"
    drift_table = f"{catalog}.{monitoring_schema}.{table_name}_drift_metrics"
    
    results = {}
    
    # Document profile_metrics
    try:
        # Table comment
        table_desc = f"Profile metrics for {table_name}. Use column_name=':table' for table-level KPIs."
        spark.sql(f"ALTER TABLE {profile_table} SET TBLPROPERTIES ('comment' = '{table_desc}')")
        
        # Column comments
        for metric_name, desc in METRIC_DESCRIPTIONS.items():
            try:
                escaped = desc.replace("'", "''")
                spark.sql(f"ALTER TABLE {profile_table} ALTER COLUMN {metric_name} COMMENT '{escaped}'")
            except:
                pass  # Column may not exist
        
        results["profile_metrics"] = "SUCCESS"
    except Exception as e:
        results["profile_metrics"] = f"ERROR: {str(e)[:50]}"
    
    # Document drift_metrics (similar)
    # ...
    
    return results
```

## Query Examples

### Profile Metrics Query (Overall KPIs)

```sql
-- Get latest custom metrics (overall, no slicing)
SELECT 
    window.start AS window_start,
    window.end AS window_end,
    total_daily_cost,
    tag_coverage_pct,
    serverless_ratio
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'       -- REQUIRED: Table-level aggregation (custom metrics)
  AND log_type = 'INPUT'           -- REQUIRED: Input data statistics
  AND slice_key IS NULL            -- No slicing (overall metrics)
ORDER BY window.start DESC
LIMIT 10;
```

### Drift Metrics Query

```sql
-- Get period-over-period changes
SELECT 
    window.start AS window_start,
    window.end AS window_end,
    cost_drift_pct,
    dbu_drift_pct,
    tag_coverage_drift
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'   -- REQUIRED: Consecutive period comparison
  AND column_name = ':table'       -- REQUIRED: Table-level drift
  AND slice_key IS NULL            -- Overall drift (no slicing)
  AND ABS(cost_drift_pct) > 10     -- Significant changes only
ORDER BY window.start DESC;
```

### Sliced Metrics Query (Dimensional Analysis)

```sql
-- Get cost breakdown by workspace
SELECT 
    window.start AS window_start,
    slice_value AS workspace_id,
    total_daily_cost,
    tag_coverage_pct
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'       -- REQUIRED: Table-level aggregation
  AND log_type = 'INPUT'           -- REQUIRED: Input data statistics
  AND slice_key = 'workspace_id'   -- Slice by workspace dimension
  AND window.start >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY total_daily_cost DESC;
```

### Sliced by Multiple Dimensions

```sql
-- Get serverless vs classic cost comparison
SELECT 
    CASE WHEN slice_value = 'true' THEN 'Serverless' ELSE 'Classic' END AS compute_type,
    SUM(total_daily_cost) AS total_cost
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'product_features_is_serverless'
GROUP BY slice_value;
```

### Query with Safe NULL Handling

```sql
-- Use COALESCE for robust no-slice filtering
SELECT 
    window.start AS window_start,
    total_daily_cost,
    tag_coverage_pct
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND COALESCE(slice_key, 'No Slice') = 'No Slice'
  AND COALESCE(slice_value, 'No Slice') = 'No Slice'
ORDER BY window.start DESC;
```

### Job Success Rate by Job Name

```sql
-- Identify jobs with lowest success rate
SELECT 
    slice_value AS job_name,
    AVG(success_rate) AS avg_success_rate,
    SUM(failure_count) AS total_failures,
    SUM(total_runs) AS total_runs
FROM catalog.gold_monitoring.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'job_name'
  AND window.start >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY slice_value
HAVING AVG(success_rate) < 95
ORDER BY avg_success_rate ASC;
```

### Security Events by User

```sql
-- Top users by security event count
SELECT 
    slice_value AS user_email,
    SUM(total_events) AS event_count,
    SUM(failed_auth_count) AS failed_logins
FROM catalog.gold_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'user_identity_email'
  AND window.start >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
GROUP BY slice_value
ORDER BY event_count DESC
LIMIT 20;
```

---

**Version:** 1.0  
**Last Updated:** January 2026

