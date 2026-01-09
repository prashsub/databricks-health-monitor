# Cost Domain - Actual Implementation

## Overview

**Dashboard:** `cost.lvdash.json`  
**Total Datasets:** 61  
**Primary Tables:**
- `fact_usage` (usage events with cost)
- `fact_usage_profile_metrics` (Lakehouse Monitoring aggregated metrics)
- `fact_usage_drift_metrics` (week-over-week drift detection)
- `dim_workspace` (workspace metadata)
- `dim_user` (user lookup for owner resolution)

---

## 📊 Metrics Catalog

### Financial KPIs

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **MTD Spend** | `SUM(list_cost)` WHERE usage_date >= month start | fact_usage | KPI card |
| **30-Day Spend** | `SUM(list_cost)` last 30 days | fact_usage | KPI card |
| **Daily Cost** | `SUM(list_cost)` GROUP BY usage_date | fact_usage | Line chart |
| **Total DBUs** | `SUM(usage_quantity)` | fact_usage | KPI card |
| **Average Cost per DBU** | `SUM(list_cost) / SUM(usage_quantity)` | fact_usage | KPI card |
| **YTD Spend** | `SUM(list_cost)` WHERE year = current year | fact_usage | KPI card |
| **Run Rate** | `(MTD spend / days elapsed) * days in month` | fact_usage | KPI card |

### Growth & Trend Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **30 vs 60 Day Growth %** | `((last_30 - prev_30) / prev_30) * 100` | fact_usage | KPI with trend |
| **WoW Growth %** | `((this_week - last_week) / last_week) * 100` | fact_usage | Line chart |
| **MoM Growth %** | `((this_month - last_month) / last_month) * 100` | fact_usage | Bar chart |
| **Cost Drift %** | Week-over-week change from monitor | fact_usage_drift_metrics | KPI card |

### Adoption Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **Serverless Adoption %** | `(serverless_cost / total_cost) * 100` | fact_usage | Gauge |
| **Tag Coverage %** | `(tagged_cost / total_cost) * 100` | fact_usage | Gauge |
| **DLT Adoption %** | `(dlt_cost / total_cost) * 100` | fact_usage | KPI card |

### Resource Utilization

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **Unique Users** | `COUNT(DISTINCT identity_metadata_run_as)` | fact_usage | KPI card |
| **Unique Jobs** | `COUNT(DISTINCT usage_metadata_job_id)` | fact_usage | KPI card |
| **Unique Job Runs** | `COUNT(DISTINCT usage_metadata_job_run_id)` | fact_usage | KPI card |
| **Top Workspaces** | `SUM(list_cost)` GROUP BY workspace_name | fact_usage + dim_workspace | Bar chart |
| **Top Owners** | `SUM(list_cost)` GROUP BY run_as | fact_usage + dim_user | Table |

### Optimization Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **Jobs on All-Purpose %** | `(ap_jobs_cost / total_jobs_cost) * 100` | fact_usage | KPI card |
| **Savings Potential $** | Estimated savings from rightsizing | ML model | KPI card |
| **Stale Dataset Cost** | Cost of tables unused >90 days | fact_usage + lineage | Table |
| **Repair Cost $** | Cost of job repairs/retries | fact_usage | KPI card |
| **Failure Cost $** | Cost of failed job runs | fact_usage | KPI card |

### Budget & Commitment Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **YTD vs Commit %** | `(ytd_spend / annual_commit) * 100` | fact_usage | Gauge |
| **Projected Year-End** | Linear forecast from current run rate | ML model | KPI card |
| **Commit Utilization %** | Current usage vs commitment | fact_usage | Gauge |
| **Variance $** | Projected - committed amount | ML model | KPI card |
| **Days to Budget** | Days until budget exhausted | ML model | KPI card |

---

## 🗃️ Dataset Catalog

### KPI Metrics (2 datasets)

#### ds_kpi_mtd
**Purpose:** Month-to-date total spend  
**Type:** Single-value KPI  
**Refresh:** Real-time  
**Query:**
```sql
SELECT 
  CONCAT('$', FORMAT_NUMBER(SUM(list_cost), 0)) AS mtd_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
```

