# AI/BI Dashboard Patterns

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SA-DB-001 |
| **Version** | 2.0 |
| **Last Updated** | January 2026 |
| **Owner** | Analytics Engineering Team |
| **Status** | Approved |

---

## Executive Summary

AI/BI Dashboards (Lakeview) provide interactive visualization of data from Gold layer tables, Metric Views, and monitoring outputs. This document defines patterns for dashboard development, query standards, and deployment automation.

---

## Golden Rules Summary

| Rule ID | Rule | Severity |
|---------|------|----------|
| MO-02 | Dashboard fieldName must match query alias | 🔴 Critical |
| MO-03 | SQL returns raw numbers (widgets format) | 🟡 Required |
| DB-01 | No hardcoded environment values | 🔴 Critical |
| DB-02 | UPDATE-or-CREATE deployment pattern | 🟡 Required |

---

## Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          AI/BI DASHBOARD (Lakeview)                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                          VISUALIZATION LAYER                                │  │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐           │  │
│   │  │  Counter   │  │   Chart    │  │   Table    │  │   Filter   │           │  │
│   │  │  Widget    │  │  Widget    │  │  Widget    │  │  Widget    │           │  │
│   │  └────────────┘  └────────────┘  └────────────┘  └────────────┘           │  │
│   │        │              │              │              │                       │  │
│   │        │    fieldName must match query column alias                         │  │
│   │        ▼              ▼              ▼              ▼                       │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                           DATASET LAYER                                     │  │
│   │  ┌─────────────────────────────────────────────────────────────────────┐   │  │
│   │  │ SELECT workspace_name, SUM(cost) as total_cost FROM fact_usage ...  │   │  │
│   │  └─────────────────────────────────────────────────────────────────────┘   │  │
│   │                                                                             │  │
│   │  • SQL queries against Gold/Semantic layer                                  │  │
│   │  • Return RAW numbers (widgets handle formatting)                           │  │
│   │  • Use ${parameter} for filters                                             │  │
│   │                                                                             │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                             │
│                                       ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │                      SERVERLESS SQL WAREHOUSE                               │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Rule MO-02: fieldName Matches Query Alias

### The Problem

Widget fieldName must exactly match the SQL column alias. Mismatch causes widget to show no data.

### Example

```json
// Dataset query
{
  "query": "SELECT workspace_name, SUM(list_cost) as total_cost FROM fact_usage GROUP BY 1"
}

// Widget configuration
{
  "spec": {
    "encodings": {
      "fields": [
        {
          "fieldName": "total_cost",  // ✅ MUST match alias exactly
          "displayName": "Total Cost"
        }
      ]
    }
  }
}
```

### Common Mistakes

| Query Alias | Widget fieldName | Result |
|-------------|------------------|--------|
| `total_cost` | `total_cost` | ✅ Works |
| `total_cost` | `totalCost` | ❌ No data |
| `SUM(cost)` | `cost` | ❌ No data (must alias) |
| `total_cost` | `Total Cost` | ❌ No data (case sensitive) |

---

## Rule MO-03: SQL Returns Raw Numbers

### The Principle

**SQL returns raw numeric values. Widget formatting handles display.**

### ❌ WRONG: Format in SQL

```sql
-- SQL
SELECT CONCAT('$', FORMAT_NUMBER(SUM(cost), 2)) as total_cost
-- Returns: "$1,234.56" (string)
-- Widget can't apply formatting
```

### ✅ CORRECT: Raw Number + Widget Format

```sql
-- SQL
SELECT SUM(cost) as total_cost
-- Returns: 1234.56 (number)
```

```json
// Widget formatting
{
  "fieldName": "total_cost",
  "numberFormat": {
    "type": "currency",
    "currency": "USD",
    "decimalPlaces": 2
  }
}
```

---

## Rule DB-01: No Hardcoded Values

### The Problem

Hardcoded catalog/schema names break dashboard portability across environments.

### The Solution: Variable Placeholders

```json
// Dashboard JSON with placeholders
{
  "datasets": [
    {
      "name": "cost_summary",
      "query": "SELECT * FROM ${catalog}.${gold_schema}.fact_usage WHERE ..."
    }
  ]
}
```

### Deployment with Substitution

