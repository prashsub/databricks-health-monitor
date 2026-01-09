# Reliability Domain - Actual Implementation

## Overview

**Dashboard:** `reliability.lvdash.json`  
**Total Datasets:** 49  
**Primary Tables:**
- `fact_job_run_timeline` (job run events with status)
- `fact_job_run_timeline_profile_metrics` (Lakehouse Monitoring aggregated metrics)
- `fact_job_run_timeline_drift_metrics` (week-over-week drift detection)
- `dim_job` (job metadata)
- `dim_workspace` (workspace metadata)
- `dim_user` (user lookup for owner resolution)

---

## 📊 Metrics Catalog

### Success/Failure Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **Success Rate %** | `(success_count / total_runs) * 100` | fact_job_run_timeline | KPI card |
| **Failure Rate %** | `(failed_count / total_runs) * 100` | fact_job_run_timeline | KPI card |
| **Total Runs** | `COUNT(run_id)` | fact_job_run_timeline | KPI card |
| **Failed Today** | `COUNT(run_id)` WHERE failed today | fact_job_run_timeline | KPI card |
| **Success Trend** | Daily success rate over time | fact_job_run_timeline | Line chart |
| **Runs by Status** | `COUNT(run_id)` GROUP BY result_state | fact_job_run_timeline | Pie chart |

### Duration Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **Avg Duration (seconds)** | `AVG(duration_seconds)` | fact_job_run_timeline | KPI card |
| **P95 Duration** | `PERCENTILE_CONT(0.95)` of duration | fact_job_run_timeline | KPI card |
| **Duration Trend** | Daily average duration | fact_job_run_timeline | Line chart |
| **Duration Regression** | Jobs with >20% duration increase | fact_job_run_timeline | Table |
| **Duration Outliers** | Jobs >3 std dev from mean | fact_job_run_timeline | Table |
| **Slowest Jobs** | Top 20 by average duration | fact_job_run_timeline | Bar chart |

### Recovery Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **MTTR (hours)** | Mean time to recovery from failures | fact_job_run_timeline | KPI card |
| **Repair Count** | `COUNT(run_id)` WHERE termination_type = 'REPAIRED' | fact_job_run_timeline | KPI card |
| **Retry Success Rate %** | `(successful_retries / total_retries) * 100` | fact_job_run_timeline | KPI card |
| **Most Repaired Jobs** | Jobs with highest repair counts | fact_job_run_timeline | Table |
| **Self-Healing Success** | ML prediction of retry success | ML model | Table |

### Incident Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **Critical Failures** | Failed jobs with HIGH severity | fact_job_run_timeline | KPI card |
| **Failure by Type** | `COUNT(run_id)` GROUP BY termination_type | fact_job_run_timeline | Bar chart |
| **Failure Trend by Type** | Daily failure counts by type | fact_job_run_timeline | Stacked area |
| **Error Categories** | `COUNT(run_id)` GROUP BY error_category | fact_job_run_timeline | Pie chart |

### ML Prediction Metrics

| Metric Name | Calculation | Source | Dashboard Widget |
|-------------|-------------|--------|------------------|
| **Failure Risk Score** | ML prediction of failure probability | ML model | Table |
| **Pipeline Health Score** | ML overall health assessment | ML model | Gauge |
| **Incident Impact Severity** | ML severity classification | ML model | Table |
| **Duration Forecast** | ML predicted future duration | ML model | Line chart |

---

## 🗃️ Dataset Catalog

### KPI Metrics (4 datasets)

#### ds_kpi_success_rate
**Purpose:** Overall success rate percentage  
**Type:** Single-value KPI  
**Query:**
```sql
SELECT 
  CONCAT(
    ROUND(
      SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / 
      COUNT(*), 
    1), 
    '%'
  ) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
```

