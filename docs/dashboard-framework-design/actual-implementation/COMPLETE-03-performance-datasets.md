# Complete Query Performance Dataset Catalog

## Overview
**Total Datasets:** 75  
**Dashboard:** `performance.lvdash.json`  
**Coverage:** ALL datasets from ALL pages with FULL details

---

## Dataset Index

| # | Dataset Name | Display Name | Has Query | Parameters |
|---|--------------|--------------|-----------|------------|
| 1 | ds_kpi_queries | KPI: Queries | ✅ | time_range |
| 2 | ds_kpi_slow | KPI: Slow | ✅ | time_range |
| 3 | ds_kpi_failed | KPI: Failed | ✅ | time_range |
| 4 | ds_query_volume | Query Volume | ✅ | time_range |
| 5 | ds_duration_trend | Duration Trend | ✅ | time_range |
| 6 | ds_slowest_queries | Slowest Queries | ✅ | time_range |
| 7 | ds_slow_by_user | Slow by User | ✅ | time_range |
| 8 | ds_slow_by_warehouse | Slow by Warehouse | ✅ | time_range |
| 9 | ds_slow_query_trend | Slow Query Trend | ✅ | time_range |
| 10 | ds_failed_queries | Failed Queries | ✅ | time_range |
| 11 | ds_failed_by_error | Failed by Error | ✅ | time_range |
| 12 | ds_failed_trend | Failed Trend | ✅ | time_range |
| 13 | ds_warehouse_perf | Warehouse Performance | ✅ | time_range |
| 14 | ds_queries_by_warehouse | Queries by Warehouse | ✅ | time_range |
| 15 | ds_warehouse_hourly | Warehouse Hourly | ✅ | time_range |
| 16 | ds_warehouse_usage_trend | Warehouse Usage Over Time | ✅ | time_range |
| 17 | ds_warehouse_type_distribution | Usage by Warehouse Type | ✅ | time_range |
| 18 | ds_warehouse_config_snapshot | Warehouse Current Config | ✅ | - |
| 19 | ds_warehouse_long_queries | Long-Running Queries by Warehouse | ✅ | time_range |
| 20 | ds_query_source_distribution | Query Source Distribution | ✅ | time_range |
| 21 | ds_warehouse_cost_ranking | Top Warehouses by Cost | ✅ | time_range |
| 22 | ds_ml_optimization | ML: Optimization | ✅ | - |
| 23 | ds_ml_regression | ML: Regression | ✅ | - |
| 24 | ds_ml_warehouse | ML: Warehouse | ✅ | - |
| 25 | ds_monitor_latest | Monitor: Latest | ✅ | time_range |
| 26 | ds_monitor_trend | Monitor: Trend | ✅ | time_range |
| 27 | ds_monitor_volume | Monitor: Volume | ✅ | time_range |
| 28 | ds_monitor_drift | Monitor: Drift | ✅ | time_range |
| 29 | ds_monitor_detailed | Monitor: Detailed | ✅ | time_range |
| 30 | ds_drift_investigation | Drift Investigation | ✅ | time_range |
| 31 | ds_kpi_utilization | KPI: Utilization | ✅ | time_range |
| 32 | ds_kpi_underutilized | KPI: Underutilized | ✅ | time_range |
| 33 | ds_kpi_overutilized | KPI: Overutilized | ✅ | time_range |
| 34 | ds_cpu_trend | CPU Trend | ✅ | time_range |
| 35 | ds_memory_trend | Memory Trend | ✅ | time_range |
| 36 | ds_disk_io_trend | Disk I/O Trend | ✅ | time_range |
| 37 | ds_underutilized_clusters | Underutilized Clusters | ✅ | time_range, param_workspace |
| 38 | ds_overutilized_clusters | Overutilized Clusters | ✅ | time_range, param_workspace |
| 39 | ds_high_memory_swap | High Memory Swap | ✅ | time_range |
| 40 | ds_high_io_wait | High I/O Wait | ✅ | time_range, param_workspace |
| 41 | ds_utilization_distribution | Utilization Distribution | ✅ | time_range |
| 42 | ds_rightsizing_recommendations | Right-Sizing Recommendations | ✅ | - |
| 43 | ds_low_cpu_high_cost | Low CPU High Cost | ✅ | param_workspace |
| 44 | ds_high_memory_jobs | High Memory Jobs | ✅ | - |
| 45 | ds_savings_opportunity | Savings Opportunity | ✅ | - |
| 46 | ds_ml_capacity_predictions | ML: Capacity Predictions | ✅ | - |
| 47 | ds_ml_rightsizing | ML: Right-Sizing | ✅ | - |
| 48 | ds_ml_dbr_risk | ML: DBR Risk | ✅ | - |
| 49 | ds_monitor_cpu_trend | Monitor: CPU Trend | ✅ | time_range |
| 50 | ds_monitor_memory_trend | Monitor: Memory Trend | ✅ | time_range |
| 51 | ds_job_expensive | Most Expensive Jobs | ✅ | time_range |
| 52 | ds_job_cost_change | Jobs with Highest Cost Change | ✅ | time_range |
| 53 | ds_job_failure_cost | Job Failure Cost Analysis | ✅ | time_range |
| 54 | ds_job_ap_clusters | Jobs on All-Purpose Clusters | ✅ | time_range |
| 55 | ds_legacy_count | Legacy Count | ✅ | time_range |
| 56 | ds_serverless_adoption | Serverless Adoption | ✅ | time_range |
| 57 | ds_current_dbr | Current Dbr | ✅ | - |
| 58 | ds_dbr_dist | Dbr Dist | ✅ | time_range |
| 59 | ds_compute_type | Compute Type | ✅ | time_range |
| 60 | ds_legacy_jobs | Legacy Jobs | ✅ | time_range, param_workspace |
| 61 | ds_time_windows | Time Windows | ✅ | - |
| 62 | ds_workspaces | Workspaces | ✅ | param_workspace |
| 63 | select_workspace | select_workspace | ✅ | param_workspace |
| 64 | select_time_key | select_time_key | ✅ | - |
| 65 | ds_select_workspace | ds_select_workspace | ✅ | - |
| 66 | ds_select_warehouse_type | ds_select_warehouse_type | ✅ | - |
| 67 | ds_monitor_performance_aggregate | Performance Aggregate Metrics | ✅ | monitor_time_start, monitor_time_end |
| 68 | ds_monitor_performance_derived | Performance Derived KPIs | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 69 | ds_monitor_performance_slice_keys | Performance Slice Keys | ✅ | monitor_time_start, monitor_time_end |
| 70 | ds_monitor_performance_slice_values | Performance Slice Values | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key |
| 71 | ds_job_low_cpu | Jobs with Low CPU Utilization | ✅ | time_range |
| 72 | ds_job_high_mem | Jobs with High Memory Utilization | ✅ | time_range |
| 73 | ds_job_cost_savings | Job Cost Savings Opportunities | ✅ | time_range |
| 74 | ds_job_utilization_distribution | Job CPU Utilization Distribution | ✅ | time_range |
| 75 | ds_job_kpi_utilization | Job Utilization KPIs | ✅ | time_range |

---

## Complete SQL Queries


### Dataset 1: ds_kpi_queries

**Display Name:** KPI: Queries  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(*) AS total_queries, ROUND(AVG(total_duration_ms / 1000.0), 1) AS avg_duration, ROUND(PERCENTILE_APPROX(total_duration_ms / 1000.0, 0.95), 1) AS p95_duration, COUNT(DISTINCT executed_by_user_id) AS unique_users FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 2: ds_kpi_slow

**Display Name:** KPI: Slow  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT(ROUND(SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), '%') AS slow_queries_pct FROM ${catalog}.${gold_schema}.fact_query_history  WHERE start_time BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 3: ds_kpi_failed

**Display Name:** KPI: Failed  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT(ROUND(SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), '%') AS failed_queries_pct FROM ${catalog}.${gold_schema}.fact_query_history  WHERE start_time BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 4: ds_query_volume

**Display Name:** Query Volume  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, COUNT(*) AS query_count, COUNT(DISTINCT executed_by_user_id) AS unique_users FROM ${catalog}.${gold_schema}.fact_query_history  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 5: ds_duration_trend

**Display Name:** Duration Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, ROUND(AVG(total_duration_ms / 1000.0), 1) AS avg_duration, ROUND(PERCENTILE_APPROX(total_duration_ms / 1000.0, 0.95), 1) AS p95_duration FROM ${catalog}.${gold_schema}.fact_query_history  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 6: ds_slowest_queries

