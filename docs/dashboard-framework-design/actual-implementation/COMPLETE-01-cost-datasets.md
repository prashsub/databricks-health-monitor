# Complete Cost Management Dataset Catalog

## Overview
**Total Datasets:** 61  
**Dashboard:** `cost.lvdash.json`  
**Coverage:** ALL datasets from ALL pages with FULL details

---

## Dataset Index

| # | Dataset Name | Display Name | Has Query | Parameters |
|---|--------------|--------------|-----------|------------|
| 1 | ds_kpi_mtd | KPI: MTD Spend | ✅ | time_range |
| 2 | ds_kpi_30d | KPI: 30d Spend | ✅ | time_range |
| 3 | ds_30_60_compare | 30 vs 60 Day Compare | ✅ | time_range |
| 4 | ds_tag_coverage | Tag Coverage | ✅ | time_range |
| 5 | ds_serverless_adoption | Serverless Adoption | ✅ | time_range |
| 6 | ds_unique_counts | Unique Counts | ✅ | time_range |
| 7 | ds_wow_growth | WoW Growth | ✅ | time_range, param_workspace |
| 8 | ds_daily_cost | Daily Cost | ✅ | time_range, param_workspace |
| 9 | ds_top_workspaces | Top Workspaces | ✅ | time_range, param_workspace |
| 10 | ds_sku_breakdown | Billing Origin Product Breakdown | ✅ | time_range, param_workspace, param_sku |
| 11 | ds_top_owners | Top Owners | ✅ | time_range, param_workspace, param_sku |
| 12 | ds_spend_by_tag | Spend by Tag | ✅ | - |
| 13 | ds_spend_by_tag_values | Spend by Tag Values | ✅ | - |
| 14 | ds_highest_change_users | Highest Change Users | ✅ | time_range |
| 15 | ds_untagged_cost | Untagged Cost | ✅ | time_range, param_workspace |
| 16 | ds_expensive_jobs | Expensive Jobs | ✅ | time_range, param_workspace |
| 17 | ds_expensive_runs | Expensive Runs | ✅ | time_range, param_workspace |
| 18 | ds_highest_change_jobs | Highest Change Jobs | ✅ | time_range, param_workspace |
| 19 | ds_outlier_runs | Outlier Runs | ✅ | time_range, param_workspace |
| 20 | ds_failure_cost | Failure Cost | ✅ | time_range, param_workspace |
| 21 | ds_repair_cost | Repair Cost | ✅ | time_range |
| 22 | ds_stale_datasets | Stale Datasets | ✅ | time_range |
| 23 | ds_ap_cluster_jobs | AP Cluster Jobs | ✅ | time_range |
| 24 | ds_no_autoscale | No Autoscale Jobs | ✅ | time_range |
| 25 | ds_low_dbr_jobs | Low DBR Jobs | ✅ | time_range |
| 26 | ds_no_tags_jobs | No Tags Jobs | ✅ | time_range, param_workspace |
| 27 | ds_savings_potential | Savings Potential | ✅ | time_range |
| 28 | ds_ml_cost_forecast | ML: Cost Forecast | ✅ | - |
| 29 | ds_ml_anomalies | ML: Cost Anomalies | ✅ | time_range, param_workspace, param_sku |
| 30 | ds_ml_budget_alerts | ML: Budget Alerts | ✅ | param_workspace |
| 31 | ds_ml_tag_recs | ML: Tag Recommendations | ✅ | - |
| 32 | ds_ml_user_behavior | ML: User Behavior | ✅ | - |
| 33 | ds_ml_migration_recs | ML: Migration Recs | ✅ | - |
| 34 | ds_monitor_cost_trend | Monitor: Cost Trend | ✅ | time_range |
| 35 | ds_monitor_serverless | Monitor: Serverless | ✅ | time_range |
| 36 | ds_monitor_drift | Monitor: Drift | ✅ | time_range |
| 37 | ds_monitor_summary | Monitor: Summary | ✅ | time_range |
| 38 | ds_commit_options | Commit Amount Options | ✅ | - |
| 39 | ds_ytd_spend | YTD Spend | ✅ | time_range |
| 40 | ds_commit_status | Commit Status | ✅ | annual_commit, time_range |
| 41 | ds_forecast_summary | Forecast Summary | ✅ | time_range |
| 42 | ds_variance | Projected Variance | ✅ | time_range, annual_commit |
| 43 | ds_run_rate | Run Rate | ✅ | time_range |
| 44 | ds_usage_forecast | Usage vs Forecast | ✅ | time_range |
| 45 | ds_cumulative_vs_commit | Cumulative vs Commit | ✅ | annual_commit, time_range |
| 46 | ds_monthly_breakdown | Monthly Breakdown | ✅ | time_range, annual_commit |
| 47 | ds_monthly_detail | Monthly Detail | ✅ | time_range, annual_commit |
| 48 | ds_ml_budget_forecast | ML: Budget Forecast | ✅ | - |
| 49 | ds_ml_commitment_rec | ML: Commitment Recommendations | ✅ | - |
| 50 | ds_time_windows | Time Windows | ✅ | - |
| 51 | ds_workspaces | Workspaces | ✅ | param_workspace |
| 52 | select_workspace | select_workspace | ✅ | param_workspace |
| 53 | select_time_key | select_time_key | ✅ | - |
| 54 | ds_select_workspace | ds_select_workspace | ✅ | - |
| 55 | ds_select_sku | ds_select_sku | ✅ | - |
| 56 | ds_select_tag_status | ds_select_tag_status | ✅ | - |
| 57 | ds_monitor_cost_aggregate | Cost Aggregate Metrics | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 58 | ds_monitor_cost_derived | Cost Derived KPIs | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 59 | ds_monitor_cost_drift | Cost Drift Metrics | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 60 | ds_monitor_cost_slice_keys | Cost Slice Keys | ✅ | monitor_time_start, monitor_time_end |
| 61 | ds_monitor_cost_slice_values | Cost Slice Values | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |

---

## Complete SQL Queries


### Dataset 1: ds_kpi_mtd

**Display Name:** KPI: MTD Spend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT('$', FORMAT_NUMBER(SUM(list_cost), 0)) AS mtd_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
```

---

### Dataset 2: ds_kpi_30d

**Display Name:** KPI: 30d Spend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT('$', FORMAT_NUMBER(SUM(list_cost), 0)) AS total_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 3: ds_30_60_compare

**Display Name:** 30 vs 60 Day Compare  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH periods AS (SELECT SUM(CASE WHEN usage_date BETWEEN :time_range.min AND :time_range.max THEN list_cost ELSE 0 END) AS last_30, SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 60 DAYS AND CURRENT_DATE() - INTERVAL 31 DAYS THEN list_cost ELSE 0 END) AS prev_30 FROM ${catalog}.${gold_schema}.fact_usage) SELECT CONCAT(ROUND((last_30 - prev_30) * 100.0 / NULLIF(prev_30, 0), 1), '%') AS growth_pct FROM periods
```

---

### Dataset 4: ds_tag_coverage

**Display Name:** Tag Coverage  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT(ROUND(SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1), '%') AS coverage_pct FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 5: ds_serverless_adoption

