# AI/BI Lakeview Dashboard Creation Guide

## 🚀 Quick Start (2 hours)

**Goal:** Create visual dashboards with AI-powered insights for business users

**What You'll Create:**
1. SQL queries from Metric Views or Gold tables
2. AI/BI Dashboard via UI or JSON
3. Auto-refresh schedule

**Fast Track (UI-Based):**
```
1. Navigate to: Databricks Workspace → Dashboards → Create AI/BI Dashboard
2. Add Data → Query Metric View or Gold table
3. Add Visualizations:
   - Counter tiles for KPIs (Total Revenue, Units, Transactions)
   - Bar charts for comparisons (Revenue by Store)
   - Line charts for trends (Daily Revenue Trend)
   - Tables for drill-down (Top Products Detail)
4. Add Filters (Date Range, Store, Category)
5. Configure Layout (Canvas: 6-column grid)
6. Enable Auto-refresh (Hourly/Daily)
7. Share with business users
```

---

## 🚨 CRITICAL: Top 10 Lessons Learned

These patterns are documented from 100+ production deployment failures. **Read these first.**

### 1. Widget-Query Column Alignment (Most Common Error)

**Widget `fieldName` MUST exactly match query output alias.**

```json
// Widget expects "total_queries"
"encodings": { "value": { "fieldName": "total_queries" } }
```

```sql
-- ❌ WRONG - Query returns different name
SELECT COUNT(*) AS query_count FROM ...

-- ✅ CORRECT - Names match
SELECT COUNT(*) AS total_queries FROM ...
```

**Common Mismatches:**
| Widget Expects | Query Returns | Fix |
|----------------|---------------|-----|
| `total_queries` | `query_count` | Alias as `total_queries` |
| `warehouse_name` | `compute_type` | Alias as `warehouse_name` |
| `unique_users` | `distinct_users` | Alias as `unique_users` |
| `query_id` | `statement_id` | Alias as `query_id` |
| `failure_count` | `failed_queries` | Alias as `failure_count` |

### 2. Number Formatting (Second Most Common)

| Format | Input | Output | Rule |
|--------|-------|--------|------|
| `number-percent` | `0.85` | `85%` | Return 0-1 decimal, widget multiplies ×100 |
| `number-currency` | `1234.56` | `$1,234.56` | Return raw number |
| `number-plain` | `1234` | `1,234` | Return raw number |

```sql
-- ❌ WRONG - Returns formatted string
SELECT CONCAT('$', FORMAT_NUMBER(SUM(cost), 2)) AS total_cost

-- ✅ CORRECT - Returns raw number
SELECT ROUND(SUM(cost), 2) AS total_cost

-- ❌ WRONG - Returns 85 (will show 8500%)
SELECT ROUND(success * 100.0 / total, 1) AS success_rate

-- ✅ CORRECT - Returns 0.85 (will show 85%)
SELECT ROUND(success * 1.0 / NULLIF(total, 0), 3) AS success_rate
```

### 3. Parameter Definition Required

Every dataset using parameters MUST define them:

```json
{
  "name": "ds_kpi_revenue",
  "query": "SELECT SUM(cost) FROM table WHERE date BETWEEN :time_range.min AND :time_range.max",
  "parameters": [
    {
      "keyword": "time_range",
      "dataType": "DATETIME_RANGE",
      "defaultSelection": {
        "range": {
          "min": { "dataType": "DATETIME", "value": "now-30d/d" },
          "max": { "dataType": "DATETIME", "value": "now/d" }
        }
      }
    }
  ]
}
```

### 4. Monitoring Table Schema (Custom Metrics)

Custom metrics use generic schema - pivot with CASE:

```sql
-- ❌ WRONG - These columns don't exist directly
SELECT success_rate, total_runs FROM fact_job_run_timeline_profile_metrics

-- ✅ CORRECT - Use CASE pivot on column_name
SELECT 
  window.start AS window_start,
  MAX(CASE WHEN column_name = 'success_rate' THEN avg END) AS success_rate_pct,
  MAX(CASE WHEN column_name = 'total_runs' THEN count END) AS total_runs
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE window.start BETWEEN :time_range.min AND :time_range.max
GROUP BY window.start
```

**Window struct access:**
```sql
-- ❌ WRONG
SELECT window_start FROM monitoring_table

-- ✅ CORRECT
SELECT window.start AS window_start FROM monitoring_table
```

### 5. Pie Chart Scale Required

Pie charts won't render without explicit `scale` properties:

```json
{
  "encodings": {
    "color": {
      "fieldName": "category",
      "scale": { "type": "categorical" }  // REQUIRED!
    },
    "angle": {
      "fieldName": "value",
      "scale": { "type": "quantitative" }  // REQUIRED!
    }
  }
}
```

### 5.1 Bar Chart Scale Required

Bar charts ALSO won't render without explicit `scale` properties:

```json
{
  "encodings": {
    "x": {
      "fieldName": "category_name",
      "scale": { "type": "categorical" }  // REQUIRED!
    },
    "y": {
      "fieldName": "value",
      "scale": { "type": "quantitative" }  // REQUIRED!
    }
  }
}
```

**Error without scale:** "Select fields to visualize"

### 6. Table Widget Version 2

Use version 2 and remove legacy properties:

```json
{
  "spec": {
    "version": 2,  // Not 1
    "widgetType": "table",
    "encodings": { "columns": [...] },
    "frame": { "showTitle": true, "title": "..." }
    // Remove: itemsPerPage, condensed, withRowNumber
  }
}
```

### 7. Multi-Series Charts with UNION ALL

```sql
SELECT date, 'Average' AS metric, AVG(value) AS amount FROM ... GROUP BY 1
UNION ALL
SELECT date, 'P95' AS metric, PERCENTILE_APPROX(value, 0.95) AS amount FROM ... GROUP BY 1
ORDER BY date, metric
```

```json
{
  "encodings": {
    "x": { "fieldName": "date", "scale": { "type": "temporal" } },
    "y": { "fieldName": "amount", "scale": { "type": "quantitative" } },
    "color": { "fieldName": "metric", "scale": { "type": "categorical" } }
  }
}
```

### 8. Stacked Area Charts

```json
{
  "encodings": {
    "y": {
      "fieldName": "run_count",
      "scale": { "type": "quantitative" },
      "stack": "zero"  // CRITICAL for stacking
    },
    "color": {
      "fieldName": "status",
      "scale": {
        "type": "categorical",
        "domain": ["Success", "Failed"],
        "range": ["#00A972", "#FF3621"]
      }
    }
  }
}
```

### 9. SQL NULL and Division Handling

```sql
-- Prevent empty results
SELECT COALESCE(SUM(cost), 0) AS total_cost

-- Prevent NULL in grouping
SELECT COALESCE(sku_name, 'Unknown') AS sku_name

-- Prevent division by zero
SELECT ROUND(success / NULLIF(total, 0), 3) AS success_rate

-- Distinct counts for users
SELECT COUNT(DISTINCT user_identity_email) AS unique_users
WHERE user_identity_email NOT LIKE '%@databricks.com'
```

### 10. Schema Variable Substitution

```sql
-- ✅ CORRECT - Use variables
FROM ${catalog}.${gold_schema}.fact_usage
FROM ${catalog}.${gold_schema}_monitoring.fact_usage_profile_metrics
FROM ${catalog}.${feature_schema}.ml_predictions

-- ❌ WRONG - Hardcoded
FROM my_catalog.my_schema.fact_usage
```

---

## 📋 Requirements Checklist

Before creating dashboards, define:

### Dashboard Purpose
- **Name:** _________________ (e.g., "Sales Performance Dashboard")
- **Audience:** _________________ (e.g., "Sales Managers")
- **Update Frequency:** [ ] Real-time [ ] Hourly [ ] Daily [ ] Weekly
- **Primary Goal:** _________________ (e.g., "Track daily KPIs")