**Display Name:** Slowest Queries  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT statement_id AS query_id, CAST(executed_by_user_id AS STRING) AS user_identity_email, compute_type AS warehouse_name, ROUND(total_duration_ms / 1000.0, 1) AS duration_sec, execution_status AS status FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max ORDER BY total_duration_ms DESC LIMIT 20
```

---

### Dataset 7: ds_slow_by_user

**Display Name:** Slow by User  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT executed_by_user_id AS user_identity_email, SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) AS slow_queries, ROUND(AVG(total_duration_ms / 1000.0), 1) AS avg_duration, COUNT(*) AS total_queries FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 HAVING SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) > 0 ORDER BY slow_queries DESC LIMIT 15
```

---

### Dataset 8: ds_slow_by_warehouse

**Display Name:** Slow by Warehouse  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  LEFT(REGEXP_REPLACE(statement_text, '\\s+', ' '), 100) AS query_preview,
  ROUND(total_duration_ms / 1000.0, 1) AS duration_seconds,
  ROUND(total_duration_ms / 60000.0, 1) AS duration_minutes,
  executed_by_user_id AS user,
  compute_type AS warehouse_name,
  DATE(start_time) AS run_date,
  statement_id,
  CASE 
    WHEN total_duration_ms > 300000 THEN '🔴 Critical (>5min)'
    WHEN total_duration_ms > 120000 THEN '🟠 High (>2min)'
    WHEN total_duration_ms > 60000 THEN '🟡 Medium (>1min)'
    ELSE '⚪ Slow (>30s)'
  END AS severity
FROM ${catalog}.${gold_schema}.fact_query_history 
WHERE start_time BETWEEN :time_range.min AND :time_range.max
  AND total_duration_ms > 30000
  AND statement_text IS NOT NULL
ORDER BY total_duration_ms DESC
LIMIT 25
```

---

### Dataset 9: ds_slow_query_trend

**Display Name:** Slow Query Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) AS slow_queries, ROUND(SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS slow_pct FROM ${catalog}.${gold_schema}.fact_query_history  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 10: ds_failed_queries

**Display Name:** Failed Queries  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT statement_id AS query_id, CAST(executed_by_user_id AS STRING) AS user_identity_email, COALESCE(warehouse_name, compute_type) AS warehouse_name, error_message, start_time AS execution_time FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max AND execution_status = 'FAILED' ORDER BY start_time DESC LIMIT 30
```

---

### Dataset 11: ds_failed_by_error

**Display Name:** Failed by Error  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COALESCE(SUBSTRING(error_message, 1, 50), 'Unknown') AS error_category, COUNT(*) AS failure_count FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max AND execution_status = 'FAILED' GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

---

### Dataset 12: ds_failed_trend