#### ds_kpi_30d
**Purpose:** Last 30 days total spend  
**Type:** Single-value KPI  
**Parameters:** `time_range` (date range filter)  
**Query:**
```sql
SELECT 
  CONCAT('$', FORMAT_NUMBER(SUM(list_cost), 0)) AS total_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

---

### Analytics & Reporting (33 datasets)

#### ds_30_60_compare
**Purpose:** Growth rate comparing last 30 days to previous 30 days  
**Type:** Percentage comparison  
**Query:**
```sql
WITH periods AS (
  SELECT 
    SUM(CASE WHEN usage_date BETWEEN :time_range.min AND :time_range.max 
        THEN list_cost ELSE 0 END) AS last_30,
    SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 60 DAYS 
        AND CURRENT_DATE() - INTERVAL 31 DAYS 
        THEN list_cost ELSE 0 END) AS prev_30
  FROM ${catalog}.${gold_schema}.fact_usage
)
SELECT 
  CONCAT(ROUND((last_30 - prev_30) * 100.0 / NULLIF(prev_30, 0), 1), '%') AS growth_pct
FROM periods
```

#### ds_tag_coverage
**Purpose:** Percentage of cost with governance tags  
**Type:** Percentage KPI  
**Query:**
```sql
SELECT 
  CONCAT(ROUND(
    SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) * 100.0 / 
    NULLIF(SUM(list_cost), 0), 
  1), '%') AS coverage_pct
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

#### ds_serverless_adoption
**Purpose:** Percentage of cost from serverless compute  
**Type:** Percentage KPI  
**Query:**
```sql
SELECT 
  CONCAT(ROUND(
    SUM(CASE WHEN (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') 
        THEN list_cost ELSE 0 END) * 100.0 / 
    NULLIF(SUM(list_cost), 0), 
  1), '%') AS serverless_pct
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

#### ds_daily_cost
**Purpose:** Daily cost trend with serverless vs classic breakdown  
**Type:** Time series  
**Query:**
```sql
SELECT 
  DATE(usage_date) AS usage_date,
  SUM(list_cost) AS daily_cost,
  SUM(CASE WHEN (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') 
      THEN list_cost ELSE 0 END) AS serverless_cost,
  SUM(CASE WHEN NOT (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') 
      THEN list_cost ELSE 0 END) AS classic_cost
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY DATE(usage_date)
ORDER BY usage_date
```

#### ds_top_workspaces
**Purpose:** Top 10 workspaces by cost with user and job counts  
**Type:** Ranked table  
**Query:**
```sql
SELECT 
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
  ROUND(SUM(f.list_cost), 2) AS total_cost,
  COUNT(DISTINCT f.identity_metadata_run_as) AS unique_users,
  COUNT(DISTINCT f.usage_metadata_job_id) AS job_count,
  COUNT(DISTINCT f.usage_metadata_job_run_id) AS job_runs
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING))
ORDER BY total_cost DESC
LIMIT 10
```

#### ds_sku_breakdown
**Purpose:** Cost breakdown by billing origin product (SKU)  
**Type:** Category breakdown  
**Query:**
```sql
SELECT 
  COALESCE(billing_origin_product, 'Unknown') AS product,
  ROUND(SUM(f.list_cost), 2) AS total_cost
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY billing_origin_product
ORDER BY total_cost DESC
LIMIT 10
```

#### ds_top_owners
**Purpose:** Top cost drivers by user/owner  
**Type:** Ranked table  
**Query:**
```sql
SELECT 
  COALESCE(u.email, f.identity_metadata_run_as, 'Unknown') AS owner,
  ROUND(SUM(f.list_cost), 2) AS total_cost,
  COUNT(DISTINCT f.usage_metadata_job_id) AS job_count,
  COUNT(DISTINCT f.usage_metadata_job_run_id) AS job_runs,
  ROUND(AVG(f.list_cost), 2) AS avg_cost_per_run
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON f.identity_metadata_run_as = u.user_id
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY COALESCE(u.email, f.identity_metadata_run_as, 'Unknown')
ORDER BY total_cost DESC
LIMIT 20
```

#### ds_expensive_jobs
**Purpose:** Top 20 most expensive jobs  
**Type:** Ranked table  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.email, f.identity_metadata_run_as, 'Unknown') AS owner,
  ROUND(SUM(f.list_cost), 2) AS total_cost,
  COUNT(DISTINCT f.usage_metadata_job_run_id) AS run_count,
  ROUND(AVG(f.list_cost), 2) AS avg_cost_per_run
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
  ON f.usage_metadata_job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
  ON f.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON f.identity_metadata_run_as = u.user_id
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
  AND f.usage_metadata_job_id IS NOT NULL
GROUP BY 
  COALESCE(j.job_name, CAST(f.usage_metadata_job_id AS STRING)),
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)),
  COALESCE(u.email, f.identity_metadata_run_as, 'Unknown')
ORDER BY total_cost DESC
LIMIT 20
```

