# Complete Unified Overview Dataset Catalog

## Overview
**Total Datasets:** 63  
**Dashboard:** `unified.lvdash.json`  
**Coverage:** ALL datasets from ALL pages with FULL details

---

## Dataset Index

| # | Dataset Name | Display Name | Has Query | Parameters |
|---|--------------|--------------|-----------|------------|
| 1 | ds_kpi_query | KPI: Query | ✅ | time_range, time_range |
| 2 | ds_ml_capacity | ML: Capacity | ✅ | - |
| 3 | ds_kpi_events | KPI: Events | ✅ | time_range |
| 4 | ds_wow_growth | WoW Growth | ✅ | time_range, param_workspace, time_range |
| 5 | ds_kpi_duration | KPI: Duration | ✅ | time_range, time_range |
| 6 | ds_kpi_slow | KPI: Slow | ✅ | time_range |
| 7 | ds_kpi_queries | KPI: Queries | ✅ | time_range, time_range |
| 8 | ds_top_workspaces | Top Workspaces | ✅ | time_range, param_workspace |
| 9 | ds_kpi_jobs | KPI: Jobs | ✅ | time_range |
| 10 | ds_unique_counts | Unique Counts | ✅ | time_range |
| 11 | ds_monitor_query_drift | Monitor: Query Drift | ✅ | time_range |
| 12 | ds_risk_trend | Risk Trend | ✅ | time_range |
| 13 | ds_tables_by_catalog | Tables by Catalog | ✅ | time_range |
| 14 | ds_kpi_cost | KPI: Cost | ✅ | time_range |
| 15 | ds_duration_trend | Duration Trend | ✅ | time_range |
| 16 | ds_ml_security_threats | ML: Security Threats | ✅ | - |
| 17 | ds_runs_by_status | Runs by Status | ✅ | time_range |
| 18 | ds_kpi_tagged | KPI: Tagged | ✅ | time_range |
| 19 | ds_job_trend | Job Trend | ✅ | time_range |
| 20 | ds_health_score | Health Score | ✅ | - |
| 21 | ds_health_trend | Health Trend | ✅ | time_range |
| 22 | ds_reliability_health | Reliability Health | ✅ | - |
| 23 | ds_daily_cost | Daily Cost | ✅ | time_range, param_workspace, time_range |
| 24 | ds_serverless_adoption | Serverless Adoption | ✅ | time_range, time_range |
| 25 | ds_cost_health | Cost Health | ✅ | - |
| 26 | ds_ml_job_risks | ML: Job Risks | ✅ | - |
| 27 | ds_kpi_mttr | KPI: MTTR | ✅ | time_range |
| 28 | ds_kpi_lineage | KPI: Lineage | ✅ | time_range |
| 29 | ds_drift_trend | Drift Trend | ✅ | time_range |
| 30 | ds_event_trend | Event Trend | ✅ | time_range |
| 31 | ds_kpi_success_rate | KPI: Success Rate | ✅ | time_range |
| 32 | ds_kpi_cluster | KPI: Cluster | ✅ | time_range, time_range |
| 33 | ds_kpi_totals | KPI: Totals | ✅ | time_range |
| 34 | ds_kpi_tables | KPI: Tables | ✅ | - |
| 35 | ds_monitor_cost_drift | Monitor: Cost Drift | ✅ | time_range |
| 36 | ds_kpi_documented | KPI: Documented | ✅ | - |
| 37 | ds_kpi_30d | KPI: 30d Spend | ✅ | time_range |
| 38 | ds_kpi_denied | KPI: Denied | ✅ | time_range |
| 39 | ds_tag_coverage | Tag Coverage | ✅ | time_range, time_range |
| 40 | ds_30_60_compare | 30 vs 60 Day Compare | ✅ | time_range |
| 41 | ds_ml_cost_anomalies | ML: Cost Anomalies | ✅ | param_workspace |
| 42 | ds_health_issues | Health Issues | ✅ | time_range |
| 43 | ds_sku_breakdown | Billing Origin Product Breakdown | ✅ | param_sku_type, time_range |
| 44 | ds_kpi_admin | KPI: Admin | ✅ | time_range, time_range |
| 45 | ds_kpi_users | KPI: Users | ✅ | time_range |
| 46 | ds_cost_trend | Cost Trend | ✅ | time_range, time_range |
| 47 | ds_monitor_job_drift | Monitor: Job Drift | ✅ | - |
| 48 | ds_kpi_mtd | KPI: MTD Spend | ✅ | time_range |
| 49 | ds_kpi_permissions | KPI: Permissions | ✅ | time_range |
| 50 | ds_kpi_high_risk | KPI: High Risk | ✅ | time_range |
| 51 | ds_success_trend | Success Trend | ✅ | time_range |
| 52 | ds_kpi_workspaces | KPI: Workspaces | ✅ | param_workspace, time_range |
| 53 | ds_drift_alerts | Drift Alerts | ✅ | - |
| 54 | ds_kpi_failed | KPI: Failed Queries | ✅ | time_range |
| 55 | ds_query_volume | Query Volume | ✅ | time_range, time_range |
| 56 | ds_lineage_trend | Lineage Trend | ✅ | time_range |
| 57 | ds_kpi_security | KPI: Security | ✅ | time_range, time_range |
| 58 | ds_time_windows | Time Windows | ✅ | - |
| 59 | ds_workspaces | Workspaces | ✅ | param_workspace |
| 60 | select_workspace | select_workspace | ✅ | param_workspace |
| 61 | select_time_key | select_time_key | ✅ | - |
| 62 | ds_select_workspace | select_workspace | ✅ | param_workspace |
| 63 | ds_select_sku | ds_select_sku | ✅ | - |

---

## Complete SQL Queries


### Dataset 1: ds_kpi_query