**Display Name:** Failed Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count, ROUND(SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS failure_rate FROM ${catalog}.${gold_schema}.fact_query_history  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 13: ds_warehouse_perf

**Display Name:** Warehouse Performance  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT compute_type AS warehouse_name, COUNT(*) AS total_queries, ROUND(AVG(total_duration_ms / 1000.0), 2) AS avg_duration, ROUND(PERCENTILE_APPROX(total_duration_ms / 1000.0, 0.95), 2) AS p95_duration, ROUND(SUM(CASE WHEN execution_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS failure_rate, ROUND(SUM(COALESCE(read_bytes, 0)) / 1073741824.0, 2) AS data_scanned_gb, ROUND(SUM(CASE WHEN COALESCE(spilled_local_bytes, 0) > 0 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS spill_pct, COUNT(DISTINCT executed_by) AS active_users FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY total_queries DESC
```

---

### Dataset 14: ds_queries_by_warehouse

**Display Name:** Queries by Warehouse  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT compute_type AS warehouse_name, COUNT(*) AS query_count FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

---

### Dataset 15: ds_warehouse_hourly

**Display Name:** Warehouse Hourly  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT HOUR(start_time) AS hour, COUNT(*) AS query_count, ROUND(AVG(total_duration_ms / 1000.0), 1) AS avg_duration FROM ${catalog}.${gold_schema}.fact_query_history  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 16: ds_warehouse_usage_trend

**Display Name:** Warehouse Usage Over Time  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS usage_date, COALESCE(w.warehouse_name, f.compute_warehouse_id, 'Unknown') AS warehouse_name, COUNT(*) AS query_count, ROUND(SUM(total_duration_ms) / 1000.0 / 3600, 2) AS compute_hours FROM ${catalog}.${gold_schema}.fact_query_history f LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w ON f.workspace_id = w.workspace_id AND f.compute_warehouse_id = w.warehouse_id WHERE start_time BETWEEN :time_range.min AND :time_range.max AND f.compute_warehouse_id IS NOT NULL GROUP BY 1, 2 ORDER BY 1, 2
```

---

### Dataset 17: ds_warehouse_type_distribution

**Display Name:** Usage by Warehouse Type  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COALESCE(w.warehouse_type, 'UNKNOWN') AS warehouse_type, COUNT(*) AS query_count, ROUND(SUM(f.total_duration_ms) / 1000.0 / 3600, 2) AS compute_hours FROM ${catalog}.${gold_schema}.fact_query_history f LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w ON f.workspace_id = w.workspace_id AND f.compute_warehouse_id = w.warehouse_id WHERE f.start_time BETWEEN :time_range.min AND :time_range.max AND f.compute_warehouse_id IS NOT NULL GROUP BY 1 ORDER BY 2 DESC
```

---

### Dataset 18: ds_warehouse_config_snapshot

**Display Name:** Warehouse Current Config  
**SQL Query:**
```sql
SELECT w.warehouse_name, w.warehouse_type, w.warehouse_size, w.min_clusters, w.max_clusters, w.auto_stop_minutes, w.warehouse_channel, w.created_by FROM ${catalog}.${gold_schema}.dim_warehouse w WHERE w.delete_time IS NULL ORDER BY w.warehouse_name
```

---

### Dataset 19: ds_warehouse_long_queries

**Display Name:** Long-Running Queries by Warehouse  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COALESCE(w.warehouse_name, f.compute_warehouse_id, 'Unknown') AS warehouse_name, COUNT(*) AS total_queries, SUM(CASE WHEN f.total_duration_ms > 30000 THEN 1 ELSE 0 END) AS long_queries_30s, SUM(CASE WHEN f.total_duration_ms > 60000 THEN 1 ELSE 0 END) AS long_queries_60s, SUM(CASE WHEN f.total_duration_ms > 300000 THEN 1 ELSE 0 END) AS long_queries_5m, ROUND(100.0 * SUM(CASE WHEN f.total_duration_ms > 30000 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS long_query_pct FROM ${catalog}.${gold_schema}.fact_query_history f LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w ON f.workspace_id = w.workspace_id AND f.compute_warehouse_id = w.warehouse_id WHERE f.start_time BETWEEN :time_range.min AND :time_range.max AND f.compute_warehouse_id IS NOT NULL GROUP BY 1 ORDER BY long_query_pct DESC
```

---

### Dataset 20: ds_query_source_distribution

**Display Name:** Query Source Distribution  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CASE WHEN query_source_dashboard_id IS NOT NULL OR query_source_legacy_dashboard_id IS NOT NULL THEN 'Dashboard' WHEN query_source_notebook_id IS NOT NULL THEN 'Notebook' WHEN query_source_job_info IS NOT NULL THEN 'Job' WHEN query_source_sql_query_id IS NOT NULL THEN 'SQL Editor' WHEN query_source_genie_space_id IS NOT NULL THEN 'Genie Space' WHEN query_source_alert_id IS NOT NULL THEN 'Alert' WHEN query_source_pipeline_info IS NOT NULL THEN 'Pipeline' ELSE 'Other/Direct' END AS query_source, COUNT(*) AS query_count, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 2 DESC
```

---

### Dataset 21: ds_warehouse_cost_ranking

**Display Name:** Top Warehouses by Cost  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COALESCE(w.warehouse_name, f.compute_warehouse_id, 'Unknown') AS warehouse_name, w.warehouse_type, COUNT(*) AS total_queries, ROUND(SUM(f.total_duration_ms) / 1000.0 / 3600, 2) AS compute_hours, ROUND(SUM(f.read_bytes) / 1024.0 / 1024.0 / 1024.0, 2) AS data_scanned_gb FROM ${catalog}.${gold_schema}.fact_query_history f LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w ON f.workspace_id = w.workspace_id AND f.compute_warehouse_id = w.warehouse_id WHERE f.start_time BETWEEN :time_range.min AND :time_range.max AND f.compute_warehouse_id IS NOT NULL GROUP BY 1, 2 ORDER BY compute_hours DESC LIMIT 15
```

---

### Dataset 22: ds_ml_optimization

**Display Name:** ML: Optimization  
**SQL Query:**
```sql
WITH slow_patterns AS (
  SELECT
    LEFT(REGEXP_REPLACE(statement_text, '\\s+', ' '), 80) AS query_pattern,
    executed_by_user_id AS user,
    compute_type AS warehouse,
    ROUND(AVG(total_duration_ms / 1000.0), 1) AS avg_duration_sec,
    ROUND(MAX(total_duration_ms / 1000.0), 1) AS max_duration_sec,
    COUNT(*) AS execution_count,
    MAX(start_time) AS last_run,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) / 1000.0, 1) AS p95_duration_sec
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND total_duration_ms > 10000
    AND statement_text IS NOT NULL
  GROUP BY 1, 2, 3
  HAVING COUNT(*) >= 3
)
SELECT
  query_pattern,
  user,
  warehouse,
  avg_duration_sec,
  p95_duration_sec,
  execution_count,
  last_run,
  CASE 
    WHEN p95_duration_sec > 120 THEN '🔴 Critical'
    WHEN p95_duration_sec > 60 THEN '🟠 High'
    WHEN p95_duration_sec > 30 THEN '🟡 Medium'
    ELSE '⚪ Low'
  END AS severity,
  CASE 
    WHEN LOWER(query_pattern) LIKE '%select *%' THEN 'Avoid SELECT * - specify columns'
    WHEN LOWER(query_pattern) LIKE '%cross join%' THEN 'Replace CROSS JOIN with explicit joins'
    WHEN LOWER(query_pattern) LIKE '%not in%' THEN 'Replace NOT IN with LEFT JOIN / NOT EXISTS'
    WHEN LOWER(query_pattern) LIKE '%distinct%' THEN 'Review DISTINCT usage - may indicate join issues'
    WHEN p95_duration_sec > avg_duration_sec * 2 THEN 'High variance - check data skew or caching'
    WHEN execution_count > 100 THEN 'Frequent query - consider materialized view'
    ELSE 'Add indexes on filter/join columns'
  END AS optimization_tip,
  CONCAT('Query runs ', execution_count, 'x with P95 of ', p95_duration_sec, 's. Last run: ', DATE(last_run)) AS rationale
FROM slow_patterns
ORDER BY p95_duration_sec DESC
LIMIT 25
```

---

### Dataset 23: ds_ml_regression

**Display Name:** ML: Regression  
**SQL Query:**
```sql
WITH query_baseline AS (
  SELECT
    LEFT(REGEXP_REPLACE(statement_text, '\\s+', ' '), 60) AS query_pattern,
    executed_by_user_id AS user,
    compute_type AS warehouse,
    ROUND(AVG(CASE WHEN start_time < CURRENT_DATE() - INTERVAL 7 DAYS THEN total_duration_ms END) / 1000.0, 1) AS baseline_avg_sec,
    ROUND(AVG(CASE WHEN start_time >= CURRENT_DATE() - INTERVAL 7 DAYS THEN total_duration_ms END) / 1000.0, 1) AS recent_avg_sec,
    COUNT(CASE WHEN start_time < CURRENT_DATE() - INTERVAL 7 DAYS THEN 1 END) AS baseline_runs,
    COUNT(CASE WHEN start_time >= CURRENT_DATE() - INTERVAL 7 DAYS THEN 1 END) AS recent_runs,
    MAX(start_time) AS last_run
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND total_duration_ms > 5000
    AND statement_text IS NOT NULL
  GROUP BY 1, 2, 3
  HAVING COUNT(CASE WHEN start_time < CURRENT_DATE() - INTERVAL 7 DAYS THEN 1 END) >= 3
    AND COUNT(CASE WHEN start_time >= CURRENT_DATE() - INTERVAL 7 DAYS THEN 1 END) >= 2
)
SELECT
  query_pattern,
  user,
  warehouse,
  baseline_avg_sec,
  recent_avg_sec,
  ROUND((recent_avg_sec - baseline_avg_sec) * 100.0 / NULLIF(baseline_avg_sec, 0), 1) AS regression_pct,
  CASE 
    WHEN (recent_avg_sec - baseline_avg_sec) / NULLIF(baseline_avg_sec, 0) > 1.0 THEN '🔴 Major regression (>100%)'
    WHEN (recent_avg_sec - baseline_avg_sec) / NULLIF(baseline_avg_sec, 0) > 0.5 THEN '🟠 Significant (>50%)'
    WHEN (recent_avg_sec - baseline_avg_sec) / NULLIF(baseline_avg_sec, 0) > 0.25 THEN '🟡 Moderate (>25%)'
    ELSE '⚪ Minor'
  END AS severity,
  CASE 
    WHEN recent_runs > baseline_runs * 2 THEN 'Increased query frequency'
    WHEN recent_avg_sec > baseline_avg_sec * 2 THEN 'Data volume growth likely'
    WHEN LOWER(query_pattern) LIKE '%join%' THEN 'Check join statistics / table growth'
    ELSE 'Resource contention or config change'
  END AS root_cause,
  CONCAT('Baseline: ', baseline_avg_sec, 's (', baseline_runs, ' runs) → Recent: ', recent_avg_sec, 's (', recent_runs, ' runs). Last: ', DATE(last_run)) AS rationale,
  'Review query plan and table statistics. Consider adding indexes or updating stats.' AS recommended_action
FROM query_baseline
WHERE recent_avg_sec > baseline_avg_sec * 1.25
ORDER BY (recent_avg_sec - baseline_avg_sec) DESC
LIMIT 20
```

---

### Dataset 24: ds_ml_warehouse

**Display Name:** ML: Warehouse  
**SQL Query:**
```sql
WITH warehouse_stats AS (
  SELECT
    compute_type AS warehouse,
    COUNT(*) AS total_queries,
    COUNT(DISTINCT executed_by_user_id) AS unique_users,
    ROUND(AVG(total_duration_ms / 1000.0), 1) AS avg_duration_sec,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) / 1000.0, 1) AS p95_duration_sec,
    SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) AS slow_queries,
    MAX(start_time) AS last_query_time,
    ROUND(SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS slow_query_pct
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY 1
  HAVING COUNT(*) >= 10
)
SELECT
  warehouse,
  total_queries,
  unique_users,
  avg_duration_sec,
  p95_duration_sec,
  slow_queries,
  slow_query_pct,
  CASE 
    WHEN slow_query_pct > 20 THEN '🔴 Scale Up Required'
    WHEN slow_query_pct > 10 THEN '🟠 Consider Scaling'
    WHEN slow_query_pct > 5 THEN '🟡 Monitor Closely'
    WHEN slow_query_pct < 1 AND total_queries < 100 THEN '🔵 Consider Scale Down'
    ELSE '✅ Optimal'
  END AS recommendation,
  CASE 
    WHEN slow_query_pct > 20 THEN CONCAT(slow_query_pct, '% queries slow - upgrade to larger cluster size')
    WHEN slow_query_pct > 10 THEN CONCAT(slow_query_pct, '% queries slow - review query patterns or scale up')
    WHEN slow_query_pct > 5 THEN CONCAT(slow_query_pct, '% queries slow - optimize queries or add resources during peak')
    WHEN slow_query_pct < 1 AND total_queries < 100 THEN 'Low utilization - consider smaller size or auto-suspend'
    ELSE 'Performance is healthy'
  END AS rationale,
  CONCAT(total_queries, ' queries from ', unique_users, ' users. P95: ', p95_duration_sec, 's. Last activity: ', DATE(last_query_time)) AS evidence,
  CASE 
    WHEN slow_query_pct > 20 THEN 'Increase cluster size by 1 tier or enable auto-scaling'
    WHEN slow_query_pct > 10 THEN 'Review top slow queries for optimization opportunities'
    WHEN slow_query_pct < 1 AND total_queries < 100 THEN 'Reduce cluster size or increase auto-suspend timeout'
    ELSE 'No action needed'
  END AS recommended_action
FROM warehouse_stats
ORDER BY slow_query_pct DESC, total_queries DESC
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
  COALESCE(query_count, 0) AS total_queries,
  ROUND(COALESCE(avg_duration_sec, 0), 2) AS avg_duration,
  ROUND(COALESCE(sla_breach_rate, 0) * 100, 2) AS slow_query_rate,
  0 AS avg_cpu,
  0 AS avg_memory,
  0 AS total_nodes,
  0 AS avg_io_wait
FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start BETWEEN :time_range.min AND :time_range.max
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
  DATE(window.start) AS window_start,
  ROUND(COALESCE(avg_duration_sec, 0), 2) AS avg_duration,
  ROUND(COALESCE(p95_duration_sec, 0), 2) AS p95_duration
FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start BETWEEN :time_range.min AND :time_range.max
ORDER BY 1
```

---

### Dataset 27: ds_monitor_volume

**Display Name:** Monitor: Volume  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(start_time) AS window_start,
  COUNT(*) AS total_queries,
  COUNT(DISTINCT executed_by_user_id) AS unique_users
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time BETWEEN :time_range.min AND :time_range.max
GROUP BY 1
ORDER BY 1
```

---

### Dataset 28: ds_monitor_drift

**Display Name:** Monitor: Drift  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Calculate week-over-week drift for cluster utilization metrics
WITH daily_metrics AS (
  SELECT
    DATE(period_start_time) AS day,
    AVG(cpu_usage_pct) AS avg_cpu,
    AVG(memory_usage_pct) AS avg_memory,
    COUNT(DISTINCT node_id) AS node_count,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) AS p95_duration,
    COUNT(*) AS activity_count
  FROM ${catalog}.${gold_schema}.fact_node_timeline
  WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY 1
),
with_prev AS (
  SELECT
    day,
    avg_cpu,
    avg_memory,
    node_count,
    p95_duration,
    activity_count,
    LAG(avg_cpu, 7) OVER (ORDER BY day) AS prev_cpu,
    LAG(avg_memory, 7) OVER (ORDER BY day) AS prev_memory,
    LAG(p95_duration) OVER (ORDER BY day) AS prev_p95,
    LAG(activity_count) OVER (ORDER BY day) AS prev_count
  FROM daily_metrics
)
SELECT
  day AS window_start,
  ROUND(COALESCE((avg_cpu - prev_cpu) * 100.0 / NULLIF(prev_cpu, 0), 0), 1) AS cpu_drift,
  ROUND(COALESCE((avg_memory - prev_memory) * 100.0 / NULLIF(prev_memory, 0), 0), 1) AS memory_drift,
  ROUND(COALESCE((p95_duration - prev_p95) * 100.0 / NULLIF(prev_p95, 0), 0), 1) AS duration_drift,
  ROUND(COALESCE((activity_count - prev_count) * 100.0 / NULLIF(prev_count, 0), 0), 1) AS volume_drift
FROM with_prev
WHERE prev_cpu IS NOT NULL OR prev_p95 IS NOT NULL
ORDER BY day
```

---

### Dataset 29: ds_monitor_detailed

**Display Name:** Monitor: Detailed  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Aggregate cluster/node utilization metrics by day
SELECT 
  DATE(period_start_time) AS window_start,
  COUNT(DISTINCT node_id) AS total_nodes,
  ROUND(AVG(cpu_usage_pct), 1) AS avg_cpu,
  ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cpu_usage_pct), 1) AS p95_cpu,
  ROUND(AVG(memory_usage_pct), 1) AS avg_memory,
  ROUND(AVG(CASE WHEN disk_io_wait_time_ms > 0 THEN disk_io_wait_time_ms ELSE NULL END), 0) AS avg_io_wait,
  -- Query metrics (for context on Query Metrics Overview tab)
  COUNT(*) AS total_queries,
  ROUND(AVG(total_duration_ms / 1000.0), 2) AS avg_duration,
  ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) / 1000.0, 2) AS p95_duration,
  ROUND(SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS slow_query_rate,
  0 AS failure_rate
FROM ${catalog}.${gold_schema}.fact_node_timeline
WHERE period_start_time BETWEEN :time_range.min AND :time_range.max
GROUP BY 1
ORDER BY 1 DESC
```

---

### Dataset 30: ds_drift_investigation

**Display Name:** Drift Investigation  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH daily_p95 AS (
  SELECT
    DATE(start_time) AS day,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) AS p95_today
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY 1
),
with_drift AS (
  SELECT
    day,
    p95_today,
    LAG(p95_today) OVER (ORDER BY day) AS p95_yesterday,
    ROUND((p95_today - LAG(p95_today) OVER (ORDER BY day)) * 100.0 / NULLIF(LAG(p95_today) OVER (ORDER BY day), 0), 1) AS drift_pct
  FROM daily_p95
),
high_drift_days AS (
  SELECT day FROM with_drift WHERE ABS(drift_pct) > 50
),
contributors AS (
  SELECT
    DATE(q.start_time) AS spike_date,
    LEFT(REGEXP_REPLACE(q.statement_text, '\\s+', ' '), 60) AS query_pattern,
    q.executed_by_user_id AS user,
    COALESCE(q.warehouse_name, q.compute_type) AS warehouse,
    COUNT(*) AS executions,
    ROUND(AVG(q.total_duration_ms / 1000.0), 1) AS avg_duration_sec,
    ROUND(MAX(q.total_duration_ms / 1000.0), 1) AS max_duration_sec,
    ROUND(SUM(q.total_duration_ms / 1000.0), 0) AS total_time_sec
  FROM ${catalog}.${gold_schema}.fact_query_history q
  INNER JOIN high_drift_days h ON DATE(q.start_time) = h.day
  WHERE q.total_duration_ms > 10000
  GROUP BY 1, 2, 3, 4
)
SELECT
  spike_date,
  query_pattern,
  user,
  warehouse,
  executions,
  avg_duration_sec,
  max_duration_sec,
  total_time_sec,
  CASE 
    WHEN total_time_sec > 3600 THEN '🔴 Major Impact'
    WHEN total_time_sec > 600 THEN '🟠 High Impact'
    WHEN total_time_sec > 60 THEN '🟡 Medium Impact'
    ELSE '⚪ Low Impact'
  END AS impact,
  CONCAT('Query ran ', executions, 'x, total ', ROUND(total_time_sec/60, 1), ' min on spike day') AS investigation_note
FROM contributors
ORDER BY spike_date DESC, total_time_sec DESC
LIMIT 30
```

---

### Dataset 31: ds_kpi_utilization

**Display Name:** KPI: Utilization  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT(ROUND(AVG(cpu_user_percent + cpu_system_percent), 1), '%') AS avg_cpu, CONCAT(ROUND(AVG(mem_used_percent), 1), '%') AS avg_memory, FORMAT_NUMBER(COUNT(DISTINCT cluster_id), 0) AS total_nodes, FORMAT_NUMBER(COUNT(DISTINCT cluster_id), 0) AS total_clusters FROM ${catalog}.${gold_schema}.fact_node_timeline  WHERE start_time BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 32: ds_kpi_underutilized

**Display Name:** KPI: Underutilized  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH cluster_util AS (SELECT cluster_id, AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu FROM ${catalog}.${gold_schema}.fact_node_timeline WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1) SELECT CONCAT(ROUND(SUM(CASE WHEN avg_cpu < 30 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), '%') AS underutilized_pct FROM cluster_util
```

---

### Dataset 33: ds_kpi_overutilized

**Display Name:** KPI: Overutilized  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH cluster_util AS (SELECT cluster_id, AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu FROM ${catalog}.${gold_schema}.fact_node_timeline WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1) SELECT CONCAT(ROUND(SUM(CASE WHEN avg_cpu > 80 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), '%') AS overutilized_pct FROM cluster_util
```

---

### Dataset 34: ds_cpu_trend

**Display Name:** CPU Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, ROUND(AVG(cpu_user_percent + cpu_system_percent), 1) AS avg_cpu, ROUND(MAX(cpu_user_percent + cpu_system_percent), 1) AS peak_cpu FROM ${catalog}.${gold_schema}.fact_node_timeline  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 35: ds_memory_trend

**Display Name:** Memory Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, ROUND(AVG(mem_used_percent), 1) AS avg_memory, ROUND(MAX(mem_used_percent), 1) AS peak_memory FROM ${catalog}.${gold_schema}.fact_node_timeline  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 36: ds_disk_io_trend

**Display Name:** Disk I/O Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, ROUND(AVG(cpu_wait_percent), 1) AS avg_disk_wait, ROUND(MAX(cpu_wait_percent), 1) AS peak_disk_wait FROM ${catalog}.${gold_schema}.fact_node_timeline  WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 37: ds_underutilized_clusters

**Display Name:** Underutilized Clusters  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH cluster_stats AS (SELECT n.cluster_id, MAX(c.cluster_name) AS cluster_name, MAX(w.workspace_name) AS workspace_name, AVG(n.cpu_user_percent + n.cpu_system_percent) AS avg_cpu, AVG(n.mem_used_percent) AS avg_memory FROM ${catalog}.${gold_schema}.fact_node_timeline n LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON n.cluster_id = c.cluster_id LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON n.workspace_id = w.workspace_id WHERE n.start_time BETWEEN :time_range.min AND :time_range.max GROUP BY n.cluster_id) SELECT COALESCE(cluster_name, cluster_id) AS cluster_name, workspace_name, ROUND(avg_cpu, 1) AS avg_cpu, ROUND(avg_memory, 1) AS avg_memory, 0.00 AS estimated_cost, ROUND((30 - avg_cpu) / 30 * 100, 2) AS potential_savings FROM cluster_stats WHERE avg_cpu < 30 ORDER BY avg_cpu ASC LIMIT 20
```

---

### Dataset 38: ds_overutilized_clusters

**Display Name:** Overutilized Clusters  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH cluster_stats AS (SELECT n.cluster_id, MAX(c.cluster_name) AS cluster_name, MAX(w.workspace_name) AS workspace_name, AVG(n.cpu_user_percent + n.cpu_system_percent) AS avg_cpu, MAX(n.cpu_user_percent + n.cpu_system_percent) AS peak_cpu, AVG(n.mem_used_percent) AS avg_memory FROM ${catalog}.${gold_schema}.fact_node_timeline n LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON n.cluster_id = c.cluster_id LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON n.workspace_id = w.workspace_id WHERE n.start_time BETWEEN :time_range.min AND :time_range.max GROUP BY n.cluster_id) SELECT COALESCE(cluster_name, cluster_id) AS cluster_name, workspace_name, ROUND(avg_cpu, 1) AS avg_cpu, ROUND(peak_cpu, 1) AS peak_cpu, ROUND(avg_memory, 1) AS avg_memory FROM cluster_stats WHERE avg_cpu > 80 ORDER BY avg_cpu DESC LIMIT 20
```

---

### Dataset 39: ds_high_memory_swap

**Display Name:** High Memory Swap  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH cluster_stats AS (SELECT n.cluster_id, MAX(c.cluster_name) AS cluster_name, AVG(n.mem_used_percent) AS avg_memory, MAX(n.mem_used_percent) AS peak_memory, SUM(CASE WHEN n.mem_used_percent > 90 THEN 1 ELSE 0 END) AS swap_events FROM ${catalog}.${gold_schema}.fact_node_timeline n LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON n.cluster_id = c.cluster_id WHERE n.start_time BETWEEN :time_range.min AND :time_range.max GROUP BY n.cluster_id) SELECT COALESCE(cluster_name, cluster_id) AS cluster_name, ROUND(avg_memory, 1) AS avg_memory, ROUND(peak_memory, 1) AS peak_memory, swap_events FROM cluster_stats WHERE peak_memory > 90 ORDER BY swap_events DESC LIMIT 15
```

---

### Dataset 40: ds_high_io_wait

**Display Name:** High I/O Wait  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH cluster_stats AS (SELECT n.cluster_id, MAX(c.cluster_name) AS cluster_name, MAX(w.workspace_name) AS workspace_name, AVG(n.cpu_wait_percent) AS avg_io_wait, MAX(n.cpu_wait_percent) AS peak_io_wait FROM ${catalog}.${gold_schema}.fact_node_timeline n LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON n.cluster_id = c.cluster_id LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON n.workspace_id = w.workspace_id WHERE n.start_time BETWEEN :time_range.min AND :time_range.max GROUP BY n.cluster_id) SELECT COALESCE(cluster_name, cluster_id) AS cluster_name, workspace_name, ROUND(avg_io_wait, 1) AS avg_io_wait, ROUND(peak_io_wait, 1) AS peak_io_wait FROM cluster_stats WHERE avg_io_wait > 10 ORDER BY avg_io_wait DESC LIMIT 15
```

---

### Dataset 41: ds_utilization_distribution

**Display Name:** Utilization Distribution  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH cluster_util AS (SELECT cluster_id, AVG(cpu_user_percent + cpu_system_percent) AS avg_cpu FROM ${catalog}.${gold_schema}.fact_node_timeline WHERE start_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1) SELECT CASE WHEN avg_cpu < 10 THEN '0-10%' WHEN avg_cpu < 20 THEN '10-20%' WHEN avg_cpu < 30 THEN '20-30%' WHEN avg_cpu < 50 THEN '30-50%' WHEN avg_cpu < 80 THEN '50-80%' ELSE '>80%' END AS utilization_bucket, COUNT(*) AS cluster_count FROM cluster_util GROUP BY 1 ORDER BY MIN(avg_cpu)
```

---

### Dataset 42: ds_rightsizing_recommendations

**Display Name:** Right-Sizing Recommendations  
**SQL Query:**
```sql
WITH warehouse_usage AS (
  SELECT
    COALESCE(compute_type, 'Unknown') AS cluster_name,
    COUNT(*) AS total_queries,
    ROUND(AVG(total_duration_ms / 1000.0), 1) AS avg_duration_sec,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) / 1000.0, 1) AS p95_duration_sec,
    SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) AS slow_queries,
    COUNT(DISTINCT executed_by_user_id) AS unique_users
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY 1
  HAVING COUNT(*) >= 10
),
cost_data AS (
  SELECT
    COALESCE(sku_name, 'All') AS wh_name,
    ROUND(SUM(list_cost), 2) AS total_cost_30d
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY 1
)
SELECT
  w.cluster_name,
  CASE 
    WHEN w.slow_queries * 100.0 / NULLIF(w.total_queries, 0) > 20 THEN 'Undersized'
    WHEN w.slow_queries * 100.0 / NULLIF(w.total_queries, 0) < 2 AND w.total_queries < 100 THEN 'Oversized'
    ELSE 'Current'
  END AS current_size,
  CASE 
    WHEN w.slow_queries * 100.0 / NULLIF(w.total_queries, 0) > 20 THEN '⬆️ Scale Up'
    WHEN w.slow_queries * 100.0 / NULLIF(w.total_queries, 0) < 2 AND w.total_queries < 100 THEN '⬇️ Scale Down'
    ELSE '✅ Optimal'
  END AS recommended_size,
  ROUND(w.slow_queries * 100.0 / NULLIF(w.total_queries, 0), 1) AS avg_cpu,
  ROUND(COALESCE(c.total_cost_30d, 0) * CASE WHEN w.slow_queries * 100.0 / NULLIF(w.total_queries, 0) < 2 AND w.total_queries < 100 THEN 0.3 ELSE 0 END, 2) AS potential_savings