#### ds_wow_growth
**Purpose:** Week-over-week cost growth trend  
**Type:** Time series with growth rate  
**Query:**
```sql
WITH weekly AS (
  SELECT 
    DATE_TRUNC('week', usage_date) AS week_start,
    SUM(list_cost) AS weekly_cost,
    COUNT(DISTINCT DATE(usage_date)) AS days
  FROM ${catalog}.${gold_schema}.fact_usage f
  LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
  WHERE usage_date BETWEEN :time_range.min AND :time_range.max
  GROUP BY DATE_TRUNC('week', usage_date)
  HAVING days = 7  -- Only complete weeks
),
with_growth AS (
  SELECT 
    week_start,
    weekly_cost,
    100 * (weekly_cost - LAG(weekly_cost) OVER (ORDER BY week_start)) / 
      NULLIF(LAG(weekly_cost) OVER (ORDER BY week_start), 0) AS growth_pct
  FROM weekly
)
SELECT * FROM with_growth
WHERE growth_pct IS NOT NULL
ORDER BY week_start
```

---

### Tag Compliance (6 datasets)

#### ds_spend_by_tag
**Purpose:** Cost breakdown by tag status (tagged vs untagged)  
**Type:** Category breakdown  
**Widget:** Pie chart  
**Query:**
```sql
SELECT 
  CASE WHEN is_tagged THEN 'Tagged' ELSE 'Untagged' END AS tag_status,
  ROUND(SUM(list_cost), 2) AS total_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY CASE WHEN is_tagged THEN 'Tagged' ELSE 'Untagged' END
```

#### ds_spend_by_tag_values
**Purpose:** Cost breakdown by individual tag key-value pairs  
**Type:** Category breakdown  
**Widget:** Bar chart  
**Query:**
```sql
SELECT 
  tag_key,
  tag_value,
  ROUND(SUM(list_cost), 2) AS total_cost,
  COUNT(DISTINCT workspace_id) AS workspace_count
FROM ${catalog}.${gold_schema}.fact_usage
LATERAL VIEW EXPLODE(custom_tags) tags AS tag_key, tag_value
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
  AND tag_key IS NOT NULL 
  AND tag_value IS NOT NULL
GROUP BY tag_key, tag_value
ORDER BY total_cost DESC
LIMIT 20
```

#### ds_untagged_cost
**Purpose:** Total cost from untagged resources  
**Type:** KPI  
**Query:**
```sql
SELECT 
  CONCAT('$', FORMAT_NUMBER(SUM(CASE WHEN NOT is_tagged THEN list_cost ELSE 0 END), 0)) AS untagged_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

#### ds_no_tags_jobs
**Purpose:** Jobs without tags for governance remediation  
**Type:** Table  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.email, f.identity_metadata_run_as, 'Unknown') AS owner,
  ROUND(SUM(f.list_cost), 2) AS total_cost,
  COUNT(DISTINCT f.usage_metadata_job_run_id) AS run_count
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
  ON f.usage_metadata_job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
  ON f.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON f.identity_metadata_run_as = u.user_id
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
  AND NOT f.is_tagged
  AND f.usage_metadata_job_id IS NOT NULL
GROUP BY 
  COALESCE(j.job_name, CAST(f.usage_metadata_job_id AS STRING)),
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)),
  COALESCE(u.email, f.identity_metadata_run_as, 'Unknown')
ORDER BY total_cost DESC
LIMIT 50
```

---

### Budget & Commitments (3 datasets)

#### ds_ytd_spend
**Purpose:** Year-to-date total spend  
**Type:** KPI  
**Query:**
```sql
SELECT 
  CONCAT('$', FORMAT_NUMBER(SUM(list_cost), 0)) AS ytd_spend
FROM ${catalog}.${gold_schema}.fact_usage
WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())
```