**Display Name:** KPI: Query  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(AVG(execution_duration_ms)/1000, 1) AS avg_duration 
FROM ${catalog}.${gold_schema}.fact_query_history 
WHERE start_time >= :time_range.min AND start_time <= :time_range.max
```

---

### Dataset 2: ds_ml_capacity

**Display Name:** ML: Capacity  
**SQL Query:**
```sql
WITH capacity_preds AS (
  SELECT
    p.warehouse_id,
    -- ML prediction is already a percentage (0-100+), NOT 0-1
    LEAST(COALESCE(p.prediction, 0), 150) AS utilization_pct,
    p.is_weekend,
    p.scored_at,
    COALESCE(w.warehouse_name, 'Unknown Warehouse') AS warehouse_name,
    COALESCE(w.warehouse_type, 'SERVERLESS') AS resource_type,
    COALESCE(w.warehouse_size, 'Unknown') AS current_size,
    COALESCE(w.min_clusters, 1) AS min_clusters,
    COALESCE(w.max_clusters, 1) AS max_clusters
  FROM ${catalog}.${feature_schema}.cluster_capacity_predictions p
  LEFT JOIN ${catalog}.${gold_schema}.dim_warehouse w ON p.warehouse_id = w.warehouse_id
  WHERE p.scored_at >= CURRENT_DATE() - INTERVAL 7 DAYS
),
size_order AS (
  SELECT 'X_SMALL' AS sz, 1 AS ord UNION ALL
  SELECT '2X_SMALL', 2 UNION ALL
  SELECT 'SMALL', 3 UNION ALL
  SELECT 'MEDIUM', 4 UNION ALL
  SELECT 'LARGE', 5 UNION ALL
  SELECT 'X_LARGE', 6 UNION ALL
  SELECT '2X_LARGE', 7 UNION ALL
  SELECT '3X_LARGE', 8 UNION ALL
  SELECT '4X_LARGE', 9
),
with_recommendations AS (
  SELECT c.*,
    so.ord AS current_ord,
    CASE
      WHEN c.utilization_pct > 90 THEN so.ord + 2
      WHEN c.utilization_pct > 75 THEN so.ord + 1
      ELSE so.ord
    END AS recommended_ord
  FROM capacity_preds c
  LEFT JOIN size_order so ON UPPER(c.current_size) = so.sz
)
SELECT
  CONCAT(r.resource_type, ': ', r.warehouse_name) AS resource_name,
  CONCAT('Type: ', r.resource_type, ' | Size: ', r.current_size, ' | Clusters: ', r.min_clusters, '-', r.max_clusters) AS resource_type,
  ROUND(r.utilization_pct, 1) AS utilization_pct,
  CASE
    WHEN r.utilization_pct > 90 THEN CONCAT('Scale to ', COALESCE(rec.sz, 'larger size'), ' + add ', LEAST(r.max_clusters + 2, 10) - r.max_clusters, ' clusters')
    WHEN r.utilization_pct > 75 THEN CONCAT('Scale to ', COALESCE(rec.sz, 'next size'), ' or add 1 cluster')
    WHEN r.utilization_pct > 60 THEN 'Monitor closely - approaching capacity'
    ELSE 'Capacity adequate'
  END AS recommended_action,
  CONCAT(
    'Current: ', r.current_size, ' (', r.min_clusters, '-', r.max_clusters, ' clusters) @ ', ROUND(r.utilization_pct, 0), '% util. ',
    CASE
      WHEN r.utilization_pct > 90 THEN 'CRITICAL: Significant scaling needed.'
      WHEN r.utilization_pct > 75 THEN 'WARNING: Approaching limits.'
      WHEN r.utilization_pct > 60 THEN 'Monitor during peak hours.'
      ELSE 'Operating normally.'
    END
  ) AS rationale
FROM with_recommendations r
LEFT JOIN size_order rec ON r.recommended_ord = rec.ord
WHERE r.utilization_pct > 50
ORDER BY r.utilization_pct DESC
LIMIT 15
```

---

### Dataset 3: ds_kpi_events

**Display Name:** KPI: Events  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(*) AS total_events FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_date >= :time_range.min AND event_date <= :time_range.max
```

---

### Dataset 4: ds_wow_growth

**Display Name:** WoW Growth  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH weekly AS (SELECT DATE_TRUNC('week', usage_date) AS week_start, SUM(list_cost) AS weekly_cost, COUNT(DISTINCT DATE(usage_date)) AS days FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage f LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_workspace w ON f.workspace_id = w.workspace_id WHERE 

 usage_date BETWEEN :time_range.min AND :time_range.max
AND (
  'all' IN (SELECT EXPLODE(:param_workspace))
  OR COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) IN (SELECT EXPLODE(:param_workspace))
) GROUP BY 1 HAVING days = 7), with_growth AS (SELECT week_start, weekly_cost, 100 * (weekly_cost - LAG(weekly_cost) OVER (ORDER BY week_start)) / NULLIF(LAG(weekly_cost) OVER (ORDER BY week_start), 0) AS wow_growth_pct FROM weekly) SELECT week_start, ROUND(weekly_cost, 2) AS weekly_cost, ROUND(wow_growth_pct, 1) AS wow_growth_pct, ROUND(AVG(wow_growth_pct) OVER (ORDER BY week_start ROWS BETWEEN 12 PRECEDING AND CURRENT ROW), 1) AS moving_avg FROM with_growth ORDER BY week_start
```

---

### Dataset 5: ds_kpi_duration

**Display Name:** KPI: Duration  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(PERCENTILE(run_duration_seconds, 0.95)/60, 1) AS p95_duration 
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max
```

---

### Dataset 6: ds_kpi_slow

**Display Name:** KPI: Slow  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(
    SUM(CASE WHEN execution_duration_ms > 60000 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 
    3) AS slow_queries_pct 
FROM ${catalog}.${gold_schema}.fact_query_history 
WHERE start_time >= :time_range.min AND start_time <= :time_range.max
```

---

### Dataset 7: ds_kpi_queries

**Display Name:** KPI: Queries  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
    COUNT(*) AS total_queries,
    ROUND(AVG(execution_duration_ms)/1000, 1) AS avg_duration,
    ROUND(PERCENTILE(execution_duration_ms, 0.95)/1000, 1) AS p95_duration,
    COUNT(DISTINCT executed_as_user_id) AS unique_users
FROM ${catalog}.${gold_schema}.fact_query_history 
WHERE start_time >= :time_range.min AND start_time <= :time_range.max
```

---

### Dataset 8: ds_top_workspaces

**Display Name:** Top Workspaces  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT 
  COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name, 
  ROUND(SUM(f.list_cost), 2) AS total_cost,
  SUM(f.usage_quantity) AS total_dbus,
  COUNT(DISTINCT f.identity_metadata_run_as) AS unique_users,
  ROUND(SUM(f.list_cost) / NULLIF(COUNT(DISTINCT f.identity_metadata_run_as), 0), 2) AS cost_per_user,
  COUNT(DISTINCT f.usage_metadata_job_id) AS job_count,
  COUNT(DISTINCT f.usage_metadata_job_run_id) AS job_runs,
  ROUND(SUM(CASE WHEN f.sku_name LIKE '%SERVERLESS%' THEN f.list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(f.list_cost), 0), 1) AS serverless_pct
FROM ${catalog}.${gold_schema}.fact_usage f 
LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id 
WHERE f.usage_date BETWEEN :time_range.min AND :time_range.max
  AND ('all' IN (SELECT EXPLODE(:param_workspace)) OR COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) IN (SELECT EXPLODE(:param_workspace)))