**Display Name:** Serverless Adoption  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT(ROUND(SUM(CASE WHEN (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1), '%') AS serverless_pct FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 6: ds_unique_counts

**Display Name:** Unique Counts  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT identity_metadata_run_as) AS unique_users, COUNT(DISTINCT usage_metadata_job_id) AS unique_jobs FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 7: ds_wow_growth

**Display Name:** WoW Growth  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH weekly AS (SELECT DATE_TRUNC('week', usage_date) AS week_start, SUM(list_cost) AS weekly_cost, COUNT(DISTINCT DATE(usage_date)) AS days FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY 1 HAVING days = 7), with_growth AS (SELECT week_start, weekly_cost, 100 * (weekly_cost - LAG(weekly_cost) OVER (ORDER BY week_start)) / NULLIF(LAG(weekly_cost) OVER (ORDER BY week_start), 0) AS wow_growth_pct FROM weekly) SELECT week_start, ROUND(weekly_cost, 2) AS weekly_cost, ROUND(wow_growth_pct, 1) AS wow_growth_pct, ROUND(AVG(wow_growth_pct) OVER (ORDER BY week_start ROWS BETWEEN 12 PRECEDING AND CURRENT ROW), 1) AS moving_avg FROM with_growth ORDER BY week_start
```

---

### Dataset 8: ds_daily_cost

**Display Name:** Daily Cost  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT DATE(usage_date) AS usage_date, SUM(list_cost) AS daily_cost, SUM(CASE WHEN (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') THEN list_cost ELSE 0 END) AS serverless_cost, SUM(CASE WHEN NOT (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') THEN list_cost ELSE 0 END) AS classic_cost FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 9: ds_top_workspaces

**Display Name:** Top Workspaces  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name, ROUND(SUM(f.list_cost), 2) AS total_cost, COUNT(DISTINCT f.identity_metadata_run_as) AS unique_users, COUNT(DISTINCT f.usage_metadata_job_id) AS job_count, COUNT(DISTINCT f.usage_metadata_job_run_id) AS job_runs FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY total_cost DESC LIMIT 15
```

---

### Dataset 10: ds_sku_breakdown

**Display Name:** Billing Origin Product Breakdown  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_sku` (STRING) - param_sku

**SQL Query:**
```sql
SELECT COALESCE(billing_origin_product, 'Unknown') AS product, ROUND(SUM(f.list_cost), 2) AS total_cost FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY billing_origin_product ORDER BY total_cost DESC LIMIT 10
```

---

### Dataset 11: ds_top_owners

**Display Name:** Top Owners  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_sku` (STRING) - param_sku

**SQL Query:**
```sql
SELECT f.identity_metadata_run_as AS owner, ROUND(SUM(f.list_cost), 2) AS total_cost, ROUND(SUM(CASE WHEN f.sku_name LIKE '%JOBS%' THEN f.list_cost ELSE 0 END), 2) AS job_cost, ROUND(SUM(CASE WHEN f.usage_metadata_notebook_id IS NOT NULL THEN f.list_cost ELSE 0 END), 2) AS notebook_cost FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max AND f.identity_metadata_run_as IS NOT NULL GROUP BY 1 ORDER BY total_cost DESC LIMIT 20
```

---

### Dataset 12: ds_spend_by_tag

**Display Name:** Spend by Tag  
**SQL Query:**
```sql
SELECT CASE WHEN is_tagged THEN 'Tagged' ELSE 'Untagged' END AS tag_bucket, ROUND(SUM(list_cost), 2) AS total_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE 1=1 GROUP BY 1 ORDER BY total_cost DESC
```

---

### Dataset 13: ds_spend_by_tag_values

**Display Name:** Spend by Tag Values  
**SQL Query:**
```sql
-- Spend breakdown by actual tag key/value pairs
SELECT
  tag_key,
  tag_value,
  ROUND(SUM(list_cost), 2) AS total_cost,
  COUNT(*) AS usage_count
FROM (
  SELECT
    list_cost,
    EXPLODE(custom_tags) AS (tag_key, tag_value)
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE is_tagged = TRUE
    AND custom_tags IS NOT NULL
    AND usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
)
WHERE tag_key IS NOT NULL AND tag_value IS NOT NULL
GROUP BY 1, 2
HAVING SUM(list_cost) > 100
ORDER BY total_cost DESC
LIMIT 25
```

---

### Dataset 14: ds_highest_change_users

**Display Name:** Highest Change Users  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH user_spend AS (
  SELECT 
    identity_metadata_run_as AS owner, 
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS last_7d, 
    SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS THEN list_cost ELSE 0 END) AS prev_7d 
  FROM ${catalog}.${gold_schema}.fact_usage 
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
    AND identity_metadata_run_as IS NOT NULL
    AND identity_metadata_run_as NOT LIKE '%.gserviceaccount.com'
    AND identity_metadata_run_as NOT LIKE 'service-principal-%'
  GROUP BY 1
) 
SELECT 
  owner, 
  ROUND(last_7d, 2) AS last_7d, 
  ROUND(prev_7d, 2) AS prev_7d, 
  ROUND(last_7d - prev_7d, 2) AS growth,
  ROUND(100 * (last_7d - prev_7d) / NULLIF(prev_7d, 0), 1) AS growth_pct 
FROM user_spend 
WHERE prev_7d > 0 OR last_7d > 0
ORDER BY (last_7d - prev_7d) DESC 
LIMIT 10
```

---

### Dataset 15: ds_untagged_cost

**Display Name:** Untagged Cost  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name, f.identity_metadata_run_as AS owner, ROUND(SUM(f.list_cost), 2) AS untagged_cost FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max AND f.is_tagged = FALSE GROUP BY 1, 2 ORDER BY untagged_cost DESC LIMIT 20
```

---

### Dataset 16: ds_expensive_jobs

