# Complete Security & Audit Dataset Catalog

## Overview
**Total Datasets:** 36  
**Dashboard:** `security.lvdash.json`  
**Coverage:** ALL datasets from ALL pages with FULL details

---

## Dataset Index

| # | Dataset Name | Display Name | Has Query | Parameters |
|---|--------------|--------------|-----------|------------|
| 1 | ds_kpi_events | KPI: Events | ✅ | time_range, param_workspace |
| 2 | ds_kpi_high_risk | KPI: High Risk | ✅ | time_range |
| 3 | ds_kpi_denied | KPI: Denied | ✅ | time_range |
| 4 | ds_kpi_permissions | KPI: Permissions | ✅ | time_range |
| 5 | ds_kpi_admin | KPI: Admin | ✅ | time_range |
| 6 | ds_event_trend | Event Trend | ✅ | time_range, param_workspace |
| 7 | ds_risk_trend | Risk Trend | ✅ | time_range |
| 8 | ds_denied_access | Denied Access | ✅ | time_range, param_service, param_workspace |
| 9 | ds_permission_changes | Permission Changes | ✅ | time_range |
| 10 | ds_denied_by_service | Denied by Service | ✅ | time_range, param_service |
| 11 | ds_denied_by_user | Denied by User | ✅ | time_range |
| 12 | ds_admin_actions | Admin Actions | ✅ | time_range, param_service |
| 13 | ds_sensitive_actions | Sensitive Actions | ✅ | time_range, param_service |
| 14 | ds_admin_by_action | Admin by Action | ✅ | time_range |
| 15 | ds_data_access | Data Access | ✅ | time_range, param_service, param_workspace |
| 16 | ds_access_by_service | Access by Service | ✅ | time_range, param_service, param_workspace |
| 17 | ds_access_hourly | Access Hourly | ✅ | time_range |
| 18 | ds_ml_threats | ML: Threats | ✅ | - |
| 19 | ds_ml_exfiltration | ML: Exfiltration | ✅ | - |
| 20 | ds_ml_privilege | ML: Privilege | ✅ | - |
| 21 | ds_monitor_latest | Monitor: Latest | ✅ | time_range |
| 22 | ds_monitor_trend | Monitor: Trend | ✅ | time_range |
| 23 | ds_monitor_access | Monitor: Access | ✅ | time_range |
| 24 | ds_monitor_drift | Monitor: Drift | ✅ | time_range |
| 25 | ds_monitor_detailed | Monitor: Detailed | ✅ | time_range |
| 26 | ds_time_windows | Time Windows | ✅ | - |
| 27 | ds_workspaces | Workspaces | ✅ | - |
| 28 | select_workspace | select_workspace | ✅ | - |
| 29 | select_time_key | select_time_key | ✅ | - |
| 30 | ds_select_workspace | ds_select_workspace | ✅ | - |
| 31 | ds_select_service | ds_select_service | ✅ | - |
| 32 | ds_select_action | ds_select_action | ✅ | - |
| 33 | ds_monitor_security_aggregate | Security Aggregate Metrics | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 34 | ds_monitor_security_derived | Security Derived KPIs | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key, monitor_slice_value |
| 35 | ds_monitor_security_slice_keys | Security Slice Keys | ✅ | monitor_time_start, monitor_time_end |
| 36 | ds_monitor_security_slice_values | Security Slice Values | ✅ | monitor_time_start, monitor_time_end, monitor_slice_key |

---

## Complete SQL Queries


### Dataset 1: ds_kpi_events