```python
def substitute_variables(dashboard_json: str, variables: dict) -> str:
    """Replace ${variable} placeholders with actual values."""
    result = dashboard_json
    for key, value in variables.items():
        result = result.replace(f"${{{key}}}", value)
    return result


# Usage
variables = {
    "catalog": "company_prod",
    "gold_schema": "gold",
    "warehouse_id": "abc123"
}

final_json = substitute_variables(dashboard_template, variables)
```

---

## Rule DB-02: UPDATE-or-CREATE Pattern

### The Pattern

Use Workspace Import API with `overwrite: true` for idempotent deployments.

```python
import base64
import json
from databricks.sdk import WorkspaceClient


def deploy_dashboard(
    w: WorkspaceClient,
    dashboard_json: str,
    workspace_path: str
):
    """
    Deploy dashboard using UPDATE-or-CREATE pattern.
    
    Benefits:
    - Preserves dashboard URL (no broken links)
    - Maintains permissions
    - Works for both new and existing
    """
    # Encode content
    content_b64 = base64.b64encode(dashboard_json.encode()).decode()
    
    # Import with overwrite
    w.workspace.import_(
        path=workspace_path,
        content=content_b64,
        format="AUTO",
        overwrite=True  # Key: enables update pattern
    )
    
    print(f"✅ Deployed dashboard: {workspace_path}")
```

---

## Query Patterns

### Counter Widget Query

```sql
-- Single KPI value
SELECT SUM(list_cost) as total_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 30)
```

### Time Series Chart Query

```sql
-- Daily trend
SELECT 
    usage_date,
    SUM(list_cost) as daily_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
GROUP BY usage_date
ORDER BY usage_date
```

### Bar Chart Query

```sql
-- Category comparison
SELECT 
    w.workspace_name,
    SUM(f.list_cost) as total_cost
FROM ${catalog}.${gold_schema}.fact_usage f
JOIN ${catalog}.${gold_schema}.dim_workspace w 
    ON f.workspace_id = w.workspace_id AND w.is_current = true
WHERE f.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY w.workspace_name
ORDER BY total_cost DESC
LIMIT 10
```

### Table Widget Query

```sql
-- Detailed breakdown
SELECT 
    w.workspace_name,
    s.sku_name,
    SUM(f.list_cost) as total_cost,
    SUM(f.dbus_consumed) as total_dbus
FROM ${catalog}.${gold_schema}.fact_usage f
JOIN ${catalog}.${gold_schema}.dim_workspace w 
    ON f.workspace_id = w.workspace_id AND w.is_current = true
JOIN ${catalog}.${gold_schema}.dim_sku s 
    ON f.sku_id = s.sku_id
WHERE f.usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY w.workspace_name, s.sku_name
ORDER BY total_cost DESC
```

---

## Monitoring Table Queries

### Profile Metrics (AGGREGATE)

```sql
-- Query AGGREGATE metrics (require PIVOT)
SELECT 
    window.start as period_start,
    MAX(CASE WHEN column_name = ':table' THEN total_cost END) as total_cost,
    MAX(CASE WHEN column_name = ':table' THEN workspace_count END) as workspace_count
FROM ${catalog}.${monitoring_schema}.fact_usage_profile_metrics
WHERE column_name = ':table'
GROUP BY window.start
ORDER BY window.start DESC
LIMIT 30
```

### Drift Metrics

```sql
-- Query drift detection
SELECT 
    window.start as period_start,
    column_name,
    chi_squared_pvalue,
    wasserstein_distance
FROM ${catalog}.${monitoring_schema}.fact_usage_drift_metrics
WHERE chi_squared_pvalue < 0.05  -- Significant drift
ORDER BY window.start DESC
```

---

## Complete Dashboard JSON Structure

