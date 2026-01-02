# Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the rationalized dashboard framework, including creating the 5 domain dashboards and the unified health monitor dashboard.

---

## Phase 1: Preparation

### 1.1 Prerequisites Checklist

- [ ] Gold layer tables created and populated
- [ ] ML prediction tables exist (can be empty with placeholder schema)
- [ ] Lakehouse Monitors created with custom metrics
- [ ] Metric Views deployed
- [ ] SQL Warehouse available for dashboard queries
- [ ] Databricks Asset Bundle configured

### 1.2 Verify ML Prediction Tables

Run this validation query to check ML table availability:

```sql
-- Check ML tables exist
SELECT table_name, 
       CASE WHEN table_catalog IS NOT NULL THEN '✓' ELSE '✗' END AS exists
FROM (
    SELECT 'cost_anomaly_predictions' AS table_name UNION ALL
    SELECT 'budget_forecast_predictions' UNION ALL
    SELECT 'job_failure_predictions' UNION ALL
    SELECT 'security_threats' UNION ALL
    SELECT 'data_drift_alerts' UNION ALL
    -- ... add all ML tables
    SELECT 'pipeline_health_scores'
) AS expected
LEFT JOIN ${catalog}.information_schema.tables 
    ON table_name = tables.table_name 
    AND table_schema = '${gold_schema}'
```

### 1.3 Verify Lakehouse Monitor Tables

```sql
-- Check monitoring tables exist
SHOW TABLES IN ${catalog}.${gold_schema}_monitoring
```

Expected tables:
- `fact_usage_profile_metrics`
- `fact_usage_drift_metrics`
- `fact_job_run_timeline_profile_metrics`
- `fact_job_run_timeline_drift_metrics`
- `fact_query_history_profile_metrics`
- `fact_query_history_drift_metrics`
- `fact_audit_logs_profile_metrics`
- `fact_audit_logs_drift_metrics`
- `fact_node_timeline_profile_metrics`
- `fact_node_timeline_drift_metrics`

---

## Phase 2: Create Domain Dashboards

### 2.1 Dashboard JSON Structure

Each domain dashboard follows this structure:

```json
{
  "displayName": "[Domain] Dashboard",
  "warehouse_id": "${warehouse_id}",
  "pages": [
    {
      "name": "page_overview",
      "displayName": "Overview",
      "layout": [...]
    },
    {
      "name": "page_detail_1",
      "displayName": "Detail Page 1",
      "layout": [...]
    }
  ],
  "datasets": [
    {
      "name": "ds_kpi_metric",
      "displayName": "KPI Metric",
      "query": "SELECT ... FROM ..."
    }
  ]
}
```

### 2.2 Widget Specification Pattern

```json
{
  "widget": {
    "name": "widget_kpi_cost",
    "queries": [
      {
        "name": "main_query",
        "query": {
          "datasetName": "ds_kpi_metric",
          "fields": [
            {
              "name": "metric_value",
              "expression": "`metric_value`"
            }
          ],
          "disaggregated": true
        }
      }
    ],
    "spec": {
      "version": 2,
      "widgetType": "counter",
      "encodings": {
        "value": {
          "fieldName": "metric_value",
          "displayName": "Metric Value"
        }
      }
    }
  },
  "position": {
    "x": 0,
    "y": 0,
    "width": 2,
    "height": 2
  }
}
```

### 2.3 Create Cost Dashboard

1. Copy `cost_management.lvdash.json` as base
2. Add datasets from `commit_tracking.lvdash.json`
3. Add ML datasets (with fallback queries)
4. Add monitor datasets
5. Reorganize pages per specification

**ML Dataset Pattern (with fallback):**
```sql
SELECT 
    prediction_date,
    anomaly_score,
    is_anomaly
FROM ${catalog}.${gold_schema}.cost_anomaly_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
-- Fallback: Returns empty if table doesn't exist
UNION ALL
SELECT NULL, NULL, NULL WHERE 1=0
```