**Display Name:** KPI: Events  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT COUNT(*) AS total_events, COUNT(DISTINCT user_identity_email) AS unique_users FROM ${catalog}.${gold_schema}.fact_audit_logs f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING))))
```

---

### Dataset 2: ds_kpi_high_risk

**Display Name:** KPI: High Risk  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT SUM(CASE WHEN action_name LIKE '%delete%' OR action_name LIKE '%drop%' OR action_name LIKE '%revoke%' OR action_name LIKE '%destroy%' OR action_name LIKE '%terminate%' THEN 1 ELSE 0 END) AS high_risk_events FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_time BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 3: ds_kpi_denied

**Display Name:** KPI: Denied  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COUNT(*) AS denied_access FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (is_failed_action = true OR response_status_code >= 400 OR LOWER(action_name) LIKE '%denied%' OR LOWER(action_name) LIKE '%unauthorized%')
```

---

### Dataset 4: ds_kpi_permissions

**Display Name:** KPI: Permissions  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT SUM(CASE WHEN action_name LIKE '%grant%' OR action_name LIKE '%revoke%' OR action_name LIKE '%permission%' OR action_name LIKE '%updatePermissions%' THEN 1 ELSE 0 END) AS permission_changes FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_time BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 5: ds_kpi_admin

**Display Name:** KPI: Admin  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT SUM(CASE WHEN service_name IN ('accounts', 'settings', 'clusters', 'workspaces') OR action_name LIKE '%admin%' OR action_name LIKE '%config%' THEN 1 ELSE 0 END) AS admin_actions FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_time BETWEEN :time_range.min AND :time_range.max
```

---

### Dataset 6: ds_event_trend

**Display Name:** Event Trend  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT DATE(event_time) AS day, COUNT(*) AS event_count, COUNT(DISTINCT user_identity_email) AS unique_users FROM ${catalog}.${gold_schema}.fact_audit_logs f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)))) GROUP BY 1 ORDER BY 1
```

---

### Dataset 7: ds_risk_trend

**Display Name:** Risk Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT DATE(event_time) AS day, SUM(CASE WHEN action_name LIKE '%delete%' OR action_name LIKE '%drop%' THEN 1 ELSE 0 END) AS high_risk, SUM(CASE WHEN action_name LIKE '%update%' OR action_name LIKE '%modify%' THEN 1 ELSE 0 END) AS medium_risk FROM ${catalog}.${gold_schema}.fact_audit_logs  WHERE event_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 8: ds_denied_access

**Display Name:** Denied Access  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_service` (STRING) - param_service
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT f.user_identity_email, f.action_name, f.service_name, f.event_time, f.source_ip_address AS source_ip, f.response_error_message AS error_message FROM ${catalog}.${gold_schema}.fact_audit_logs f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.event_time BETWEEN :time_range.min AND :time_range.max AND (f.is_failed_action = true OR f.response_status_code >= 400 OR LOWER(f.action_name) LIKE '%denied%' OR LOWER(f.action_name) LIKE '%unauthorized%') AND (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)))) ORDER BY f.event_time DESC LIMIT 50
```

---

### Dataset 9: ds_permission_changes

**Display Name:** Permission Changes  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT user_identity_email, action_name, COALESCE(get_json_object(to_json(request_params), '$.securable_full_name'), COALESCE(get_json_object(to_json(request_params), '$.full_name'), get_json_object(to_json(request_params), '$.name')), 'N/A') AS target_entity, event_time FROM ${catalog}.${gold_schema}.fact_audit_logs  WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (action_name LIKE '%grant%' OR action_name LIKE '%revoke%' OR action_name LIKE '%permission%') ORDER BY event_time DESC LIMIT 30
```

---

### Dataset 10: ds_denied_by_service

**Display Name:** Denied by Service  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_service` (STRING) - param_service

**SQL Query:**
```sql
SELECT COALESCE(service_name, 'Unknown') AS service_name, COUNT(*) AS denial_count FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (is_failed_action = true OR response_status_code >= 400 OR LOWER(action_name) LIKE '%denied%' OR LOWER(action_name) LIKE '%unauthorized%') GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

---

### Dataset 11: ds_denied_by_user

**Display Name:** Denied by User  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT COALESCE(user_identity_email, 'Unknown') AS user_identity_email, COUNT(*) AS denial_count FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (is_failed_action = true OR response_status_code >= 400 OR LOWER(action_name) LIKE '%denied%' OR LOWER(action_name) LIKE '%unauthorized%') GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

---

### Dataset 12: ds_admin_actions

**Display Name:** Admin Actions  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_service` (STRING) - param_service