FROM warehouse_usage w
LEFT JOIN cost_data c ON w.cluster_name = c.wh_name
ORDER BY potential_savings DESC, w.slow_queries DESC
LIMIT 15
```

---

### Dataset 43: ds_low_cpu_high_cost

**Display Name:** Low CPU High Cost  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
-- High-success, high-cost jobs that may be overprovisioned
WITH job_metrics AS (
  SELECT
    j.job_id,
    COALESCE(j.name, CAST(j.job_id AS STRING)) AS job_name,
    COALESCE(w.workspace_name, CAST(j.workspace_id AS STRING)) AS workspace_name,
    COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
    COUNT(*) AS total_runs,
    ROUND(AVG(f.run_duration_seconds), 0) AS avg_duration_sec,
    SUM(CASE WHEN f.termination_code = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_runs,
    ROUND(SUM(CASE WHEN f.termination_code = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS success_rate_pct
  FROM ${catalog}.${gold_schema}.dim_job j
  LEFT JOIN ${catalog}.${gold_schema}.fact_job_run_timeline f ON j.job_id = f.job_id AND j.workspace_id = f.workspace_id
  LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON j.workspace_id = w.workspace_id
  LEFT JOIN ${catalog}.${gold_schema}.dim_user u ON j.creator_id = u.user_id
  WHERE f.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, w.workspace_name))
  GROUP BY 1, 2, 3, 4
  HAVING COUNT(*) >= 3
),
job_costs AS (
  SELECT
    j.job_id,
    ROUND(SUM(u.list_cost), 2) AS cost_30d
  FROM ${catalog}.${gold_schema}.fact_usage u
  JOIN ${catalog}.${gold_schema}.dim_job j ON u.workspace_id = j.workspace_id
  WHERE u.usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY 1
)
SELECT
  m.job_name,
  m.workspace_name,
  m.owner,
  m.success_rate_pct,
  m.total_runs,
  COALESCE(c.cost_30d, 0) AS cost_30d,
  ROUND(COALESCE(c.cost_30d, 0) * 0.3, 2) AS potential_savings,
  CONCAT(
    'Job has ', m.success_rate_pct, '% success rate with $', COALESCE(c.cost_30d, 0), ' cost. ',
    'High success suggests overprovisioning. Review cluster size, auto-scaling config, and spot instance usage to save ~30%.'
  ) AS recommendation
FROM job_metrics m
LEFT JOIN job_costs c ON m.job_id = c.job_id
WHERE m.success_rate_pct > 90
  AND COALESCE(c.cost_30d, 0) > 10
ORDER BY c.cost_30d DESC NULLS LAST
LIMIT 15
```

