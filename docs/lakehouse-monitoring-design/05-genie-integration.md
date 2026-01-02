# 05 - Genie Integration

## Overview

Lakehouse Monitoring creates output tables (`_profile_metrics`, `_drift_metrics`) but **does not add descriptions by default**. Without documentation, Genie and other LLMs cannot interpret the custom metric columns for natural language queries.

This document explains how to add Genie-friendly documentation to monitoring output tables.

## The Problem

### Default State (No Documentation)

```sql
DESCRIBE TABLE catalog.gold_monitoring.fact_usage_profile_metrics;
```

| Column | Type | Comment |
|--------|------|---------|
| `window_start` | TIMESTAMP | |
| `window_end` | TIMESTAMP | |
| `column_name` | STRING | |
| `total_daily_cost` | DOUBLE | |
| `tag_coverage_pct` | DOUBLE | |
| ... | ... | (empty) |

**Result**: Genie sees columns like `tag_coverage_pct` but has no idea what it means.

### With Documentation

```sql
DESCRIBE TABLE catalog.gold_monitoring.fact_usage_profile_metrics;
```

| Column | Type | Comment |
|--------|------|---------|
| `window_start` | TIMESTAMP | |
| `column_name` | STRING | |
| `total_daily_cost` | DOUBLE | Total daily cost in list prices. Business: Primary FinOps metric... |
| `tag_coverage_pct` | DOUBLE | Percentage of cost covered by tags. Business: FinOps maturity KPI... |

**Result**: Genie understands the business context and can answer questions like "What's the tag coverage trend?"

## Documentation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         monitor_utils.py                                     │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ METRIC_DESCRIPTIONS = {                                              │   │
│   │   "total_daily_cost": "Total daily cost... Business: ... Tech: ...", │   │
│   │   "tag_coverage_pct": "Percentage of... Business: ... Tech: ...",    │   │
│   │   ... (100+ metrics)                                                 │   │
│   │ }                                                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ MONITOR_TABLE_DESCRIPTIONS = {                                       │   │
│   │   "fact_usage": {                                                    │   │
│   │     "profile_table": "Lakehouse Monitoring profile metrics...",      │   │
│   │     "drift_table": "Lakehouse Monitoring drift metrics..."           │   │
│   │   },                                                                 │   │
│   │   ... (8 tables)                                                     │   │
│   │ }                                                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ def document_monitor_output_tables(spark, catalog, gold_schema,      │   │
│   │                                    table_name, custom_metrics):      │   │
│   │     # ALTER TABLE ... SET TBLPROPERTIES ('comment' = '...')          │   │
│   │     # ALTER TABLE ... ALTER COLUMN ... COMMENT '...'                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         document_monitors.py                                 │
│                         (Databricks Notebook)                                │
│                                                                              │
│   - Iterates through all 8 monitored tables                                 │
│   - Calls document_monitor_output_tables() for each                         │
│   - Handles tables not yet ready (async creation)                           │
│   - Reports documentation summary                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Description Format

### Dual-Purpose Format

All descriptions follow a consistent format that serves both business users and LLMs:

```
"[Natural description]. Business: [business context]. Technical: [calculation details]."
```

### Examples

```python
METRIC_DESCRIPTIONS = {
    "total_daily_cost": 
        "Total daily cost in list prices. Business: Primary FinOps metric for "
        "budgeting and forecasting. Technical: SUM(list_cost), aggregated per time window.",
    
    "tag_coverage_pct": 
        "Percentage of cost covered by tags. Business: FinOps maturity KPI "
        "(target: >90%). Technical: tagged_cost / total_cost * 100.",
    
    "success_rate": 
        "Job success rate percentage. Business: Primary reliability KPI "
        "(target: >95%). Technical: success_count / total_runs * 100.",
}
```

## Implementation

### METRIC_DESCRIPTIONS Registry

The registry in `monitor_utils.py` contains descriptions for all 100+ custom metrics:

```python
METRIC_DESCRIPTIONS = {
    # ==========================================
    # COST MONITOR METRICS (fact_usage)
    # ==========================================
    "total_daily_cost": "Total daily cost in list prices. Business: Primary FinOps metric...",
    "total_daily_dbu": "Total Databricks Units consumed. Business: Usage volume...",
    "tag_coverage_pct": "Percentage of cost covered by tags. Business: FinOps maturity KPI...",
    # ... more cost metrics
    
    # ==========================================
    # JOB MONITOR METRICS (fact_job_run_timeline)
    # ==========================================
    "total_runs": "Total number of job runs. Business: Workload volume...",
    "success_rate": "Job success rate percentage. Business: Primary reliability KPI...",
    # ... more job metrics
    
    # ==========================================
    # QUERY MONITOR METRICS (fact_query_history)
    # ==========================================
    "query_count": "Total number of queries executed. Business: Query workload volume...",
    # ... more query metrics
    
    # ... (100+ total)
}
```

### MONITOR_TABLE_DESCRIPTIONS Registry

Table-level descriptions explain how to use the output tables:

```python
MONITOR_TABLE_DESCRIPTIONS = {
    "fact_usage": {
        "profile_table": 
            "Lakehouse Monitoring profile metrics for fact_usage (billing/cost data). "
            "Contains daily cost aggregations, tag coverage metrics, SKU breakdowns, "
            "and derived business ratios. Use column_name=':table' for table-level KPIs. "
            "Business: Primary source for FinOps dashboards tracking spend, efficiency, "
            "and cost attribution.",
        "drift_table": 
            "Lakehouse Monitoring drift metrics for fact_usage (billing/cost data). "
            "Contains period-over-period comparisons for cost, DBU consumption, and "
            "tag coverage. Business: Alert source for budget variance and FinOps trend monitoring."
    },
    "fact_job_run_timeline": {
        "profile_table": 
            "Lakehouse Monitoring profile metrics for fact_job_run_timeline (job execution data). "
            "Contains success rates, duration percentiles, failure counts, and trigger breakdowns. "
            "Use column_name=':table' for table-level KPIs. Business: Primary source for reliability "
            "dashboards tracking job health and SLA compliance.",
        "drift_table": 
            "Lakehouse Monitoring drift metrics for fact_job_run_timeline (job execution data). "
            "Contains period-over-period comparisons for success rates, failure counts, and "
            "duration changes. Business: Alert source for reliability degradation detection."
    },
    # ... (8 total)
}
```

### Documentation Function

```python
def document_monitor_output_tables(
    spark,
    catalog: str,
    gold_schema: str,
    table_name: str,
    custom_metrics: List = None
) -> dict:
    """
    Add detailed table and column descriptions to Lakehouse Monitoring output tables.
    
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
    
    # Get table descriptions
    table_descs = MONITOR_TABLE_DESCRIPTIONS.get(table_name, {})
    profile_desc = table_descs.get("profile_table", f"Profile metrics for {table_name}")
    drift_desc = table_descs.get("drift_table", f"Drift metrics for {table_name}")
    
    # Document profile_metrics table
    try:
        # Add table comment
        escaped_desc = profile_desc.replace("'", "''")
        spark.sql(f"ALTER TABLE {profile_table} SET TBLPROPERTIES ('comment' = '{escaped_desc}')")
        
        # Add column comments
        columns_documented = 0
        for metric_name, description in METRIC_DESCRIPTIONS.items():
            try:
                escaped_col_desc = description.replace("'", "''")
                spark.sql(f"ALTER TABLE {profile_table} ALTER COLUMN {metric_name} COMMENT '{escaped_col_desc}'")
                columns_documented += 1
            except Exception:
                pass  # Column may not exist in this table
        
        results["profile_metrics"] = f"SUCCESS: {columns_documented} columns"
        
    except Exception as e:
        if "TABLE_OR_VIEW_NOT_FOUND" in str(e):
            results["profile_metrics"] = "NOT_READY"
        else:
            results["profile_metrics"] = f"ERROR: {str(e)[:50]}"
    
    # Document drift_metrics table (similar pattern)
    # ...
    
    return results
```

