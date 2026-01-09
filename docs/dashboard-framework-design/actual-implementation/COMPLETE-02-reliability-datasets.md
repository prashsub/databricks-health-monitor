# Complete Job Reliability Dataset Catalog

## Overview
**Total Datasets:** 49  
**Dashboard:** `reliability.lvdash.json`  
**Coverage:** ALL datasets from ALL pages with FULL details

---

## Dataset Index

| # | Dataset Name | Display Name | Has Query | Parameters |
|---|--------------|--------------|-----------|------------|
| 1 | ds_kpi_success_rate | KPI: Success Rate | ✅ | time_range, param_job_status |
| 2 | ds_kpi_totals | KPI: Totals | ✅ | time_range, param_job_status |
| 3 | ds_kpi_duration | KPI: Duration | ✅ | time_range, param_job_status |
| 4 | ds_kpi_mttr | KPI: MTTR | ✅ | time_range, param_job_status |
| 5 | ds_success_trend | Success Trend | ✅ | time_range, param_job_status |
| 6 | ds_runs_by_status | Runs by Status | ✅ | time_range, param_job_status |
| 7 | ds_duration_trend | Duration Trend | ✅ | time_range, param_job_status |
| 8 | ds_failed_today | Failed Today | ✅ | time_range, param_workspace, param_job_status |
| 9 | ds_low_success_jobs | Low Success Jobs | ✅ | time_range, param_workspace, param_job_status |
| 10 | ds_highest_failure_jobs | Highest Failure Jobs | ✅ | time_range, param_workspace, param_job_status |
| 11 | ds_failure_by_type | Failure by Type | ✅ | time_range, param_job_status |
| 12 | ds_failure_trend_by_type | Failure Trend by Type | ✅ | time_range, param_job_status |
| 13 | ds_most_repaired | Most Repaired | ✅ | time_range |
| 14 | ds_slowest_jobs | Slowest Jobs | ✅ | time_range, param_workspace, param_job_status |
| 15 | ds_duration_regression | Duration Regression | ✅ | time_range, param_workspace, param_job_status |
| 16 | ds_duration_outliers | Duration Outliers | ✅ | time_range, param_workspace, param_job_status |
| 17 | ds_runs_by_hour | Runs by Hour | ✅ | time_range, param_job_status |
| 18 | ds_runs_by_day | Runs by Day | ✅ | time_range, param_job_status |
| 19 | ds_ml_failure_risk | ML: Failure Risk | ✅ | - |
| 20 | ds_ml_pipeline_health | ML: Pipeline Health | ✅ | - |
| 21 | ds_ml_retry_success | ML: Retry Success | ✅ | - |
| 22 | ds_ml_incident_impact | ML: Incident Impact | ✅ | - |
| 23 | ds_ml_self_healing | ML: Self Healing | ✅ | - |
| 24 | ds_ml_duration_forecast | ML: Duration Forecast | ✅ | - |
| 25 | ds_monitor_latest | Monitor: Latest | ✅ | time_range |
| 26 | ds_monitor_trend | Monitor: Trend | ✅ | time_range |
| 27 | ds_monitor_duration | Monitor: Duration | ✅ | time_range |
| 28 | ds_monitor_run_types | Monitor: Run Types | ✅ | time_range |
| 29 | ds_monitor_errors | Monitor: Errors | ✅ | time_range |
| 30 | ds_monitor_drift | Monitor: Drift | ✅ | time_range |
| 31 | ds_monitor_detailed | Monitor: Detailed | ✅ | time_range |
| 32 | ds_no_autoscale_count | No Autoscale Count | ✅ | - |
| 33 | ds_stale_count | Stale Count | ✅ | time_range |
| 34 | ds_ap_count | Ap Count | ✅ | - |
| 35 | ds_no_autoscale | No Autoscale | ✅ | time_range, param_workspace |
| 36 | ds_stale_datasets | Stale Datasets | ✅ | time_range, param_workspace |
| 37 | ds_ap_jobs | Ap Jobs | ✅ | time_range, param_workspace |
| 38 | ds_outliers | Outliers | ✅ | time_range, param_workspace, param_job_status |
| 39 | ds_time_windows | Time Windows | ✅ | - |
| 40 | ds_workspaces | Workspaces | ✅ | param_workspace |
| 41 | select_workspace | select_workspace | ✅ | param_workspace |
| 42 | select_time_key | select_time_key | ✅ | - |
| 43 | ds_select_workspace | ds_select_workspace | ✅ | - |
| 44 | ds_select_job_status | ds_select_job_status | ✅ | - |
| 45 | ds_monitor_reliability_aggregate | Reliability Aggregate Metrics | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 46 | ds_monitor_reliability_derived | Reliability Derived KPIs | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 47 | ds_monitor_reliability_drift | Reliability Drift Metrics | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 48 | ds_monitor_reliability_slice_keys | Reliability Slice Keys | ✅ | monitor_time_start, monitor_time_end |
| 49 | ds_monitor_reliability_slice_values | Reliability Slice Values | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key |

---

## Complete SQL Queries


### Dataset 1: ds_kpi_success_rate