#### ds_cumulative_vs_commit
**Purpose:** Monthly cumulative spend vs annual commitment  
**Type:** Area chart comparing actuals to linear commitment burn  
**Parameters:** `commitment_amount` (annual contract value)  
**Query:**
```sql
WITH monthly_spend AS (
  SELECT 
    DATE_TRUNC('month', usage_date) AS month,
    SUM(list_cost) AS monthly_cost
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())
  GROUP BY DATE_TRUNC('month', usage_date)
),
cumulative AS (
  SELECT 
    month,
    monthly_cost,
    SUM(monthly_cost) OVER (ORDER BY month) AS cumulative_spend
  FROM monthly_spend
)
SELECT 
  month,
  cumulative_spend AS actual_spend,
  (:commitment_amount / 12) * ROW_NUMBER() OVER (ORDER BY month) AS committed_spend
FROM cumulative
ORDER BY month
```

#### ds_commit_status
**Purpose:** Current commitment utilization summary  
**Type:** Summary KPIs  
**Parameters:** `commitment_amount`  
**Query:**
```sql
WITH ytd AS (
  SELECT SUM(list_cost) AS ytd_spend
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())
),
days AS (
  SELECT 
    DATEDIFF(CURRENT_DATE(), DATE_TRUNC('year', CURRENT_DATE())) AS days_elapsed,
    DATEDIFF(DATE_TRUNC('year', CURRENT_DATE() + INTERVAL 1 YEAR), DATE_TRUNC('year', CURRENT_DATE())) AS days_in_year
)
SELECT 
  y.ytd_spend,
  :commitment_amount AS annual_commit,
  ROUND((y.ytd_spend / :commitment_amount) * 100, 1) AS utilization_pct,
  ROUND((y.ytd_spend / d.days_elapsed) * d.days_in_year, 0) AS projected_year_end,
  ROUND(((y.ytd_spend / d.days_elapsed) * d.days_in_year) - :commitment_amount, 0) AS projected_variance
FROM ytd y, days d
```

---

### Lakehouse Monitoring (9 datasets)

#### ds_monitor_summary
**Purpose:** Latest monitor metrics snapshot  
**Type:** Table of key metrics  
**Source:** `fact_usage_profile_metrics`  
**Query:**
```sql
SELECT 
  column_name AS metric_name,
  ROUND(CAST(column_values.aggregate_metrics['sum'] AS DOUBLE), 2) AS value,
  window_start_time AS as_of_time
FROM ${catalog}.${gold_schema}.fact_usage_profile_metrics
WHERE column_name = ':table'  -- Table-level metrics only
  AND window_start_time = (
    SELECT MAX(window_start_time) 
    FROM ${catalog}.${gold_schema}.fact_usage_profile_metrics
  )
ORDER BY metric_name
```

#### ds_monitor_cost_aggregate
**Purpose:** Custom aggregate metrics from Lakehouse Monitoring  
**Type:** Table  
**Source:** `fact_usage_profile_metrics`  
**Query:**
```sql
SELECT 
  window_start_time AS date,
  ROUND(CAST(column_values.aggregate_metrics['sum'] AS DOUBLE), 2) AS total_cost,
  ROUND(CAST(column_values.aggregate_metrics['avg'] AS DOUBLE), 2) AS avg_cost,
  ROUND(CAST(column_values.aggregate_metrics['max'] AS DOUBLE), 2) AS max_cost
FROM ${catalog}.${gold_schema}.fact_usage_profile_metrics
WHERE column_name = 'total_daily_cost'
  AND window_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY window_start_time DESC
```

#### ds_monitor_drift
**Purpose:** Week-over-week drift metrics  
**Type:** Table showing % change in key metrics  
**Source:** `fact_usage_drift_metrics`  
**Query:**
```sql
SELECT 
  column_name AS metric_name,
  ROUND(CAST(drift_values.drift_metrics['absolute_diff'] AS DOUBLE), 2) AS absolute_change,
  ROUND(CAST(drift_values.drift_metrics['percent_diff'] AS DOUBLE), 2) AS percent_change,
  drift_type,
  window_start_time
FROM ${catalog}.${gold_schema}.fact_usage_drift_metrics
WHERE window_start_time = (
  SELECT MAX(window_start_time)
  FROM ${catalog}.${gold_schema}.fact_usage_drift_metrics
)
ORDER BY ABS(CAST(drift_values.drift_metrics['percent_diff'] AS DOUBLE)) DESC
LIMIT 10
```