### Data Sources
- **Catalog:** `${catalog}` → _________________
- **Gold Schema:** `${gold_schema}` → _________________
- **Monitoring Schema:** `${gold_schema}_monitoring` → _________________
- **Primary Table/View:** _________________

### KPIs (3-6 metrics)

| # | KPI Name | SQL Expression | Format | Widget `fieldName` |
|---|----------|----------------|--------|-------------------|
| 1 | Total Revenue | `SUM(net_revenue)` | `number-currency` | `total_revenue` |
| 2 | Success Rate | `SUM(success)/NULLIF(COUNT(*),0)` | `number-percent` | `success_rate` |
| 3 | _____________ | _____________ | _____________ | _____________ |

### Filters

| Filter Name | Type | Dataset Query |
|-------------|------|---------------|
| Date Range | `filter-date-range-picker` | N/A (built-in) |
| Workspace | `filter-multi-select` | `ds_select_workspace` |
| _________ | _____________ | _____________ |

---

## 🏗️ Dashboard JSON Structure

### Complete Template

```json
{
  "datasets": [
    {
      "name": "ds_kpi_revenue",
      "displayName": "Revenue KPIs",
      "query": "SELECT SUM(net_revenue) AS total_revenue, COUNT(*) AS transaction_count FROM ${catalog}.${gold_schema}.fact_sales WHERE sale_date BETWEEN :time_range.min AND :time_range.max",
      "parameters": [
        {
          "keyword": "time_range",
          "dataType": "DATETIME_RANGE",
          "defaultSelection": {
            "range": {
              "min": { "dataType": "DATETIME", "value": "now-30d/d" },
              "max": { "dataType": "DATETIME", "value": "now/d" }
            }
          }
        }
      ]
    }
  ],
  
  "pages": [
    {
      "name": "page_overview",
      "displayName": "📊 Overview",
      "layout": [
        // Widgets go here
      ]
    },
    {
      "name": "page_global_filters",
      "displayName": "Global Filters",
      "pageType": "PAGE_TYPE_GLOBAL_FILTERS",
      "layout": [
        // Global filter widgets
      ]
    }
  ]
}
```

---

## 📊 Widget Specifications

### KPI Counter (Version 2)

```json
{
  "widget": {
    "name": "kpi_total_revenue",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "ds_kpi_revenue",
        "fields": [{ "name": "total_revenue", "expression": "`total_revenue`" }],
        "disaggregated": false
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "counter",
      "encodings": {
        "value": { "fieldName": "total_revenue", "displayName": "Revenue" }
      },
      "frame": {
        "showTitle": true,
        "title": "Total Revenue",
        "showDescription": true,
        "description": "Revenue for selected period"
      }
    }
  },
  "position": { "x": 0, "y": 0, "width": 2, "height": 2 }
}
```

### Line Chart (Version 3)

```json
{
  "widget": {
    "name": "chart_revenue_trend",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "ds_revenue_trend",
        "fields": [
          { "name": "sale_date", "expression": "`sale_date`" },
          { "name": "revenue", "expression": "`revenue`" }
        ],
        "disaggregated": false
      }
    }],
    "spec": {
      "version": 3,
      "widgetType": "line",
      "encodings": {
        "x": { "fieldName": "sale_date", "displayName": "Date", "scale": { "type": "temporal" } },
        "y": { "fieldName": "revenue", "displayName": "Revenue", "scale": { "type": "quantitative" } }
      },
      "frame": { "showTitle": true, "title": "Revenue Trend" }
    }
  },
  "position": { "x": 0, "y": 2, "width": 3, "height": 6 }
}
```

### Bar Chart (Version 3) - MUST Have Scale

**⚠️ Bar charts require `scale` on both `x` and `y` or they show "Select fields to visualize"**