### 2.4 Create Remaining Domain Dashboards

Repeat the process for:
- Performance Dashboard (merge query_performance, cluster_utilization, dbr_migration, job_optimization)
- Quality Dashboard (merge table_health, governance_hub quality aspects)
- Security Dashboard (merge security_audit, governance_hub security aspects)
- Reliability Dashboard (enhance job_reliability)

---

## Phase 3: Implement Global Filters

### 3.1 Filter Parameter Definitions

Add to each dashboard's datasets:

```json
{
  "name": "gf_ds_time_windows",
  "displayName": "Time Windows",
  "query": "SELECT 'Last 7 Days' AS time_window UNION ALL SELECT 'Last 30 Days' UNION ALL SELECT 'Last 90 Days' UNION ALL SELECT 'Last 6 Months' UNION ALL SELECT 'Last Year'"
},
{
  "name": "gf_ds_workspaces",
  "displayName": "Workspaces", 
  "query": "SELECT DISTINCT CAST(workspace_id AS STRING) AS workspace_id, workspace_name FROM ${catalog}.${gold_schema}.dim_workspace UNION ALL SELECT 'All' AS workspace_id, 'All' AS workspace_name"
}
```

### 3.2 Bind Filters to Datasets

Every dataset must include filter bindings:

```sql
SELECT ...
FROM ${catalog}.${gold_schema}.fact_table
WHERE 
  (CASE 
    WHEN :time_window = 'Last 7 Days' THEN date_col >= CURRENT_DATE() - INTERVAL 7 DAYS
    WHEN :time_window = 'Last 30 Days' THEN date_col >= CURRENT_DATE() - INTERVAL 30 DAYS
    WHEN :time_window = 'Last 90 Days' THEN date_col >= CURRENT_DATE() - INTERVAL 90 DAYS
    WHEN :time_window = 'Last 6 Months' THEN date_col >= CURRENT_DATE() - INTERVAL 6 MONTHS
    WHEN :time_window = 'Last Year' THEN date_col >= CURRENT_DATE() - INTERVAL 1 YEAR
    ELSE TRUE
  END)
  AND (:workspace_filter = 'All' OR CAST(workspace_id AS STRING) = :workspace_filter)
```

### 3.3 Create Filter Widgets

```json
{
  "widget": {
    "name": "filter_time_window",
    "queries": [...],
    "spec": {
      "version": 2,
      "widgetType": "filter-single-select",
      "encodings": {
        "fields": {
          "fieldName": "time_window",
          "displayName": "Time Window"
        }
      }
    },
    "frame": {
      "title": "Time Window"
    }
  }
}
```

---

## Phase 4: Build Unified Dashboard

### 4.1 Update build_unified_dashboard.py

```python
def build_unified_dashboard(dashboard_dir: Path, config: dict) -> dict:
    """Build unified dashboard by extracting overview pages from domain dashboards."""
    
    unified = {
        "displayName": "[Health Monitor] Platform Overview",
        "warehouse_id": config["warehouse_id"],
        "pages": [],
        "datasets": []
    }
    
    # 1. Add global filters page
    filters_page = create_filters_page(config)
    unified["pages"].append(filters_page)
    
    # 2. Add executive summary page
    exec_summary = create_executive_summary_page(config)
    unified["pages"].append(exec_summary)
    
    # 3. Extract overview pages from each domain
    domain_dashboards = [
        ("cost_management.lvdash.json", "Cost Overview"),
        ("job_reliability.lvdash.json", "Reliability Overview"),
        ("query_performance.lvdash.json", "Performance Overview"),
        ("security_audit.lvdash.json", "Security Overview"),
        ("governance_hub.lvdash.json", "Quality Overview"),
    ]
    
    for dashboard_file, page_name in domain_dashboards:
        dashboard = load_dashboard(dashboard_dir / dashboard_file)
        overview_page = extract_overview_page(dashboard, page_name)
        unified["pages"].append(overview_page)
        
        # Add referenced datasets
        datasets = get_page_datasets(dashboard, overview_page)
        unified["datasets"].extend(datasets)
    
    # 4. Add ML intelligence page
    ml_page = create_ml_intelligence_page(config)
    unified["pages"].append(ml_page)
    
    # 5. Add drift monitoring page
    drift_page = create_drift_monitoring_page(config)
    unified["pages"].append(drift_page)
    
    # 6. Deduplicate and prefix datasets
    unified["datasets"] = deduplicate_datasets(unified["datasets"])
    
    # 7. Verify under 100 datasets
    if len(unified["datasets"]) > 100:
        unified["datasets"] = rationalize_datasets(unified["datasets"])
    
    return unified
```