## Usage

### Run Documentation Job

After monitors are created and initialized (~15 minutes), run the documentation job:

```bash
# Deploy and run documentation job
databricks bundle run -t dev lakehouse_monitoring_document_job
```

### Sample Output

```
======================================================================
Documenting Lakehouse Monitoring Tables for Genie
======================================================================
  Documenting monitoring tables for fact_usage...
    ✓ Added table comment to fact_usage_profile_metrics
    ✓ Documented 35 custom metric columns
    ✓ Added table comment to fact_usage_drift_metrics
    ✓ Documented 3 drift metric columns
  Documenting monitoring tables for fact_job_run_timeline...
    ✓ Added table comment to fact_job_run_timeline_profile_metrics
    ✓ Documented 50 custom metric columns
    ...

======================================================================
Documentation Summary
======================================================================
  Tables documented: 8
  Tables not ready:  0
  Tables with errors: 0
```

### Verify Documentation

```sql
-- Check table comment
SELECT comment FROM system.information_schema.tables 
WHERE table_name = 'fact_usage_profile_metrics';

-- Check column comments
DESCRIBE TABLE catalog.gold_monitoring.fact_usage_profile_metrics;
```

## Timing Considerations

### Why Wait ~15 Minutes?

Lakehouse Monitoring creates output tables **asynchronously**:

1. `quality_monitors.create()` returns immediately
2. Monitor starts initial data scan (1-5 minutes)
3. Profile/drift tables are created (5-10 minutes)
4. Tables are ready for documentation

### Automation Pattern

```python
# In setup_all_monitors.py

# Create all monitors
create_all_monitors(...)

# Wait for tables to be created
if not skip_wait:
    wait_for_monitor_tables(minutes=15)
    
    # Document all monitoring tables for Genie
    print("Documenting monitoring tables for Genie...")
    document_all_monitor_tables(spark, catalog, gold_schema)
```

## Critical Query Patterns for Genie

Lakehouse Monitoring tables have special query patterns that Genie must understand to correctly answer user questions.

### Profile Metrics Query Pattern

The `_profile_metrics` tables contain custom business KPIs. To query them correctly:

```sql
-- Pattern: Get table-level business KPIs
SELECT 
  window.start AS window_start,
  window.end AS window_end,
  total_daily_cost,
  tag_coverage_pct,
  serverless_ratio
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'     -- CRITICAL: Filters to custom metrics (not per-column stats)
  AND log_type = 'INPUT'         -- CRITICAL: Input data statistics
  AND slice_key IS NULL          -- Optional: No slicing (overall metrics)
  AND window.start >= '2024-01-01'
ORDER BY window.start DESC
```

### Key Filter Columns Explained

| Column | Purpose | Values | Required |
|--------|---------|--------|----------|
| `column_name` | Filters to table-level vs column-level stats | `':table'` for custom metrics | ✅ |
| `log_type` | Input vs output statistics | `'INPUT'` for source data | ✅ |
| `slice_key` | Dimension for sliced analysis | `NULL`, `'workspace_id'`, etc. | Optional |
| `slice_value` | Value of the slicing dimension | Depends on slice_key | Optional |
| `window.start` | Time window start | TIMESTAMP | Optional |
| `window.end` | Time window end | TIMESTAMP | Optional |

### Slicing (Dimensional Analysis)

To get metrics broken down by a dimension:

```sql
-- Pattern: Get cost breakdown by workspace
SELECT 
  slice_value AS workspace_id,
  total_daily_cost,
  tag_coverage_pct
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'workspace_id'  -- Slice by workspace
ORDER BY total_daily_cost DESC
```

```sql
-- Pattern: Get cost breakdown by SKU
SELECT 
  slice_value AS sku_name,
  total_daily_cost
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'sku_name'  -- Slice by SKU
ORDER BY total_daily_cost DESC
```

### Available Slicing Dimensions by Monitor