```json
{
  "widget": {
    "name": "chart_revenue_by_category",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "ds_revenue_by_category",
        "fields": [
          { "name": "category", "expression": "`category`" },
          { "name": "revenue", "expression": "`revenue`" }
        ],
        "disaggregated": false
      }
    }],
    "spec": {
      "version": 3,
      "widgetType": "bar",
      "encodings": {
        "x": { "fieldName": "category", "displayName": "Category", "scale": { "type": "categorical" } },  // REQUIRED!
        "y": { "fieldName": "revenue", "displayName": "Revenue", "scale": { "type": "quantitative" } }   // REQUIRED!
      },
      "frame": { "showTitle": true, "title": "Revenue by Category" }
    }
  },
  "position": { "x": 3, "y": 2, "width": 3, "height": 6 }
}
```

### Pie Chart (Version 3) - MUST Have Scale

```json
{
  "widget": {
    "name": "chart_distribution",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "ds_distribution",
        "fields": [
          { "name": "category", "expression": "`category`" },
          { "name": "value", "expression": "`value`" }
        ],
        "disaggregated": false
      }
    }],
    "spec": {
      "version": 3,
      "widgetType": "pie",
      "encodings": {
        "color": {
          "fieldName": "category",
          "displayName": "Category",
          "scale": { "type": "categorical" }
        },
        "angle": {
          "fieldName": "value",
          "displayName": "Value",
          "scale": { "type": "quantitative" }
        }
      },
      "frame": { "showTitle": true, "title": "Distribution" }
    }
  },
  "position": { "x": 0, "y": 8, "width": 3, "height": 6 }
}
```

### Table Widget (Version 2)

```json
{
  "widget": {
    "name": "table_details",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "ds_details",
        "fields": [
          { "name": "name", "expression": "`name`" },
          { "name": "value", "expression": "`value`" },
          { "name": "status", "expression": "`status`" }
        ],
        "disaggregated": false
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "table",
      "encodings": {
        "columns": [
          { "fieldName": "name", "title": "Name", "type": "string" },
          { "fieldName": "value", "title": "Value", "type": "number" },
          { "fieldName": "status", "title": "Status", "type": "string" }
        ]
      },
      "frame": { "showTitle": true, "title": "Details" }
    }
  },
  "position": { "x": 0, "y": 14, "width": 6, "height": 6 }
}
```

### Filter Widgets

**Date Range Picker:**
```json
{
  "widget": {
    "name": "filter_time_range",
    "spec": {
      "version": 2,
      "widgetType": "filter-date-range-picker",
      "encodings": {
        "start": { "parameterKeyword": "time_range.min" },
        "end": { "parameterKeyword": "time_range.max" }
      },
      "frame": { "showTitle": true, "title": "Time Range" }
    },
    "param_queries": [
      { "paramDatasetName": "ds_kpi_revenue", "queryName": "param_ds_kpi_revenue" },
      { "paramDatasetName": "ds_trend", "queryName": "param_ds_trend" }
    ]
  },
  "position": { "x": 0, "y": 0, "width": 2, "height": 1 }
}
```

**Multi-Select Filter:**
```json
{
  "widget": {
    "name": "filter_workspace",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "ds_select_workspace",
        "fields": [{ "name": "workspace_name", "expression": "`workspace_name`" }],
        "disaggregated": false
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "filter-multi-select",
      "encodings": {
        "fields": [{
          "displayName": "Workspace",
          "fieldName": "workspace_name",
          "queryName": "main_query"
        }]
      },
      "frame": { "showTitle": true, "title": "Workspace" }
    },
    "param_queries": [
      { "paramDatasetName": "ds_kpi_events", "queryName": "param_workspace" }
    ]
  },
  "position": { "x": 2, "y": 0, "width": 2, "height": 1 }
}
```

---

## 📐 Grid Layout (6-Column)