### 4.2 Dataset Rationalization Logic

```python
def rationalize_datasets(datasets: list) -> list:
    """Reduce datasets to stay under 100 limit."""
    
    # Priority order for keeping datasets
    priority_prefixes = [
        "gf_ds_",      # Global filters (required)
        "exec_ds_",    # Executive summary (required)
        "cost_ds_kpi", # Cost KPIs
        "rel_ds_kpi",  # Reliability KPIs
        "perf_ds_kpi", # Performance KPIs
        "sec_ds_kpi",  # Security KPIs
        "qual_ds_kpi", # Quality KPIs
        "ml_ds_",      # ML summaries
        "drift_ds_",   # Drift summaries
    ]
    
    # Keep datasets in priority order until limit reached
    kept = []
    for prefix in priority_prefixes:
        matching = [d for d in datasets if d["name"].startswith(prefix)]
        kept.extend(matching)
        if len(kept) >= 95:
            break
    
    return kept[:100]
```

---

## Phase 5: Validation and Deployment

### 5.1 Local SQL Validation

Run before deployment:

```bash
python scripts/validate_dashboard_sql_local.py
```

### 5.2 Databricks SQL Validation

Deploy validation job:

```bash
databricks bundle deploy -t dev
databricks bundle run -t dev dashboard_validation_job
```

### 5.3 Deploy Dashboards

```bash
# Deploy all dashboards
databricks bundle run -t dev dashboard_deployment_job
```

### 5.4 Post-Deployment Verification

1. Open each dashboard in Databricks UI
2. Verify all widgets display data (not empty)
3. Test global filters on unified dashboard
4. Verify ML datasets show data (or graceful empty state)
5. Verify monitor datasets show metrics

---

## Phase 6: Maintenance

### 6.1 Adding New Datasets

1. Add to appropriate domain dashboard JSON
2. Update unified dashboard if overview-level
3. Run SQL validation
4. Deploy

### 6.2 Adding New ML Models

1. Create prediction table in Gold layer
2. Add dataset with fallback query
3. Add widget to appropriate page
4. Test with empty table first

### 6.3 Adding New Monitor Metrics

1. Add metric to Lakehouse Monitor config
2. Wait for monitor refresh
3. Add dataset querying metric
4. Add widget to appropriate page

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty widgets | `disaggregated: false` | Set to `true` |
| Widget shows "no fields" | Missing `displayName` in encoding | Add displayName |
| Filter not working | Dataset missing parameter | Add WHERE clause with parameter |
| Dataset limit exceeded | Too many datasets | Rationalize using priority logic |
| SQL error on deploy | Column name mismatch | Validate with local script |

### Debug Queries

```sql
-- Check dataset count
SELECT COUNT(*) FROM (
    SELECT DISTINCT name 
    FROM dashboard_json.datasets
);

-- Verify parameter binding
EXPLAIN SELECT ... WHERE :time_window = 'Last 7 Days' ...
```

---

## References

- [Databricks Lakeview API](https://docs.databricks.com/api/workspace/lakeview)
- [Dashboard JSON Specification](https://docs.databricks.com/dashboards/lakeview-dashboards.html)
- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring/)
- [MLflow Model Registry](https://docs.databricks.com/mlflow/)