#### ds_kpi_totals
**Purpose:** Total runs, successes, failures  
**Type:** Multi-value KPI  
**Query:**
```sql
SELECT 
  COUNT(*) AS total_runs,
  SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
  SUM(CASE WHEN result_state IN ('FAILED', 'TIMEDOUT', 'CANCELED') THEN 1 ELSE 0 END) AS failure_count
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
```

#### ds_kpi_duration
**Purpose:** Average and P95 duration  
**Type:** Multi-value KPI  
**Query:**
```sql
SELECT 
  ROUND(AVG(duration_seconds), 0) AS avg_duration_seconds,
  ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds), 0) AS p95_duration_seconds
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
  AND result_state = 'SUCCESS'
```

#### ds_kpi_mttr
**Purpose:** Mean Time To Recovery  
**Type:** Single-value KPI  
**Query:**
```sql
WITH failures AS (
  SELECT 
    job_id,
    period_start_time AS failure_time,
    LEAD(period_start_time) OVER (PARTITION BY job_id ORDER BY period_start_time) AS next_run_time,
    LEAD(result_state) OVER (PARTITION BY job_id ORDER BY period_start_time) AS next_result
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE result_state IN ('FAILED', 'TIMEDOUT')
    AND period_start_time BETWEEN :time_range.min AND :time_range.max
)
SELECT 
  ROUND(
    AVG(TIMESTAMPDIFF(HOUR, failure_time, next_run_time)),
  1) AS mttr_hours
FROM failures
WHERE next_result = 'SUCCESS'
```

---

### Analytics & Reporting (27 datasets)

#### ds_success_trend
**Purpose:** Daily success rate trend  
**Type:** Time series  
**Query:**
```sql
SELECT 
  DATE(period_start_time) AS run_date,
  ROUND(
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / 
    COUNT(*), 
  1) AS success_rate,
  COUNT(*) AS total_runs
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
GROUP BY DATE(period_start_time)
ORDER BY run_date
```

#### ds_failed_today
**Purpose:** Failed jobs today for immediate attention  
**Type:** Alert table  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  r.result_state,
  r.termination_type,
  r.error_message,
  r.period_start_time AS failure_time,
  ROUND(r.duration_seconds / 60, 1) AS duration_minutes
FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON r.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON COALESCE(j.run_as, j.creator_id) = u.user_id
WHERE DATE(r.period_start_time) = CURRENT_DATE()
  AND r.result_state IN ('FAILED', 'TIMEDOUT', 'CANCELED')
ORDER BY r.period_start_time DESC
```

#### ds_low_success_jobs
**Purpose:** Jobs with <80% success rate in time window  
**Type:** Risk table  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN r.result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
  ROUND(
    SUM(CASE WHEN r.result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / 
    COUNT(*), 
  1) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON r.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON COALESCE(j.run_as, j.creator_id) = u.user_id
WHERE r.period_start_time BETWEEN :time_range.min AND :time_range.max
GROUP BY 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)),
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)),
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown')
HAVING success_rate < 80.0
ORDER BY success_rate ASC, total_runs DESC
LIMIT 50
```

#### ds_highest_failure_jobs
**Purpose:** Top 20 jobs by failure count  
**Type:** Ranked table  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  SUM(CASE WHEN r.result_state IN ('FAILED', 'TIMEDOUT', 'CANCELED') THEN 1 ELSE 0 END) AS failure_count,
  COUNT(*) AS total_runs,
  ROUND(
    SUM(CASE WHEN r.result_state IN ('FAILED', 'TIMEDOUT', 'CANCELED') THEN 1 ELSE 0 END) * 100.0 / 
    COUNT(*), 
  1) AS failure_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON r.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON COALESCE(j.run_as, j.creator_id) = u.user_id
WHERE r.period_start_time BETWEEN :time_range.min AND :time_range.max
GROUP BY 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)),
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)),
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown')
ORDER BY failure_count DESC
LIMIT 20
```

#### ds_failure_by_type
**Purpose:** Failure distribution by termination type  
**Type:** Category breakdown  
**Query:**
```sql
SELECT 
  termination_type,
  COUNT(*) AS failure_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
  AND result_state IN ('FAILED', 'TIMEDOUT', 'CANCELED')