GROUP BY 1 
ORDER BY total_cost DESC 
LIMIT 15
```

---

### Dataset 9: ds_kpi_jobs

**Display Name:** KPI: Jobs  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT job_id) AS total_jobs 
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max
```

---

### Dataset 10: ds_unique_counts

**Display Name:** Unique Counts  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT user_identity_email) AS active_users
FROM ${catalog}.${gold_schema}.fact_audit_logs 
WHERE event_date >= :time_range.min AND event_date <= :time_range.max
  AND user_identity_email IS NOT NULL
  AND user_identity_email NOT LIKE '%.gserviceaccount.com'
  AND user_identity_email NOT LIKE 'service-principal-%'
  AND user_identity_email NOT LIKE '%[ServicePrincipal]%'
  AND user_identity_email NOT LIKE '%@databricks.com'
  AND LOWER(user_identity_email) NOT IN ('system-user', 'system', 'admin', 'root', 'databricks', 'unity-catalog-service')
```

---

### Dataset 11: ds_monitor_query_drift

**Display Name:** Monitor: Query Drift  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start, 
  ROUND(COALESCE(p95_duration_drift_pct, 0) / 100.0, 4) AS drift_pct 
FROM ${catalog}.${gold_schema}_monitoring.fact_query_history_drift_metrics 
WHERE column_name = ':table' 
  AND drift_type = 'CONSECUTIVE'
  AND slice_key IS NULL
  AND window.end >= :time_range.min AND window.end <= :time_range.max
ORDER BY window.start DESC
LIMIT 1
```

---

### Dataset 12: ds_risk_trend

**Display Name:** Risk Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(event_date) AS day, 
  SUM(CASE WHEN action_name IN ('deleteTable', 'deleteSchema', 'deleteCatalog', 'dropUser', 'deleteCluster', 'createAccessToken') THEN 1 ELSE 0 END) AS high_risk,
  SUM(CASE WHEN action_name IN ('addUserToGroup', 'removeUserFromGroup', 'updatePermissions', 'createNotebook') THEN 1 ELSE 0 END) AS medium_risk,
  COUNT(*) AS events 
FROM ${catalog}.${gold_schema}.fact_audit_logs 
WHERE event_date >= :time_range.min AND event_date <= :time_range.max 
GROUP BY 1 ORDER BY 1
```

---

### Dataset 13: ds_tables_by_catalog

**Display Name:** Tables by Catalog  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT catalog_name, COUNT(DISTINCT table_full_name) AS table_count FROM (SELECT COALESCE(source_table_catalog, target_table_catalog) AS catalog_name, COALESCE(source_table_full_name, target_table_full_name) AS table_full_name FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE (source_table_catalog IS NOT NULL OR target_table_catalog IS NOT NULL) AND event_date BETWEEN :time_range.min AND :time_range.max) WHERE catalog_name IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

---

### Dataset 14: ds_kpi_cost

**Display Name:** KPI: Cost  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT SUM(list_cost) AS cost_30d 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
```

---

### Dataset 15: ds_duration_trend

**Display Name:** Duration Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH daily_stats AS (
  SELECT DATE(start_time) AS day, 
    ROUND(AVG(execution_duration_ms)/60000, 2) AS avg_duration_min,
    ROUND(PERCENTILE(execution_duration_ms, 0.95)/60000, 2) AS p95_duration_min
  FROM ${catalog}.${gold_schema}.fact_query_history 
  WHERE start_time >= :time_range.min AND start_time <= :time_range.max 
  GROUP BY 1
)
SELECT day, 'Average' AS metric, avg_duration_min AS duration_min FROM daily_stats
UNION ALL
SELECT day, 'P95 (Slow Queries)' AS metric, p95_duration_min AS duration_min FROM daily_stats
ORDER BY day, metric
```

---

### Dataset 16: ds_ml_security_threats

**Display Name:** ML: Security Threats  
**SQL Query:**
```sql
WITH security_events AS (
  SELECT
    user_identity_email,
    SUM(CASE WHEN response_result = 'denied' OR LOWER(response_error_message) LIKE '%denied%' OR LOWER(response_error_message) LIKE '%unauthorized%' THEN 1 ELSE 0 END) AS access_denied_count,
    SUM(CASE WHEN action_name IN ('deleteTable', 'deleteSchema', 'deleteCatalog', 'dropTable', 'dropDatabase', 'deleteExperiment', 'deleteModel', 'deleteFile') THEN 1 ELSE 0 END) AS destructive_actions,
    SUM(CASE WHEN action_name IN ('updatePermissions', 'grantPermission', 'revokePermission', 'addUserToGroup', 'removeUserFromGroup', 'changeSecuritySettings') THEN 1 ELSE 0 END) AS permission_changes,
    COUNT(DISTINCT service_name) AS services_accessed,
    MAX(CASE WHEN response_result = 'denied' THEN action_name END) AS last_denied_action,
    MAX(CASE WHEN response_result = 'denied' THEN service_name END) AS last_denied_service,
    MAX(CASE WHEN response_result = 'denied' THEN event_time END) AS last_denied_time
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    AND user_identity_email IS NOT NULL
    AND user_identity_email NOT LIKE '%.gserviceaccount.com'
    AND user_identity_email NOT LIKE 'service-principal-%'
    AND user_identity_email NOT LIKE '%[ServicePrincipal]%'
    AND LOWER(user_identity_email) NOT IN ('system', 'admin', 'root', 'databricks')
  GROUP BY user_identity_email
  HAVING SUM(CASE WHEN response_result = 'denied' OR LOWER(response_error_message) LIKE '%denied%' THEN 1 ELSE 0 END) > 5
      OR SUM(CASE WHEN action_name IN ('deleteTable', 'deleteSchema', 'deleteCatalog', 'dropTable', 'dropDatabase') THEN 1 ELSE 0 END) > 2
      OR SUM(CASE WHEN action_name IN ('updatePermissions', 'grantPermission', 'revokePermission', 'addUserToGroup') THEN 1 ELSE 0 END) > 3
)
SELECT
  s.user_identity_email AS user_identity,
  CASE 
    WHEN s.access_denied_count > 50 THEN 'High Access Denial Rate'
    WHEN s.destructive_actions > 5 THEN 'Excessive Data Deletion'
    WHEN s.permission_changes > 5 THEN 'Permission Modification Activity'
    ELSE 'Elevated Activity Pattern'
  END AS threat_type,
  LEAST(100, ROUND(s.access_denied_count * 0.5 + s.destructive_actions * 10 + s.permission_changes * 5, 0)) AS risk_score,
  CONCAT(
    s.access_denied_count, ' access denials, ',
    s.destructive_actions, ' delete operations, ',
    s.permission_changes, ' permission changes'
  ) AS incident_summary,
  COALESCE(s.last_denied_action, 'None recorded') AS last_suspicious_action,
  COALESCE(s.last_denied_service, 'N/A') AS affected_service,
  CASE 
    WHEN s.access_denied_count > 50 THEN 'Review access permissions - user may need correct access'
    WHEN s.destructive_actions > 5 THEN 'Verify deleted resources were authorized'
    WHEN s.permission_changes > 5 THEN 'Audit recent permission changes for appropriateness'
    ELSE 'Monitor user activity pattern'
  END AS recommended_action