---

### Dataset 44: ds_high_memory_jobs

**Display Name:** High Memory Jobs  
**SQL Query:**
```sql
-- Long-running jobs with duration variance indicating potential optimization opportunities
WITH job_duration AS (
  SELECT
    f.job_id,
    COALESCE(j.name, CAST(f.job_id AS STRING)) AS job_name,
    COALESCE(u.email, j.run_as, j.creator_id, 'Unknown') AS owner,
    COUNT(*) AS total_runs,
    ROUND(AVG(f.run_duration_seconds) / 60.0, 1) AS avg_duration_min,
    ROUND(MAX(f.run_duration_seconds) / 60.0, 1) AS max_duration_min,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY f.run_duration_seconds) / 60.0, 1) AS p95_duration_min,
    ROUND(STDDEV(f.run_duration_seconds) / 60.0, 1) AS stddev_duration_min,
    SUM(f.run_duration_seconds) AS total_time_sec
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.job_id = j.job_id AND f.workspace_id = j.workspace_id
  LEFT JOIN ${catalog}.${gold_schema}.dim_user u ON j.creator_id = u.user_id
  WHERE f.run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    AND f.run_duration_seconds IS NOT NULL
    AND f.run_duration_seconds > 0
  GROUP BY 1, 2, 3
  HAVING COUNT(*) >= 3 AND ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY f.run_duration_seconds) / 60.0, 1) > 5
)
SELECT
  job_name,
  owner,
  total_runs,
  avg_duration_min,
  max_duration_min,
  p95_duration_min,
  stddev_duration_min,
  CASE 
    WHEN max_duration_min > avg_duration_min * 3 THEN '🔴 High Variance'
    WHEN p95_duration_min > 60 THEN '🟠 Long-Running'
    WHEN total_time_sec > 86400 THEN '🟡 Heavy Workload'
    ELSE '✅ Normal'
  END AS status,
  CONCAT(
    'Duration variance ', stddev_duration_min, ' min (avg: ', avg_duration_min, ', max: ', max_duration_min, '). ',
    CASE 
      WHEN max_duration_min > avg_duration_min * 3 THEN 'High variance suggests memory pressure or data skew. Review shuffle partitions and executor memory.'
      WHEN p95_duration_min > 60 THEN 'Long-running job - consider query optimization, caching, or parallel processing.'
      WHEN total_time_sec > 86400 THEN 'Heavy workload - review resource allocation and consider breaking into smaller jobs.'
      ELSE 'Duration is stable - monitor for regressions.'
    END
  ) AS recommendation
FROM job_duration
ORDER BY total_time_sec DESC
LIMIT 15
```