GROUP BY termination_type
ORDER BY failure_count DESC
```

#### ds_slowest_jobs
**Purpose:** Top 20 jobs by average duration  
**Type:** Ranked table  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  COUNT(*) AS run_count,
  ROUND(AVG(r.duration_seconds), 0) AS avg_duration_seconds,
  ROUND(MIN(r.duration_seconds), 0) AS min_duration_seconds,
  ROUND(MAX(r.duration_seconds), 0) AS max_duration_seconds
FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON r.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON COALESCE(j.run_as, j.creator_id) = u.user_id
WHERE r.period_start_time BETWEEN :time_range.min AND :time_range.max
  AND r.result_state = 'SUCCESS'
GROUP BY 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)),
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)),
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown')
ORDER BY avg_duration_seconds DESC
LIMIT 20
```

#### ds_duration_regression
**Purpose:** Jobs with >20% duration increase  
**Type:** Alert table  
**Query:**
```sql
WITH current_period AS (
  SELECT 
    job_id,
    AVG(duration_seconds) AS avg_duration
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
    AND result_state = 'SUCCESS'
  GROUP BY job_id
),
previous_period AS (
  SELECT 
    job_id,
    AVG(duration_seconds) AS avg_duration
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE period_start_time BETWEEN 
    DATE_SUB(:time_range.min, DATEDIFF(:time_range.max, :time_range.min)) 
    AND :time_range.min
    AND result_state = 'SUCCESS'
  GROUP BY job_id
)
SELECT 
  COALESCE(j.job_name, CAST(c.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(j.workspace_id AS STRING)) AS workspace_name,
  ROUND(p.avg_duration, 0) AS previous_avg_seconds,
  ROUND(c.avg_duration, 0) AS current_avg_seconds,
  ROUND(((c.avg_duration - p.avg_duration) / p.avg_duration) * 100, 1) AS regression_pct
FROM current_period c
INNER JOIN previous_period p ON c.job_id = p.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON c.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON j.workspace_id = w.workspace_id
WHERE ((c.avg_duration - p.avg_duration) / p.avg_duration) > 0.20  -- >20% increase
ORDER BY regression_pct DESC
LIMIT 30
```

#### ds_most_repaired
**Purpose:** Jobs requiring most manual repairs  
**Type:** Operational table  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)) AS workspace_name,
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
  COUNT(*) AS repair_count,
  MAX(r.period_start_time) AS last_repair_time
FROM ${catalog}.${gold_schema}.fact_job_run_timeline r
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON r.workspace_id = w.workspace_id
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON COALESCE(j.run_as, j.creator_id) = u.user_id
WHERE r.period_start_time BETWEEN :time_range.min AND :time_range.max
  AND r.termination_type = 'REPAIRED'
GROUP BY 
  COALESCE(j.job_name, CAST(r.job_id AS STRING)),
  COALESCE(w.workspace_name, CAST(r.workspace_id AS STRING)),
  COALESCE(u.email, j.run_as, j.creator_id, 'Unknown')
ORDER BY repair_count DESC, last_repair_time DESC
LIMIT 30
```

---

### Lakehouse Monitoring (12 datasets)

#### ds_monitor_latest
**Purpose:** Latest monitor metrics snapshot  
**Type:** Summary table  
**Source:** `fact_job_run_timeline_profile_metrics`  
**Query:**
```sql
SELECT 
  column_name AS metric_name,
  ROUND(CAST(column_values.aggregate_metrics['sum'] AS DOUBLE), 2) AS value,
  window_start_time AS as_of_time
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_profile_metrics
WHERE column_name = ':table'
  AND window_start_time = (
    SELECT MAX(window_start_time)
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline_profile_metrics
  )