---

### ML Predictions (8 datasets)

#### ds_ml_anomalies
**Purpose:** Cost anomalies detected by ML model  
**Type:** Alerts table  
**Source:** ML model predictions  
**Query:**
```sql
SELECT 
  usage_date,
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
  COALESCE(j.job_name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name,
  ROUND(f.list_cost, 2) AS actual_cost,
  ROUND(p.prediction, 2) AS expected_cost,
  ROUND(p.anomaly_score, 2) AS anomaly_score,
  p.anomaly_severity AS severity
FROM ${catalog}.${gold_schema}.fact_usage f
INNER JOIN ${catalog}.${feature_schema}.cost_anomaly_predictions p
  ON f.workspace_id = p.workspace_id
  AND f.usage_metadata_job_id = p.job_id
  AND f.usage_date = p.usage_date
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.usage_metadata_job_id = j.job_id
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
  AND p.anomaly_score > 0.7  -- High confidence anomalies only
ORDER BY p.anomaly_score DESC, f.list_cost DESC
LIMIT 50
```

#### ds_ml_budget_alerts
**Purpose:** Budget exhaustion predictions and alerts  
**Type:** Alerts table  
**Source:** ML model predictions  
**Query:**
```sql
SELECT 
  workspace_name,
  ROUND(current_spend, 2) AS current_spend,
  ROUND(predicted_mtd, 2) AS predicted_mtd,
  ROUND(budget_amount, 2) AS budget_amount,
  days_to_budget,
  alert_severity,
  recommended_action
FROM ${catalog}.${feature_schema}.budget_alert_predictions
WHERE alert_date = CURRENT_DATE()
  AND alert_severity IN ('High', 'Critical')
ORDER BY days_to_budget ASC, current_spend DESC
```

#### ds_ml_tag_recs
**Purpose:** Tag recommendations for untagged resources  
**Type:** Recommendations table  
**Source:** ML model predictions  
**Query:**
```sql
SELECT 
  job_name,
  workspace_name,
  ROUND(total_cost, 2) AS total_cost,
  recommended_tag_key,
  recommended_tag_value,
  ROUND(confidence_score, 2) AS confidence,
  reasoning
FROM ${catalog}.${feature_schema}.tag_recommendation_predictions
WHERE prediction_date = CURRENT_DATE()
  AND confidence_score > 0.6
  AND total_cost > 10  -- Focus on material cost items
ORDER BY total_cost DESC, confidence_score DESC
LIMIT 50
```

#### ds_ml_migration_recs
**Purpose:** Serverless migration recommendations  
**Type:** Recommendations table  
**Source:** ML model predictions  
**Query:**
```sql
SELECT 
  job_name,
  workspace_name,
  current_compute_type,
  recommended_compute_type,
  ROUND(current_monthly_cost, 2) AS current_cost,
  ROUND(estimated_serverless_cost, 2) AS serverless_cost,
  ROUND(estimated_monthly_savings, 2) AS monthly_savings,
  ROUND(confidence_score, 2) AS confidence,
  migration_complexity,
  blockers
FROM ${catalog}.${feature_schema}.serverless_migration_predictions
WHERE prediction_date = CURRENT_DATE()
  AND estimated_monthly_savings > 50  -- Minimum $50/month savings
  AND migration_complexity != 'High'
ORDER BY estimated_monthly_savings DESC, confidence_score DESC
LIMIT 30
```

---

## 🔍 SQL Query Patterns

### Common Join Patterns

#### Workspace Enrichment
```sql
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
  ON f.workspace_id = w.workspace_id
```

#### Job Enrichment
```sql
LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
  ON f.usage_metadata_job_id = j.job_id
```

#### Owner Resolution
```sql
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON f.identity_metadata_run_as = u.user_id
```

#### Complete Enrichment Pattern
```sql
FROM ${catalog}.${gold_schema}.fact_usage f
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.usage_metadata_job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u ON f.identity_metadata_run_as = u.user_id
```

### Time Filtering Patterns