```json
{
  "displayName": "Databricks Cost Intelligence",
  
  "warehouse_id": "${warehouse_id}",
  
  "datasets": [
    {
      "name": "total_cost",
      "displayName": "Total Cost",
      "query": "SELECT SUM(list_cost) as total_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), ${days_back})"
    },
    {
      "name": "daily_trend",
      "displayName": "Daily Cost Trend",
      "query": "SELECT usage_date, SUM(list_cost) as daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= DATE_SUB(CURRENT_DATE(), ${days_back}) GROUP BY 1 ORDER BY 1"
    },
    {
      "name": "by_workspace",
      "displayName": "Cost by Workspace",
      "query": "SELECT w.workspace_name, SUM(f.list_cost) as total_cost FROM ${catalog}.${gold_schema}.fact_usage f JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.usage_date >= DATE_SUB(CURRENT_DATE(), ${days_back}) GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
    }
  ],
  
  "pages": [
    {
      "name": "overview",
      "displayName": "Overview",
      "layout": [
        {
          "widget": {
            "name": "total_cost_counter",
            "queries": [{"name": "total_cost"}],
            "spec": {
              "version": 3,
              "widgetType": "counter",
              "encodings": {
                "value": {
                  "fieldName": "total_cost",
                  "displayName": "Total Cost (30d)"
                }
              },
              "overrides": {
                "NumberFormat": {
                  "type": "currency",
                  "currency": "USD"
                }
              }
            }
          },
          "position": {"x": 0, "y": 0, "width": 2, "height": 2}
        },
        {
          "widget": {
            "name": "trend_chart",
            "queries": [{"name": "daily_trend"}],
            "spec": {
              "version": 3,
              "widgetType": "area",
              "encodings": {
                "x": {"fieldName": "usage_date", "displayName": "Date"},
                "y": {"fieldName": "daily_cost", "displayName": "Daily Cost"}
              }
            }
          },
          "position": {"x": 2, "y": 0, "width": 4, "height": 3}
        }
      ]
    }
  ],
  
  "parameters": [
    {
      "name": "days_back",
      "displayName": "Days Back",
      "type": "number",
      "defaultValue": 30
    }
  ]
}
```

---

## Pre-Deployment Validation

### Query Validation Script

```python
def validate_dashboard_queries(
    spark,
    dashboard_json: dict,
    variables: dict
):
    """
    Validate all dashboard queries with SELECT LIMIT 1.
    
    Catches:
    - Missing columns
    - Invalid table references
    - Syntax errors
    - Type mismatches
    """
    errors = []
    
    for dataset in dashboard_json.get("datasets", []):
        query = dataset["query"]
        
        # Substitute variables
        for key, value in variables.items():
            query = query.replace(f"${{{key}}}", str(value))
        
        # Add LIMIT 1 for fast validation
        validation_query = f"SELECT * FROM ({query}) LIMIT 1"
        
        try:
            spark.sql(validation_query).collect()
            print(f"✅ {dataset['name']}: Valid")
        except Exception as e:
            error_msg = str(e)
            errors.append({
                "dataset": dataset["name"],
                "error": error_msg
            })
            print(f"❌ {dataset['name']}: {error_msg[:100]}")
    
    if errors:
        print(f"\n❌ {len(errors)} queries failed validation")
        return False
    
    print(f"\n✅ All {len(dashboard_json.get('datasets', []))} queries valid")
    return True
```

---

## Validation Checklist

### Query Development
- [ ] All queries return raw numbers (no formatting in SQL)
- [ ] All columns have explicit aliases
- [ ] JOIN conditions include SCD2 filters (is_current = true)
- [ ] Date filters use parameters (${days_back})
- [ ] No hardcoded catalog/schema names

### Widget Configuration
- [ ] fieldName exactly matches query alias
- [ ] Number formatting in widget spec (not SQL)
- [ ] Display names set for user-friendly labels
- [ ] Widget type appropriate for data

### Deployment
- [ ] Variables substitution working
- [ ] Pre-deployment validation passes
- [ ] UPDATE-or-CREATE pattern used
- [ ] Dashboard accessible after deployment

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| Widget shows no data | fieldName mismatch | Match exactly to query alias |
| "Column not found" | Missing alias | Add explicit `AS alias` |
| Wrong numbers | Formatting in SQL | Return raw, format in widget |
| Dashboard not updating | Not using overwrite | Set `overwrite: true` |
| Env mismatch | Hardcoded values | Use ${variable} placeholders |

---

## Related Documents

- [Lakehouse Monitoring](../monitoring/41-lakehouse-monitoring.md)
- [TVF Patterns](../semantic-layer/31-tvf-patterns.md)
- [Gold Layer Patterns](../data-pipelines/12-gold-layer-patterns.md)

---

## References

- [AI/BI Dashboards](https://docs.databricks.com/dashboards/)
- [Lakeview Reference](https://docs.databricks.com/dashboards/lakeview/)