ORDER BY metric_name
```

#### ds_monitor_trend
**Purpose:** Success rate trend from monitor  
**Type:** Time series  
**Source:** `fact_job_run_timeline_profile_metrics`  
**Query:**
```sql
SELECT 
  window_start_time AS date,
  ROUND(CAST(column_values.aggregate_metrics['avg'] AS DOUBLE), 2) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_profile_metrics
WHERE column_name = 'success_rate'
  AND window_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
ORDER BY window_start_time
```

#### ds_monitor_drift
**Purpose:** Week-over-week drift in key metrics  
**Type:** Drift alerts  
**Source:** `fact_job_run_timeline_drift_metrics`  
**Query:**
```sql
SELECT 
  column_name AS metric_name,
  ROUND(CAST(drift_values.drift_metrics['absolute_diff'] AS DOUBLE), 2) AS absolute_change,
  ROUND(CAST(drift_values.drift_metrics['percent_diff'] AS DOUBLE), 2) AS percent_change,
  drift_type,
  window_start_time
FROM ${catalog}.${gold_schema}.fact_job_run_timeline_drift_metrics
WHERE window_start_time = (
  SELECT MAX(window_start_time)
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline_drift_metrics
)
  AND ABS(CAST(drift_values.drift_metrics['percent_diff'] AS DOUBLE)) > 10.0
ORDER BY ABS(CAST(drift_values.drift_metrics['percent_diff'] AS DOUBLE)) DESC
LIMIT 10
```

#### ds_monitor_reliability_aggregate
**Purpose:** All aggregate metrics from monitor  
**Type:** Wide table for comprehensive dashboard  
**Source:** Aggregated directly from `fact_job_run_timeline`  
**Query:**
```sql
SELECT 
  DATE(period_start_time) AS date,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
  SUM(CASE WHEN result_state IN ('FAILED', 'TIMEDOUT', 'CANCELED') THEN 1 ELSE 0 END) AS failure_count,
  ROUND(
    SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
  2) AS success_rate,
  ROUND(AVG(duration_seconds), 2) AS avg_duration_seconds,
  ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds), 2) AS p95_duration_seconds
FROM ${catalog}.${gold_schema}.fact_job_run_timeline
WHERE period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DATE(period_start_time)
ORDER BY date DESC
```

---

### ML Predictions (6 datasets)

#### ds_ml_failure_risk
**Purpose:** Jobs at risk of failure based on ML model  
**Type:** Predictive alerts  
**Source:** ML model predictions  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(p.job_id AS STRING)) AS job_name,
  COALESCE(w.workspace_name, CAST(p.workspace_id AS STRING)) AS workspace_name,
  ROUND(p.failure_probability, 2) AS failure_risk,
  p.risk_category AS severity,
  p.contributing_factors,
  p.recommended_action,
  p.prediction_date
FROM ${catalog}.${feature_schema}.job_failure_risk_predictions p
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON p.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON p.workspace_id = w.workspace_id
WHERE p.prediction_date = CURRENT_DATE()
  AND p.failure_probability > 0.3  -- >30% risk
ORDER BY p.failure_probability DESC, p.job_id
LIMIT 50
```

#### ds_ml_retry_success
**Purpose:** Prediction of retry success likelihood  
**Type:** Operational guidance  
**Source:** ML model predictions  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(r1.job_id AS STRING)) AS job_name,
  r1.period_start_time AS failure_time,
  p.retry_success_probability,
  p.recommended_wait_hours,
  p.confidence_score
FROM ${catalog}.${gold_schema}.fact_job_run_timeline r1
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON r1.job_id = j.job_id
LEFT JOIN ${catalog}.${feature_schema}.retry_success_predictions p
  ON r1.job_id = p.job_id 
  AND DATE(r1.period_start_time) = p.prediction_date
WHERE r1.result_state IN ('FAILED', 'TIMEDOUT')
  AND r1.period_start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  -- Look ahead to see if retry happened
  AND EXISTS (
    SELECT 1 
    FROM ${catalog}.${gold_schema}.fact_job_run_timeline r2
    WHERE r2.job_id = r1.job_id
      AND r2.period_start_time > r1.period_start_time
      AND r2.period_start_time < r1.period_start_time + INTERVAL 4 HOURS
  )