### Grid Rules
- **Width:** 1-6 (6 = full width)
- **Height:** 1-2 for filters, 2 for KPIs, 6+ for charts/tables
- **X position:** 0-5

### Standard Layout Patterns

```
Row 0: KPIs (height: 2)
├── KPI 1 (x:0, width:1)
├── KPI 2 (x:1, width:1)
├── KPI 3 (x:2, width:1)
├── KPI 4 (x:3, width:1)
├── KPI 5 (x:4, width:1)
└── KPI 6 (x:5, width:1)

Row 2: Charts (height: 6)
├── Chart 1 (x:0, width:3)
└── Chart 2 (x:3, width:3)

Row 8: Full-width chart (height: 6)
└── Chart 3 (x:0, width:6)

Row 14: Table (height: 6)
└── Table (x:0, width:6)
```

### Position Examples

```json
// Two side-by-side charts
{ "x": 0, "y": 2, "width": 3, "height": 6 }  // Left
{ "x": 3, "y": 2, "width": 3, "height": 6 }  // Right

// Six KPIs in a row
{ "x": 0, "y": 0, "width": 1, "height": 2 }
{ "x": 1, "y": 0, "width": 1, "height": 2 }
{ "x": 2, "y": 0, "width": 1, "height": 2 }
{ "x": 3, "y": 0, "width": 1, "height": 2 }
{ "x": 4, "y": 0, "width": 1, "height": 2 }
{ "x": 5, "y": 0, "width": 1, "height": 2 }

// Full-width table
{ "x": 0, "y": 14, "width": 6, "height": 6 }
```

---

## 📊 Domain-Specific Patterns

### Cost & Usage Dashboards

**Key Metrics:**
- `total_cost` (currency)
- `total_dbus` (number)
- `serverless_pct` (percent: 0-1)
- `tag_coverage_pct` (percent: 0-1)
- `unique_users` (number, use COUNT DISTINCT)

**Sample Queries:**
```sql
-- Cost KPIs
SELECT 
  ROUND(SUM(list_cost), 2) AS total_cost,
  SUM(usage_quantity) AS total_dbus,
  COUNT(DISTINCT identity_metadata_run_as) AS unique_users
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN :time_range.min AND :time_range.max

-- Cost by SKU
SELECT 
  COALESCE(sku_name, 'Unknown') AS sku_name,
  ROUND(SUM(list_cost), 2) AS total_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY 1
HAVING SUM(list_cost) > 0
ORDER BY total_cost DESC
LIMIT 15
```

### Reliability Dashboards

**Key Metrics:**
- `success_rate` (percent: 0-1)
- `total_runs` (number)
- `avg_duration_sec` (number)
- `mttr_min` (number)

**Sample Queries:**
```sql
-- Job Success Rate
SELECT 
  ROUND(SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0), 3) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE run_date BETWEEN :time_range.min AND :time_range.max

-- Failure by Type (for pie chart)
SELECT 
  COALESCE(termination_code, 'UNKNOWN') AS termination_code,
  COUNT(*) AS failure_count
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE result_state NOT IN ('SUCCESS', 'SUCCEEDED')
  AND run_date BETWEEN :time_range.min AND :time_range.max
GROUP BY 1
ORDER BY failure_count DESC
```

### Performance Dashboards

**Key Metrics:**
- `total_queries` (number)
- `avg_duration_sec` (number)
- `p95_duration_sec` (number)
- `slow_query_rate` (percent: 0-1)

**Sample Queries:**
```sql
-- Query Performance
SELECT 
  COUNT(*) AS total_queries,
  ROUND(AVG(total_duration_ms) / 1000, 2) AS avg_duration_sec,
  ROUND(PERCENTILE_APPROX(total_duration_ms, 0.95) / 1000, 2) AS p95_duration_sec,
  ROUND(SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0), 3) AS slow_query_rate
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time BETWEEN :time_range.min AND :time_range.max

-- Note: Use execution_status (not query_status) for status checks
-- Use 'FINISHED' for success (not 'SUCCESS')
```