FROM security_events s
ORDER BY (s.access_denied_count * 0.5 + s.destructive_actions * 10 + s.permission_changes * 5) DESC
LIMIT 20
```

---

### Dataset 17: ds_runs_by_status

**Display Name:** Runs by Status  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(run_date) AS run_date,
  CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 'Success' ELSE 'Failed' END AS status, 
  COUNT(*) AS count 
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max 
GROUP BY 1, 2 
ORDER BY 1
```

---

### Dataset 18: ds_kpi_tagged

**Display Name:** KPI: Tagged  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) / NULLIF(SUM(list_cost), 0), 3) AS tagged_pct 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
```

---

### Dataset 19: ds_job_trend

**Display Name:** Job Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(run_date) AS day, 
    COUNT(*) AS runs,
    ROUND(SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max 
GROUP BY 1 ORDER BY 1
```

---

### Dataset 20: ds_health_score

**Display Name:** Health Score  
**SQL Query:**
```sql
WITH reliability_health AS (
  SELECT COALESCE(ROUND(SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
performance_health AS (
  SELECT COALESCE(ROUND(SUM(CASE WHEN execution_status = 'FINISHED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= CURRENT_DATE() - INTERVAL 30 DAYS
),
cost_health AS (
  SELECT COALESCE(ROUND(SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
security_health AS (
  SELECT COALESCE(ROUND((1 - (SUM(CASE WHEN response_result = 'denied' OR action_name IN ('deleteTable', 'deleteSchema', 'deleteCatalog', 'dropUser') THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0))) * 100, 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
),
quality_health AS (
  SELECT COALESCE(ROUND(COUNT(DISTINCT target_table_full_name) * 100.0 / NULLIF((SELECT COUNT(*) FROM ${catalog}.${gold_schema}.fact_table_lineage), 0), 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_table_lineage
  WHERE event_time >= CURRENT_DATE() - INTERVAL 30 DAYS
)
SELECT ROUND((COALESCE(r.score, 100) + COALESCE(p.score, 100) + COALESCE(c.score, 100) + COALESCE(s.score, 100) + COALESCE(q.score, 100)) / 5.0, 1) AS health_score
FROM reliability_health r, performance_health p, cost_health c, security_health s, quality_health q
```

---

### Dataset 21: ds_health_trend