**SQL Query:**
```sql
SELECT user_identity_email, action_name, service_name, COALESCE(get_json_object(to_json(request_params), '$.securable_full_name'), COALESCE(get_json_object(to_json(request_params), '$.full_name'), get_json_object(to_json(request_params), '$.name')), 'N/A') AS target_entity, event_time FROM ${catalog}.${gold_schema}.fact_audit_logs  WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (action_name LIKE '%admin%' OR action_name LIKE '%create%' OR action_name LIKE '%delete%') ORDER BY event_time DESC LIMIT 30
```

---

### Dataset 13: ds_sensitive_actions

**Display Name:** Sensitive Actions  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_service` (STRING) - param_service

**SQL Query:**
```sql
SELECT user_identity_email, action_name, service_name, event_time FROM ${catalog}.${gold_schema}.fact_audit_logs  WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (action_name LIKE '%delete%' OR action_name LIKE '%drop%' OR action_name LIKE '%revoke%') ORDER BY event_time DESC LIMIT 30
```

---

### Dataset 14: ds_admin_by_action

**Display Name:** Admin by Action  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT action_name, COUNT(*) AS action_count FROM ${catalog}.${gold_schema}.fact_audit_logs  WHERE event_time BETWEEN :time_range.min AND :time_range.max AND (action_name LIKE '%admin%' OR action_name LIKE '%create%' OR action_name LIKE '%delete%') GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

---

### Dataset 15: ds_data_access

**Display Name:** Data Access  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_service` (STRING) - param_service
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT f.user_identity_email, f.action_name, COALESCE(get_json_object(to_json(f.request_params), '$.securable_full_name'), COALESCE(get_json_object(to_json(f.request_params), '$.full_name'), get_json_object(to_json(f.request_params), '$.name')), 'N/A') AS target_table, COUNT(*) AS access_count FROM ${catalog}.${gold_schema}.fact_audit_logs f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.event_time BETWEEN :time_range.min AND :time_range.max AND f.service_name = 'unityCatalog' AND (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)))) GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 30
```

---

### Dataset 16: ds_access_by_service

**Display Name:** Access by Service  
**Parameters:**
- `time_range` (DATE) - time_range
- `param_service` (STRING) - param_service
- `param_workspace` (STRING) - param_workspace

**SQL Query:**
```sql
SELECT f.service_name, COUNT(*) AS access_count FROM ${catalog}.${gold_schema}.fact_audit_logs f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.event_time BETWEEN :time_range.min AND :time_range.max AND (ARRAY_CONTAINS(:param_workspace, 'all') OR ARRAY_CONTAINS(:param_workspace, COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)))) GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```

---

### Dataset 17: ds_access_hourly

**Display Name:** Access Hourly  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT HOUR(event_time) AS hour, COUNT(*) AS access_count FROM ${catalog}.${gold_schema}.fact_audit_logs  WHERE event_time BETWEEN :time_range.min AND :time_range.max GROUP BY 1 ORDER BY 1
```

---

### Dataset 18: ds_ml_threats

**Display Name:** ML: Threats  
**SQL Query:**
```sql
SELECT
  user_id AS user_identity_email,
  CASE 
    WHEN prediction > 0.8 THEN 'Potential Data Breach'
    WHEN prediction > 0.5 THEN 'Suspicious Activity'
    ELSE 'Low Risk'
  END AS threat_type,
  ROUND(prediction * 100, 1) AS risk_score,
  ROUND(prediction, 2) AS confidence,
  scored_at AS prediction_date
FROM ${catalog}.${feature_schema}.security_threat_predictions
WHERE scored_at >= :time_range.min AND scored_at <= :time_range.max
ORDER BY prediction DESC
LIMIT 50
```