### Security Dashboards

**Key Metrics:**
- `total_events` (number)
- `unique_users` (number, COUNT DISTINCT)
- `high_risk_events` (number)
- `access_denied` (number)

**Sample Queries:**
```sql
-- Security KPIs
SELECT 
  COUNT(*) AS total_events,
  COUNT(DISTINCT user_identity_email) AS unique_users,
  COUNT(DISTINCT CASE WHEN is_failed_action = TRUE OR response_status_code >= 400 THEN request_id END) AS access_denied
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_time BETWEEN :time_range.min AND :time_range.max
  AND user_identity_email NOT LIKE '%@databricks.com'

-- Access Denials with Details
SELECT 
  DATE(event_time) AS event_date,
  user_identity_email AS user,
  action_name,
  response_error_message AS error_message
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE (is_failed_action = TRUE OR response_status_code >= 400)
  AND event_time BETWEEN :time_range.min AND :time_range.max
ORDER BY event_time DESC
LIMIT 100
```

### Quality & Governance Dashboards

**Key Metrics:**
- `table_count` (number)
- `tagged_pct` (percent: 0-1)
- `lineage_events` (number)

**Sample Queries:**
```sql
-- Tables by Catalog (capture both reads and writes)
SELECT 
  COALESCE(source_table_catalog, target_table_catalog) AS catalog_name,
  COUNT(DISTINCT COALESCE(source_table_full_name, target_table_full_name)) AS table_count
FROM ${catalog}.${gold_schema}.fact_table_lineage
WHERE event_date BETWEEN :time_range.min AND :time_range.max
  AND COALESCE(source_table_catalog, target_table_catalog) IS NOT NULL
GROUP BY 1
ORDER BY table_count DESC
```

---

## 🔍 Lakehouse Monitoring Queries

### Profile Metrics (CASE Pivot Pattern)

```sql
SELECT 
  DATE(window.start) AS window_start,
  MAX(CASE WHEN column_name = 'success_rate' THEN avg END) AS success_rate_pct,
  MAX(CASE WHEN column_name = 'total_runs' THEN count END) AS total_runs,
  MAX(CASE WHEN column_name = 'avg_duration' THEN avg END) AS avg_duration_sec,
  MAX(CASE WHEN column_name = 'p95_duration' THEN p95 END) AS p95_duration_sec
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE window.start BETWEEN :time_range.min AND :time_range.max
GROUP BY 1
ORDER BY 1
```

### Drift Metrics

**⚠️ CRITICAL: Custom drift metrics are DIRECT COLUMNS, not in avg_delta!**

```sql
-- ✅ CORRECT: Custom drift metrics are stored as named columns
SELECT 
  DATE(window.start) AS window_start,
  success_rate_drift,        -- Direct column (not avg_delta!)
  duration_drift_pct,        -- Direct column
  cost_drift_pct             -- Direct column
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_drift_metrics
WHERE column_name = ':table'        -- MUST filter to :table row
  AND drift_type = 'CONSECUTIVE'
  AND slice_key IS NULL             -- MUST be NULL for table-level metrics
ORDER BY window.start
```

```sql
-- ❌ WRONG: avg_delta returns 0 for custom metrics!
SELECT COALESCE(avg_delta, 0) AS drift_pct
FROM drift_metrics WHERE column_name = ':table'  -- Returns 0!
```

**Custom drift columns by domain:**
| Domain | Table | Columns |
|--------|-------|---------|
| Cost | `fact_usage_drift_metrics` | `cost_drift_pct`, `dbu_drift_pct` |
| Jobs | `fact_job_run_timeline_drift_metrics` | `success_rate_drift`, `duration_drift_pct` |
| Queries | `fact_query_history_drift_metrics` | `p95_duration_drift_pct`, `failure_rate_drift` |

### Monitoring Table Reference