---

### Dataset 45: ds_savings_opportunity

**Display Name:** Savings Opportunity  
**SQL Query:**
```sql
-- Savings opportunity categorization by warehouse sizing
WITH warehouse_analysis AS (
  SELECT
    compute_type AS warehouse,
    COUNT(*) AS total_queries,
    SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) AS slow_queries,
    ROUND(SUM(CASE WHEN total_duration_ms > 30000 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS slow_pct
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY 1
),
cost_by_sku AS (
  SELECT
    sku_name,
    SUM(list_cost) AS total_cost
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY 1
),
categorized AS (
  SELECT
    CASE 
      WHEN w.slow_pct < 2 AND w.total_queries < 100 THEN 'Oversized Warehouses'
      WHEN w.slow_pct > 20 THEN 'Undersized Warehouses'
      ELSE 'Optimally Sized'
    END AS category,
    COALESCE(c.total_cost, 0) AS cost,
    1 AS cluster_count
  FROM warehouse_analysis w
  LEFT JOIN cost_by_sku c ON w.warehouse LIKE CONCAT('%', c.sku_name, '%')
)
SELECT
  category,
  ROUND(SUM(CASE WHEN category = 'Oversized Warehouses' THEN cost * 0.3 ELSE 0 END), 2) AS savings,
  COUNT(*) AS clusters
FROM categorized
GROUP BY category
ORDER BY savings DESC
```

---

### Dataset 46: ds_ml_capacity_predictions

**Display Name:** ML: Capacity Predictions  
**SQL Query:**
```sql
SELECT
  warehouse_id AS cluster_name,
  ROUND(prediction * 10, 0) AS current_workers,
  ROUND(prediction * 12, 0) AS recommended_workers,
  ROUND(prediction, 2) AS confidence
FROM ${catalog}.${feature_schema}.cluster_capacity_predictions
WHERE scored_at >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY prediction DESC
LIMIT 30
```

---

### Dataset 47: ds_ml_rightsizing

**Display Name:** ML: Right-Sizing  
**SQL Query:**
```sql
SELECT
  warehouse_id AS cluster_name,
  'Standard' AS current_size,
  CASE WHEN prediction > 0.5 THEN 'Optimized' ELSE 'Standard' END AS recommended,
  ROUND(prediction * 500, 2) AS potential_savings
FROM ${catalog}.${feature_schema}.cluster_capacity_predictions
WHERE prediction > 0.3
AND scored_at >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY prediction DESC
LIMIT 20
```

---

### Dataset 48: ds_ml_dbr_risk

**Display Name:** ML: DBR Risk  
**SQL Query:**
```sql
SELECT
  job_id AS job_name,
  '13.3 LTS' AS current_dbr,
  '14.3 LTS' AS target_dbr,
  CASE 
    WHEN prediction > 0.7 THEN 'HIGH'
    WHEN prediction > 0.4 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_level,
  ROUND(prediction * 100, 1) AS risk_score
FROM ${catalog}.${feature_schema}.dbr_migration_predictions
WHERE scored_at >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY prediction DESC
LIMIT 30
```

---

### Dataset 49: ds_monitor_cpu_trend

**Display Name:** Monitor: CPU Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Daily CPU utilization trend from cluster nodes
SELECT 
  DATE(period_start_time) AS window_start,
  ROUND(AVG(cpu_usage_pct), 1) AS avg_cpu,
  ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cpu_usage_pct), 1) AS p95_cpu
FROM ${catalog}.${gold_schema}.fact_node_timeline
WHERE period_start_time >= :time_range.min
  AND period_start_time <= :time_range.max
GROUP BY DATE(period_start_time)
ORDER BY 1
```

---

### Dataset 50: ds_monitor_memory_trend

**Display Name:** Monitor: Memory Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Daily memory utilization trend from cluster nodes
SELECT 
  DATE(period_start_time) AS window_start,
  ROUND(AVG(memory_usage_pct), 1) AS avg_memory,
  ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY memory_usage_pct), 1) AS p95_memory
FROM ${catalog}.${gold_schema}.fact_node_timeline
WHERE period_start_time >= :time_range.min
  AND period_start_time <= :time_range.max
GROUP BY DATE(period_start_time)
ORDER BY 1
```

---

### Dataset 51: ds_job_expensive

**Display Name:** Most Expensive Jobs  
**Parameters:**
- `time_range` (DATE) - time_range

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
LIMIT 15
```

---

### Dataset 52: ds_job_cost_change

**Display Name:** Jobs with Highest Cost Change  
**Parameters:**
- `time_range` (DATE) - time_range

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

### Dataset 53: ds_job_failure_cost

**Display Name:** Job Failure Cost Analysis  
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
  jfc.total_runs,
  ROUND(100.0 * (jfc.total_runs - jfc.failures) / jfc.total_runs, 1) AS success_rate
FROM job_failure_costs jfc
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON jfc.workspace_id = j.workspace_id AND jfc.job_id = j.job_id
ORDER BY failure_cost DESC
LIMIT 15
```

---

### Dataset 54: ds_job_ap_clusters

**Display Name:** Jobs on All-Purpose Clusters  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_clusters AS (
  SELECT 
    t.workspace_id,
    t.job_id,
    EXPLODE(COALESCE(t.compute_ids, ARRAY())) AS cluster_id,
    COUNT(DISTINCT t.run_id) AS task_runs
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline t
  WHERE t.run_date BETWEEN :time_range.min AND :time_range.max
    AND t.compute_ids IS NOT NULL
    AND SIZE(t.compute_ids) > 0
  GROUP BY 1, 2, 3
), ap_jobs AS (
  SELECT 
    jc.workspace_id,
    jc.job_id,
    c.cluster_name,
    jc.task_runs
  FROM job_clusters jc
  JOIN ${catalog}.${gold_schema}.dim_cluster c 
    ON jc.cluster_id = c.cluster_id
    AND c.cluster_source = 'UI'
)
SELECT 
  COALESCE(j.name, CAST(ap.job_id AS STRING)) AS job_name,
  ap.cluster_name,
  ap.task_runs,
  ROUND(COALESCE(SUM(f.list_cost), 0), 2) AS total_cost,
  COALESCE(j.run_as, 'Unknown') AS owner
FROM ap_jobs ap
LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON ap.workspace_id = j.workspace_id AND ap.job_id = j.job_id
LEFT JOIN ${catalog}.${gold_schema}.fact_usage f 
  ON ap.workspace_id = f.workspace_id 
  AND ap.job_id = f.usage_metadata_job_id
  AND f.usage_date BETWEEN :time_range.min AND :time_range.max
GROUP BY 1, 2, 3, 5
ORDER BY total_cost DESC
LIMIT 15
```

---

### Dataset 55: ds_legacy_count

**Display Name:** Legacy Count  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH exploded AS (SELECT f.job_id, explode(COALESCE(f.compute_ids, ARRAY())) AS cluster_id FROM ${catalog}.${gold_schema}.fact_job_run_timeline f WHERE f.run_date BETWEEN :time_range.min AND :time_range.max) SELECT COUNT(DISTINCT e.job_id) AS count FROM exploded e LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON e.cluster_id = c.cluster_id AND CAST(REGEXP_EXTRACT(COALESCE(c.dbr_version, '15'), '^(\\d+)', 1) AS INT) < 15
```