---

### Dataset 19: ds_ml_exfiltration

**Display Name:** ML: Exfiltration  
**SQL Query:**
```sql
SELECT
  user_id AS user_identity_email,
  ROUND(prediction * 1000, 0) AS data_volume,
  CASE 
    WHEN prediction > 0.7 THEN 'HIGH'
    WHEN prediction > 0.4 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_level,
  ROUND(prediction, 3) AS anomaly_score,
  scored_at
FROM ${catalog}.${feature_schema}.exfiltration_predictions
WHERE scored_at >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY prediction DESC
LIMIT 30
```

---

### Dataset 20: ds_ml_privilege

**Display Name:** ML: Privilege  
**SQL Query:**
```sql
SELECT
  user_id AS user_identity_email,
  'User' AS current_role,
  CASE 
    WHEN prediction > 0.7 THEN 'HIGH'
    WHEN prediction > 0.4 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS escalation_risk,
  ROUND(prediction, 2) AS confidence,
  scored_at
FROM ${catalog}.${feature_schema}.privilege_escalation_predictions
WHERE scored_at >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY prediction DESC
LIMIT 30
```

---

### Dataset 21: ds_monitor_latest

**Display Name:** Monitor: Latest  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  COALESCE(total_events, 0) AS total_events,
  COALESCE(distinct_users, 0) AS unique_users,
  ROUND(COALESCE(sensitive_action_count, 0) * 100.0 / NULLIF(total_events, 0), 2) AS high_risk_rate
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= :time_range.min
ORDER BY window.start DESC
LIMIT 1
```

---

### Dataset 22: ds_monitor_trend

**Display Name:** Monitor: Trend  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  COALESCE(total_events, 0) AS total_events,
  COALESCE(sensitive_action_count, 0) AS high_risk_events,
  COALESCE(distinct_users, 0) AS unique_users
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= :time_range.min
ORDER BY window_start
```

---

### Dataset 23: ds_monitor_access

**Display Name:** Monitor: Access  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  COALESCE(failed_action_count, 0) AS denied_accesses,
  COALESCE(permission_change_count, 0) AS permission_changes,
  COALESCE(account_level_events, 0) AS admin_actions
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= :time_range.min
ORDER BY window_start
```

---

### Dataset 24: ds_monitor_drift

**Display Name:** Monitor: Drift  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  COALESCE(event_volume_drift_pct, 0) AS event_volume_drift,
  COALESCE(sensitive_action_drift, 0) AS risk_level_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
  AND slice_key IS NULL
  AND window.start >= :time_range.min
ORDER BY window_start
```

---

### Dataset 25: ds_monitor_detailed

**Display Name:** Monitor: Detailed  
**Parameters:**
- `time_range` (DATE) - time_range

**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  COALESCE(total_events, 0) AS total_events,
  COALESCE(distinct_users, 0) AS unique_users,
  COALESCE(sensitive_action_count, 0) AS high_risk_events,
  COALESCE(failed_action_count, 0) AS denied_accesses
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= :time_range.min
ORDER BY window_start DESC
LIMIT 30
```

---

### Dataset 26: ds_time_windows

**Display Name:** Time Windows  
**SQL Query:**
```sql
SELECT 'Last 7 Days' AS time_window UNION ALL SELECT 'Last 30 Days' UNION ALL SELECT 'Last 90 Days' UNION ALL SELECT 'Last 6 Months' UNION ALL SELECT 'Last Year' UNION ALL SELECT 'All Time'
```

---

### Dataset 27: ds_workspaces

**Display Name:** Workspaces  
**SQL Query:**
```sql
SELECT 'All' AS workspace_name UNION ALL SELECT DISTINCT workspace_name FROM ${catalog}.${gold_schema}.dim_workspace WHERE workspace_name IS NOT NULL ORDER BY workspace_name
```

---

### Dataset 28: select_workspace

**Display Name:** select_workspace  
**SQL Query:**
```sql
SELECT DISTINCT 
  COALESCE(workspace_name, CONCAT('id: ', workspace_id)) AS workspace_name