**Display Name:** KPI: Success Rate  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT CONCAT(ROUND(SUM(CASE WHEN termination_code = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), '%') AS success_rate FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max AND termination_code IS NOT NULL
```

---

### Dataset 2: ds_kpi_totals

**Display Name:** KPI: Totals  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT COUNT(*) AS total_runs, SUM(CASE WHEN termination_code IS NOT NULL AND termination_code != 'SUCCESS' THEN 1 ELSE 0 END) AS total_failures, COUNT(DISTINCT job_id) AS unique_jobs FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max AND termination_code IS NOT NULL
```

---

### Dataset 3: ds_kpi_duration

**Display Name:** KPI: Duration  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT ROUND(PERCENTILE(run_duration_seconds / 60.0, 0.95), 1) AS p95_duration FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max AND termination_code = 'SUCCESS' AND run_duration_seconds IS NOT NULL
```

---

### Dataset 4: ds_kpi_mttr

**Display Name:** KPI: MTTR  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT COALESCE(ROUND(AVG(run_duration_seconds / 60.0), 1), 0) AS mttr_minutes FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max AND termination_code IS NOT NULL AND termination_code != 'SUCCESS'
```

---

### Dataset 5: ds_success_trend

**Display Name:** Success Trend  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT DATE(run_date) AS run_date, ROUND(SUM(CASE WHEN termination_code = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS success_rate, ROUND(SUM(CASE WHEN termination_code IS NOT NULL AND termination_code != 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS failure_rate FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max AND termination_code IS NOT NULL GROUP BY 1 ORDER BY 1
```

---

### Dataset 6: ds_runs_by_status

**Display Name:** Runs by Status  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
-- Daily job runs by status using result_state (handles various status spellings)
SELECT 
  DATE(run_date) AS run_date,
  SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) AS successful,
  SUM(CASE WHEN result_state IN ('FAILED', 'INTERNAL_ERROR', 'ERROR') THEN 1 ELSE 0 END) AS failed,
  SUM(CASE WHEN result_state IN ('TIMEDOUT', 'TIMED_OUT', 'TIMEOUT') OR termination_code IN ('TIMEDOUT', 'TIMED_OUT') THEN 1 ELSE 0 END) AS timed_out,
  SUM(CASE WHEN result_state IN ('CANCELED', 'CANCELLED') OR termination_code IN ('CANCELED', 'CANCELLED', 'USER_CANCELLED') THEN 1 ELSE 0 END) AS cancelled
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE run_date BETWEEN :time_range.min AND :time_range.max
  AND result_state IS NOT NULL
GROUP BY 1
ORDER BY 1
```

---

### Dataset 7: ds_duration_trend

**Display Name:** Duration Trend  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT DATE(run_date) AS run_date, ROUND(AVG(run_duration_seconds / 60.0), 1) AS avg_duration, ROUND(PERCENTILE(run_duration_seconds / 60.0, 0.5), 1) AS p50_duration, ROUND(PERCENTILE(run_duration_seconds / 60.0, 0.95), 1) AS p95_duration FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max AND termination_code = 'SUCCESS' AND run_duration_seconds IS NOT NULL GROUP BY 1 ORDER BY 1
```

---

### Dataset 8: ds_failed_today

**Display Name:** Failed Today  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT 
  COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name,
  f.termination_code,
  f.run_date AS run_time,
  ROUND(f.run_duration_seconds / 60.0, 1) AS duration_minutes,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  COALESCE(j.tags_json, '{}') AS tags
FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
LEFT JOIN ${catalog}.${gold_schema}.dim_job j 
  ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w 
  ON f.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON CAST(COALESCE(j.run_as, j.creator_id) AS STRING) = u.user_id
WHERE f.run_date BETWEEN :time_range.min AND :time_range.max
  AND f.termination_code IS NOT NULL 
  AND f.termination_code NOT IN ('SUCCESS', 'SKIPPED')
  AND (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, w.workspace_name))
ORDER BY f.run_date DESC
LIMIT 50
```

---

### Dataset 9: ds_low_success_jobs

**Display Name:** Low Success Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT 
  COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN f.termination_code IS NOT NULL AND f.termination_code != 'SUCCESS' THEN 1 ELSE 0 END) AS failures,
  ROUND(SUM(CASE WHEN f.termination_code = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS success_rate,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  COALESCE(j.tags_json, '{}') AS tags
FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u ON CAST(COALESCE(j.run_as, j.creator_id) AS STRING) = u.user_id
WHERE f.run_date BETWEEN :time_range.min AND :time_range.max 
  AND f.termination_code IS NOT NULL
GROUP BY 1, u.email, j.run_as, j.creator_id, j.tags_json
HAVING COUNT(*) >= 5
ORDER BY success_rate ASC
LIMIT 15
```

---

### Dataset 10: ds_highest_failure_jobs

**Display Name:** Highest Failure Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT 
  COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name,
  SUM(CASE WHEN f.termination_code IS NOT NULL AND f.termination_code != 'SUCCESS' THEN 1 ELSE 0 END) AS failures,
  ROUND(SUM(CASE WHEN f.termination_code = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS success_rate,
  ROUND(SUM(CASE WHEN f.termination_code != 'SUCCESS' THEN COALESCE(f.run_duration_seconds, 0) / 3600.0 * 0.15 ELSE 0 END), 2) AS failure_cost,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  COALESCE(j.tags_json, '{}') AS tags
FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u ON CAST(COALESCE(j.run_as, j.creator_id) AS STRING) = u.user_id
WHERE f.run_date BETWEEN :time_range.min AND :time_range.max 
  AND f.termination_code IS NOT NULL
GROUP BY 1, u.email, j.run_as, j.creator_id, j.tags_json
ORDER BY failures DESC
LIMIT 15
```

---

### Dataset 11: ds_failure_by_type

**Display Name:** Failure by Type  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT COALESCE(termination_code, 'UNKNOWN') AS termination_code, COUNT(*) AS failure_count FROM ${catalog}.${gold_schema}.fact_job_run_timeline WHERE run_date BETWEEN :time_range.min AND :time_range.max AND result_state NOT IN ('SUCCESS', 'SUCCEEDED') GROUP BY 1 ORDER BY failure_count DESC LIMIT 10
```

---

### Dataset 12: ds_failure_trend_by_type

**Display Name:** Failure Trend by Type  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT DATE(run_date) AS run_date, SUM(CASE WHEN termination_code = 'INTERNAL_ERROR' THEN 1 ELSE 0 END) AS internal_error, SUM(CASE WHEN termination_code = 'TIMED_OUT' THEN 1 ELSE 0 END) AS timeout, SUM(CASE WHEN termination_code = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled, SUM(CASE WHEN termination_code NOT IN ('SUCCESS', 'INTERNAL_ERROR', 'TIMED_OUT', 'CANCELLED') AND termination_code IS NOT NULL THEN 1 ELSE 0 END) AS other FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 13: ds_most_repaired

**Display Name:** Most Repaired  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Jobs with most retry/repair runs (failures followed by success within same job)
WITH job_runs AS (
  SELECT 
    f.job_id,
    f.workspace_id,
    f.run_date,
    f.result_state,
    f.run_duration_seconds,
    LEAD(f.result_state) OVER (PARTITION BY f.job_id ORDER BY f.period_start_time) AS next_state,
    LEAD(f.run_duration_seconds) OVER (PARTITION BY f.job_id ORDER BY f.period_start_time) AS retry_duration
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
  WHERE f.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
repair_runs AS (
  SELECT 
    job_id,
    workspace_id,
    COUNT(*) AS repairs,
    SUM(retry_duration) AS total_repair_seconds
  FROM job_runs
  WHERE result_state IN ('FAILED', 'ERROR', 'INTERNAL_ERROR')
    AND next_state IN ('SUCCESS', 'SUCCEEDED')
  GROUP BY job_id, workspace_id
)
SELECT 
  COALESCE(j.name, CAST(r.job_id AS STRING)) AS job_name,
  r.repairs,
  ROUND(r.repairs * 0.50, 2) AS repair_cost,
  ROUND(r.total_repair_seconds / 60.0, 1) AS repair_time_min,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  COALESCE(j.tags_json, '{}') AS tags
FROM repair_runs r
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u ON CAST(COALESCE(j.run_as, j.creator_id) AS STRING) = u.user_id
WHERE r.repairs > 0
ORDER BY r.repairs DESC
LIMIT 15
```

---

### Dataset 14: ds_slowest_jobs

**Display Name:** Slowest Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name, ROUND(AVG(f.run_duration_seconds / 60.0), 1) AS avg_duration, ROUND(PERCENTILE(f.run_duration_seconds / 60.0, 0.95), 1) AS p95_duration, ROUND(MAX(f.run_duration_seconds / 60.0), 1) AS max_duration, COUNT(*) AS runs FROM ${catalog}.${gold_schema}.fact_job_run_timeline f LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id WHERE f.run_date BETWEEN :time_range.min AND :time_range.max AND f.termination_code = 'SUCCESS' AND f.run_duration_seconds IS NOT NULL GROUP BY 1 HAVING COUNT(*) >= 3 ORDER BY avg_duration DESC LIMIT 20
```

---

### Dataset 15: ds_duration_regression

**Display Name:** Duration Regression  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
WITH job_duration AS (SELECT COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name, AVG(CASE WHEN f.run_date BETWEEN :time_range.min AND :time_range.max THEN f.run_duration_seconds / 60.0 END) AS last_7d_avg, AVG(CASE WHEN f.run_date BETWEEN CURRENT_DATE() - INTERVAL 14 DAYS AND CURRENT_DATE() - INTERVAL 8 DAYS THEN f.run_duration_seconds / 60.0 END) AS prev_7d_avg FROM ${catalog}.${gold_schema}.fact_job_run_timeline f LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id WHERE f.run_date BETWEEN :time_range.min AND :time_range.max AND f.termination_code = 'SUCCESS' AND f.run_duration_seconds IS NOT NULL GROUP BY 1) SELECT job_name, ROUND(last_7d_avg, 1) AS last_7d_avg, ROUND(prev_7d_avg, 1) AS prev_7d_avg, ROUND((last_7d_avg - prev_7d_avg) * 100.0 / NULLIF(prev_7d_avg, 0), 1) AS increase_pct FROM job_duration WHERE prev_7d_avg > 0 AND last_7d_avg > prev_7d_avg * 1.2 ORDER BY increase_pct DESC LIMIT 15
```

---

### Dataset 16: ds_duration_outliers

**Display Name:** Duration Outliers  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
WITH job_stats AS (SELECT COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name, AVG(f.run_duration_seconds / 60.0) AS avg_duration, MAX(f.run_duration_seconds / 60.0) AS max_duration, PERCENTILE(f.run_duration_seconds / 60.0, 0.9) AS p90 FROM ${catalog}.${gold_schema}.fact_job_run_timeline f LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.workspace_id = j.workspace_id AND f.job_id = j.job_id WHERE f.run_date BETWEEN :time_range.min AND :time_range.max AND f.termination_code = 'SUCCESS' AND f.run_duration_seconds IS NOT NULL GROUP BY 1 HAVING COUNT(*) >= 5) SELECT job_name, ROUND(avg_duration, 1) AS avg_duration, ROUND(max_duration, 1) AS max_duration, ROUND(p90, 1) AS p90, ROUND(max_duration - p90, 1) AS deviation FROM job_stats WHERE max_duration > p90 * 1.5 ORDER BY deviation DESC LIMIT 15
```

---

### Dataset 17: ds_runs_by_hour

**Display Name:** Runs by Hour  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT HOUR(run_date) AS hour, COUNT(*) AS total_runs, SUM(CASE WHEN termination_code IS NOT NULL AND termination_code != 'SUCCESS' THEN 1 ELSE 0 END) AS failures FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 18: ds_runs_by_day

**Display Name:** Runs by Day  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
SELECT DATE_FORMAT(run_date, 'EEEE') AS day_name, COUNT(*) AS total_runs, ROUND(SUM(CASE WHEN termination_code = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS success_rate FROM ${catalog}.${gold_schema}.fact_job_run_timeline  WHERE run_date BETWEEN :time_range.min AND :time_range.max AND termination_code IS NOT NULL GROUP BY 1
```

---

### Dataset 19: ds_ml_failure_risk

**Display Name:** ML: Failure Risk  
**SQL Query:**
```sql
-- Actionable failure risk with context, owner, and last failure details
WITH job_stats AS (
  SELECT 
    r.job_id,
    COALESCE(j.name, CAST(r.job_id AS STRING)) AS job_name,
    COALESCE(j.creator_id, 'Unknown') AS owner,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) AS failed_runs,
    MAX(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN r.run_date END) AS last_failure_date,
    MAX(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN r.result_state END) AS last_failure_state,
    MAX(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN r.termination_code END) AS last_error_code,
    ROUND(STDDEV(r.run_duration_seconds), 1) AS duration_variance,
    AVG(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN r.run_duration_seconds END) AS avg_failure_duration
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
  WHERE r.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY r.job_id, j.name, j.creator_id
  HAVING COUNT(*) >= 3
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY (failed_runs * 100.0 / total_runs) DESC) AS priority,
  job_name,
  owner,
  ROUND(failed_runs * 100.0 / total_runs, 1) AS failure_rate_pct,
  CASE 
    WHEN failed_runs * 100.0 / total_runs > 50 THEN 'CRITICAL'
    WHEN failed_runs * 100.0 / total_runs > 25 THEN 'HIGH'
    WHEN failed_runs * 100.0 / total_runs > 10 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_level,
  failed_runs || ' of ' || total_runs || ' runs failed' AS failure_summary,
  COALESCE(last_failure_state, 'N/A') || COALESCE(' (' || last_error_code || ')', '') AS last_issue,
  COALESCE(CAST(last_failure_date AS STRING), 'N/A') AS last_failure,
  CASE 
    WHEN last_error_code LIKE '%TIMEOUT%' THEN 'Increase timeout or optimize job'
    WHEN last_error_code LIKE '%OOM%' OR last_error_code LIKE '%MEMORY%' THEN 'Increase cluster memory'
    WHEN last_error_code LIKE '%INTERNAL%' THEN 'Check cluster health, retry may help'
    WHEN duration_variance > 300 THEN 'High duration variance - investigate data skew'
    WHEN failed_runs * 100.0 / total_runs > 50 THEN 'Critical: Review job config and dependencies'
    ELSE 'Review logs for recent failures'
  END AS recommended_action
FROM job_stats
WHERE failed_runs > 0
ORDER BY (failed_runs * 100.0 / total_runs) DESC
LIMIT 15
```

---

### Dataset 20: ds_ml_pipeline_health

**Display Name:** ML: Pipeline Health  
**SQL Query:**
```sql
-- Pipeline health score based on success rate, consistency, and recent trend
WITH job_health AS (
  SELECT 
    r.job_id,
    COALESCE(j.name, CAST(r.job_id AS STRING)) AS job_name,
    COALESCE(j.creator_id, 'Unknown') AS owner,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN r.result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) AS success_runs,
    AVG(r.run_duration_seconds) AS avg_duration,
    STDDEV(r.run_duration_seconds) AS duration_stddev,
    MAX(r.run_date) AS last_run_date,
    MAX(CASE WHEN r.result_state IN ('SUCCESS', 'SUCCEEDED') THEN r.run_date END) AS last_success_date,
    MAX(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN r.run_date END) AS last_failure_date
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
  WHERE r.run_date >= CURRENT_DATE() - INTERVAL 14 DAYS
  GROUP BY r.job_id, j.name, j.creator_id
  HAVING COUNT(*) >= 3
),
recent_health AS (
  SELECT job_id,
    SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS recent_success_rate
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 3 DAYS
  GROUP BY job_id
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY (jh.success_runs * 100.0 / jh.total_runs) ASC) AS priority,
  jh.job_name,
  jh.owner,
  ROUND(jh.success_runs * 100.0 / jh.total_runs, 0) AS health_score,
  CASE 
    WHEN jh.success_runs * 100.0 / jh.total_runs >= 95 THEN '🟢 Healthy'
    WHEN jh.success_runs * 100.0 / jh.total_runs >= 80 THEN '🟡 Degraded'
    WHEN jh.success_runs * 100.0 / jh.total_runs >= 50 THEN '🟠 Poor'
    ELSE '🔴 Critical'
  END AS health_status,
  CASE 
    WHEN COALESCE(rh.recent_success_rate, 0) > jh.success_runs * 100.0 / jh.total_runs THEN '📈 Improving'
    WHEN COALESCE(rh.recent_success_rate, 0) < jh.success_runs * 100.0 / jh.total_runs - 10 THEN '📉 Declining'
    ELSE '➡️ Stable'
  END AS trend,
  jh.total_runs || ' runs, ' || (jh.total_runs - jh.success_runs) || ' failed' AS run_summary,
  CASE 
    WHEN jh.last_failure_date > jh.last_success_date THEN 'Last run failed - investigate immediately'
    WHEN jh.success_runs * 100.0 / jh.total_runs < 50 THEN 'Critical: Review job config and dependencies'
    WHEN COALESCE(rh.recent_success_rate, 0) < 80 THEN 'Recent degradation - check recent changes'
    ELSE 'Monitor for further issues'
  END AS action_needed
FROM job_health jh
LEFT JOIN recent_health rh ON jh.job_id = rh.job_id
WHERE jh.success_runs * 100.0 / jh.total_runs < 95
ORDER BY (jh.success_runs * 100.0 / jh.total_runs) ASC
LIMIT 15
```

---

### Dataset 21: ds_ml_retry_success

**Display Name:** ML: Retry Success  
**SQL Query:**
```sql
-- Jobs where retry is likely to succeed based on historical retry patterns
WITH job_retries AS (
  SELECT 
    r1.job_id,
    COALESCE(j.name, CAST(r1.job_id AS STRING)) AS job_name,
    COALESCE(j.creator_id, 'Unknown') AS owner,
    r1.result_state AS initial_state,
    r1.termination_code AS error_code,
    r2.result_state AS retry_state,
    r1.run_date
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline r1
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r1.job_id = j.job_id
  JOIN ${catalog}.${gold_schema}.fact_job_run_timeline r2 
    ON r1.job_id = r2.job_id 
    AND DATE(r1.run_date) = DATE(r2.run_date)
    AND r2.period_start_time > r1.period_start_time
    AND r2.period_start_time < r1.period_start_time + INTERVAL 4 HOURS
  WHERE r1.result_state NOT IN ('SUCCESS', 'SUCCEEDED')
    AND r1.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
retry_stats AS (
  SELECT 
    job_id,
    job_name,
    owner,
    COUNT(*) AS total_retries,
    SUM(CASE WHEN retry_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) AS successful_retries,
    MAX(error_code) AS common_error,
    MAX(run_date) AS last_retry_date
  FROM job_retries
  GROUP BY job_id, job_name, owner
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY (successful_retries * 100.0 / total_retries) DESC) AS priority,
  job_name,
  owner,
  ROUND(successful_retries * 100.0 / total_retries, 0) AS retry_success_pct,
  successful_retries || ' of ' || total_retries || ' retries succeeded' AS retry_summary,
  CASE 
    WHEN successful_retries * 100.0 / total_retries >= 80 THEN '✅ Auto-retry recommended'
    WHEN successful_retries * 100.0 / total_retries >= 50 THEN '⚠️ Retry may help'
    ELSE '🔍 Investigate first'
  END AS recommendation,
  COALESCE(common_error, 'Unknown') AS typical_error,
  CASE 
    WHEN successful_retries * 100.0 / total_retries >= 80 THEN 'Configure max_retries=3 in job settings'
    WHEN common_error LIKE '%TIMEOUT%' THEN 'Increase timeout before retry'
    WHEN common_error LIKE '%OOM%' THEN 'Increase cluster resources'
    ELSE 'Review logs before enabling auto-retry'
  END AS action
FROM retry_stats
WHERE total_retries >= 2
ORDER BY (successful_retries * 100.0 / total_retries) DESC, total_retries DESC
LIMIT 15
```

---

### Dataset 22: ds_ml_incident_impact

**Display Name:** ML: Incident Impact  
**SQL Query:**
```sql
-- Jobs with highest impact when they fail (based on frequency and recent failures)
WITH job_impact AS (
  SELECT 
    r.job_id,
    COALESCE(j.name, CAST(r.job_id AS STRING)) AS job_name,
    COALESCE(j.creator_id, 'Unknown') AS owner,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) AS failed_runs,
    AVG(r.run_duration_seconds / 60.0) AS avg_duration_min,
    COUNT(DISTINCT DATE(r.run_date)) AS active_days,
    MAX(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN r.run_date END) AS last_failure,
    MAX(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN r.termination_code END) AS last_error
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
  WHERE r.run_date >= CURRENT_DATE() - INTERVAL 14 DAYS
  GROUP BY r.job_id, j.name, j.creator_id
  HAVING SUM(CASE WHEN r.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) > 0
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY (active_days * failed_runs * avg_duration_min) DESC) AS priority,
  job_name,
  owner,
  CASE 
    WHEN active_days >= 12 AND failed_runs > 5 THEN '🔴 Critical'
    WHEN active_days >= 7 AND failed_runs > 2 THEN '🟠 High'
    WHEN active_days >= 3 THEN '🟡 Medium'
    ELSE '⚪ Low'
  END AS impact_level,
  active_days || ' days active, ' || failed_runs || ' failures' AS impact_summary,
  ROUND(avg_duration_min, 1) || ' min avg runtime' AS resource_impact,
  COALESCE(CAST(last_failure AS STRING), 'N/A') AS last_incident,
  COALESCE(last_error, 'Unknown') AS error_type,
  CASE 
    WHEN active_days >= 12 THEN 'Critical path job - prioritize fix and add monitoring'
    WHEN failed_runs > 5 THEN 'Frequent failures - investigate root cause'
    WHEN avg_duration_min > 60 THEN 'Long-running job - failures waste significant resources'
    ELSE 'Monitor and fix when capacity allows'
  END AS recommended_action
FROM job_impact
ORDER BY (active_days * failed_runs * avg_duration_min) DESC
LIMIT 15
```

---

### Dataset 23: ds_ml_self_healing

**Display Name:** ML: Self Healing  
**SQL Query:**
```sql
-- Self-healing recommendations based on error patterns and historical resolution
WITH error_patterns AS (
  SELECT 
    r.termination_code AS error_pattern,
    COALESCE(j.name, CAST(r.job_id AS STRING)) AS example_job,
    COALESCE(j.creator_id, 'Unknown') AS owner,
    COUNT(*) AS occurrences,
    COUNT(DISTINCT r.job_id) AS affected_jobs,
    MAX(r.run_date) AS last_seen
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
  WHERE r.result_state NOT IN ('SUCCESS', 'SUCCEEDED')
    AND r.run_date >= CURRENT_DATE() - INTERVAL 14 DAYS
    AND r.termination_code IS NOT NULL
  GROUP BY r.termination_code, j.name, r.job_id, j.creator_id
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY occurrences DESC) AS priority,
  error_pattern,
  CASE 
    WHEN error_pattern LIKE '%TIMEOUT%' OR error_pattern LIKE '%TIMED_OUT%' THEN '⏱️ Auto-retry with backoff'
    WHEN error_pattern LIKE '%OOM%' OR error_pattern LIKE '%MEMORY%' THEN '📈 Scale cluster memory'
    WHEN error_pattern LIKE '%INTERNAL%' THEN '🔄 Auto-retry (transient)'
    WHEN error_pattern LIKE '%CANCEL%' THEN '⚠️ Manual review needed'
    WHEN error_pattern LIKE '%DRIVER%' THEN '🔧 Check driver logs'
    WHEN error_pattern LIKE '%NETWORK%' OR error_pattern LIKE '%CONNECTION%' THEN '🌐 Retry with network check'
    ELSE '🔍 Manual investigation'
  END AS healing_action,
  occurrences AS total_occurrences,
  affected_jobs AS jobs_affected,
  example_job AS example_affected_job,
  owner AS job_owner,
  CASE 
    WHEN error_pattern LIKE '%TIMEOUT%' THEN 'Configure retry policy: max_retries=3, retry_on_timeout=true'
    WHEN error_pattern LIKE '%OOM%' THEN 'Increase spark.executor.memory or use larger instance type'
    WHEN error_pattern LIKE '%INTERNAL%' THEN 'Usually transient - auto-retry resolves 80%+ cases'
    WHEN error_pattern LIKE '%CANCEL%' THEN 'Check if job was manually cancelled or hit cluster termination'
    ELSE 'Review job logs in Spark UI for detailed error'
  END AS implementation_guide
FROM error_patterns
WHERE occurrences >= 2
ORDER BY occurrences DESC
LIMIT 15
```

---

### Dataset 24: ds_ml_duration_forecast

**Display Name:** ML: Duration Forecast  
**SQL Query:**
```sql
-- Duration analysis: Jobs with significant deviation from baseline (prioritized by impact)
WITH job_durations AS (
  SELECT 
    r.job_id,
    COALESCE(j.name, CAST(r.job_id AS STRING)) AS job_name,
    COALESCE(j.creator_id, 'Unknown') AS owner,
    COUNT(*) AS total_runs,
    ROUND(AVG(r.run_duration_seconds / 60.0), 1) AS avg_duration_min,
    ROUND(PERCENTILE(r.run_duration_seconds / 60.0, 0.5), 1) AS median_duration_min,
    ROUND(PERCENTILE(r.run_duration_seconds / 60.0, 0.95), 1) AS p95_duration_min,
    ROUND(MAX(r.run_duration_seconds / 60.0), 1) AS max_duration_min,
    ROUND(STDDEV(r.run_duration_seconds / 60.0), 1) AS std_dev_min
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
  WHERE r.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND r.result_state IN ('SUCCESS', 'SUCCEEDED')
    AND r.run_duration_seconds > 0
  GROUP BY r.job_id, j.name, j.creator_id
  HAVING COUNT(*) >= 5
),
recent_runs AS (
  SELECT 
    r.job_id,
    ROUND(AVG(r.run_duration_seconds / 60.0), 1) AS recent_avg_min
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
  WHERE r.run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND r.result_state IN ('SUCCESS', 'SUCCEEDED')
  GROUP BY r.job_id
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY ABS(rr.recent_avg_min - jd.avg_duration_min) DESC) AS priority,
  jd.job_name,
  jd.owner,
  COALESCE(rr.recent_avg_min, jd.avg_duration_min) AS recent_duration_min,
  jd.avg_duration_min AS baseline_duration_min,
  ROUND(((COALESCE(rr.recent_avg_min, jd.avg_duration_min) - jd.avg_duration_min) / NULLIF(jd.avg_duration_min, 0)) * 100, 1) AS deviation_pct,
  CASE 
    WHEN rr.recent_avg_min > jd.p95_duration_min THEN '🔴 Critical: Exceeds P95'
    WHEN rr.recent_avg_min > jd.avg_duration_min * 1.5 THEN '🟠 High: >50% slower'
    WHEN rr.recent_avg_min > jd.avg_duration_min * 1.2 THEN '🟡 Medium: >20% slower'
    WHEN rr.recent_avg_min < jd.avg_duration_min * 0.7 THEN '🟢 Improved: >30% faster'
    ELSE '✅ Normal range'
  END AS status,
  CASE 
    WHEN rr.recent_avg_min > jd.p95_duration_min THEN 'Check for data growth, cluster sizing, or new dependencies'
    WHEN rr.recent_avg_min > jd.avg_duration_min * 1.5 THEN 'Review recent code changes or data volume increases'
    WHEN jd.std_dev_min > jd.avg_duration_min * 0.5 THEN 'High variability - investigate data skew or resource contention'
    ELSE 'Duration within expected range'
  END AS recommendation
FROM job_durations jd
LEFT JOIN recent_runs rr ON jd.job_id = rr.job_id
WHERE ABS(COALESCE(rr.recent_avg_min, jd.avg_duration_min) - jd.avg_duration_min) > jd.avg_duration_min * 0.1
ORDER BY ABS(rr.recent_avg_min - jd.avg_duration_min) DESC
LIMIT 15
```

---

### Dataset 25: ds_monitor_latest

**Display Name:** Monitor: Latest  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  ROUND(COALESCE(success_rate, 0), 1) AS success_rate_pct,
  COALESCE(total_runs, 0) AS total_runs,
  ROUND(COALESCE(p95_duration_minutes, 0), 1) AS p95_duration
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window.start DESC
LIMIT 1
```

---

### Dataset 26: ds_monitor_trend

**Display Name:** Monitor: Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  window.start AS window_start,
  ROUND(COALESCE(success_rate, 0), 1) AS success_rate,
  ROUND(COALESCE(failure_rate, 0), 1) AS failure_rate,
  ROUND(COALESCE(timeout_rate, 0), 1) AS timeout_rate
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE window.start >= :time_range.min
  AND column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window_start
```

---

### Dataset 27: ds_monitor_duration

**Display Name:** Monitor: Duration  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  window.start AS window_start,
  ROUND(COALESCE(avg_duration_minutes, 0), 1) AS avg_duration,
  ROUND(COALESCE(p50_duration_minutes, 0), 1) AS p50_duration,
  ROUND(COALESCE(p95_duration_minutes, 0), 1) AS p95_duration,
  ROUND(COALESCE(p99_duration_minutes, 0), 1) AS p99_duration
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE window.start >= :time_range.min
  AND column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window_start
```

---

### Dataset 28: ds_monitor_run_types

**Display Name:** Monitor: Run Types  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  window.start AS window_start,
  COALESCE(scheduled_runs, 0) AS scheduled_runs,
  COALESCE(manual_runs, 0) AS manual_runs,
  COALESCE(retry_runs, 0) AS retry_runs
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE window.start >= :time_range.min
  AND column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window_start
```

---

### Dataset 29: ds_monitor_errors

**Display Name:** Monitor: Errors  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  window.start AS window_start,
  COALESCE(timeout_count, 0) AS timeout_count,
  COALESCE(cancelled_count, 0) AS cancelled_count,
  COALESCE(internal_error_count, 0) AS internal_error_count
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE window.start >= :time_range.min
  AND column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window_start
```

---

### Dataset 30: ds_monitor_drift

**Display Name:** Monitor: Drift  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  window.start AS window_start,
  ROUND(COALESCE(success_rate_drift, 0), 2) AS success_rate_drift,
  ROUND(COALESCE(duration_drift_pct, 0), 2) AS duration_drift,
  ROUND(COALESCE(run_count_drift_pct, 0), 2) AS volume_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_drift_metrics
WHERE window.start >= :time_range.min
  AND column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
  AND slice_key IS NULL
ORDER BY window.start
```

---

### Dataset 31: ds_monitor_detailed

**Display Name:** Monitor: Detailed  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  window.start AS window_start,
  COALESCE(total_runs, 0) AS total_runs,
  ROUND(COALESCE(success_rate, 0), 1) AS success_rate,
  ROUND(COALESCE(failure_rate, 0), 1) AS failure_rate,
  ROUND(COALESCE(p95_duration_minutes, 0), 1) AS p95_duration,
  COALESCE(retry_runs, 0) AS retry_runs,
  COALESCE(distinct_jobs, 0) AS distinct_jobs
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE window.start >= :time_range.min
  AND column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
ORDER BY window_start DESC
```

---

### Dataset 32: ds_no_autoscale_count

**Display Name:** No Autoscale Count  
**SQL Query:**
```sql
SELECT COUNT(DISTINCT j.job_id) AS count FROM ${catalog}.${gold_schema}.dim_job j WHERE j.delete_time IS NULL
```

---

### Dataset 33: ds_stale_count

**Display Name:** Stale Count  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT entity_metadata_job_id) AS count FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE 1=1  AND  event_date BETWEEN :time_range.min AND :time_range.max AND target_table_full_name IS NOT NULL AND entity_type = 'JOB'
```

---

### Dataset 34: ds_ap_count

**Display Name:** Ap Count  
**SQL Query:**
```sql
SELECT COUNT(DISTINCT j.job_id) AS count FROM ${catalog}.${gold_schema}.dim_job j WHERE j.delete_time IS NULL
```

---

### Dataset 35: ds_no_autoscale

**Display Name:** No Autoscale  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT j.name AS job_name, w.workspace_name, ROUND(COALESCE(u.total_cost, 0), 2) AS cost_30d FROM ${catalog}.${gold_schema}.dim_job j LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON j.workspace_id = w.workspace_id LEFT JOIN (SELECT usage_metadata_job_id AS job_id, SUM(list_cost) AS total_cost FROM ${catalog}.${gold_schema}.fact_usage  WHERE usage_date BETWEEN :time_range.min AND :time_range.max AND usage_metadata_job_id IS NOT NULL GROUP BY usage_metadata_job_id) u ON j.job_id = u.job_id AND j.delete_time IS NULL ORDER BY cost_30d DESC LIMIT 20
```

---

### Dataset 36: ds_stale_datasets

**Display Name:** Stale Datasets  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT COALESCE(j.name, CONCAT('Job ', l.entity_metadata_job_id)) AS job_name, COUNT(DISTINCT l.target_table_full_name) AS unused_tables, COUNT(DISTINCT l.event_date) AS runs_30d FROM ${catalog}.${gold_schema}.fact_table_lineage l LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON l.entity_metadata_job_id = j.job_id AND l.workspace_id = j.workspace_id WHERE 1=1 AND l.event_date BETWEEN :time_range.min AND :time_range.max AND l.target_table_full_name IS NOT NULL AND l.entity_type = 'JOB' GROUP BY COALESCE(j.name, CONCAT('Job ', l.entity_metadata_job_id)) ORDER BY runs_30d DESC LIMIT 20
```

---

### Dataset 37: ds_ap_jobs

**Display Name:** Ap Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT COALESCE(j.name, f.job_id) AS job_name, w.workspace_name, 'Interactive Cluster' AS cluster_name, COUNT(*) AS task_runs FROM ${catalog}.${gold_schema}.fact_job_run_timeline f LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.job_id = j.job_id AND f.workspace_id = j.workspace_id LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.run_date BETWEEN :time_range.min AND :time_range.max GROUP BY COALESCE(j.name, f.job_id), w.workspace_name ORDER BY task_runs DESC LIMIT 20
```

---

### Dataset 38: ds_outliers

**Display Name:** Outliers  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `param_job_status` (STRING) - param_job_status

**SQL Query:**
```sql
WITH job_stats AS (SELECT COALESCE(j.name, f.job_id) AS job_name, f.job_id, COUNT(*) AS runs, AVG(TIMESTAMPDIFF(SECOND, f.run_date, f.period_end_time)) AS avg_duration, PERCENTILE(TIMESTAMPDIFF(SECOND, f.run_date, f.period_end_time), 0.9) AS p90_duration, MAX(TIMESTAMPDIFF(SECOND, f.run_date, f.period_end_time)) AS max_duration FROM ${catalog}.${gold_schema}.fact_job_run_timeline f LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.job_id = j.job_id AND f.workspace_id = j.workspace_id WHERE f.run_date BETWEEN :time_range.min AND :time_range.max AND f.result_state IS NOT NULL GROUP BY COALESCE(j.name, f.job_id), f.job_id HAVING COUNT(*) > 5) SELECT job_name, runs, ROUND(avg_duration / 60, 1) AS avg_cost, ROUND(p90_duration / 60, 1) AS p90_cost, ROUND(max_duration / 60, 1) AS max_cost, ROUND((max_duration - p90_duration) / 60, 1) AS deviation FROM job_stats ORDER BY deviation DESC LIMIT 20
```

---

### Dataset 39: ds_time_windows

**Display Name:** Time Windows  
**SQL Query:**
```sql
SELECT 'Last 7 Days' AS time_window UNION ALL SELECT 'Last 30 Days' UNION ALL SELECT 'Last 90 Days' UNION ALL SELECT 'Last 6 Months' UNION ALL SELECT 'Last Year' UNION ALL SELECT 'All Time'
```

---

### Dataset 40: ds_workspaces

**Display Name:** Workspaces  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name
```

---

### Dataset 41: select_workspace

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

### Dataset 42: select_time_key

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

### Dataset 43: ds_select_workspace

**Display Name:** ds_select_workspace  
**SQL Query:**
```sql
SELECT DISTINCT COALESCE(workspace_name, CAST(workspace_id AS STRING)) AS workspace_name FROM ${catalog}.${gold_schema}.dim_workspace ORDER BY 1
```

---

### Dataset 44: ds_select_job_status

**Display Name:** ds_select_job_status  
**SQL Query:**
```sql
SELECT 'All' AS status UNION ALL SELECT 'SUCCESS' UNION ALL SELECT 'FAILED' UNION ALL SELECT 'CANCELED'
```

---

### Dataset 45: ds_monitor_reliability_aggregate

**Display Name:** Reliability Aggregate Metrics  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
-- Reliability aggregate metrics from fact_job_run_timeline
SELECT
  DATE(period_start_time) AS window_start,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
  SUM(CASE WHEN result_state IN ('FAILED', 'ERROR') THEN 1 ELSE 0 END) AS failure_count,
  SUM(CASE WHEN result_state = 'TIMEDOUT' OR termination_code = 'TIMED_OUT' THEN 1 ELSE 0 END) AS timeout_count,
  COUNT(DISTINCT job_id) AS distinct_jobs
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time >= :monitor_time_start
  AND period_start_time <= COALESCE(:monitor_time_end, CURRENT_TIMESTAMP())
GROUP BY DATE(period_start_time)
ORDER BY window_start DESC
```

---

### Dataset 46: ds_monitor_reliability_derived

**Display Name:** Reliability Derived KPIs  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
SELECT 
  window.start AS window_start,
  window.end AS window_end,
  ROUND(COALESCE(success_rate, 0), 2) AS success_rate,
  ROUND(COALESCE(failure_rate, 0), 2) AS failure_rate,
  ROUND(COALESCE(timeout_rate, 0), 2) AS timeout_rate
FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND window.start >= :monitor_time_start
  AND window.end <= :monitor_time_end
  AND COALESCE(slice_key, 'No Slice') = :monitor_slice_key
  AND COALESCE(slice_value, 'No Slice') = :monitor_slice_value
ORDER BY window.start DESC
```

---

### Dataset 47: ds_monitor_reliability_drift

**Display Name:** Reliability Drift Metrics  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
-- Calculate week-over-week drift from fact_job_run_timeline
WITH weekly_stats AS (
  SELECT
    DATE_TRUNC('week', period_start_time) AS week_start,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS successes,
    ROUND(AVG(total_duration_ms / 60000.0), 2) AS avg_duration_min
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE period_start_time >= :monitor_time_start
    AND period_start_time <= COALESCE(:monitor_time_end, CURRENT_TIMESTAMP())
  GROUP BY DATE_TRUNC('week', period_start_time)
),
drift_calc AS (
  SELECT
    week_start AS window_start,
    total_runs,
    successes,
    avg_duration_min,
    LAG(total_runs) OVER (ORDER BY week_start) AS prev_runs,
    LAG(successes) OVER (ORDER BY week_start) AS prev_successes,
    LAG(avg_duration_min) OVER (ORDER BY week_start) AS prev_duration
  FROM weekly_stats
)
SELECT
  window_start,
  ROUND(CASE WHEN prev_successes > 0 THEN ((successes * 100.0 / total_runs) - (prev_successes * 100.0 / prev_runs)) ELSE 0 END, 2) AS success_rate_drift,
  ROUND(CASE WHEN prev_duration > 0 THEN ((avg_duration_min - prev_duration) / prev_duration * 100) ELSE 0 END, 2) AS duration_drift,
  ROUND(CASE WHEN prev_runs > 0 THEN ((total_runs - prev_runs) / prev_runs * 100.0) ELSE 0 END, 2) AS volume_drift
FROM drift_calc
WHERE prev_runs IS NOT NULL
ORDER BY window_start
```

---

### Dataset 48: ds_monitor_reliability_slice_keys

**Display Name:** Reliability Slice Keys  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end

**SQL Query:**
```sql
WITH profile_metrics AS (
  SELECT DISTINCT slice_key
  FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
  WHERE window.start >= :monitor_time_start 
    AND window.end <= :monitor_time_end
    AND slice_key IS NOT NULL
)
SELECT 'No Slice' AS slice_key
UNION ALL
SELECT slice_key FROM profile_metrics
ORDER BY slice_key
```

---

### Dataset 49: ds_monitor_reliability_slice_values

**Display Name:** Reliability Slice Values  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key

**SQL Query:**
```sql
WITH profile_metrics AS (
  SELECT DISTINCT slice_value, COALESCE(slice_key, 'No Slice') AS sk
  FROM ${catalog}.${gold_schema}_monitoring.fact_job_run_timeline_profile_metrics
  WHERE window.start >= :monitor_time_start 
    AND window.end <= :monitor_time_end
    AND slice_value IS NOT NULL
)
SELECT 'No Slice' AS slice_value
UNION ALL
SELECT slice_value FROM profile_metrics WHERE sk = :monitor_slice_key
ORDER BY slice_value
```

---