**Display Name:** Health Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH daily_reliability AS (
  SELECT run_date AS day, 
    COALESCE(ROUND(SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= :time_range.min AND run_date <= :time_range.max
  GROUP BY run_date
),
daily_performance AS (
  SELECT DATE(start_time) AS day, 
    COALESCE(ROUND(SUM(CASE WHEN execution_status = 'FINISHED' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE DATE(start_time) >= :time_range.min AND DATE(start_time) <= :time_range.max
  GROUP BY DATE(start_time)
),
daily_cost AS (
  SELECT usage_date AS day, 
    COALESCE(ROUND(SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
  GROUP BY usage_date
),
daily_security AS (
  SELECT event_date AS day, 
    COALESCE(ROUND((1 - (SUM(CASE WHEN response_result = 'denied' OR action_name IN ('deleteTable', 'deleteSchema') THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0))) * 100, 1), 100) AS score
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= :time_range.min AND event_date <= :time_range.max
  GROUP BY event_date
)
SELECT COALESCE(r.day, p.day, c.day, s.day) AS day,
  ROUND((COALESCE(r.score, 100) + COALESCE(p.score, 100) + COALESCE(c.score, 100) + COALESCE(s.score, 100)) / 4.0, 1) AS health_score
FROM daily_reliability r
FULL OUTER JOIN daily_performance p ON r.day = p.day
FULL OUTER JOIN daily_cost c ON COALESCE(r.day, p.day) = c.day
FULL OUTER JOIN daily_security s ON COALESCE(r.day, p.day, c.day) = s.day
ORDER BY 1
```

---

### Dataset 22: ds_reliability_health

**Display Name:** Reliability Health  
**SQL Query:**
```sql
SELECT COALESCE(
  ROUND(SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') OR result_state IS NULL THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1),
  100
) AS status 
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= CURRENT_DATE() - INTERVAL 30 DAYS
```

---

### Dataset 23: ds_daily_cost

**Display Name:** Daily Cost  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(usage_date) AS usage_date, SUM(list_cost) AS daily_cost, SUM(CASE WHEN product_features_is_serverless THEN list_cost ELSE 0 END) AS serverless_cost, SUM(CASE WHEN NOT product_features_is_serverless THEN list_cost ELSE 0 END) AS classic_cost FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.fact_usage f LEFT JOIN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold.dim_workspace w ON f.workspace_id = w.workspace_id WHERE 

 usage_date BETWEEN :time_range.min AND :time_range.max
AND (
  'all' IN (SELECT EXPLODE(:param_workspace))
  OR COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) IN (SELECT EXPLODE(:param_workspace))
) GROUP BY 1 ORDER BY 1
```

---

### Dataset 24: ds_serverless_adoption

**Display Name:** Serverless Adoption  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(SUM(CASE WHEN product_features_is_serverless THEN list_cost ELSE 0 END) / NULLIF(SUM(list_cost), 0), 3) AS serverless_pct 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
```

---

### Dataset 25: ds_cost_health

**Display Name:** Cost Health  
**SQL Query:**
```sql
SELECT ROUND(SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) * 100.0 / NULLIF(SUM(list_cost), 0), 1) AS status 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
```

---

### Dataset 26: ds_ml_job_risks

**Display Name:** ML: Job Risks  
**SQL Query:**
```sql
-- Uses ACTUAL job failure data (more reliable than ML predictions that return 1.0 for everything)
WITH job_stats AS (
  SELECT
    f.job_id,
    COALESCE(j.name, f.run_name, CAST(f.job_id AS STRING)) AS job_name,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN f.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) AS failed_runs,
    ROUND(SUM(CASE WHEN f.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS failure_rate,
    MAX(CASE WHEN f.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN f.termination_code END) AS last_error_type,
    MAX(CASE WHEN f.result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN f.run_date END) AS last_failure_date,
    ROUND(STDDEV(f.run_duration_seconds), 1) AS duration_variance_sec,
    MAX(f.run_date) AS last_run_date
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline f
  LEFT JOIN ${catalog}.${gold_schema}.dim_job j ON f.job_id = j.job_id
  WHERE f.run_date >= CURRENT_DATE() - INTERVAL 14 DAYS
  GROUP BY f.job_id, j.name, f.run_name
  HAVING COUNT(*) >= 3  -- Only jobs with enough runs to calculate risk
)
SELECT
  job_name,
  ROUND(failure_rate / 100.0, 2) AS failure_probability,
  CASE 
    WHEN failure_rate > 50 THEN 'HIGH'
    WHEN failure_rate > 20 THEN 'MEDIUM'
    WHEN failure_rate > 5 THEN 'LOW'
    ELSE 'HEALTHY'
  END AS risk_level,
  CONCAT(
    failed_runs, ' failures in ', total_runs, ' runs (', failure_rate, '%). ',
    'Last error: ', COALESCE(last_error_type, 'N/A'), '. ',
    'Duration variance: ', COALESCE(duration_variance_sec, 0), 's'
  ) AS rationale,
  COALESCE(last_error_type, 'No recent errors') AS last_error_preview,
  last_failure_date,
  CASE 
    WHEN failure_rate > 50 THEN 'CRITICAL: Add retry logic, check resources, review error patterns'
    WHEN failure_rate > 20 THEN 'WARNING: Monitor closely, review recent config changes'
    WHEN failure_rate > 5 THEN 'Watch: Occasional failures, review logs'
    ELSE 'Healthy: Continue normal monitoring'
  END AS recommended_action
FROM job_stats
WHERE failed_runs > 0  -- Only show jobs with actual failures
ORDER BY failure_rate DESC, failed_runs DESC
LIMIT 15
```

---

### Dataset 27: ds_kpi_mttr

**Display Name:** KPI: MTTR  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COALESCE(ROUND(AVG(run_duration_seconds)/60, 1), 0) AS mttr_min 
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max 
AND result_state NOT IN ('SUCCESS', 'SUCCEEDED')
```

---

### Dataset 28: ds_kpi_lineage

**Display Name:** KPI: Lineage  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT target_table_full_name) AS lineage_tables FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE event_time >= :time_range.min AND event_time <= :time_range.max
```

---

### Dataset 29: ds_drift_trend

**Display Name:** Drift Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
-- Calculates week-over-week drift from actual Gold layer data
WITH cost_weekly AS (
  SELECT
    DATE_TRUNC('week', usage_date) AS week_start,
    SUM(list_cost) AS weekly_cost
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
  GROUP BY DATE_TRUNC('week', usage_date)
),
job_weekly AS (
  SELECT
    DATE_TRUNC('week', run_date) AS week_start,
    COUNT(*) AS weekly_jobs
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= :time_range.min AND run_date <= :time_range.max
  GROUP BY DATE_TRUNC('week', run_date)
),
query_weekly AS (
  SELECT
    DATE_TRUNC('week', start_time) AS week_start,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) AS p95_duration
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= :time_range.min AND start_time <= :time_range.max
  GROUP BY DATE_TRUNC('week', start_time)
),
cost_drift AS (
  SELECT week_start AS day,
    ROUND(((weekly_cost - LAG(weekly_cost) OVER (ORDER BY week_start)) * 100.0 / NULLIF(LAG(weekly_cost) OVER (ORDER BY week_start), 0)), 1) AS cost_drift
  FROM cost_weekly
),
job_drift AS (
  SELECT week_start AS day,
    ROUND(((weekly_jobs - LAG(weekly_jobs) OVER (ORDER BY week_start)) * 100.0 / NULLIF(LAG(weekly_jobs) OVER (ORDER BY week_start), 0)), 1) AS job_drift
  FROM job_weekly
),
query_drift AS (
  SELECT week_start AS day,
    ROUND(((p95_duration - LAG(p95_duration) OVER (ORDER BY week_start)) * 100.0 / NULLIF(LAG(p95_duration) OVER (ORDER BY week_start), 0)), 1) AS query_drift
  FROM query_weekly
)
SELECT
  COALESCE(c.day, j.day, q.day) AS day,
  COALESCE(c.cost_drift, 0) AS cost_drift,
  COALESCE(j.job_drift, 0) AS job_drift,
  COALESCE(q.query_drift, 0) AS query_drift
FROM cost_drift c
FULL OUTER JOIN job_drift j ON c.day = j.day
FULL OUTER JOIN query_drift q ON COALESCE(c.day, j.day) = q.day
WHERE COALESCE(c.day, j.day, q.day) IS NOT NULL
ORDER BY day
```

---

### Dataset 30: ds_event_trend

**Display Name:** Event Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(event_date) AS day, 
  COUNT(*) AS events,
  COUNT(DISTINCT user_identity_email) AS unique_users 
FROM ${catalog}.${gold_schema}.fact_audit_logs 
WHERE event_date >= :time_range.min AND event_date <= :time_range.max 
GROUP BY 1 ORDER BY 1
```

---

### Dataset 31: ds_kpi_success_rate

**Display Name:** KPI: Success Rate  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 3) AS success_rate 
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max
```

---

### Dataset 32: ds_kpi_cluster

**Display Name:** KPI: Cluster  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(AVG(CASE WHEN driver THEN 80 ELSE 60 END), 0) AS avg_cpu 
FROM ${catalog}.${gold_schema}.fact_node_timeline 
WHERE start_time >= :time_range.min AND start_time <= :time_range.max
```

---

### Dataset 33: ds_kpi_totals

**Display Name:** KPI: Totals  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
    COUNT(*) AS total_runs,
    SUM(CASE WHEN result_state NOT IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) AS total_failures
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max
```

---

### Dataset 34: ds_kpi_tables

**Display Name:** KPI: Tables  
**SQL Query:**
```sql
SELECT COUNT(DISTINCT target_table_full_name) AS total_tables FROM ${catalog}.${gold_schema}.fact_table_lineage
```

---

### Dataset 35: ds_monitor_cost_drift

**Display Name:** Monitor: Cost Drift  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start, 
  ROUND(COALESCE(cost_drift_pct, 0) / 100.0, 4) AS drift_pct 
FROM ${catalog}.${gold_schema}_monitoring.fact_usage_drift_metrics 
WHERE column_name = ':table' 
  AND drift_type = 'CONSECUTIVE'
  AND slice_key IS NULL
  AND window.end >= :time_range.min AND window.end <= :time_range.max
ORDER BY window.start DESC
LIMIT 1
```

---

### Dataset 36: ds_kpi_documented

**Display Name:** KPI: Documented  
**SQL Query:**
```sql
SELECT COUNT(DISTINCT table_full_name) AS documented_tables FROM (SELECT source_table_full_name AS table_full_name FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE source_table_full_name IS NOT NULL UNION SELECT target_table_full_name AS table_full_name FROM ${catalog}.${gold_schema}.fact_table_lineage WHERE target_table_full_name IS NOT NULL)
```

---

### Dataset 37: ds_kpi_30d

**Display Name:** KPI: 30d Spend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT SUM(list_cost) AS cost_30d 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS
```

---

### Dataset 38: ds_kpi_denied

**Display Name:** KPI: Denied  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT request_id) AS denied_access FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE (response_status_code IN ('403', 'FORBIDDEN', 'PERMISSION_DENIED', 'ACCESS_DENIED') OR response_result IN ('DENIED', 'PERMISSION_DENIED', 'FORBIDDEN')) AND event_date >= :time_range.min AND event_date <= :time_range.max
```

---

### Dataset 39: ds_tag_coverage

**Display Name:** Tag Coverage  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(SUM(CASE WHEN is_tagged THEN list_cost ELSE 0 END) / NULLIF(SUM(list_cost), 0), 3) AS tag_coverage 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
```

---

### Dataset 40: ds_30_60_compare

**Display Name:** 30 vs 60 Day Compare  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH periods AS (SELECT SUM(CASE WHEN usage_date >= CURRENT_DATE() - INTERVAL 30 DAYS THEN list_cost ELSE 0 END) AS last_30, SUM(CASE WHEN usage_date BETWEEN CURRENT_DATE() - INTERVAL 60 DAYS AND CURRENT_DATE() - INTERVAL 31 DAYS THEN list_cost ELSE 0 END) AS prev_30 FROM ${catalog}.${gold_schema}.fact_usage) SELECT CONCAT(ROUND((last_30 - prev_30) * 100.0 / NULLIF(prev_30, 0), 1), '%') AS growth_pct FROM periods
```

---

### Dataset 41: ds_ml_cost_anomalies

**Display Name:** ML: Cost Anomalies  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
WITH top_cost_drivers AS (
  SELECT
    workspace_id,
    MAX(usage_date) AS latest_cost_date,
    billing_origin_product,
    sku_name,
    COALESCE(usage_metadata_job_id, usage_metadata_warehouse_id, CONCAT('SKU:', sku_name)) AS resource_id,
    SUM(list_cost) AS resource_cost,
    ROW_NUMBER() OVER (PARTITION BY workspace_id ORDER BY SUM(list_cost) DESC) AS cost_rank
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY workspace_id, billing_origin_product, sku_name, COALESCE(usage_metadata_job_id, usage_metadata_warehouse_id, CONCAT('SKU:', sku_name))
),
workspace_names AS (
  SELECT DISTINCT workspace_id, workspace_name
  FROM ${catalog}.${gold_schema}.dim_workspace
)
SELECT
  COALESCE(w.workspace_name, CAST(t.workspace_id AS STRING)) AS workspace,
  CASE 
    WHEN t.resource_cost > 5000 THEN 'HIGH'
    WHEN t.resource_cost > 1000 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS severity,
  CASE
    WHEN t.billing_origin_product = 'JOBS' THEN CONCAT('Job ID: ', t.resource_id)
    WHEN t.billing_origin_product = 'SQL' THEN CONCAT('Warehouse ID: ', t.resource_id)
    ELSE CONCAT(t.billing_origin_product, ' - ', t.sku_name)
  END AS cost_driver,
  ROUND(t.resource_cost, 2) AS daily_cost,
  CASE 
    WHEN t.resource_cost > 5000 THEN 'Investigate immediately - high cost resource'
    WHEN t.resource_cost > 1000 THEN 'Review for optimization opportunities'
    ELSE 'Monitor cost trends'
  END AS recommended_action,
  CONCAT(
    'SKU: ', t.sku_name, '. ',
    '7-day total: $', FORMAT_NUMBER(t.resource_cost, 2), '. ',
    'Product: ', t.billing_origin_product, '. ',
    'Resource: ', t.resource_id
  ) AS rationale
FROM top_cost_drivers t
LEFT JOIN workspace_names w ON t.workspace_id = w.workspace_id
WHERE t.cost_rank <= 5
ORDER BY t.resource_cost DESC
LIMIT 20
```

---

### Dataset 42: ds_health_issues

**Display Name:** Health Issues  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
WITH job_issues AS (
  SELECT 
    '🔧 Reliability' AS category,
    COALESCE(job_id, 'Unknown') AS asset_id,
    COALESCE(run_name, job_id, 'Unknown Job') AS asset_name,
    COUNT(*) AS issue_count,
    CONCAT(COUNT(*), ' job failures') AS reason,
    MAX(run_date) AS last_occurrence,
    CASE WHEN COUNT(*) > 10 THEN 'High' WHEN COUNT(*) > 5 THEN 'Medium' ELSE 'Low' END AS severity
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= :time_range.min AND run_date <= :time_range.max
    AND result_state NOT IN ('SUCCESS', 'SUCCEEDED') AND result_state IS NOT NULL
  GROUP BY job_id, run_name
  HAVING COUNT(*) > 0
),
query_issues AS (
  SELECT 
    '⚡ Performance' AS category,
    COALESCE(statement_id, 'Unknown') AS asset_id,
    COALESCE(LEFT(statement_text, 50), 'Unknown Query') AS asset_name,
    COUNT(*) AS issue_count,
    CONCAT(COUNT(*), ' query failures') AS reason,
    MAX(DATE(start_time)) AS last_occurrence,
    CASE WHEN COUNT(*) > 20 THEN 'High' WHEN COUNT(*) > 10 THEN 'Medium' ELSE 'Low' END AS severity
  FROM ${catalog}.${gold_schema}.fact_query_history
  WHERE start_time >= :time_range.min AND start_time <= :time_range.max
    AND execution_status != 'FINISHED'
  GROUP BY statement_id, LEFT(statement_text, 50)
  HAVING COUNT(*) > 0
),
cost_issues AS (
  SELECT 
    '💰 Cost' AS category,
    workspace_id AS asset_id,
    COALESCE(workspace_id, 'Unknown Workspace') AS asset_name,
    ROUND(SUM(list_cost), 2) AS issue_count,
    CONCAT('$', ROUND(SUM(list_cost), 0), ' untagged spend') AS reason,
    MAX(usage_date) AS last_occurrence,
    CASE WHEN SUM(list_cost) > 10000 THEN 'High' WHEN SUM(list_cost) > 1000 THEN 'Medium' ELSE 'Low' END AS severity
  FROM ${catalog}.${gold_schema}.fact_usage
  WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
    AND NOT COALESCE(is_tagged, false)
  GROUP BY workspace_id
  HAVING SUM(list_cost) > 100
),
security_issues AS (
  SELECT 
    '🔒 Security' AS category,
    COALESCE(user_identity_email, 'Unknown User') AS asset_id,
    COALESCE(user_identity_email, 'Unknown User') AS asset_name,
    COUNT(*) AS issue_count,
    CONCAT(COUNT(*), ' high-risk actions') AS reason,
    MAX(event_date) AS last_occurrence,
    CASE WHEN COUNT(*) > 50 THEN 'High' WHEN COUNT(*) > 20 THEN 'Medium' ELSE 'Low' END AS severity
  FROM ${catalog}.${gold_schema}.fact_audit_logs
  WHERE event_date >= :time_range.min AND event_date <= :time_range.max
    AND (response_result = 'denied' OR action_name IN ('deleteTable', 'deleteSchema', 'deleteCatalog', 'dropUser', 'addUserToGroup', 'removeUserFromGroup'))
  GROUP BY user_identity_email
  HAVING COUNT(*) > 5
),
quality_issues AS (
  SELECT 
    '📊 Quality' AS category,
    COALESCE(target_table_full_name, 'Unknown Table') AS asset_id,
    COALESCE(SPLIT(target_table_full_name, '.')[2], target_table_full_name) AS asset_name,
    COUNT(*) AS issue_count,
    CONCAT('Low lineage activity (', COUNT(*), ' events)') AS reason,
    MAX(DATE(event_time)) AS last_occurrence,
    'Medium' AS severity
  FROM ${catalog}.${gold_schema}.fact_table_lineage
  WHERE event_time >= :time_range.min AND event_time <= :time_range.max
  GROUP BY target_table_full_name
  HAVING COUNT(*) < 5
)
SELECT * FROM (
  SELECT category, asset_id, asset_name, issue_count, reason, last_occurrence, severity FROM job_issues
  UNION ALL
  SELECT category, asset_id, asset_name, issue_count, reason, last_occurrence, severity FROM query_issues
  UNION ALL
  SELECT category, asset_id, asset_name, issue_count, reason, last_occurrence, severity FROM cost_issues
  UNION ALL
  SELECT category, asset_id, asset_name, issue_count, reason, last_occurrence, severity FROM security_issues
  UNION ALL
  SELECT category, asset_id, asset_name, issue_count, reason, last_occurrence, severity FROM quality_issues
) combined
ORDER BY 
  CASE severity WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
  issue_count DESC
LIMIT 20
```

---

### Dataset 43: ds_sku_breakdown

**Display Name:** Billing Origin Product Breakdown  
**Parameters:**
- `param_sku_type` (STRING) - param_sku_type
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  COALESCE(billing_origin_product, 'Unknown') AS product, 
  ROUND(SUM(list_cost), 2) AS cost 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max 
  AND (ARRAY_CONTAINS(:param_sku_type, 'all') OR ARRAY_CONTAINS(:param_sku_type, sku_name) OR :param_sku_type IS NULL)
GROUP BY 1 
HAVING SUM(list_cost) > 0
ORDER BY cost DESC 
LIMIT 10
```

---

### Dataset 44: ds_kpi_admin

**Display Name:** KPI: Admin  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(*) AS admin_actions FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE action_name LIKE '%Admin%' AND event_date >= :time_range.min AND event_date <= :time_range.max
```

---

### Dataset 45: ds_kpi_users

**Display Name:** KPI: Users  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT user_identity_email) AS active_users 
FROM ${catalog}.${gold_schema}.fact_audit_logs 
WHERE event_date >= :time_range.min AND event_date <= :time_range.max
  AND user_identity_email IS NOT NULL
  AND user_identity_email NOT LIKE '%.gserviceaccount.com'
  AND user_identity_email NOT LIKE 'service-principal-%'
  AND user_identity_email NOT LIKE '%[ServicePrincipal]%'
  AND user_identity_email NOT IN ('System-User', 'system', 'admin', 'root', 'databricks')
```

---

### Dataset 46: ds_cost_trend

**Display Name:** Cost Trend  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(usage_date) AS day, SUM(list_cost) AS daily_cost 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max 
GROUP BY 1 ORDER BY 1
```

---

### Dataset 47: ds_monitor_job_drift

**Display Name:** Monitor: Job Drift  
**SQL Query:**
```sql
-- Calculates week-over-week job volume drift from actual data
WITH current_week AS (
  SELECT COUNT(*) AS runs
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
previous_week AS (
  SELECT COUNT(*) AS runs
  FROM ${catalog}.${gold_schema}.fact_job_run_timeline
  WHERE run_date >= CURRENT_DATE() - INTERVAL 14 DAYS
    AND run_date < CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT
  ROUND(
    CASE 
      WHEN p.runs = 0 THEN 0
      ELSE (c.runs - p.runs) * 1.0 / p.runs
    END,
    4
  ) AS drift_pct
FROM current_week c, previous_week p
```

---

### Dataset 48: ds_kpi_mtd

**Display Name:** KPI: MTD Spend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT SUM(list_cost) AS cost_mtd 
FROM ${catalog}.${gold_schema}.fact_usage 
WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE())
```

---

### Dataset 49: ds_kpi_permissions

**Display Name:** KPI: Permissions  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT request_id) AS permission_changes FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE action_name IN ('updatePermissions', 'grantPermission', 'revokePermission', 'addUserToGroup', 'removeUserFromGroup', 'setPermissions', 'changeOwner', 'createGrant', 'deleteGrant') AND event_date >= :time_range.min AND event_date <= :time_range.max
```

---

### Dataset 50: ds_kpi_high_risk

**Display Name:** KPI: High Risk  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT request_id) AS high_risk_events FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE action_name IN ('deleteTable', 'deleteSchema', 'deleteCatalog', 'dropUser', 'deleteCluster', 'deleteWarehouse', 'deletePipeline', 'deleteExperiment', 'deleteModel') AND event_date >= :time_range.min AND event_date <= :time_range.max
```

---

### Dataset 51: ds_success_trend

**Display Name:** Success Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(run_date) AS day, 
  ROUND(SUM(CASE WHEN result_state IN ('SUCCESS', 'SUCCEEDED') THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS success_rate
FROM ${catalog}.${gold_schema}.fact_job_run_timeline 
WHERE run_date >= :time_range.min AND run_date <= :time_range.max 
GROUP BY 1 ORDER BY 1
```

---

### Dataset 52: ds_kpi_workspaces

**Display Name:** KPI: Workspaces  
**Parameters:**
- `param_workspace` (STRING) - param_workspace
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(DISTINCT workspace_id) AS total_workspaces FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= :time_range.min AND usage_date <= :time_range.max
```

---

### Dataset 53: ds_drift_alerts

**Display Name:** Drift Alerts  
**SQL Query:**
```sql
-- Calculates week-over-week drift alerts from actual Gold layer data
WITH this_week_cost AS (
  SELECT SUM(list_cost) AS total FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
last_week_cost AS (
  SELECT SUM(list_cost) AS total FROM ${catalog}.${gold_schema}.fact_usage WHERE usage_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND usage_date < CURRENT_DATE() - INTERVAL 7 DAYS
),
this_week_jobs AS (
  SELECT COUNT(*) AS total FROM ${catalog}.${gold_schema}.fact_job_run_timeline WHERE run_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
last_week_jobs AS (
  SELECT COUNT(*) AS total FROM ${catalog}.${gold_schema}.fact_job_run_timeline WHERE run_date >= CURRENT_DATE() - INTERVAL 14 DAYS AND run_date < CURRENT_DATE() - INTERVAL 7 DAYS
),
this_week_p95 AS (
  SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) AS p95 FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time >= CURRENT_DATE() - INTERVAL 7 DAYS
),
last_week_p95 AS (
  SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) AS p95 FROM ${catalog}.${gold_schema}.fact_query_history WHERE start_time >= CURRENT_DATE() - INTERVAL 14 DAYS AND start_time < CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT 
  'Cost' AS area,
  'Week-over-Week Cost %' AS metric,
  ROUND((tw.total - lw.total) * 100.0 / NULLIF(lw.total, 0), 2) AS drift_pct,
  CASE 
    WHEN ABS((tw.total - lw.total) * 100.0 / NULLIF(lw.total, 0)) > 20 THEN 'high'
    WHEN ABS((tw.total - lw.total) * 100.0 / NULLIF(lw.total, 0)) > 10 THEN 'medium'
    ELSE 'low'
  END AS severity
FROM this_week_cost tw, last_week_cost lw
UNION ALL
SELECT 
  'Reliability' AS area,
  'Week-over-Week Job Volume %' AS metric,
  ROUND((tw.total - lw.total) * 100.0 / NULLIF(lw.total, 0), 2) AS drift_pct,
  CASE 
    WHEN ABS((tw.total - lw.total) * 100.0 / NULLIF(lw.total, 0)) > 50 THEN 'high'
    WHEN ABS((tw.total - lw.total) * 100.0 / NULLIF(lw.total, 0)) > 25 THEN 'medium'
    ELSE 'low'
  END AS severity
FROM this_week_jobs tw, last_week_jobs lw
UNION ALL
SELECT 
  'Performance' AS area,
  'Week-over-Week P95 Query Duration %' AS metric,
  ROUND((tw.p95 - lw.p95) * 100.0 / NULLIF(lw.p95, 0), 2) AS drift_pct,
  CASE 
    WHEN ABS((tw.p95 - lw.p95) * 100.0 / NULLIF(lw.p95, 0)) > 30 THEN 'high'
    WHEN ABS((tw.p95 - lw.p95) * 100.0 / NULLIF(lw.p95, 0)) > 15 THEN 'medium'
    ELSE 'low'
  END AS severity
FROM this_week_p95 tw, last_week_p95 lw
ORDER BY ABS(drift_pct) DESC
```

---

### Dataset 54: ds_kpi_failed

**Display Name:** KPI: Failed Queries  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT ROUND(
    SUM(CASE WHEN execution_status != 'FINISHED' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 
    3) AS failed_queries_pct 
FROM ${catalog}.${gold_schema}.fact_query_history 
WHERE start_time >= :time_range.min AND start_time <= :time_range.max
```

---

### Dataset 55: ds_query_volume

**Display Name:** Query Volume  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(start_time) AS day, COUNT(*) AS query_count 
FROM ${catalog}.${gold_schema}.fact_query_history 
WHERE start_time >= :time_range.min AND start_time <= :time_range.max 
GROUP BY 1 ORDER BY 1
```

---

### Dataset 56: ds_lineage_trend

**Display Name:** Lineage Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(event_time) AS day, COUNT(*) AS events, COUNT(DISTINCT target_table_full_name) AS tables 
FROM ${catalog}.${gold_schema}.fact_table_lineage 
WHERE event_time >= :time_range.min AND event_time <= :time_range.max 
GROUP BY 1 ORDER BY 1
```

---

### Dataset 57: ds_kpi_security

**Display Name:** KPI: Security  
**Parameters:**
- `time_range` (DATE) - time_range
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(*) AS high_risk 
FROM ${catalog}.${gold_schema}.fact_audit_logs 
WHERE action_name IN ('deleteTable', 'deleteSchema', 'deleteCatalog', 'dropUser') 
AND event_date >= :time_range.min AND event_date <= :time_range.max
```

---

### Dataset 58: ds_time_windows

**Display Name:** Time Windows  
**SQL Query:**
```sql
SELECT 'Last 7 Days' AS time_window UNION ALL SELECT 'Last 30 Days' UNION ALL SELECT 'Last 90 Days' UNION ALL SELECT 'Last 6 Months' UNION ALL SELECT 'Last Year'
```

---

### Dataset 59: ds_workspaces

**Display Name:** Workspaces  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT 'All' AS workspace_name 
UNION ALL 
SELECT DISTINCT workspace_name 
FROM ${catalog}.${gold_schema}.dim_workspace 
WHERE workspace_name IS NOT NULL 
ORDER BY workspace_name
```

---

### Dataset 60: select_workspace

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

### Dataset 61: select_time_key

**Display Name:** select_time_key  
**SQL Query:**
```sql
SELECT 'Day' AS time_key UNION ALL SELECT 'Week' UNION ALL SELECT 'Month' UNION ALL SELECT 'Quarter'
```

---

### Dataset 62: ds_select_workspace

**Display Name:** select_workspace  
**Parameters:**
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT DISTINCT 
  COALESCE(workspace_name, CAST(workspace_id AS STRING)) AS workspace_name
FROM ${catalog}.${gold_schema}.dim_workspace
ORDER BY 1
```

---

### Dataset 63: ds_select_sku

**Display Name:** ds_select_sku  
**SQL Query:**
```sql
SELECT 'all' AS sku_category UNION ALL SELECT DISTINCT sku_name AS sku_category FROM ${catalog}.${gold_schema}.fact_usage WHERE sku_name IS NOT NULL ORDER BY 1
```

---
