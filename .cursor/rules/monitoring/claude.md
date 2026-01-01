# Monitoring Rules for Claude Code

This file combines all monitoring-related cursor rules for use by Claude Code.

---

## Table of Contents
1. [Lakehouse Monitoring](#lakehouse-monitoring)
2. [AI/BI Dashboards](#aibi-dashboards)
3. [SQL Alerting Patterns](#sql-alerting-patterns)

---

## Lakehouse Monitoring

### Core Principles

1. **Graceful Degradation**: Always handle existing monitors gracefully
2. **Business-First Metrics**: Design metrics for business KPIs
3. **Table-Level KPIs**: Use `input_columns=[":table"]` for cross-referencing metrics

### Monitor Creation Pattern

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import (
    MonitorSnapshot, MonitorTimeSeries, MonitorCronSchedule
)
from databricks.sdk.errors import ResourceAlreadyExists, ResourceDoesNotExist

def create_table_monitor(
    workspace_client: WorkspaceClient, 
    catalog: str, 
    schema: str,
    table: str,
    monitor_type: str = "time_series"
):
    """Create Lakehouse monitor with comprehensive error handling."""
    table_name = f"{catalog}.{schema}.{table}"
    
    print(f"Creating {monitor_type} monitor for {table_name}...")
    
    try:
        # Configure monitor based on type
        if monitor_type == "snapshot":
            config = {"snapshot": MonitorSnapshot()}
        elif monitor_type == "time_series":
            config = {
                "time_series": MonitorTimeSeries(
                    timestamp_col="transaction_date",
                    granularities=["1 day"]
                )
            }
        
        monitor = workspace_client.quality_monitors.create(
            table_name=table_name,
            assets_dir=f"/Workspace/Shared/lakehouse_monitoring/{catalog}/{schema}",
            output_schema_name=f"{catalog}.{schema}_monitoring",
            **config,
            custom_metrics=[
                # Add custom metrics here
            ],
            slicing_exprs=["store_number", "upc_code"],
            schedule=MonitorCronSchedule(
                quartz_cron_expression="0 0 2 * * ?",
                timezone_id="America/New_York"
            )
        )
        
        print(f"✓ Monitor created for {table_name}")
        return monitor
        
    except ResourceAlreadyExists:
        print(f"⚠️ Monitor for {table} already exists - skipping")
        return None
        
    except ResourceDoesNotExist:
        print(f"⚠️ Table {table} does not exist - skipping")
        return None
        
    except Exception as e:
        print(f"❌ Failed to create monitor for {table}: {str(e)}")
        raise
```

### Custom Metrics Design

#### AGGREGATE Metrics (Table-Level)

```python
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
    name="total_revenue",
    input_columns=[":table"],  # ✅ Table-level
    definition="SUM(net_revenue)",
    output_data_type="DOUBLE"
)
```

#### DERIVED Metrics

```python
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
    name="avg_transaction_value",
    input_columns=[":table"],  # ✅ Same as related AGGREGATE
    definition="total_revenue / NULLIF(transaction_count, 0)",
    output_data_type="DOUBLE"
)
```

#### DRIFT Metrics

```python
MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_DRIFT,
    name="revenue_pct_change",
    input_columns=[":table"],
    definition="(current.total_revenue - baseline.total_revenue) / NULLIF(baseline.total_revenue, 0) * 100",
    output_data_type="DOUBLE"
)
```

### Querying Metrics

#### AGGREGATE Metrics Query

```sql
SELECT 
    window_start,
    window_end,
    -- Metrics stored with column_name = input_columns value
    MAX(CASE WHEN column_name = ':table' AND metric_name = 'total_revenue' 
        THEN metric_value END) as total_revenue
FROM {catalog}.{schema}_monitoring.{table}_profile_metrics
WHERE granularity = 'day'
GROUP BY window_start, window_end
ORDER BY window_start DESC
```

#### DRIFT Metrics Query

```sql
SELECT
    window_start,
    window_end,
    MAX(CASE WHEN column_name = ':table' AND metric_name = 'revenue_pct_change'
        THEN drift_value END) as revenue_pct_change
FROM {catalog}.{schema}_monitoring.{table}_drift_metrics
WHERE granularity = 'day'
GROUP BY window_start, window_end
```

### Monitor Output Table Documentation

**Add descriptions for Genie compatibility:**

```python
def document_monitor_output_tables(spark, catalog, monitoring_schema, table_name):
    """Add table and column comments for Genie."""
    
    # Profile metrics table
    profile_table = f"{catalog}.{monitoring_schema}.{table_name}_profile_metrics"
    
    spark.sql(f"""
        ALTER TABLE {profile_table}
        SET TBLPROPERTIES (
            'comment' = 'Lakehouse Monitoring profile metrics for {table_name}'
        )
    """)
    
    # Add column comments
    METRIC_DESCRIPTIONS = {
        "total_revenue": "Total net revenue. Business: Primary financial KPI.",
        "transaction_count": "Number of transactions. Business: Volume indicator.",
        "avg_transaction_value": "Average transaction value. Business: Basket size KPI."
    }
    
    for metric, desc in METRIC_DESCRIPTIONS.items():
        try:
            spark.sql(f"""
                ALTER TABLE {profile_table}
                ALTER COLUMN {metric} COMMENT '{desc}'
            """)
        except:
            pass  # Column may not exist