| Monitor | Table | Slicing Dimensions | Use Cases |
|---------|-------|-------------------|-----------|
| **Cost** | `fact_usage_profile_metrics` | `workspace_id`, `sku_name`, `cloud`, `is_tagged`, `product_features_is_serverless` | Cost by workspace, SKU breakdown, serverless vs classic comparison, tagged vs untagged spend |
| **Job** | `fact_job_run_timeline_profile_metrics` | `workspace_id`, `result_state`, `trigger_type`, `job_name`, `termination_code` | Success by job name, failures by termination code, scheduled vs manual runs |
| **Query** | `fact_query_history_profile_metrics` | `workspace_id`, `compute_warehouse_id`, `execution_status`, `statement_type`, `executed_by` | Performance by warehouse, queries by user, status breakdown |
| **Cluster** | `fact_node_timeline_profile_metrics` | `workspace_id`, `cluster_id`, `node_type`, `cluster_name`, `driver` | Utilization by cluster, driver vs worker analysis |
| **Security** | `fact_audit_logs_profile_metrics` | `workspace_id`, `service_name`, `audit_level`, `action_name`, `user_identity_email` | Events by service, actions by user, audit level breakdown |
| **Quality** | `fact_table_quality_profile_metrics` | `catalog_name`, `schema_name`, `table_name`, `has_critical_violations` | Quality by schema/table, critical violations filtering |
| **Governance** | `fact_governance_metrics_profile_metrics` | `workspace_id`, `entity_type`, `created_by`, `source_catalog_name` | Coverage by entity type, ownership analysis |
| **Inference (Anomaly)** | `fact_cost_anomaly_predictions_profile_metrics` | `workspace_id`, `is_anomaly`, `anomaly_category` | Anomaly distribution, category breakdown |
| **Inference (Failure)** | `fact_job_failure_predictions_profile_metrics` | `workspace_id`, `predicted_result`, `risk_level` | Prediction accuracy, risk level distribution |

### Drift Metrics Query Pattern

The `_drift_metrics` tables contain period-over-period comparisons:

```sql
-- Pattern: Get cost drift over time
SELECT 
  window.start AS window_start,
  cost_drift_pct,
  dbu_drift_pct,
  tag_coverage_drift
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'  -- CRITICAL: Compare consecutive periods
  AND column_name = ':table'       -- CRITICAL: Table-level drift
  AND slice_key IS NULL            -- Optional: Overall drift
ORDER BY window.start
```

### Handling No Slicing (Overall Metrics)

When slice columns are NULL, use COALESCE pattern for safer filtering:

```sql
-- Pattern: Safe handling of no slicing
WHERE COALESCE(slice_key, 'No Slice') = 'No Slice'
  AND COALESCE(slice_value, 'No Slice') = 'No Slice'
```

### Complete Dashboard Query Example

This example from a monitoring dashboard shows all patterns together:

```sql
SELECT 
  window.start AS window_start,
  window.end AS window_end,
  total_gross_revenue,
  total_net_revenue,
  total_return_amount,
  avg_daily_revenue,
  total_units_sold,
  revenue_volatility
FROM catalog.gold_monitoring.fact_sales_daily_profile_metrics
WHERE window.start >= :time_window_start
  AND window.end <= :time_window_end
  AND log_type = 'INPUT'
  AND column_name = ':table'
  AND COALESCE(slice_key, 'No Slice') = :slice_key
  AND COALESCE(slice_value, 'No Slice') = :slice_value
ORDER BY window.start DESC
```

## Genie Query Examples

With documentation in place, users can ask natural language questions:

| Question | Genie Understanding | Query Pattern |
|----------|---------------------|---------------|
| "What's the total cost this month?" | Uses `total_daily_cost` | Filter `column_name=':table'`, SUM over window |
| "Show cost breakdown by workspace" | Uses `slice_key='workspace_id'` | Dimensional slicing |
| "What's the tag coverage trend?" | Uses `tag_coverage_pct` | Time series on profile_metrics |
| "Show job success rate by workspace" | Uses `success_rate` with slicing | slice_key='workspace_id' |
| "Which queries breached SLA yesterday?" | Uses `sla_breach_count` | Filter by window |
| "What's the cost drift this week?" | Uses `cost_drift_pct` | drift_type='CONSECUTIVE' |
| "Compare serverless vs classic cost" | Uses slice_key='product_features_is_serverless' | Dimensional comparison |
| "Which job failed most?" | Uses slice_key='job_name', result_state='FAILED' | Multi-dimensional |

### Detailed Query Examples

#### Example 1: Cost by SKU (Sliced Analysis)

```sql
-- Question: "Show me cost breakdown by SKU"
SELECT 
  slice_value AS sku_name,
  SUM(total_daily_cost) AS total_cost,
  AVG(tag_coverage_pct) AS avg_tag_coverage
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'sku_name'
  AND window.start >= DATEADD(day, -30, CURRENT_DATE())
GROUP BY slice_value
ORDER BY total_cost DESC
```

#### Example 2: Serverless vs Classic Comparison

```sql
-- Question: "Compare serverless vs classic compute cost"
SELECT 
  CASE 
    WHEN slice_value = 'true' THEN 'Serverless'
    ELSE 'Classic'
  END AS compute_type,
  SUM(total_daily_cost) AS total_cost,
  COUNT(*) AS days
FROM catalog.gold_monitoring.fact_usage_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'product_features_is_serverless'
GROUP BY slice_value
```

#### Example 3: Job Success by Name (Multi-Dimensional)

```sql
-- Question: "Which jobs have lowest success rate?"
SELECT 
  slice_value AS job_name,
  AVG(success_rate) AS avg_success_rate,
  SUM(failure_count) AS total_failures
FROM catalog.gold_monitoring.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'job_name'
  AND window.start >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY slice_value
HAVING AVG(success_rate) < 95
ORDER BY avg_success_rate ASC
```

#### Example 4: Security Events by User

```sql
-- Question: "Show security events by user in the last 24 hours"
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
LIMIT 20
```

#### Example 5: Cost Drift Detection

```sql
-- Question: "Show cost drift trend over last month"
SELECT 
  window.start AS period_start,
  cost_drift_pct,
  dbu_drift_pct,
  tag_coverage_drift
FROM catalog.gold_monitoring.fact_usage_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
  AND slice_key IS NULL
  AND window.start >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY window.start
```

## Validation Checklist

### Documentation Deployment

- [ ] Documentation job deployed via Asset Bundle
- [ ] Run ~15 min after monitor creation
- [ ] All 8 tables documented successfully
- [ ] Profile and drift tables both covered

### Description Quality

- [ ] All custom metrics have descriptions
- [ ] Descriptions follow dual-purpose format
- [ ] Business context is clear
- [ ] Technical calculation is documented

### Genie Testing

- [ ] Test 5+ natural language queries
- [ ] Verify Genie selects correct columns
- [ ] Confirm business context understood

## Troubleshooting

### Tables Not Ready

**Symptom**: Documentation returns `NOT_READY`

**Cause**: Monitor still initializing

**Solution**: Wait 15+ minutes and retry

```bash
# Wait and retry
sleep 900  # 15 minutes
databricks bundle run -t dev lakehouse_monitoring_document_job
```

### Column Not Found

**Symptom**: Some columns not documented

**Cause**: Metric names don't match column names

**Solution**: Verify metric names in `METRIC_DESCRIPTIONS` match actual column names in output tables

### Permission Denied

**Symptom**: `ALTER TABLE` fails

**Cause**: Insufficient permissions on monitoring schema

**Solution**: Grant ALTER on monitoring tables:

```sql
GRANT MODIFY ON TABLE catalog.gold_monitoring.* TO `user@company.com`;
```

## References

- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring)
- [Genie Spaces](https://docs.databricks.com/genie)
- [Cursor Rule: Lakehouse Monitoring](../../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

---

**Version:** 1.0  
**Last Updated:** January 2026

