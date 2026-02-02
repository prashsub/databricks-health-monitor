# Lakehouse Monitoring Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-MO-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Data Engineering Team |
| **Status** | Approved |

---

## Executive Summary

Lakehouse Monitoring provides automated data quality monitoring with drift detection, profiling, and custom metrics. This document defines patterns for implementing monitors, querying metric tables, and integrating with Genie Spaces.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| MO-01 | Use `input_columns=[":table"]` for table-level KPIs | 🔴 Critical |
| MO-05 | Document monitor output tables for Genie | 🟡 Required |
| MO-06 | All related metrics must use same `input_columns` | 🔴 Critical |
| MO-07 | Monitor creation is async - implement wait pattern | 🟡 Required |

---

## Monitor Architecture

### Output Table Structure

When you create a monitor, Databricks creates two output tables:

```
catalog.schema.{table_name}_profile_metrics   # Profiling and custom metrics
catalog.schema.{table_name}_drift_metrics     # Drift detection results
```

### Metric Types

| Type | Purpose | `input_columns` Storage |
|------|---------|------------------------|
| **AGGREGATE** | SUM, AVG, COUNT aggregations | Stored under specified `input_columns` value |
| **DERIVED** | Calculations from other metrics | Same `input_columns` as referenced metrics |
| **DRIFT** | Distribution change detection | Same `input_columns` as source metric |

---

## Rule MO-01: input_columns for Table-Level KPIs

### The Problem

Custom metrics are stored in the `column_name` column based on their `input_columns` value. If `input_columns` differs between related metrics, DERIVED metrics return NULL.

### The Pattern

**ALL table-level business KPIs must use `input_columns=[":table"]`**

```python
from databricks.sdk.service.catalog import MonitorMetric, MonitorMetricType

# Table-level KPIs - ALL use :table
custom_metrics = [
    # AGGREGATE metrics
    MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
        name="total_cost",
        input_columns=[":table"],  # ✅ Table-level
        definition="SUM(list_cost)",
        output_data_type="DECIMAL(18,2)"
    ),
    MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
        name="total_dbus",
        input_columns=[":table"],  # ✅ Same as total_cost
        definition="SUM(dbus_consumed)",
        output_data_type="DECIMAL(18,6)"
    ),
    
    # DERIVED metric - references AGGREGATE metrics
    MonitorMetric(
        type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
        name="cost_per_dbu",
        input_columns=[":table"],  # ✅ MUST match AGGREGATE metrics!
        definition="total_cost / NULLIF(total_dbus, 0)",
        output_data_type="DECIMAL(18,4)"
    )
]
```

### Why This Matters

DERIVED metrics can ONLY reference metrics stored in the SAME `column_name` row:

```
column_name = ":table"
├── total_cost (AGGREGATE)       ← Accessible by DERIVED
├── total_dbus (AGGREGATE)       ← Accessible by DERIVED
└── cost_per_dbu (DERIVED)       ← Can reference above metrics

column_name = "workspace_id"
├── workspace_count (AGGREGATE)  ← NOT accessible from ":table" row!
```

---

## Rule MO-06: Consistent input_columns

### The Problem

Mixing `input_columns` values causes NULL values in DERIVED metrics.

```python
# ❌ WRONG: Different input_columns
MonitorMetric(
    name="total_cost",
    input_columns=[":table"],      # Stored in column_name = ":table"
    definition="SUM(list_cost)"
),
MonitorMetric(
    name="workspace_count",
    input_columns=["workspace_id"],  # Stored in column_name = "workspace_id"
    definition="COUNT(DISTINCT workspace_id)"
),
MonitorMetric(
    name="cost_per_workspace",
    input_columns=[":table"],      # Can't find workspace_count!
    definition="total_cost / workspace_count"  # Returns NULL!
)
```

### The Solution

**Group ALL related metrics under the same `input_columns` value:**

```python
# ✅ CORRECT: All table-level KPIs use :table
MonitorMetric(
    name="total_cost",
    input_columns=[":table"],
    definition="SUM(list_cost)"
),
MonitorMetric(
    name="workspace_count",
    input_columns=[":table"],      # ✅ Changed to :table
    definition="COUNT(DISTINCT workspace_id)"
),
MonitorMetric(
    name="cost_per_workspace",
    input_columns=[":table"],
    definition="total_cost / NULLIF(workspace_count, 0)"  # ✅ Works!
)
```

---

## Rule MO-07: Async Monitor Wait Pattern

### The Problem

`create_monitor()` returns immediately but tables take ~15 minutes to create.

### The Pattern