ORDER BY p.retry_success_probability DESC
LIMIT 30
```

#### ds_ml_duration_forecast
**Purpose:** Predicted job duration for capacity planning  
**Type:** Forecasting  
**Source:** ML model predictions  
**Query:**
```sql
SELECT 
  COALESCE(j.job_name, CAST(p.job_id AS STRING)) AS job_name,
  ROUND(r.avg_duration_seconds, 0) AS historical_avg_seconds,
  ROUND(p.predicted_duration_seconds, 0) AS predicted_duration_seconds,
  ROUND(p.confidence_interval_lower, 0) AS ci_lower_seconds,
  ROUND(p.confidence_interval_upper, 0) AS ci_upper_seconds,
  p.prediction_date
FROM ${catalog}.${feature_schema}.job_duration_forecast_predictions p
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON p.job_id = j.job_id
LEFT JOIN (
  SELECT 
    job_id,
    AVG(duration_seconds) AS avg_duration_seconds
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE period_start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND result_state = 'SUCCESS'
  GROUP BY job_id
) r ON p.job_id = r.job_id
WHERE p.prediction_date = CURRENT_DATE()
ORDER BY p.predicted_duration_seconds DESC
LIMIT 50
```

---

## 🔍 SQL Query Patterns

### Success Rate Calculation Pattern
```sql
ROUND(
  SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / 
  COUNT(*), 
1) AS success_rate
```

### Duration Percentile Pattern
```sql
ROUND(
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds), 
0) AS p95_duration_seconds
```

### MTTR Calculation Pattern
```sql
WITH failures AS (
  SELECT 
    job_id,
    period_start_time AS failure_time,
    LEAD(period_start_time) OVER (PARTITION BY job_id ORDER BY period_start_time) AS next_run_time,
    LEAD(result_state) OVER (PARTITION BY job_id ORDER BY period_start_time) AS next_result
  FROM fact_job_run_timeline
  WHERE result_state IN ('FAILED', 'TIMEDOUT')
)
SELECT 
  AVG(TIMESTAMPDIFF(HOUR, failure_time, next_run_time)) AS mttr_hours
FROM failures
WHERE next_result = 'SUCCESS'
```

### Period-over-Period Comparison Pattern
```sql
WITH current_period AS (
  SELECT job_id, AVG(metric) AS current_avg
  FROM fact_job_run_timeline
  WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY job_id
),
previous_period AS (
  SELECT job_id, AVG(metric) AS prev_avg
  FROM fact_job_run_timeline
  WHERE period_start_time BETWEEN 
    DATE_SUB(:time_range.min, DATEDIFF(:time_range.max, :time_range.min)) 
    AND :time_range.min
  GROUP BY job_id
)
SELECT 
  c.job_id,
  p.prev_avg,
  c.current_avg,
  ((c.current_avg - p.prev_avg) / p.prev_avg) * 100 AS change_pct
FROM current_period c
INNER JOIN previous_period p ON c.job_id = p.job_id
```

---

## 📑 Data Source Reference

### fact_job_run_timeline Columns Used

| Column | Type | Purpose |
|--------|------|---------|
| `period_start_time` | TIMESTAMP | Time dimension |
| `job_id` | BIGINT | Job FK |
| `workspace_id` | BIGINT | Workspace FK |
| `run_id` | BIGINT | Unique run identifier |
| `result_state` | STRING | SUCCESS/FAILED/TIMEDOUT/CANCELED |
| `termination_type` | STRING | SUCCESS/FAILED/REPAIRED/etc |
| `duration_seconds` | BIGINT | Runtime |
| `error_message` | STRING | Failure reason |
| `error_category` | STRING | Classified error type |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial comprehensive documentation |