FROM ${catalog}.${gold_schema}.dim_workspace 
WHERE workspace_name IS NOT NULL 
ORDER BY workspace_name
```

---

### Dataset 29: select_time_key

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

### Dataset 30: ds_select_workspace

**Display Name:** ds_select_workspace  
**SQL Query:**
```sql
SELECT DISTINCT COALESCE(w.workspace_name, CAST(f.workspace_id AS STRING)) AS workspace_name FROM ${catalog}.${gold_schema}.fact_audit_logs f LEFT JOIN ${catalog}.${gold_schema}.dim_workspace w ON f.workspace_id = w.workspace_id WHERE f.workspace_id IS NOT NULL ORDER BY 1
```

---

### Dataset 31: ds_select_service

**Display Name:** ds_select_service  
**SQL Query:**
```sql
SELECT DISTINCT service_name FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE service_name IS NOT NULL ORDER BY 1 LIMIT 50
```

---

### Dataset 32: ds_select_action

**Display Name:** ds_select_action  
**SQL Query:**
```sql
SELECT DISTINCT action_name FROM ${catalog}.${gold_schema}.fact_audit_logs WHERE action_name IS NOT NULL ORDER BY 1 LIMIT 50
```

---

### Dataset 33: ds_monitor_security_aggregate

**Display Name:** Security Aggregate Metrics  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
-- Security aggregate metrics from fact_audit_logs
SELECT
  DATE(event_time) AS window_start,
  COUNT(*) AS total_events,
  COUNT(DISTINCT user_identity_email) AS distinct_users,
  SUM(CASE WHEN service_name = 'accounts' OR action_name LIKE '%admin%' THEN 1 ELSE 0 END) AS admin_actions,
  SUM(CASE
    WHEN action_name IN ('deleteCluster', 'deleteJob', 'deleteWarehouse', 'deleteSecret',
                         'removePermissions', 'revokeToken', 'deleteUser', 'removeGroupMember',
                         'updateClusterPermissions', 'updateJobPermissions') THEN 1
    WHEN action_name LIKE '%secret%' OR action_name LIKE '%token%' OR action_name LIKE '%permission%' THEN 1
    ELSE 0
  END) AS high_risk_events
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_time >= :monitor_time_start
  AND event_time <= COALESCE(:monitor_time_end, CURRENT_TIMESTAMP())
GROUP BY DATE(event_time)
ORDER BY window_start DESC
```

---

### Dataset 34: ds_monitor_security_derived

**Display Name:** Security Derived KPIs  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key
- `monitor_slice_value` (STRING) - monitor_slice_value

**SQL Query:**
```sql
SELECT 
  DATE(window.start) AS window_start,
  ROUND(COALESCE(sensitive_action_rate, 0) * 100, 2) AS admin_action_rate,
  ROUND(COALESCE(failure_rate, 0) * 100, 2) AS high_risk_event_rate
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key IS NULL
  AND window.start >= :monitor_time_start
ORDER BY window_start DESC
```

---

### Dataset 35: ds_monitor_security_slice_keys

**Display Name:** Security Slice Keys  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end

**SQL Query:**
```sql
WITH profile_metrics AS (
  SELECT DISTINCT slice_key
  FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
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

### Dataset 36: ds_monitor_security_slice_values

**Display Name:** Security Slice Values  
**Parameters:**
- `monitor_time_start` (DATETIME) - monitor_time_start
- `monitor_time_end` (DATETIME) - monitor_time_end
- `monitor_slice_key` (STRING) - monitor_slice_key

**SQL Query:**
```sql
WITH profile_metrics AS (
  SELECT DISTINCT slice_value, COALESCE(slice_key, 'No Slice') AS sk
  FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
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