```python
from databricks.sdk import WorkspaceClient
import time

def wait_for_monitor_tables(
    w: WorkspaceClient,
    table_name: str,
    timeout_minutes: int = 30
) -> bool:
    """
    Wait for monitor output tables to be created.
    
    Monitor creation is async - tables don't exist immediately.
    """
    profile_table = f"{table_name}_profile_metrics"
    drift_table = f"{table_name}_drift_metrics"
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    while time.time() - start_time < timeout_seconds:
        try:
            # Check if tables exist
            spark.table(profile_table).limit(1).collect()
            spark.table(drift_table).limit(1).collect()
            print(f"✅ Monitor tables ready: {profile_table}, {drift_table}")
            return True
        except Exception:
            elapsed = int(time.time() - start_time)
            print(f"⏳ Waiting for monitor tables... ({elapsed}s)")
            time.sleep(30)
    
    print(f"❌ Timeout waiting for monitor tables")
    return False


# Usage
w = WorkspaceClient()

# Create monitor
w.quality_monitors.create(
    table_name=f"{catalog}.{schema}.fact_usage",
    assets_dir=f"/Shared/monitoring/{schema}",
    output_schema_name=f"{catalog}.{schema}",
    custom_metrics=custom_metrics,
    schedule=MonitorCronSchedule(
        quartz_cron_expression="0 0 2 * * ?",
        timezone_id="UTC"
    )
)

# Wait for tables
if wait_for_monitor_tables(w, f"{catalog}.{schema}.fact_usage"):
    # Safe to query or document tables
    document_monitor_tables(...)
```

---

## Querying Monitor Output Tables

### AGGREGATE Metric Query Pattern

AGGREGATE metrics require PIVOT to convert rows to columns:

```sql
-- Query AGGREGATE metrics from profile_metrics table
SELECT 
    window.start as period_start,
    window.end as period_end,
    MAX(CASE WHEN column_name = ':table' THEN total_cost END) as total_cost,
    MAX(CASE WHEN column_name = ':table' THEN total_dbus END) as total_dbus,
    MAX(CASE WHEN column_name = ':table' THEN workspace_count END) as workspace_count
FROM catalog.schema.fact_usage_profile_metrics
WHERE column_name = ':table'
GROUP BY window.start, window.end
ORDER BY window.start DESC;
```

### DERIVED Metric Query Pattern

DERIVED metrics are in the same row, so direct SELECT works:

```sql
-- Query DERIVED metrics
SELECT 
    window.start as period_start,
    window.end as period_end,
    cost_per_dbu,
    cost_per_workspace,
    dbu_efficiency
FROM catalog.schema.fact_usage_profile_metrics
WHERE column_name = ':table'
ORDER BY window.start DESC;
```

### DRIFT Metric Query Pattern

```sql
-- Query drift detection results
SELECT 
    window.start as period_start,
    window.end as period_end,
    drift_type,
    column_name,
    chi_squared_statistic,
    chi_squared_pvalue,
    ks_statistic,
    wasserstein_distance
FROM catalog.schema.fact_usage_drift_metrics
WHERE chi_squared_pvalue < 0.05  -- Significant drift
ORDER BY window.start DESC;
```

---

## Rule MO-05: Document Monitor Tables for Genie

### The Problem

By default, monitor output tables (`_profile_metrics`, `_drift_metrics`) have no descriptions. Genie cannot interpret custom metric columns.

### The Solution: Post-Deployment Documentation

```python
def document_monitor_tables(
    spark,
    catalog: str,
    schema: str,
    source_table: str,
    metric_descriptions: dict
):
    """
    Add table and column comments to monitor output tables.
    
    Call after monitor tables are created (~15 min after create_monitor).
    """
    profile_table = f"{catalog}.{schema}.{source_table}_profile_metrics"
    drift_table = f"{catalog}.{schema}.{source_table}_drift_metrics"
    
    # Document profile metrics table
    table_comment = f"""
    Profile and custom metrics for {source_table}.
    Business: Quality and business KPIs tracked over time.
    Technical: Auto-refreshed by Lakehouse Monitoring. Query with column_name filter.
    """.replace("'", "''")
    
    spark.sql(f"ALTER TABLE {profile_table} SET TBLPROPERTIES ('comment' = '{table_comment}')")
    
    # Document custom metric columns
    for metric_name, description in metric_descriptions.items():
        desc = description.replace("'", "''")
        try:
            spark.sql(f"ALTER TABLE {profile_table} ALTER COLUMN {metric_name} COMMENT '{desc}'")
            print(f"✅ Documented {metric_name}")
        except Exception as e:
            print(f"⚠ Could not document {metric_name}: {e}")


# Usage
metric_descriptions = {
    "total_cost": "Total list cost in USD. Business: Primary spend metric. Technical: SUM(list_cost).",
    "total_dbus": "Total DBUs consumed. Business: Compute usage metric. Technical: SUM(dbus_consumed).",
    "cost_per_dbu": "Cost efficiency ratio. Business: Higher = less efficient. Technical: total_cost / total_dbus."
}

document_monitor_tables(spark, catalog, schema, "fact_usage", metric_descriptions)
```