| Base Table | Profile Metrics | Drift Metrics |
|------------|-----------------|---------------|
| `fact_usage` | `fact_usage_profile_metrics` | `fact_usage_drift_metrics` |
| `fact_query_history` | `fact_query_history_profile_metrics` | `fact_query_history_drift_metrics` |
| `fact_job_run_timeline` | `fact_job_run_timeline_profile_metrics` | `fact_job_run_timeline_drift_metrics` |
| `fact_audit_logs` | `fact_audit_logs_profile_metrics` | `fact_audit_logs_drift_metrics` |
| `fact_table_lineage` | `fact_table_lineage_profile_metrics` | `fact_table_lineage_drift_metrics` |
| `fact_node_timeline` | `fact_node_timeline_profile_metrics` | `fact_node_timeline_drift_metrics` |

---

## ✅ Validation Checklist

### Before Deployment

**1. Widget-Query Alignment:**
- [ ] Every widget `fieldName` matches query output alias
- [ ] No typos in column names

**2. Number Formats:**
- [ ] Percentage widgets receive 0-1 decimals
- [ ] Currency widgets receive raw numbers
- [ ] No `FORMAT_NUMBER()` or `CONCAT()` in KPI queries

**3. Parameters:**
- [ ] Every dataset has `parameters` array with all used parameters
- [ ] Time range uses `:time_range.min` and `:time_range.max`
- [ ] Filter widgets have `param_queries` connecting to datasets

**4. Monitoring Queries:**
- [ ] Using `window.start` not `window_start`
- [ ] Using CASE pivot on `column_name`
- [ ] Schema suffix is `_monitoring`

**5. Pie Charts:**
- [ ] `color` encoding has `scale: { "type": "categorical" }`
- [ ] `angle` encoding has `scale: { "type": "quantitative" }`

**6. Tables:**
- [ ] Version is 2
- [ ] No `itemsPerPage`, `condensed`, `withRowNumber`

**7. SQL Quality:**
- [ ] Using `COALESCE` for NULL handling
- [ ] Using `NULLIF(x, 0)` for division safety
- [ ] Using `COUNT(DISTINCT)` for unique counts
- [ ] Filtering system/internal users where appropriate
- [ ] Parentheses around OR conditions

### Run SQL Validation (CRITICAL - Reduces Dev Loop Time by 90%)

**Why validate before deploying?**
- Without validation: Deploy → Open dashboard → See errors → Fix → Redeploy (2-5 min/iteration)
- With validation: Validate → See ALL errors → Fix all → Deploy once (30-60 sec total)

**Validation Approach: Use `SELECT LIMIT 1`, not `EXPLAIN`**
- `EXPLAIN` only checks syntax
- `SELECT LIMIT 1` catches runtime errors:
  - `UNRESOLVED_COLUMN` - column doesn't exist
  - `TABLE_OR_VIEW_NOT_FOUND` - table doesn't exist
  - `UNBOUND_SQL_PARAMETER` - parameter not defined
  - `DATATYPE_MISMATCH` - type conversion errors

**Development Workflow:**
```bash
# 1. Make changes to dashboard JSON files
vim src/dashboards/cost.lvdash.json

# 2. Run local widget encoding validation (fast, no DB connection)
python src/dashboards/validate_widget_encodings.py --check

# 3. Run SQL validation (requires Databricks connection)
cd src/dashboards && python validate_dashboard_queries.py

# 4. Check for regressions (git diff)
git diff --stat origin/main -- src/dashboards/*.json

# 5. Deploy only after ALL validations pass
databricks bundle deploy -t dev --force

# 6. Run dashboard deployment job
databricks bundle run -t dev dashboard_deployment_job
```

**Parameter Substitution for Validation:**
| Parameter | Test Value |
|-----------|------------|
| `:time_range.min` | `CURRENT_DATE() - INTERVAL 30 DAYS` |
| `:time_range.max` | `CURRENT_DATE()` |
| `:param_workspace` | `ARRAY('All')` |
| `:param_catalog` | `ARRAY('All')` |
| `:monitor_slice_key` | `'No Slice'` |
| `:annual_commit` | `1000000` |