```

### Validation Checklist

- [ ] Monitor type is ONE of: snapshot, time_series, inference_log
- [ ] `input_columns=[":table"]` for table-level KPIs
- [ ] Related metrics use same `input_columns`
- [ ] Custom metrics have descriptive names
- [ ] Output schema ends with `_monitoring`
- [ ] Error handling for ResourceAlreadyExists

---

## AI/BI Dashboards

### Critical: 6-Column Grid Layout

**ALWAYS use 6-column grid, NOT 12-column:**

```json
{
  "pages": [{
    "layout": [{
      "widget": { "name": "widget1" },
      "position": { "x": 0, "y": 0, "width": 3, "height": 2 }
    }, {
      "widget": { "name": "widget2" },
      "position": { "x": 3, "y": 0, "width": 3, "height": 2 }
    }]
  }]
}
```

| Width | Columns (6-grid) |
|-------|------------------|
| 1 | ~17% |
| 2 | ~33% |
| 3 | 50% (half) |
| 4 | ~67% |
| 6 | 100% (full) |

### Dataset with Parameters

```json
{
  "datasets": [{
    "name": "job_runs",
    "displayName": "Job Runs",
    "query": "SELECT * FROM system.lakeflow.job_task_run_timeline WHERE period_start >= :start_date AND period_start <= :end_date",
    "parameters": [
      {
        "name": "start_date",
        "type": "DATE",
        "bind": true
      },
      {
        "name": "end_date", 
        "type": "DATE",
        "bind": true
      }
    ]
  }]
}
```

### disaggregated Mode

**Charts and tables MUST have `disaggregated: true`:**

```json
{
  "widget": {
    "name": "revenue_chart",
    "spec": {
      "version": 3,
      "widgetType": "area",
      "encodings": {
        "x": { "fieldName": "date", "scale": { "type": "temporal" }, "displayName": "Date" },
        "y": { "fieldName": "revenue", "scale": { "type": "quantitative" }, "displayName": "Revenue" }
      },
      "frame": {
        "showTitle": true,
        "title": "Revenue Trend"
      }
    },
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "revenue_data",
        "disaggregated": true,
        "fields": [
          { "name": "date", "expression": "`date`" },
          { "name": "revenue", "expression": "`revenue`" }
        ]
      }
    }]
  }
}
```

### Global Filter Parameters

**Every dataset must bind filter parameters:**

```json
{
  "datasets": [
    {
      "name": "dataset1",
      "query": "SELECT * FROM table1 WHERE date >= :start_date",
      "parameters": [{ "name": "start_date", "type": "DATE", "bind": true }]
    },
    {
      "name": "dataset2",
      "query": "SELECT * FROM table2 WHERE date >= :start_date",
      "parameters": [{ "name": "start_date", "type": "DATE", "bind": true }]
    }
  ]
}
```

### System Table Joins

```sql
WITH latest_jobs AS (
  SELECT workspace_id, job_id, name,
    ROW_NUMBER() OVER(PARTITION BY workspace_id, job_id 
                      ORDER BY change_time DESC) as rn
  FROM system.lakeflow.jobs
  WHERE delete_time IS NULL
  QUALIFY rn = 1
)
SELECT 
  jtr.*,
  COALESCE(lj.name, 'Job ' || CAST(jtr.job_id AS STRING)) AS job_name
FROM system.lakeflow.job_task_run_timeline jtr
LEFT JOIN latest_jobs lj 
  ON jtr.workspace_id = lj.workspace_id 
  AND jtr.job_id = lj.job_id
```

### SDK Deployment

```python
from databricks.sdk import WorkspaceClient
import json

def deploy_dashboard(ws: WorkspaceClient, dashboard_json: dict, name: str):
    """Deploy or update a Lakeview dashboard."""
    
    # Check if exists
    existing = None
    try:
        dashboards = ws.lakeview.list()
        for d in dashboards:
            if d.display_name == name:
                existing = d
                break
    except:
        pass
    
    serialized = json.dumps(dashboard_json)
    
    if existing:
        # Update
        ws.lakeview.update(
            dashboard_id=existing.dashboard_id,
            display_name=name,
            serialized_dashboard=serialized
        )
        print(f"✓ Updated dashboard: {name}")
    else:
        # Create
        ws.lakeview.create(
            display_name=name,
            serialized_dashboard=serialized
        )
        print(f"✓ Created dashboard: {name}")
```

### Validation Checklist

- [ ] Grid uses 6 columns (not 12)
- [ ] All charts/tables have `disaggregated: true`
- [ ] Date parameters use `DATE` type
- [ ] Every dataset binds filter parameters
- [ ] System table queries use window functions for latest records
- [ ] No combo charts with y2 encoding (not supported)

---

## SQL Alerting Patterns

### V2 API Endpoint

**⚠️ CRITICAL: Use `/api/2.0/alerts` (NOT `/api/2.0/sql/alerts`)**

### Fully Qualified Table Names

```sql
-- ❌ WRONG: Parameterized query (NOT SUPPORTED)
SELECT * FROM ${catalog}.${schema}.fact_booking_daily