---

## Complete Monitor Setup Pattern

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import (
    MonitorMetric, 
    MonitorMetricType,
    MonitorCronSchedule,
    MonitorTimeSeries
)


def setup_usage_monitor(
    spark,
    w: WorkspaceClient,
    catalog: str,
    schema: str
):
    """
    Complete monitor setup with custom metrics and documentation.
    """
    table_name = f"{catalog}.{schema}.fact_usage"
    
    # Step 1: Define custom metrics
    custom_metrics = [
        # AGGREGATE metrics (all :table for table-level KPIs)
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_cost",
            input_columns=[":table"],
            definition="SUM(list_cost)",
            output_data_type="DECIMAL(18,2)"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_dbus",
            input_columns=[":table"],
            definition="SUM(dbus_consumed)",
            output_data_type="DECIMAL(18,6)"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="workspace_count",
            input_columns=[":table"],
            definition="COUNT(DISTINCT workspace_id)",
            output_data_type="BIGINT"
        ),
        
        # DERIVED metrics (same :table input_columns)
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
            name="cost_per_dbu",
            input_columns=[":table"],
            definition="total_cost / NULLIF(total_dbus, 0)",
            output_data_type="DECIMAL(18,4)"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
            name="cost_per_workspace",
            input_columns=[":table"],
            definition="total_cost / NULLIF(workspace_count, 0)",
            output_data_type="DECIMAL(18,2)"
        )
    ]
    
    # Step 2: Delete existing monitor (for clean setup)
    try:
        w.quality_monitors.delete(table_name=table_name)
        print(f"Deleted existing monitor for {table_name}")
        time.sleep(10)
    except Exception:
        pass
    
    # Step 3: Create monitor
    w.quality_monitors.create(
        table_name=table_name,
        assets_dir=f"/Shared/monitoring/{schema}",
        output_schema_name=f"{catalog}.{schema}",
        custom_metrics=custom_metrics,
        time_series=MonitorTimeSeries(
            timestamp_col="usage_date",
            granularities=["1 day"]
        ),
        schedule=MonitorCronSchedule(
            quartz_cron_expression="0 0 2 * * ?",  # Daily at 2 AM
            timezone_id="UTC"
        )
    )
    print(f"✅ Created monitor for {table_name}")
    
    # Step 4: Wait for tables
    if not wait_for_monitor_tables(w, table_name):
        raise RuntimeError("Monitor tables not created in time")
    
    # Step 5: Document for Genie
    metric_descriptions = {
        "total_cost": "Total list cost in USD. Business: Primary spend metric.",
        "total_dbus": "Total DBUs consumed. Business: Compute usage metric.",
        "workspace_count": "Distinct workspaces. Business: Platform adoption metric.",
        "cost_per_dbu": "Cost efficiency. Business: Higher = less efficient.",
        "cost_per_workspace": "Average cost per workspace. Business: Cost allocation."
    }
    document_monitor_tables(spark, catalog, schema, "fact_usage", metric_descriptions)
    
    print("✅ Monitor setup complete with documentation")
```

---

## Validation Checklist

### Pre-Setup
- [ ] Source table exists in Unity Catalog
- [ ] Timestamp column identified for time series
- [ ] Custom metrics defined with correct types
- [ ] All related metrics use same `input_columns`

### Post-Setup
- [ ] Wait pattern implemented (~15 min)
- [ ] `_profile_metrics` table exists
- [ ] `_drift_metrics` table exists
- [ ] Table and column COMMENTs added
- [ ] Query patterns tested

### Genie Integration
- [ ] Tables documented with business context
- [ ] Custom metric columns have COMMENTs
- [ ] Query examples available

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| DERIVED metric returns NULL | Different `input_columns` | Use same value for all related metrics |
| Table not found | Async creation | Implement wait pattern |
| Monitor already exists | Duplicate creation | Delete first, then create |
| Genie can't interpret metrics | Missing documentation | Add COMMENTs to tables/columns |

---

## Related Documents

- [Dashboard Patterns](../dashboards/40-aibi-dashboard-patterns.md)
- [Alerting Patterns](42-alerting-patterns.md)
- [Gold Layer Patterns](../data-pipelines/12-gold-layer-patterns.md)

---

## References

- [Lakehouse Monitoring API](https://docs.databricks.com/lakehouse-monitoring/)
- [Custom Metrics Reference](https://docs.databricks.com/lakehouse-monitoring/custom-metrics)