#### Date Range Parameter
```sql
WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

#### Month-to-Date
```sql
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
```

#### Year-to-Date
```sql
WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())
```

#### Last N Days
```sql
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
```

#### Complete Weeks Only
```sql
WITH weekly AS (
  SELECT 
    DATE_TRUNC('week', usage_date) AS week_start,
    COUNT(DISTINCT DATE(usage_date)) AS days
  GROUP BY week_start
  HAVING days = 7  -- Only complete weeks
)
```

### Aggregation Patterns

#### Conditional Aggregation
```sql
SELECT 
  SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) AS tagged_cost,
  SUM(CASE WHEN NOT is_tagged THEN list_cost ELSE 0 END) AS untagged_cost
```

#### Growth Calculation
```sql
SELECT 
  metric_value,
  LAG(metric_value) OVER (ORDER BY date) AS prev_value,
  100 * (metric_value - LAG(metric_value) OVER (ORDER BY date)) / 
    NULLIF(LAG(metric_value) OVER (ORDER BY date), 0) AS growth_pct
```

#### Cumulative Sum
```sql
SELECT 
  date,
  daily_value,
  SUM(daily_value) OVER (ORDER BY date) AS cumulative_value
```

### Tag Processing Pattern

#### Explode Custom Tags Map
```sql
SELECT 
  workspace_id,
  tag_key,
  tag_value,
  SUM(list_cost) AS total_cost
FROM ${catalog}.${gold_schema}.fact_usage
LATERAL VIEW EXPLODE(custom_tags) tags AS tag_key, tag_value
WHERE tag_key IS NOT NULL AND tag_value IS NOT NULL
GROUP BY workspace_id, tag_key, tag_value
```

### Null Handling Pattern

#### Display Name with Fallback
```sql
COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name
COALESCE(j.job_name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name
COALESCE(u.email, f.identity_metadata_run_as, 'Unknown') AS owner
```

#### Safe Division
```sql
value1 * 100.0 / NULLIF(value2, 0) AS percentage
```

---

## 📑 Data Source Reference

### fact_usage Columns Used

| Column | Type | Purpose | Example Usage |
|--------|------|---------|---------------|
| `usage_date` | DATE | Time dimension | Daily aggregations, trends |
| `workspace_id` | BIGINT | Workspace FK | Group by workspace |
| `list_cost` | DECIMAL | Cost amount | SUM for totals |
| `usage_quantity` | DECIMAL | DBU amount | DBU calculations |
| `sku_name` | STRING | Product type | Serverless detection |
| `billing_origin_product` | STRING | Billing category | Product breakdowns |
| `identity_metadata_run_as` | STRING | User ID | Owner attribution |
| `usage_metadata_job_id` | BIGINT | Job ID FK | Job-level analytics |
| `usage_metadata_job_run_id` | BIGINT | Run ID | Run count |
| `custom_tags` | MAP<STRING,STRING> | Tag key-values | Tag compliance |
| `is_tagged` | BOOLEAN | Tag flag | Tag coverage |

### dim_workspace Columns Used

| Column | Type | Purpose |
|--------|------|---------|
| `workspace_id` | BIGINT | PK |
| `workspace_name` | STRING | Display name |
| `workspace_url` | STRING | Link |
| `is_active` | BOOLEAN | Filter inactive |

### dim_user Columns Used

| Column | Type | Purpose |
|--------|------|---------|
| `user_id` | STRING | PK |
| `email` | STRING | Display name |
| `display_name` | STRING | Friendly name |

### dim_job Columns Used

| Column | Type | Purpose |
|--------|------|---------|
| `job_id` | BIGINT | PK |
| `job_name` | STRING | Display name |
| `creator_id` | STRING | Owner FK |

---

## 🎯 Optimization Opportunities Identified

### Current Query Patterns
1. **Repeated joins** - workspace/job/user joins in almost every query
2. **Tag explosion** - LATERAL VIEW EXPLODE used frequently
3. **Window functions** - LAG/LEAD for growth calculations
4. **Date filtering** - Consistent time_range parameter

### Recommended Optimizations
1. Create materialized view with pre-joined dimensions
2. Pre-aggregate daily metrics with tags expanded
3. Index on (usage_date, workspace_id, job_id)
4. Partition fact_usage by usage_date (month)

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial comprehensive documentation |