**Anti-Regression Checks:**
```bash
# Before EVERY deployment:
python src/dashboards/validate_widget_encodings.py --check  # Widget alignment
python src/dashboards/validate_dashboard_queries.py         # SQL validation
git diff --name-status HEAD~1 -- src/dashboards/            # What changed?
```

---

## 🔧 Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "no fields to visualize" | Widget `fieldName` mismatch | Align SQL alias with widget |
| "Select fields to visualize" | Bar chart missing `scale` | Add `scale` to `x` and `y` encodings |
| "UNRESOLVED_COLUMN" | Column doesn't exist | Check table schema |
| "UNBOUND_SQL_PARAMETER" | Missing parameter def | Add to `parameters` array |
| Empty pie chart | Missing `scale` | Add scale to both `color` and `angle` |
| Empty bar chart | Missing `scale` | Add scale to both `x` and `y` |
| 0% or wrong percentage | Returning 85 not 0.85 | Return 0-1 decimal |
| Empty currency KPI | Formatted string | Return raw number |
| "Invalid spec version" | Wrong version | KPI=2, Chart=3, Table=2 |
| Drift metrics all 0% | Using `avg_delta` | Use custom drift columns (e.g., `success_rate_drift`) |
| Flat drift trend line | Wrong drift query | Filter `column_name = ':table'`, `slice_key IS NULL` |

---

## 📁 Project Structure

```
src/dashboards/
├── deploy_dashboards.py           # Deployment script
├── validate_dashboard_queries.py  # SQL validation
├── validate_widget_encodings.py   # Widget alignment
├── cost.lvdash.json              # Cost dashboard
├── performance.lvdash.json       # Performance dashboard
├── reliability.lvdash.json       # Reliability dashboard
├── security.lvdash.json          # Security dashboard
├── quality.lvdash.json           # Quality dashboard
└── unified.lvdash.json           # Executive summary

docs/dashboards/
└── dashboard-changelog.md         # Change tracking
```

---

## 📚 Widget Version Reference

| Widget Type | Version | Notes |
|-------------|---------|-------|
| Counter (KPI) | 2 | No `period` encoding |
| Bar Chart | 3 | MUST have `scale` on both `x` and `y` |
| Line Chart | 3 | |
| Area Chart | 3 | Use `stack: "zero"` |
| Pie Chart | 3 | MUST have `scale` |
| Table | 2 | Remove v1 properties |
| All Filters | 2 | |

---

## 📖 References

### Official Documentation
- [AI/BI Dashboards](https://docs.databricks.com/dashboards/lakeview/)
- [System Tables](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring/)

### Cursor Rules
- [databricks-aibi-dashboards.mdc](.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)
- [lakehouse-monitoring-comprehensive.mdc](.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

### Project Files
- [Dashboard Changelog](docs/dashboards/dashboard-changelog.md)

---

## Summary

**Critical Rules (Memorize These):**
1. Widget `fieldName` MUST match query alias exactly
2. `number-percent` expects 0-1, multiplies by 100
3. Never use `FORMAT_NUMBER()` in KPI queries
4. Parameters MUST be defined in dataset's `parameters` array
5. Monitoring tables: use `window.start`, select custom metrics as columns directly
6. Pie charts: MUST have `scale` on both `color` and `angle`
7. Bar charts: MUST have `scale` on both `x` and `y`
8. Tables: use version 2, remove legacy properties
9. **ALWAYS validate SQL before deployment** - reduces dev loop time by 90%
10. **Drift metrics**: Use DIRECT columns (e.g., `success_rate_drift`), NOT `avg_delta`!

**Time Estimate:** 2-4 hours for a complete dashboard

**Version:** 3.1 (January 2026) - Added pre-deployment SQL validation patterns for 90% faster dev loops