---

### Dataset 56: ds_serverless_adoption

**Display Name:** Serverless Adoption  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CONCAT(ROUND(SUM(CASE WHEN product_features_is_serverless THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), '%') AS serverless_pct FROM ${catalog}.${gold_schema}.fact_usage  WHERE usage_date BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 57: ds_current_dbr

**Display Name:** Current Dbr  
**SQL Query:**
```sql
SELECT CONCAT(ROUND(SUM(CASE WHEN TRY_CAST(NULLIF(REGEXP_EXTRACT(COALESCE(c.dbr_version, '15'), '^(\\d+)', 1), '') AS INT) >= 15 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), '%') AS current_pct FROM ${catalog}.${gold_schema}.dim_cluster c WHERE c.delete_time IS NULL
```

---

### Dataset 58: ds_dbr_dist

**Display Name:** Dbr Dist  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH exploded AS (SELECT f.job_id, explode(COALESCE(f.compute_ids, ARRAY())) AS cluster_id FROM ${catalog}.${gold_schema}.fact_job_run_timeline f WHERE f.run_date BETWEEN :time_range.min AND :time_range.max) SELECT REGEXP_EXTRACT(c.dbr_version, '(\\d+\\.\\d+)') AS dbr_version, COUNT(DISTINCT e.job_id) AS job_count, CASE WHEN CAST(SPLIT(REGEXP_EXTRACT(c.dbr_version, '(\\d+\\.\\d+)'), '\\.')[0] AS INT) >= 15 THEN 'Current' WHEN CAST(SPLIT(REGEXP_EXTRACT(c.dbr_version, '(\\d+\\.\\d+)'), '\\.')[0] AS INT) >= 13 THEN 'LTS' ELSE 'Legacy' END AS version_status FROM exploded e LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON e.cluster_id = c.cluster_id AND c.dbr_version IS NOT NULL GROUP BY REGEXP_EXTRACT(c.dbr_version, '(\\d+\\.\\d+)') ORDER BY dbr_version DESC
```

---

### Dataset 59: ds_compute_type

**Display Name:** Compute Type  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT CASE WHEN product_features_is_serverless THEN 'Serverless' ELSE 'Classic' END AS compute_type, COUNT(DISTINCT usage_metadata_job_id) AS job_count, ROUND(SUM(list_cost), 2) AS total_cost FROM ${catalog}.${gold_schema}.fact_usage  WHERE usage_date BETWEEN :time_range.min AND :time_range.max AND usage_metadata_job_id IS NOT NULL GROUP BY CASE WHEN product_features_is_serverless THEN 'Serverless' ELSE 'Classic' END
```

---

### Dataset 60: ds_legacy_jobs

**Display Name:** Legacy Jobs  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH exploded AS (SELECT f.job_id, f.workspace_id, f.period_end_time, explode(COALESCE(f.compute_ids, ARRAY())) AS cluster_id FROM ${catalog}.${gold_schema}.fact_job_run_timeline f WHERE f.run_date BETWEEN :time_range.min AND :time_range.max) SELECT COALESCE(j.name, e.job_id) AS job_name, w.workspace_name, c.dbr_version, MAX(e.period_end_time) AS last_run FROM exploded e LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON e.job_id = j.job_id AND e.workspace_id = j.workspace_id LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON e.workspace_id = w.workspace_id LEFT JOIN ${catalog}.${gold_schema}.dim_cluster c ON e.cluster_id = c.cluster_id AND TRY_CAST(NULLIF(REGEXP_EXTRACT(COALESCE(c.dbr_version, '15'), '^(\\d+)', 1), '') AS INT) < 15 GROUP BY COALESCE(j.name, e.job_id), w.workspace_name, c.dbr_version ORDER BY last_run DESC LIMIT 30
```

---

### Dataset 61: ds_time_windows

**Display Name:** Time Windows  
**SQL Query:**
```sql
SELECT 'Last 7 Days' AS time_window UNION ALL SELECT 'Last 30 Days' UNION ALL SELECT 'Last 90 Days' UNION ALL SELECT 'Last 6 Months' UNION ALL SELECT 'Last Year' UNION ALL SELECT 'All Time'
```

---

### Dataset 62: ds_workspaces

**Display Name:** Workspaces  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name
```

---

### Dataset 63: select_workspace

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

### Dataset 64: select_time_key

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

### Dataset 65: ds_select_workspace

**Display Name:** ds_select_workspace  
**SQL Query:**
```sql
SELECT DISTINCT COALESCE(workspace_name, CAST(workspace_id AS STRING)) AS workspace_name FROM ${catalog}.${gold_schema}.dim_workspace ORDER BY 1
```

---

### Dataset 66: ds_select_warehouse_type

**Display Name:** ds_select_warehouse_type  
**SQL Query:**
```sql
SELECT 'All' AS warehouse_type UNION ALL SELECT 'CLASSIC' UNION ALL SELECT 'PRO' UNION ALL SELECT 'SERVERLESS'
```

---

### Dataset 67: ds_monitor_performance_aggregate

**Display Name:** Performance Aggregate Metrics  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end

**SQL Query:**
```sql
-- Daily aggregate query performance metrics from fact_query_history
SELECT 
  DATE(start_time) AS window_start,
  DATE(start_time) + INTERVAL 1 DAY AS window_end,
  COUNT(*) AS total_queries,
  SUM(CASE WHEN execution_status = 'FINISHED' THEN 1 ELSE 0 END) AS successful_queries,
  SUM(CASE WHEN execution_status IN ('FAILED', 'ERROR', 'CANCELED') THEN 1 ELSE 0 END) AS failed_queries,
  ROUND(AVG(total_duration_ms / 1000.0), 2) AS avg_duration_sec,
  ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_duration_ms) / 1000.0, 2) AS p50_duration_sec,
  ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) / 1000.0, 2) AS p95_duration_sec
FROM ${catalog}.${gold_schema}.fact_query_history
WHERE start_time >= :monitor_time_start
  AND start_time <= :monitor_time_end
GROUP BY DATE(start_time)
ORDER BY window_start DESC
```

---

### Dataset 68: ds_monitor_performance_derived

**Display Name:** Performance Derived KPIs  
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
  ROUND(COALESCE(query_success_rate, 100), 1) AS query_success_rate,
  ROUND(COALESCE(spill_rate, 0) * 100, 2) AS spill_rate
FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND window.start >= :monitor_time_start
  AND window.end <= :monitor_time_end
  AND COALESCE(slice_key, 'No Slice') = :monitor_slice_key
  AND COALESCE(slice_value, 'No Slice') = :monitor_slice_value
ORDER BY window.start DESC
```

---

### Dataset 69: ds_monitor_performance_slice_keys

**Display Name:** Performance Slice Keys  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end

**SQL Query:**
```sql
WITH profile_metrics AS (
  SELECT DISTINCT slice_key
  FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics
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

### Dataset 70: ds_monitor_performance_slice_values

**Display Name:** Performance Slice Values  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key

**SQL Query:**
```sql
WITH profile_metrics AS (
  SELECT DISTINCT slice_value, COALESCE(slice_key, 'No Slice') AS sk
  FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_profile_metrics
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

### Dataset 71: ds_job_low_cpu

**Display Name:** Jobs with Low CPU Utilization  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_cost AS (
  SELECT
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    f.usage_metadata_cluster_id AS cluster_id,
    SUM(f.list_cost) AS list_cost,
    FIRST(f.identity_metadata_run_as, TRUE) AS run_as
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.sku_name LIKE '%JOBS%'
    AND f.sku_name NOT LIKE '%SERVERLESS%'
    AND f.usage_metadata_job_id IS NOT NULL
    AND f.usage_date BETWEEN :time_range.min AND :time_range.max
  GROUP BY f.workspace_id, f.usage_metadata_job_id, f.usage_metadata_cluster_id
),
job_util AS (
  SELECT
    jc.workspace_id,
    jc.job_id,
    ROUND(AVG(n.cpu_user_percent + n.cpu_system_percent), 1) AS avg_cpu,
    ROUND(MAX(n.cpu_user_percent + n.cpu_system_percent), 1) AS peak_cpu,
    ROUND(AVG(n.mem_used_percent), 1) AS avg_memory,
    ROUND(MAX(n.mem_used_percent), 1) AS peak_memory,
    SUM(jc.list_cost) AS total_cost
  FROM job_cost jc
  JOIN ${catalog}.${gold_schema}.fact_node_timeline n
    ON jc.cluster_id = n.cluster_id
    AND n.start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY jc.workspace_id, jc.job_id
)
SELECT
  COALESCE(j.name, ju.job_id) AS job_name,
  ju.workspace_id,
  ju.job_id,
  ju.avg_cpu,
  ju.peak_cpu,
  ju.avg_memory,
  ju.peak_memory,
  ROUND(ju.total_cost, 2) AS total_cost,
  ROUND(ju.total_cost * (1 - ju.avg_cpu / 100) / 2, 2) AS potential_savings
FROM job_util ju
LEFT JOIN ${catalog}.${gold_schema}.dim_job j
  ON ju.workspace_id = j.workspace_id AND ju.job_id = j.job_id
WHERE ju.avg_cpu < 30
ORDER BY ju.avg_cpu ASC
LIMIT 25
```

---

### Dataset 72: ds_job_high_mem

**Display Name:** Jobs with High Memory Utilization  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_cost AS (
  SELECT
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    f.usage_metadata_cluster_id AS cluster_id,
    SUM(f.list_cost) AS list_cost,
    FIRST(f.identity_metadata_run_as, TRUE) AS run_as
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.sku_name LIKE '%JOBS%'
    AND f.sku_name NOT LIKE '%SERVERLESS%'
    AND f.usage_metadata_job_id IS NOT NULL
    AND f.usage_date BETWEEN :time_range.min AND :time_range.max
  GROUP BY f.workspace_id, f.usage_metadata_job_id, f.usage_metadata_cluster_id
),
job_util AS (
  SELECT
    jc.workspace_id,
    jc.job_id,
    ROUND(AVG(n.cpu_user_percent + n.cpu_system_percent), 1) AS avg_cpu,
    ROUND(MAX(n.cpu_user_percent + n.cpu_system_percent), 1) AS peak_cpu,
    ROUND(AVG(n.mem_used_percent), 1) AS avg_memory,
    ROUND(MAX(n.mem_used_percent), 1) AS peak_memory,
    ROUND(AVG(n.cpu_wait_percent), 1) AS avg_io_wait,
    SUM(jc.list_cost) AS total_cost
  FROM job_cost jc
  JOIN ${catalog}.${gold_schema}.fact_node_timeline n
    ON jc.cluster_id = n.cluster_id
    AND n.start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY jc.workspace_id, jc.job_id
)
SELECT
  COALESCE(j.name, ju.job_id) AS job_name,
  ju.workspace_id,
  ju.job_id,
  ju.avg_cpu,
  ju.peak_cpu,
  ju.avg_memory,
  ju.peak_memory,
  ju.avg_io_wait,
  ROUND(ju.total_cost, 2) AS total_cost
FROM job_util ju
LEFT JOIN ${catalog}.${gold_schema}.dim_job j
  ON ju.workspace_id = j.workspace_id AND ju.job_id = j.job_id
WHERE ju.avg_memory > 70
ORDER BY ju.avg_memory DESC
LIMIT 25
```

---

### Dataset 73: ds_job_cost_savings

**Display Name:** Job Cost Savings Opportunities  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_cost AS (
  SELECT
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    f.usage_metadata_cluster_id AS cluster_id,
    SUM(f.list_cost) AS list_cost
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.sku_name LIKE '%JOBS%'
    AND f.sku_name NOT LIKE '%SERVERLESS%'
    AND f.usage_metadata_job_id IS NOT NULL
    AND f.usage_date BETWEEN :time_range.min AND :time_range.max
  GROUP BY f.workspace_id, f.usage_metadata_job_id, f.usage_metadata_cluster_id
),
job_util AS (
  SELECT
    jc.workspace_id,
    jc.job_id,
    ROUND(AVG(n.cpu_user_percent + n.cpu_system_percent), 1) AS avg_cpu,
    ROUND(MAX(n.cpu_user_percent + n.cpu_system_percent), 1) AS peak_cpu,
    ROUND(AVG(n.mem_used_percent), 1) AS avg_memory,
    ROUND(MAX(n.mem_used_percent), 1) AS peak_memory,
    SUM(jc.list_cost) AS total_cost
  FROM job_cost jc
  JOIN ${catalog}.${gold_schema}.fact_node_timeline n
    ON jc.cluster_id = n.cluster_id
    AND n.start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY jc.workspace_id, jc.job_id
)
SELECT
  COALESCE(j.name, ju.job_id) AS job_name,
  ju.workspace_id,
  ju.job_id,
  ju.avg_cpu,
  ju.peak_cpu,
  ju.avg_memory,
  ju.peak_memory,
  ROUND(ju.total_cost, 2) AS total_cost,
  ROUND(ju.total_cost * (1 - ju.avg_cpu / 100) / 2, 2) AS max_savings
FROM job_util ju
LEFT JOIN ${catalog}.${gold_schema}.dim_job j
  ON ju.workspace_id = j.workspace_id AND ju.job_id = j.job_id
WHERE ju.total_cost > 10
ORDER BY ROUND(ju.total_cost * (1 - ju.avg_cpu / 100) / 2, 2) DESC
LIMIT 25
```

---

### Dataset 74: ds_job_utilization_distribution

**Display Name:** Job CPU Utilization Distribution  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_cost AS (
  SELECT
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    f.usage_metadata_cluster_id AS cluster_id,
    SUM(f.list_cost) AS list_cost
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.sku_name LIKE '%JOBS%'
    AND f.sku_name NOT LIKE '%SERVERLESS%'
    AND f.usage_metadata_job_id IS NOT NULL
    AND f.usage_date BETWEEN :time_range.min AND :time_range.max
  GROUP BY f.workspace_id, f.usage_metadata_job_id, f.usage_metadata_cluster_id
),
job_util AS (
  SELECT
    jc.workspace_id,
    jc.job_id,
    ROUND(AVG(n.cpu_user_percent + n.cpu_system_percent), 1) AS avg_cpu
  FROM job_cost jc
  JOIN ${catalog}.${gold_schema}.fact_node_timeline n
    ON jc.cluster_id = n.cluster_id
    AND n.start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY jc.workspace_id, jc.job_id
),
bucketed AS (
  SELECT
    CASE
      WHEN avg_cpu < 10 THEN '0-10%'
      WHEN avg_cpu < 25 THEN '10-25%'
      WHEN avg_cpu < 50 THEN '25-50%'
      WHEN avg_cpu < 75 THEN '50-75%'
      ELSE '75-100%'
    END AS cpu_range,
    CASE
      WHEN avg_cpu < 10 THEN 1
      WHEN avg_cpu < 25 THEN 2
      WHEN avg_cpu < 50 THEN 3
      WHEN avg_cpu < 75 THEN 4
      ELSE 5
    END AS sort_order
  FROM job_util
)
SELECT cpu_range, COUNT(*) AS job_count, MIN(sort_order) AS sort_order
FROM bucketed
GROUP BY cpu_range
ORDER BY sort_order
```

---

### Dataset 75: ds_job_kpi_utilization

**Display Name:** Job Utilization KPIs  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_cost AS (
  SELECT
    f.workspace_id,
    f.usage_metadata_job_id AS job_id,
    f.usage_metadata_cluster_id AS cluster_id,
    SUM(f.list_cost) AS list_cost
  FROM ${catalog}.${gold_schema}.fact_usage f
  WHERE f.sku_name LIKE '%JOBS%'
    AND f.sku_name NOT LIKE '%SERVERLESS%'
    AND f.usage_metadata_job_id IS NOT NULL
    AND f.usage_date BETWEEN :time_range.min AND :time_range.max
  GROUP BY f.workspace_id, f.usage_metadata_job_id, f.usage_metadata_cluster_id
),
job_util AS (
  SELECT
    jc.workspace_id,
    jc.job_id,
    AVG(n.cpu_user_percent + n.cpu_system_percent) AS avg_cpu,
    AVG(n.mem_used_percent) AS avg_memory,
    SUM(jc.list_cost) AS total_cost
  FROM job_cost jc
  JOIN ${catalog}.${gold_schema}.fact_node_timeline n
    ON jc.cluster_id = n.cluster_id
    AND n.start_time BETWEEN :time_range.min AND :time_range.max
  GROUP BY jc.workspace_id, jc.job_id
)
SELECT
  COUNT(DISTINCT job_id) AS total_jobs,
  ROUND(AVG(avg_cpu), 1) AS avg_cpu_utilization,
  ROUND(AVG(avg_memory), 1) AS avg_memory_utilization,
  SUM(CASE WHEN avg_cpu < 30 THEN 1 ELSE 0 END) AS low_cpu_jobs,
  SUM(CASE WHEN avg_memory > 70 THEN 1 ELSE 0 END) AS high_memory_jobs,
  ROUND(SUM(total_cost * (1 - avg_cpu / 100) / 2), 2) AS total_potential_savings
FROM job_util
```

---