**Display Name:** Expensive Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT 
  COALESCE(j.name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name, 
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name, 
  COUNT(DISTINCT f.usage_metadata_job_run_id) AS runs, 
  ROUND(SUM(f.list_cost), 2) AS total_cost, 
  MAX(f.identity_metadata_run_as) AS owner,
  MAX(DATE(f.usage_date)) AS last_run
FROM ${catalog}.${gold_schema}.fact_usage f 
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.usage_metadata_job_id = j.job_id 
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id 
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max 
  AND f.usage_metadata_job_id IS NOT NULL 
GROUP BY 1, 2 
ORDER BY total_cost DESC 
LIMIT 25
```

---

### Dataset 17: ds_expensive_runs

**Display Name:** Expensive Runs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT 
  COALESCE(j.name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name, 
  CAST(f.usage_metadata_job_run_id AS STRING) AS run_id, 
  ROUND(SUM(f.list_cost), 2) AS run_cost, 
  MAX(DATE(f.usage_date)) AS run_date,
  MAX(f.identity_metadata_run_as) AS owner
FROM ${catalog}.${gold_schema}.fact_usage f 
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.usage_metadata_job_id = j.job_id 
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max 
  AND f.usage_metadata_job_run_id IS NOT NULL 
GROUP BY 1, 2 
ORDER BY run_cost DESC 
LIMIT 25
```

---

### Dataset 18: ds_highest_change_jobs

**Display Name:** Highest Change Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH job_spend AS (
  SELECT 
    COALESCE(j.name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name, 
    SUM(CASE WHEN f.usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS THEN f.list_cost ELSE 0 END) AS last_7d, 
    SUM(CASE WHEN f.usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND f.usage_date < CURRENT_DATE() - INTERVAL 7 DAYS THEN f.list_cost ELSE 0 END) AS prev_7d 
  FROM ${catalog}.${gold_schema}.fact_usage f 
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.usage_metadata_job_id = j.job_id 
  WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS
    AND f.usage_metadata_job_id IS NOT NULL 
  GROUP BY 1
) 
SELECT 
  job_name, 
  ROUND(last_7d, 2) AS last_7d, 
  ROUND(prev_7d, 2) AS prev_7d, 
  ROUND(last_7d - prev_7d, 2) AS growth,
  ROUND(100 * (last_7d - prev_7d) / NULLIF(prev_7d, 0), 1) AS growth_pct 
FROM job_spend 
WHERE prev_7d > 0 OR last_7d > 0
ORDER BY (last_7d - prev_7d) DESC 
LIMIT 10
```

---

### Dataset 19: ds_outlier_runs

**Display Name:** Outlier Runs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH run_costs AS (
  SELECT 
    COALESCE(j.name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name, 
    f.usage_metadata_job_run_id AS run_id, 
    SUM(f.list_cost) AS run_cost 
  FROM ${catalog}.${gold_schema}.fact_usage f 
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.usage_metadata_job_id = j.job_id 
  WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max 
    AND f.usage_metadata_job_run_id IS NOT NULL 
  GROUP BY 1, 2
), job_stats AS (
  SELECT 
    job_name, 
    COUNT(*) AS runs, 
    ROUND(AVG(run_cost), 2) AS avg_cost, 
    ROUND(MAX(run_cost), 2) AS max_cost, 
    ROUND(PERCENTILE_APPROX(run_cost, 0.9), 2) AS p90 
  FROM run_costs 
  GROUP BY 1
  HAVING COUNT(*) >= 3
) 
SELECT 
  job_name, 
  runs, 
  avg_cost, 
  max_cost, 
  p90,
  ROUND((max_cost - p90) / NULLIF(p90, 0) * 100, 0) AS deviation
FROM job_stats 
WHERE max_cost > p90 * 1.5
ORDER BY (max_cost - p90) DESC 
LIMIT 20
```

---

### Dataset 20: ds_failure_cost

**Display Name:** Failure Cost  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH job_runs AS (
  SELECT 
    f.workspace_id, 
    f.usage_metadata_job_id AS job_id, 
    f.usage_metadata_job_run_id AS run_id, 
    SUM(f.list_cost) AS run_cost 
  FROM ${catalog}.${gold_schema}.fact_usage f 
  WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max 
    AND f.usage_metadata_job_run_id IS NOT NULL 
  GROUP BY 1, 2, 3
), run_status AS (
  SELECT 
    jr.workspace_id,
    jr.job_id,
    jr.run_id,
    jr.run_cost,
    CASE WHEN t.result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END AS is_success
  FROM job_runs jr 
  LEFT JOIN ${catalog}.${gold_schema}.fact_job_run_timeline t 
    ON jr.workspace_id = t.workspace_id AND jr.job_id = t.job_id AND jr.run_id = t.run_id
), job_failure_costs AS (
  SELECT 
    rs.workspace_id,
    rs.job_id,
    SUM(CASE WHEN is_success = 0 THEN run_cost ELSE 0 END) AS failure_cost,
    SUM(CASE WHEN is_success = 0 THEN 1 ELSE 0 END) AS failures,
    COUNT(*) AS total_runs
  FROM run_status rs
  GROUP BY 1, 2
  HAVING SUM(CASE WHEN is_success = 0 THEN 1 ELSE 0 END) > 0
)
SELECT 
  COALESCE(j.name, CAST(jfc.job_id AS STRING)) AS job_name,
  ROUND(jfc.failure_cost, 2) AS failure_cost,
  jfc.failures,
  ROUND((jfc.total_runs - jfc.failures) * 100.0 / jfc.total_runs, 1) AS success_rate
FROM job_failure_costs jfc
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON jfc.workspace_id = j.workspace_id AND jfc.job_id = j.job_id
ORDER BY failure_cost DESC
LIMIT 15
```

---

### Dataset 21: ds_repair_cost

**Display Name:** Repair Cost  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_runs AS (
  SELECT 
    t.workspace_id,
    t.job_id,
    t.run_id,
    t.run_name,
    t.run_date,
    t.result_state,
    t.run_duration_minutes,
    ROW_NUMBER() OVER (PARTITION BY t.workspace_id, t.job_id, DATE(t.run_date) ORDER BY t.run_date) AS run_seq
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline t
  WHERE t.run_date BETWEEN :time_range.min AND :time_range.max
), repairs AS (
  SELECT 
    jr.workspace_id,
    jr.job_id,
    jr.run_id,
    jr.run_name,
    jr.run_duration_minutes
  FROM job_runs jr
  WHERE jr.run_seq > 1
    AND EXISTS (
      SELECT 1 FROM job_runs prev 
      WHERE prev.workspace_id = jr.workspace_id 
        AND prev.job_id = jr.job_id 
        AND DATE(prev.run_date) = DATE(jr.run_date)
        AND prev.run_seq < jr.run_seq
        AND prev.result_state NOT IN ('SUCCESS', 'SUCCEEDED')
    )
), repair_costs AS (
  SELECT 
    r.workspace_id,
    r.job_id,
    r.run_id,
    r.run_name,
    r.run_duration_minutes,
    COALESCE(SUM(f.list_cost), 0) AS repair_cost
  FROM repairs r
  LEFT JOIN ${catalog}.${gold_schema}.fact_usage f 
    ON r.workspace_id = f.workspace_id 
    AND r.job_id = f.usage_metadata_job_id 
    AND r.run_id = f.usage_metadata_job_run_id
  GROUP BY 1, 2, 3, 4, 5
)
SELECT 
  COALESCE(j.name, rc.run_name, CAST(rc.job_id AS STRING)) AS job_name,
  COUNT(*) AS repairs,
  ROUND(SUM(rc.repair_cost), 2) AS repair_cost,
  ROUND(SUM(rc.run_duration_minutes), 1) AS repair_time_min
FROM repair_costs rc
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON rc.workspace_id = j.workspace_id AND rc.job_id = j.job_id
GROUP BY 1
HAVING COUNT(*) > 0
ORDER BY repair_cost DESC
LIMIT 15
```

---

### Dataset 22: ds_stale_datasets

**Display Name:** Stale Datasets  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH writes AS (
  SELECT DISTINCT
    entity_metadata_job_id AS job_id,
    workspace_id,
    target_table_full_name AS table_name
  FROM ${catalog}.${gold_schema}.fact_table_lineage
  WHERE event_date BETWEEN :time_range.min AND :time_range.max
    AND target_table_full_name IS NOT NULL
    AND entity_metadata_job_id IS NOT NULL
), reads AS (
  SELECT DISTINCT source_table_full_name AS table_name
  FROM ${catalog}.${gold_schema}.fact_table_lineage
  WHERE event_date BETWEEN :time_range.min AND :time_range.max
    AND source_table_full_name IS NOT NULL
), unread_tables AS (
  SELECT w.job_id, w.workspace_id, w.table_name
  FROM writes w
  LEFT JOIN reads r ON w.table_name = r.table_name
  WHERE r.table_name IS NULL
), job_unread AS (
  SELECT 
    ut.workspace_id,
    ut.job_id,
    COUNT(DISTINCT ut.table_name) AS unused_tables
  FROM unread_tables ut
  GROUP BY 1, 2
)
SELECT 
  COALESCE(j.name, CAST(ju.job_id AS STRING)) AS job_name,
  ju.unused_tables,
  COALESCE(ROUND(SUM(f.list_cost), 2), 0) AS total_cost,
  MAX(DATE(f.usage_date)) AS last_run
FROM job_unread ju
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON ju.workspace_id = j.workspace_id AND ju.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.fact_usage f ON ju.workspace_id = f.workspace_id AND ju.job_id = f.usage_metadata_job_id
  AND f.usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY 1, 2
ORDER BY total_cost DESC
LIMIT 15
```

---

### Dataset 23: ds_ap_cluster_jobs

**Display Name:** AP Cluster Jobs  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_clusters AS (
  SELECT 
    t.workspace_id,
    t.job_id,
    EXPLODE(t.compute_ids) AS cluster_id,
    COUNT(DISTINCT t.run_id) AS task_runs
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline t
  WHERE t.run_date BETWEEN :time_range.min AND :time_range.max
    AND t.compute_ids IS NOT NULL
    AND SIZE(t.compute_ids) > 0
  GROUP BY 1, 2, 3
)
SELECT 
  COALESCE(j.name, CAST(jc.job_id AS STRING)) AS job_name,
  jc.cluster_id AS cluster_name,
  jc.task_runs,
  ROUND(COALESCE(SUM(f.list_cost), 0), 2) AS total_cost
FROM job_clusters jc
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON jc.workspace_id = j.workspace_id AND jc.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.fact_usage f ON jc.workspace_id = f.workspace_id AND jc.job_id = f.usage_metadata_job_id
  AND f.usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY 1, 2, 3
ORDER BY total_cost DESC
LIMIT 15
```

---

### Dataset 24: ds_no_autoscale

**Display Name:** No Autoscale Jobs  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_runs AS (
  SELECT 
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    f.usage_metadata_job_run_id AS run_id,
    SUM(f.list_cost) AS run_cost,
    SUM(f.usage_quantity) AS run_dbus
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
    AND f.usage_metadata_job_id IS NOT NULL
    AND f.usage_metadata_job_run_id IS NOT NULL
  GROUP BY 1, 2, 3
), job_stats AS (
  SELECT 
    workspace_id,
    job_id,
    COUNT(*) AS total_runs,
    ROUND(AVG(run_dbus), 0) AS avg_dbus,
    ROUND(STDDEV(run_dbus), 2) AS stddev_dbus,
    ROUND(SUM(run_cost), 2) AS total_cost
  FROM job_runs
  GROUP BY 1, 2
  HAVING COUNT(*) >= 5
)
SELECT 
  COALESCE(j.name, CAST(js.job_id AS STRING)) AS job_name,
  CAST(js.avg_dbus AS INT) AS worker_count,
  js.total_cost,
  COALESCE(j.run_as, 'Unknown') AS owner
FROM job_stats js
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON js.workspace_id = j.workspace_id AND js.job_id = j.job_id
WHERE js.stddev_dbus < js.avg_dbus * 0.1
ORDER BY js.total_cost DESC
LIMIT 15
```

---

### Dataset 25: ds_low_dbr_jobs

**Display Name:** Low DBR Jobs  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH old_jobs AS (
  SELECT 
    j.workspace_id,
    j.job_id,
    j.name AS job_name,
    j.change_time,
    j.run_as AS owner,
    DATEDIFF(CURRENT_DATE(), DATE(j.change_time)) AS days_since_update
  FROM ${catalog}.${gold_schema}.dim_job j
  WHERE j.delete_time IS NULL
    AND j.change_time IS NOT NULL
    AND j.change_time < CURRENT_DATE() - INTERVAL 180 DAYS
), job_costs AS (
  SELECT 
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    ROUND(SUM(f.list_cost), 2) AS total_cost
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
    AND f.usage_metadata_job_id IS NOT NULL
  GROUP BY 1, 2
)
SELECT 
  COALESCE(oj.job_name, CAST(oj.job_id AS STRING)) AS job_name,
  CONCAT(CAST(FLOOR(oj.days_since_update / 30) AS STRING), ' months old') AS dbr_version,
  COALESCE(jc.total_cost, 0) AS total_cost,
  COALESCE(oj.owner, 'Unknown') AS owner
FROM old_jobs oj
LEFT JOIN job_costs jc ON oj.workspace_id = jc.workspace_id AND oj.job_id = jc.job_id
WHERE jc.total_cost > 0
ORDER BY jc.total_cost DESC
LIMIT 15
```

---

### Dataset 26: ds_no_tags_jobs

**Display Name:** No Tags Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT COALESCE(j.name, CAST(f.usage_metadata_job_id AS STRING)) AS job_name, COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name, MAX(f.identity_metadata_run_as) AS owner FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.usage_metadata_job_id = j.job_id LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max AND f.usage_metadata_job_id IS NOT NULL AND f.is_tagged = FALSE GROUP BY 1, 2 ORDER BY COUNT(*) DESC LIMIT 20
```

---

### Dataset 27: ds_savings_potential

**Display Name:** Savings Potential  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_runs AS (
  SELECT 
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    f.usage_metadata_job_run_id AS run_id,
    SUM(f.list_cost) AS run_cost
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
    AND f.usage_metadata_job_id IS NOT NULL
    AND f.usage_metadata_job_run_id IS NOT NULL
  GROUP BY 1, 2, 3
), job_stats AS (
  SELECT 
    workspace_id,
    job_id,
    COUNT(*) AS total_runs,
    ROUND(MIN(run_cost), 2) AS min_cost,
    ROUND(AVG(run_cost), 2) AS avg_cost,
    ROUND(MAX(run_cost), 2) AS max_cost,
    ROUND(SUM(run_cost), 2) AS total_cost,
    ROUND((MAX(run_cost) - MIN(run_cost)) / NULLIF(AVG(run_cost), 0) * 100, 0) AS cost_variance_pct
  FROM job_runs
  GROUP BY 1, 2
  HAVING COUNT(*) >= 5 AND AVG(run_cost) > 0
)
SELECT 
  COALESCE(j.name, CAST(js.job_id AS STRING)) AS job_name,
  js.cost_variance_pct AS avg_cpu,
  js.total_cost,
  ROUND((js.total_cost - (js.total_runs * js.min_cost)), 2) AS max_savings
FROM job_stats js
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON js.workspace_id = j.workspace_id AND js.job_id = j.job_id
WHERE js.cost_variance_pct > 50
ORDER BY max_savings DESC
LIMIT 15
```

---

### Dataset 28: ds_ml_cost_forecast

**Display Name:** ML: Cost Forecast  
**SQL Query:**
```sql
WITH daily_avg AS (
  SELECT 
    ROUND(AVG(list_cost), 2) AS avg_daily_cost
  FROM (
    SELECT DATE(usage_date) AS day, SUM(list_cost) AS list_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    GROUP BY 1
  )
), forecast AS (
  SELECT DATE_ADD(CURRENT_DATE(), day_offset) AS forecast_date, day_offset
  FROM (SELECT EXPLODE(SEQUENCE(1, 30)) AS day_offset)
)
SELECT 
  f.forecast_date,
  ROUND(d.avg_daily_cost * (1 + (RAND() - 0.5) * 0.2), 2) AS forecasted_cost,
  ROUND(d.avg_daily_cost * 0.9, 2) AS lower_bound,
  ROUND(d.avg_daily_cost * 1.1, 2) AS upper_bound
FROM forecast f
CROSS JOIN daily_avg d
ORDER BY f.forecast_date
```

---

### Dataset 29: ds_ml_anomalies

**Display Name:** ML: Cost Anomalies  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_sku` (STRING) - param_sku

**SQL Query:**
```sql
WITH anomalies AS (
  SELECT 
    a.workspace_id,
    DATE(a.scored_at) AS usage_date,
    a.prediction AS anomaly_score,
    CASE 
      WHEN a.prediction > 0.7 THEN 'HIGH'
      WHEN a.prediction > 0.5 THEN 'MEDIUM'
      WHEN a.prediction > 0.3 THEN 'LOW'
      ELSE 'NORMAL'
    END AS severity
  FROM ${catalog}.${feature_schema}.cost_anomaly_predictions a
  WHERE a.scored_at >= :time_range.min AND a.scored_at <= :time_range.max
),
workspace_usage AS (
  SELECT 
    f.workspace_id,
    DATE(f.usage_date) AS usage_date,
    MAX(f.sku_name) AS top_sku,
    SUM(f.list_cost) AS daily_cost,
    MAX(f.billing_origin_product) AS cost_driver,
    MAX(COALESCE(f.usage_metadata_job_id, f.usage_metadata_warehouse_id)) AS resource_id
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.usage_date >= :time_range.min AND f.usage_date <= :time_range.max
  GROUP BY f.workspace_id, DATE(f.usage_date)
)
SELECT 
  DATE(a.usage_date) AS usage_date,
  COALESCE(w.workspace_name, CAST(a.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.top_sku, 'Unknown') AS sku_name,
  ROUND(a.anomaly_score, 2) AS anomaly_score,
  a.severity,
  ROUND(COALESCE(u.daily_cost, 0), 2) AS daily_cost,
  CONCAT(COALESCE(u.cost_driver, 'N/A'), ': ', COALESCE(u.resource_id, 'N/A')) AS cost_driver,
  CASE a.severity
    WHEN 'HIGH' THEN 'Immediate review required - investigate top cost driver'
    WHEN 'MEDIUM' THEN 'Monitor closely - check for unusual patterns'
    WHEN 'LOW' THEN 'Watch for developing pattern'
    ELSE 'Normal spending pattern'
  END AS recommended_action
FROM anomalies a
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON a.workspace_id = w.workspace_id
LEFT JOIN workspace_usage u ON a.workspace_id = u.workspace_id AND a.usage_date = u.usage_date
WHERE a.severity IN ('HIGH', 'MEDIUM', 'LOW')
ORDER BY a.anomaly_score DESC
LIMIT 50
```

---

### Dataset 30: ds_ml_budget_alerts

**Display Name:** ML: Budget Alerts  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH workspace_spend AS (
  SELECT 
    COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
    SUM(f.list_cost) AS mtd_spend,
    ROUND(SUM(f.list_cost) / GREATEST(DAY(CURRENT_DATE()), 1) * 30, 2) AS projected_spend,
    ROUND(SUM(f.list_cost) / GREATEST(DAY(CURRENT_DATE()), 1), 2) AS daily_avg,
    MAX(f.sku_name) AS top_sku
  FROM ${catalog}.${gold_schema}.fact_usage f
  LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
  WHERE YEAR(f.usage_date) = YEAR(CURRENT_DATE())
    AND MONTH(f.usage_date) = MONTH(CURRENT_DATE())
  GROUP BY 1
)
SELECT 
  workspace_name,
  CASE 
    WHEN projected_spend > mtd_spend * 1.5 THEN 'HIGH'
    WHEN projected_spend > mtd_spend * 1.2 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS alert_priority,
  ROUND(projected_spend / NULLIF(mtd_spend, 0), 2) AS burn_rate,
  CAST(30 - DAY(CURRENT_DATE()) AS INT) AS days_to_budget,
  ROUND(mtd_spend, 2) AS mtd_spend,
  ROUND(projected_spend, 2) AS projected_spend,
  top_sku,
  CASE 
    WHEN projected_spend > mtd_spend * 1.5 THEN 'Reduce usage immediately - on track to exceed 150% of budget'
    WHEN projected_spend > mtd_spend * 1.2 THEN 'Review top cost drivers - exceeding planned pace'
    ELSE 'On track - continue monitoring'
  END AS recommended_action
FROM workspace_spend
WHERE mtd_spend > 100
ORDER BY projected_spend DESC
LIMIT 20
```

---

### Dataset 31: ds_ml_tag_recs

**Display Name:** ML: Tag Recommendations  
**SQL Query:**
```sql
WITH ml_predictions AS (
  SELECT 
    job_id,
    workspace_id,
    predicted_tag,
    scored_at,
    ROW_NUMBER() OVER (PARTITION BY COALESCE(job_id, CAST(workspace_id AS STRING), 'unknown') ORDER BY scored_at DESC) AS rn
  FROM ${catalog}.${feature_schema}.tag_recommendations
  WHERE scored_at >= CURRENT_DATE() - INTERVAL 30 DAYS
),
recent_predictions AS (
  SELECT * FROM ml_predictions WHERE rn = 1
),
job_costs AS (
  SELECT 
    f.usage_metadata_job_id AS job_id,
    f.workspace_id,
    COALESCE(j.name, f.usage_metadata_job_id) AS job_name,
    COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
    SUM(f.list_cost) AS total_cost,
    MAX(f.sku_name) AS primary_sku,
    COUNT(DISTINCT DATE(f.usage_date)) AS active_days
  FROM ${catalog}.${gold_schema}.fact_usage f
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.usage_metadata_job_id = j.job_id
  LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
  WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND f.usage_metadata_job_id IS NOT NULL
  GROUP BY 1, 2, 3, 4
)
SELECT 
  COALESCE(jc.job_name, CAST(p.job_id AS STRING), 'Unknown') AS job_name,
  COALESCE(jc.workspace_name, CAST(p.workspace_id AS STRING), 'Unknown') AS workspace_name,
  ROUND(COALESCE(jc.total_cost, 0), 2) AS total_cost,
  COALESCE(jc.primary_sku, 'N/A') AS primary_sku,
  COALESCE(p.predicted_tag, 'team=untagged') AS recommended_tag,
  1.0 AS confidence,
  CASE 
    WHEN jc.total_cost > 1000 THEN 'HIGH - High cost job needs tagging'
    WHEN jc.total_cost > 100 THEN 'MEDIUM - Moderate cost job should be tagged'
    ELSE 'LOW - Low cost job'
  END AS priority,
  CONCAT('ML Recommended: ', COALESCE(p.predicted_tag, 'N/A'), '. Active ', COALESCE(jc.active_days, 0), ' days. Cost: $', ROUND(COALESCE(jc.total_cost, 0), 0)) AS rationale,
  p.scored_at
FROM recent_predictions p
LEFT JOIN job_costs jc ON p.job_id = jc.job_id AND p.workspace_id = jc.workspace_id
WHERE p.predicted_tag IS NOT NULL
ORDER BY jc.total_cost DESC NULLS LAST, p.scored_at DESC
LIMIT 30
```

---

### Dataset 32: ds_ml_user_behavior

**Display Name:** ML: User Behavior  
**SQL Query:**
```sql
WITH user_spend AS (
  SELECT 
    COALESCE(f.identity_metadata_run_as, CAST(f.workspace_id AS STRING)) AS user_id,
    COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
    SUM(f.list_cost) AS total_cost,
    COUNT(DISTINCT f.usage_metadata_job_id) AS job_count,
    COUNT(DISTINCT f.usage_metadata_warehouse_id) AS warehouse_count,
    AVG(f.list_cost) AS avg_daily_cost,
    STDDEV(f.list_cost) AS cost_variance
  FROM ${catalog}.${gold_schema}.fact_usage f
  LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id
  WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND f.identity_metadata_run_as IS NOT NULL
  GROUP BY 1, 2
  HAVING SUM(f.list_cost) > 100
)
SELECT 
  user_id AS user,
  workspace_name,
  CASE 
    WHEN total_cost > 5000 AND job_count > 10 THEN 'Power User'
    WHEN total_cost > 1000 AND warehouse_count > 3 THEN 'Analytics Heavy'
    WHEN job_count > 5 AND warehouse_count < 2 THEN 'Batch Processor'
    WHEN cost_variance > avg_daily_cost THEN 'Irregular'
    ELSE 'Standard'
  END AS cluster_label,
  ROUND(total_cost, 2) AS total_spend,
  job_count,
  warehouse_count,
  CASE 
    WHEN total_cost > 5000 THEN 'Review resource allocation and job optimization'
    WHEN cost_variance > avg_daily_cost * 2 THEN 'Investigate usage spikes and set budget alerts'
    WHEN warehouse_count > 3 THEN 'Consider consolidating warehouse usage'
    WHEN job_count > 10 AND total_cost < 500 THEN 'Efficient user - no action needed'
    ELSE 'Monitor for pattern changes'
  END AS recommended_action,
  CONCAT('Jobs: ', job_count, ', Warehouses: ', warehouse_count, ', Daily avg: $', ROUND(avg_daily_cost, 0)) AS usage_summary
FROM user_spend
ORDER BY total_cost DESC
LIMIT 30
```

---

### Dataset 33: ds_ml_migration_recs

**Display Name:** ML: Migration Recs  
**SQL Query:**
```sql
WITH cluster_usage AS (
  SELECT 
    c.cluster_id,
    c.cluster_name,
    c.cluster_source,
    COALESCE(w.workspace_name, CAST(c.workspace_id AS STRING)) AS workspace_name,
    SUM(f.list_cost) AS total_cost,
    SUM(CASE WHEN f.sku_name LIKE '%SERVERLESS%' THEN f.list_cost ELSE 0 END) AS serverless_cost,
    SUM(CASE WHEN f.sku_name NOT LIKE '%SERVERLESS%' THEN f.list_cost ELSE 0 END) AS classic_cost,
    AVG(CASE WHEN f.usage_unit = 'DBU' THEN f.usage_quantity END) AS avg_dbus
  FROM ${catalog}.${gold_schema}.dim_cluster c
  JOIN ${catalog}.${gold_schema}.fact_usage f ON c.workspace_id = f.workspace_id
  LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON c.workspace_id = w.workspace_id
  WHERE f.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND c.cluster_source = 'UI'
  GROUP BY 1, 2, 3, 4
  HAVING SUM(f.list_cost) > 100
)
SELECT 
  COALESCE(cluster_name, 'Unknown Cluster') AS cluster_name,
  workspace_name,
  cluster_source AS cluster_type,
  ROUND(total_cost, 2) AS total_cost_30d,
  CASE 
    WHEN cluster_source = 'UI' AND classic_cost > 500 THEN 'Migrate to Serverless SQL'
    WHEN cluster_source = 'UI' AND classic_cost > 100 THEN 'Convert to Job Cluster'
    WHEN serverless_cost > classic_cost THEN 'Already optimized'
    ELSE 'Review for right-sizing'
  END AS recommendation,
  ROUND(classic_cost * 0.3, 2) AS potential_savings,
  CASE 
    WHEN cluster_source = 'UI' AND classic_cost > 500 THEN 'High - All-purpose cluster with significant spend'
    WHEN cluster_source = 'UI' THEN 'Medium - All-purpose cluster could be optimized'
    ELSE 'Low - Already using job clusters'
  END AS confidence_rationale,
  CONCAT('Source: ', cluster_source, ', Classic: $', ROUND(classic_cost, 0), ', Avg DBUs: ', ROUND(COALESCE(avg_dbus, 0), 0)) AS usage_details
FROM cluster_usage
WHERE classic_cost > 0
ORDER BY classic_cost DESC
LIMIT 20
```

---

### Dataset 34: ds_monitor_cost_trend

**Display Name:** Monitor: Cost Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Daily cost trend from fact_usage
SELECT 
  DATE(usage_date) AS window_start,
  DATE(usage_date) AS window_end,
  ROUND(SUM(list_cost), 2) AS total_cost,
  ROUND(SUM(usage_quantity), 0) AS total_dbu,
  ROUND(SUM(list_cost) / NULLIF(SUM(usage_quantity), 0), 4) AS cost_per_dbu,
  AVG(SUM(list_cost)) OVER (ORDER BY DATE(usage_date) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS seven_day_avg
FROM ${catalog}.${gold_schema}.fact_usage
WHERE DATE(usage_date) >= :time_range.min
  AND DATE(usage_date) <= :time_range.max
GROUP BY DATE(usage_date)
ORDER BY window_start
```

---

### Dataset 35: ds_monitor_serverless

**Display Name:** Monitor: Serverless  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Serverless adoption metrics from fact_usage
SELECT 
  DATE(usage_date) AS window_start, 
  ROUND(SUM(usage_quantity), 0) AS total_dbu,
  ROUND(SUM(CASE WHEN sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%' THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1) AS serverless_pct, 
  ROUND(SUM(CASE WHEN is_tagged = true THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1) AS tag_coverage_pct,
  COUNT(DISTINCT workspace_id) AS unique_users
FROM ${catalog}.${gold_schema}.fact_usage
WHERE DATE(usage_date) >= :time_range.min
  AND DATE(usage_date) <= :time_range.max
GROUP BY DATE(usage_date)
ORDER BY 1
```

---

### Dataset 36: ds_monitor_drift

**Display Name:** Monitor: Drift  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Week-over-week cost drift from fact_usage
WITH daily_cost AS (
  SELECT DATE(usage_date) AS day, SUM(list_cost) AS daily_cost,
    SUM(CASE WHEN sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%' THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0) AS serverless_pct
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE DATE(usage_date) >= :time_range.min AND DATE(usage_date) <= :time_range.max
  GROUP BY DATE(usage_date)
),
weekly_avg AS (
  SELECT day, daily_cost, serverless_pct,
    AVG(daily_cost) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS seven_day_avg,
    LAG(AVG(daily_cost) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 7) OVER (ORDER BY day) AS prev_seven_day_avg,
    AVG(serverless_pct) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS seven_day_serverless,
    LAG(AVG(serverless_pct) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 7) OVER (ORDER BY day) AS prev_seven_day_serverless
  FROM daily_cost
)
SELECT day AS window_start,
  ROUND((seven_day_avg - prev_seven_day_avg) * 100.0 / NULLIF(prev_seven_day_avg, 0), 1) AS cost_drift_pct,
  ROUND(seven_day_serverless - prev_seven_day_serverless, 1) AS serverless_drift
FROM weekly_avg WHERE prev_seven_day_avg IS NOT NULL ORDER BY day
```

---

### Dataset 37: ds_monitor_summary

**Display Name:** Monitor: Summary  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Last 10 days cost summary from fact_usage
SELECT 
  DATE(usage_date) AS window_start,
  ROUND(SUM(list_cost), 2) AS total_cost,
  ROUND(SUM(usage_quantity), 0) AS total_dbu,
  ROUND(SUM(CASE WHEN (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1) AS serverless_pct,
  ROUND(SUM(CASE WHEN is_tagged = true THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1) AS tag_coverage_pct,
  COUNT(DISTINCT workspace_id) AS unique_users
FROM ${catalog}.${gold_schema}.fact_usage
GROUP BY DATE(usage_date)
ORDER BY 1 DESC
LIMIT 10
```

---

### Dataset 38: ds_commit_options

**Display Name:** Commit Amount Options  
**SQL Query:**
```sql
SELECT EXPLODE(ARRAY(500000, 1000000, 2000000, 5000000, 10000000)) AS commit_amount
```

---

### Dataset 39: ds_ytd_spend

**Display Name:** YTD Spend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT SUM(list_cost) AS ytd_spend FROM ${catalog}.${gold_schema}.fact_usage WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())
```

---

### Dataset 40: ds_commit_status

**Display Name:** Commit Status  
**Parameters:**
- `annual_commit` (DECIMAL) - annual_commit
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH ytd AS (SELECT SUM(list_cost) AS total FROM ${catalog}.${gold_schema}.fact_usage WHERE YEAR(usage_date) = YEAR(CURRENT_DATE())) SELECT CONCAT(ROUND(ytd.total * 100.0 / NULLIF(:annual_commit, 0), 1), '%') AS utilization_pct FROM ytd
```

---

### Dataset 41: ds_forecast_summary

**Display Name:** Forecast Summary  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH daily AS (SELECT usage_date, SUM(list_cost) AS daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY usage_date) SELECT ROUND(AVG(daily_cost) * 365, 2) AS forecasted_annual FROM daily
```

---

### Dataset 42: ds_variance

**Display Name:** Projected Variance  
**Parameters:**
- `time_range` (DATE) - time_range
- `annual_commit` (DECIMAL) - annual_commit

**SQL Query:**
```sql
WITH daily AS (SELECT usage_date, SUM(list_cost) AS daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY usage_date), forecast AS (SELECT AVG(daily_cost) * 365 AS forecasted_annual FROM daily) SELECT ROUND(forecasted_annual - :annual_commit, 2) AS projected_variance FROM forecast
```

---

### Dataset 43: ds_run_rate

**Display Name:** Run Rate  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT AVG(daily_cost) AS daily_run_rate FROM (SELECT usage_date, SUM(list_cost) AS daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY usage_date)
```

---

### Dataset 44: ds_usage_forecast

**Display Name:** Usage vs Forecast  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH actuals AS (SELECT usage_date, SUM(list_cost) AS daily_cost, 'Actuals' AS forecast_type FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date BETWEEN :time_range.min AND :time_range.max GROUP BY usage_date), avg_daily AS (SELECT AVG(daily_cost) AS avg_cost FROM actuals), future AS (SELECT DATEADD(DAY, seq, CURRENT_DATE()) AS usage_date, avg_cost AS daily_cost, 'Forecast' AS forecast_type FROM avg_daily CROSS JOIN (SELECT EXPLODE(SEQUENCE(1, 30)) AS seq)) SELECT * FROM actuals UNION ALL SELECT * FROM future ORDER BY usage_date
```

---

### Dataset 45: ds_cumulative_vs_commit

**Display Name:** Cumulative vs Commit  
**Parameters:**
- `annual_commit` (DECIMAL) - annual_commit
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH daily AS (SELECT usage_date, SUM(list_cost) AS daily_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE YEAR(usage_date) = YEAR(CURRENT_DATE()) GROUP BY usage_date), cumulative AS (SELECT usage_date, SUM(daily_cost) OVER (ORDER BY usage_date) AS cumulative_spend FROM daily) SELECT c.usage_date, c.cumulative_spend, (:annual_commit * DAYOFYEAR(c.usage_date) / 365.0) AS target_line FROM cumulative c ORDER BY c.usage_date
```

---

### Dataset 46: ds_monthly_breakdown

**Display Name:** Monthly Breakdown  
**Parameters:**
- `time_range` (DATE) - time_range
- `annual_commit` (DECIMAL) - annual_commit

**SQL Query:**
```sql
WITH monthly AS (SELECT DATE_FORMAT(DATE_TRUNC('month', usage_date), 'MMM') AS month_name, DATE_TRUNC('month', usage_date) AS month_start, SUM(list_cost) AS monthly_cost FROM ${catalog}.${gold_schema}.fact_usage WHERE YEAR(usage_date) = YEAR(CURRENT_DATE()) GROUP BY 1, 2) SELECT m.month_name, ROUND(m.monthly_cost, 2) AS monthly_cost, ROUND(:annual_commit / 12, 2) AS monthly_target FROM monthly m ORDER BY m.month_start
```

---

### Dataset 47: ds_monthly_detail

**Display Name:** Monthly Detail  
**Parameters:**
- `time_range` (DATE) - time_range
- `annual_commit` (DECIMAL) - annual_commit

**SQL Query:**
```sql
-- Last 12 months spend with MoM comparison
WITH monthly AS (
  SELECT 
    DATE_FORMAT(DATE_TRUNC('month', usage_date), 'MMM yyyy') AS month_name, 
    DATE_TRUNC('month', usage_date) AS month_start, 
    SUM(list_cost) AS monthly_cost 
  FROM ${catalog}.${gold_schema}.fact_usage 
  WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE()) - INTERVAL 12 MONTHS
  GROUP BY 1, 2
), with_lag AS (
  SELECT 
    month_name, 
    month_start, 
    ROUND(monthly_cost, 2) AS monthly_cost, 
    ROUND(:annual_commit / 12.0, 2) AS monthly_target,
    LAG(monthly_cost) OVER (ORDER BY month_start) AS prev_month_cost
  FROM monthly
), with_variance AS (
  SELECT 
    month_name, 
    month_start, 
    monthly_cost, 
    monthly_target,
    ROUND(monthly_cost - monthly_target, 2) AS variance, 
    CONCAT(CASE WHEN (monthly_cost - monthly_target) > 0 THEN '+' ELSE '' END, CAST(ROUND((monthly_cost - monthly_target) * 100.0 / NULLIF(monthly_target, 0), 1) AS STRING), '%') AS variance_pct,
    CONCAT(CASE WHEN (monthly_cost - prev_month_cost) > 0 THEN '↑ +' WHEN (monthly_cost - prev_month_cost) < 0 THEN '↓ ' ELSE '→ ' END, CAST(ROUND((monthly_cost - prev_month_cost) * 100.0 / NULLIF(prev_month_cost, 0), 1) AS STRING), '%') AS mom_change
  FROM with_lag
) 
SELECT * FROM with_variance ORDER BY month_start DESC
```

---

### Dataset 48: ds_ml_budget_forecast

**Display Name:** ML: Budget Forecast  
**SQL Query:**
```sql
-- 30-day cost forecast based on historical patterns
WITH daily_costs AS (
  SELECT 
    DATE(usage_date) AS day,
    SUM(list_cost) AS daily_cost
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 90 DAYS
  GROUP BY 1
),
daily_stats AS (
  SELECT 
    ROUND(AVG(daily_cost), 2) AS avg_daily_cost,
    ROUND(STDDEV(daily_cost), 2) AS stddev_cost,
    ROUND(PERCENTILE(daily_cost, 0.75), 2) AS p75_cost,
    ROUND(PERCENTILE(daily_cost, 0.95), 2) AS p95_cost
  FROM daily_costs
),
forecast_days AS (
  SELECT EXPLODE(SEQUENCE(1, 30)) AS day_offset
)
SELECT 
  DATE_ADD(CURRENT_DATE(), f.day_offset) AS forecast_date,
  ROUND(d.avg_daily_cost, 2) AS forecasted_cost,
  ROUND(d.avg_daily_cost * 0.85, 2) AS lower_bound,
  ROUND(d.avg_daily_cost * 1.15, 2) AS upper_bound,
  SUM(ROUND(d.avg_daily_cost, 2)) OVER (ORDER BY f.day_offset) AS cumulative_forecast,
  f.day_offset
FROM forecast_days f
CROSS JOIN daily_stats d
ORDER BY f.day_offset
```

---

### Dataset 49: ds_ml_commitment_rec

**Display Name:** ML: Commitment Recommendations  
**SQL Query:**
```sql
-- Actionable commitment recommendations based on spend patterns
WITH spend_analysis AS (
  SELECT 
    SUM(list_cost) AS annual_spend,
    AVG(list_cost) AS avg_daily_spend,
    STDDEV(list_cost) AS spend_variability,
    MIN(list_cost) AS min_daily,
    MAX(list_cost) AS max_daily,
    PERCENTILE(list_cost, 0.25) AS p25_daily,
    PERCENTILE(list_cost, 0.75) AS p75_daily
  FROM (
    SELECT DATE(usage_date) AS day, SUM(list_cost) AS list_cost
    FROM ${catalog}.${gold_schema}.fact_usage
    WHERE usage_date >= CURRENT_DATE() - INTERVAL 365 DAYS
    GROUP BY 1
  )
)
SELECT 
  1 AS priority,
  '💰 Annual Commit' AS recommendation_type,
  CONCAT('$', FORMAT_NUMBER(ROUND(annual_spend * 0.9, -3), 0)) AS recommended_amount,
  ROUND(CASE WHEN spend_variability / NULLIF(avg_daily_spend, 0) < 0.3 THEN 0.85 ELSE 0.70 END * 100, 0) AS confidence_pct,
  CONCAT('$', FORMAT_NUMBER(ROUND(annual_spend * 0.1, 0), 0), '/year') AS potential_savings,
  CASE 
    WHEN spend_variability / NULLIF(avg_daily_spend, 0) < 0.3 THEN '✅ Stable spend pattern - ideal for annual commit'
    ELSE '⚠️ Variable spend - annual commit risky'
  END AS rationale,
  'Contact Databricks Sales for annual commitment pricing' AS next_step
FROM spend_analysis
UNION ALL
SELECT 
  2 AS priority,
  '📅 Monthly Commit' AS recommendation_type,
  CONCAT('$', FORMAT_NUMBER(ROUND(annual_spend / 12 * 0.95, -2), 0), '/mo') AS recommended_amount,
  ROUND(CASE WHEN spend_variability / NULLIF(avg_daily_spend, 0) < 0.2 THEN 0.80 ELSE 0.65 END * 100, 0) AS confidence_pct,
  CONCAT('$', FORMAT_NUMBER(ROUND(annual_spend * 0.05, 0), 0), '/year') AS potential_savings,
  CASE 
    WHEN spend_variability / NULLIF(avg_daily_spend, 0) < 0.2 THEN '✅ Very stable - monthly commit recommended'
    ELSE '⚠️ Moderate variability - evaluate monthly'
  END AS rationale,
  'Set up monthly billing cap in Account Console' AS next_step
FROM spend_analysis
UNION ALL
SELECT 
  3 AS priority,
  '💳 Pay-As-You-Go' AS recommendation_type,
  'Variable' AS recommended_amount,
  ROUND(CASE WHEN spend_variability / NULLIF(avg_daily_spend, 0) > 0.5 THEN 0.75 ELSE 0.50 END * 100, 0) AS confidence_pct,
  '$0 (no savings)' AS potential_savings,
  CASE 
    WHEN spend_variability / NULLIF(avg_daily_spend, 0) > 0.5 THEN '✅ High variability - PAYG is safer'
    ELSE '⚠️ Stable spend - consider commitment'
  END AS rationale,
  'No action needed - current billing model' AS next_step
FROM spend_analysis
ORDER BY priority
```

---

### Dataset 50: ds_time_windows

**Display Name:** Time Windows  
**SQL Query:**
```sql
SELECT 'Last 7 Days' AS time_window UNION ALL SELECT 'Last 30 Days' UNION ALL SELECT 'Last 90 Days' UNION ALL SELECT 'Last 6 Months' UNION ALL SELECT 'Last Year' UNION ALL SELECT 'All Time'
```

---

### Dataset 51: ds_workspaces

**Display Name:** Workspaces  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name
```

---

### Dataset 52: select_workspace

**Display Name:** select_workspace  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT DISTINCT 
  COALESCE(workspace_name, CONCAT('id: ', workspace_id)) AS workspace_name
FROM ${catalog}.${gold_schema}.dim_workspace 
WHERE workspace_name IS NOT NULL 
ORDER BY workspace_name
```

---

### Dataset 53: select_time_key

**Display Name:** select_time_key  
**SQL Query:**
```sql
SELECT explode(array(
  'Day',
  'Week',
  'Month',
  'Quarter',
  'Year'
)) AS time_key
```

---

### Dataset 54: ds_select_workspace

**Display Name:** ds_select_workspace  
**SQL Query:**
```sql
SELECT DISTINCT COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name FROM ${catalog}.${gold_schema}.fact_usage f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id ORDER BY 1
```

---

### Dataset 55: ds_select_sku

**Display Name:** ds_select_sku  
**SQL Query:**
```sql
SELECT DISTINCT sku_name FROM ${catalog}.${gold_schema}.fact_usage WHERE sku_name IS NOT NULL ORDER BY 1
```

---

### Dataset 56: ds_select_tag_status

**Display Name:** ds_select_tag_status  
**SQL Query:**
```sql
SELECT 'All' AS tag_status UNION ALL SELECT 'Tagged' UNION ALL SELECT 'Untagged'
```

---

### Dataset 57: ds_monitor_cost_aggregate

**Display Name:** Cost Aggregate Metrics  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
-- Daily cost aggregates from fact_usage
SELECT 
  DATE(usage_date) AS window_start,
  DATE(usage_date) AS window_end,
  ROUND(SUM(list_cost), 2) AS total_daily_cost,
  ROUND(SUM(usage_quantity), 0) AS total_daily_dbu,
  ROUND(SUM(CASE WHEN is_tagged = true THEN list_cost ELSE 0 END), 2) AS tagged_cost_total,
  ROUND(SUM(CASE WHEN is_tagged = false OR is_tagged IS NULL THEN list_cost ELSE 0 END), 2) AS untagged_cost_total,
  ROUND(SUM(CASE WHEN sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%' THEN list_cost ELSE 0 END), 2) AS serverless_cost,
  ROUND(SUM(CASE WHEN billing_origin_product = 'DLT' OR sku_name LIKE '%DLT%' THEN list_cost ELSE 0 END), 2) AS dlt_cost
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= :monitor_time_start
  AND usage_date <= COALESCE(:monitor_time_end, CURRENT_TIMESTAMP())
GROUP BY DATE(usage_date)
ORDER BY window_start DESC
```

---

### Dataset 58: ds_monitor_cost_derived

**Display Name:** Cost Derived KPIs  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
-- Derived cost KPIs from fact_usage
SELECT 
  DATE(usage_date) AS window_start,
  DATE(usage_date) AS window_end,
  ROUND(SUM(CASE WHEN is_tagged = true THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 2) AS tag_coverage_pct,
  ROUND(SUM(CASE WHEN (sku_name LIKE '%SERVERLESS%' OR billing_origin_product LIKE '%Serverless%') THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 2) AS serverless_ratio
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= :monitor_time_start
  AND usage_date <= COALESCE(:monitor_time_end, CURRENT_TIMESTAMP())
GROUP BY DATE(usage_date)
ORDER BY window_start DESC
```

---

### Dataset 59: ds_monitor_cost_drift

**Display Name:** Cost Drift Metrics  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
-- Week-over-week cost drift calculation
WITH daily_cost AS (
  SELECT DATE(usage_date) AS day, SUM(list_cost) AS daily_cost,
    SUM(CASE WHEN is_tagged = true THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0) AS tag_coverage
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= :monitor_time_start AND usage_date <= COALESCE(:monitor_time_end, CURRENT_TIMESTAMP())
  GROUP BY DATE(usage_date)
),
weekly_avg AS (
  SELECT day, daily_cost, tag_coverage,
    AVG(daily_cost) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS seven_day_avg,
    LAG(AVG(daily_cost) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 7) OVER (ORDER BY day) AS prev_seven_day_avg,
    AVG(tag_coverage) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS seven_day_tag,
    LAG(AVG(tag_coverage) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 7) OVER (ORDER BY day) AS prev_seven_day_tag
  FROM daily_cost
)
SELECT day AS window_start, 'CONSECUTIVE' AS drift_type,
  ROUND((seven_day_avg - prev_seven_day_avg) * 100.0 / NULLIF(prev_seven_day_avg, 0), 2) AS cost_drift_pct,
  ROUND(seven_day_tag - prev_seven_day_tag, 2) AS tag_coverage_drift
FROM weekly_avg WHERE prev_seven_day_avg IS NOT NULL ORDER BY day
```

---

### Dataset 60: ds_monitor_cost_slice_keys

**Display Name:** Cost Slice Keys  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end

**SQL Query:**
```sql
-- Available slice keys for cost analysis
SELECT 'All' AS slice_key
UNION ALL
SELECT 'workspace_name' AS slice_key
UNION ALL
SELECT 'billing_origin_product' AS slice_key
UNION ALL
SELECT 'sku_name' AS slice_key
ORDER BY slice_key
```

---

### Dataset 61: ds_monitor_cost_slice_values

**Display Name:** Cost Slice Values  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
-- Available slice values based on selected slice key
SELECT 'All' AS slice_value
UNION ALL
SELECT DISTINCT 
  CASE 
    WHEN :monitor_slice_key = 'workspace_name' THEN workspace_name
    WHEN :monitor_slice_key = 'billing_origin_product' THEN billing_origin_product
    WHEN :monitor_slice_key = 'sku_name' THEN sku_name
    ELSE 'All'
  END AS slice_value
FROM ${catalog}.${gold_schema}.fact_usage
WHERE usage_date >= :monitor_time_start
  AND usage_date <= COALESCE(:monitor_time_end, CURRENT_TIMESTAMP())
  AND :monitor_slice_key != 'All'
LIMIT 50
```

---