-- ✅ CORRECT: Fully qualified names embedded
SELECT * FROM wanderbricks_dev.gold.fact_booking_daily
```

### Alert Configuration Table

```sql
CREATE TABLE alert_rules (
    alert_id STRING NOT NULL COMMENT 'Unique alert identifier: DOMAIN-NUMBER-SEVERITY',
    alert_name STRING NOT NULL COMMENT 'Human-readable alert name',
    domain STRING NOT NULL COMMENT 'Agent domain: cost, security, performance, reliability, quality',
    severity STRING NOT NULL COMMENT 'Alert severity: critical, high, medium, low, info',
    query_text STRING NOT NULL COMMENT 'SQL query returning numeric value',
    comparison_operator STRING NOT NULL COMMENT 'Operator: GREATER_THAN, LESS_THAN, EQUAL',
    threshold DOUBLE NOT NULL COMMENT 'Threshold value for comparison',
    schedule_cron STRING NOT NULL COMMENT 'Cron expression for schedule',
    notification_channels STRING COMMENT 'Comma-separated notification destinations',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether alert is active',
    CONSTRAINT pk_alert_rules PRIMARY KEY (alert_id) NOT ENFORCED
)
```

### Alert ID Convention

```
<DOMAIN>-<NUMBER>-<SEVERITY>

Examples:
- COST-001-HIGH
- SECURITY-003-CRITICAL
- QUALITY-007-MEDIUM
```

### SDK Version Requirement

```python
# Databricks notebook source
# MAGIC %pip install --upgrade databricks-sdk>=0.40.0 --quiet

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import AlertV2
```

### Create Alert

```python
def create_alert(ws: WorkspaceClient, config: dict) -> str:
    """Create SQL alert from configuration."""
    
    alert = AlertV2(
        display_name=config["alert_name"],
        query_text=config["query_text"],
        warehouse_id=config["warehouse_id"],
        schedule=AlertSchedule(
            cron=CronSchedule(
                expression=config["schedule_cron"],
                timezone_id="UTC"
            )
        ),
        condition=AlertCondition(
            op=ComparisonOperator[config["comparison_operator"]],
            threshold=AlertConditionThreshold(value=config["threshold"]),
            empty_result_state=AlertState.OK
        ),
        custom_summary=f"Alert: {config['alert_name']}",
        custom_description=f"Domain: {config['domain']}, Severity: {config['severity']}"
    )
    
    try:
        result = ws.alerts_v2.create_alert(alert=alert)
        return result.id
    except Exception as e:
        if "RESOURCE_ALREADY_EXISTS" in str(e):
            # Find and update existing
            existing = find_alert_by_name(ws, config["alert_name"])
            if existing:
                return update_alert(ws, existing.id, alert)
        raise
```

### Update Alert with update_mask

**⚠️ update_mask is REQUIRED for PATCH:**

```python
def update_alert(ws: WorkspaceClient, alert_id: str, alert: AlertV2) -> str:
    """Update existing SQL alert."""
    
    result = ws.alerts_v2.update_alert(
        id=alert_id,
        alert=alert,
        update_mask="display_name,query_text,warehouse_id,schedule,condition,custom_summary,custom_description"
    )
    return result.id
```

### Query Patterns

#### Threshold Alert

```sql
SELECT COUNT(*) as failed_jobs
FROM system.lakeflow.job_task_run_timeline
WHERE result_state = 'FAILED'
  AND period_start >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
```

#### Percentage Change Alert

```sql
WITH current_period AS (
    SELECT SUM(cost) as current_cost
    FROM fact_usage
    WHERE usage_date >= DATEADD(day, -1, CURRENT_DATE())
),
previous_period AS (
    SELECT SUM(cost) as previous_cost
    FROM fact_usage
    WHERE usage_date >= DATEADD(day, -2, CURRENT_DATE())
      AND usage_date < DATEADD(day, -1, CURRENT_DATE())
)
SELECT 
    (c.current_cost - p.previous_cost) / NULLIF(p.previous_cost, 0) * 100 as pct_change
FROM current_period c
CROSS JOIN previous_period p
```

### Unity Catalog Limitations

**These are NOT supported in UC:**
- CHECK constraints
- DEFAULT values
- PARTITIONED BY (conflicts with CLUSTER BY AUTO)

### Validation Checklist

- [ ] API endpoint is `/api/2.0/alerts` (V2)
- [ ] SDK version >= 0.40.0
- [ ] `%restart_python` after pip install
- [ ] Queries use fully qualified table names
- [ ] update_mask included in PATCH requests
- [ ] Alert IDs follow DOMAIN-NUMBER-SEVERITY pattern
- [ ] Handle RESOURCE_ALREADY_EXISTS error

