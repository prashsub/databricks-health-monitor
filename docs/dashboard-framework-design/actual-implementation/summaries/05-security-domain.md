# Security Domain - Actual Implementation

## Overview

**Dashboard:** `security.lvdash.json`  
**Total Datasets:** 36  
**Primary Tables:**
- `fact_audit_logs` (audit events)
- `fact_audit_logs_profile_metrics` (Lakehouse Monitoring metrics)
- `fact_audit_logs_drift_metrics` (drift detection)
- `dim_workspace` (workspace metadata)
- `dim_user` (user lookup)

---

## 📊 Key Metrics

### Event Metrics
- **Total Events**: Count of all audit events
- **Failed Events**: Count of failed access attempts
- **High-Risk Events**: Critical security events requiring review
- **Unique Users**: Active user count
- **Events by Service**: Distribution across Databricks services

### Access Control Metrics
- **Failed Access Attempts**: Count of denied access
- **Success Rate %**: Percentage of successful authentications
- **Sensitive Actions**: High-privilege operations count
- **Policy Violations**: Access control violations

### Compliance Metrics
- **Compliance Score %**: Overall security posture
- **Audit Coverage %**: Percentage of resources audited
- **Encryption Enabled %**: Resources with encryption
- **MFA Adoption %**: Users with multi-factor authentication

---

## 🔑 Key Datasets

### ds_events_by_service
**Purpose:** Event distribution by Databricks service  
**Source:** `fact_audit_logs`  
**Key Query:**
```sql
SELECT 
  service_name,
  COUNT(*) AS event_count,
  SUM(CASE WHEN response_status_code >= 400 THEN 1 ELSE 0 END) AS failed_count,
  ROUND(SUM(CASE WHEN response_status_code < 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS success_rate
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date BETWEEN :time_range.min AND :time_range.max
GROUP BY service_name
ORDER BY event_count DESC
```

### ds_failed_access
**Purpose:** Failed access attempts for security review  
**Source:** `fact_audit_logs`  
**Key Query:**
```sql
SELECT 
  event_date,
  event_time,
  user_identity_email,
  service_name,
  action_name,
  response_status_code,
  error_message,
  request_params,
  source_ip_address
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date BETWEEN :time_range.min AND :time_range.max
  AND response_status_code >= 400
ORDER BY event_date DESC, event_time DESC
LIMIT 100
```

### ds_high_risk_events
**Purpose:** Critical security events requiring attention  
**Source:** `fact_audit_logs`  
**Key Query:**
```sql
SELECT 
  event_date,
  event_time,
  user_identity_email,
  service_name,
  action_name,
  risk_level,
  CASE 
    WHEN action_name LIKE '%delete%' THEN 'Deletion'
    WHEN action_name LIKE '%permission%' THEN 'Permission Change'
    WHEN action_name LIKE '%secret%' THEN 'Secret Access'
    ELSE 'Other'
  END AS event_category,
  request_params
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date BETWEEN :time_range.min AND :time_range.max
  AND risk_level IN ('High', 'Critical')
ORDER BY event_date DESC, risk_level DESC
LIMIT 50
```

### ds_events_by_user
**Purpose:** Top users by event volume  
**Source:** `fact_audit_logs`  
**Key Query:**
```sql
SELECT 
  COALESCE(u.email, a.user_identity_email, 'Unknown') AS user_email,
  COUNT(*) AS total_events,
  SUM(CASE WHEN a.response_status_code >= 400 THEN 1 ELSE 0 END) AS failed_events,
  COUNT(DISTINCT a.service_name) AS services_accessed,
  MAX(a.event_date) AS last_activity
FROM ${catalog}.${gold_schema}.fact_audit_logs a
LEFT JOIN ${catalog}.${gold_schema}.dim_user u 
  ON a.user_identity_email = u.email
WHERE a.event_date BETWEEN :time_range.min AND :time_range.max
GROUP BY COALESCE(u.email, a.user_identity_email, 'Unknown')
ORDER BY total_events DESC
LIMIT 30
```

### ds_monitor_security_aggregate
**Purpose:** All security metrics from Lakehouse Monitoring  
**Source:** Aggregated directly from `fact_audit_logs`  
**Key Query:**
```sql
SELECT 
  event_date AS date,
  COUNT(*) AS total_events,
  SUM(CASE WHEN response_status_code < 400 THEN 1 ELSE 0 END) AS success_count,
  SUM(CASE WHEN response_status_code >= 400 THEN 1 ELSE 0 END) AS failed_count,
  ROUND(
    SUM(CASE WHEN response_status_code < 400 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
  2) AS success_rate,
  COUNT(DISTINCT user_identity_email) AS unique_users,
  SUM(CASE WHEN risk_level IN ('High', 'Critical') THEN 1 ELSE 0 END) AS high_risk_events
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY event_date
ORDER BY event_date DESC
```

---

## 📑 Data Sources

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `fact_audit_logs` | event_date, user_identity_email, service_name, action_name, response_status_code | Audit events |
| `fact_audit_logs_profile_metrics` | window_start_time, column_name, aggregate_metrics | Monitor metrics |
| `fact_audit_logs_drift_metrics` | drift_type, drift_metrics | Week-over-week changes |
| `dim_user` | user_id, email | User resolution |
| `dim_workspace` | workspace_id, workspace_name | Workspace context |

---

## 🔍 Common Query Patterns

### Failed Event Detection
```sql
WHERE response_status_code >= 400
```

### Risk Level Filtering
```sql
WHERE risk_level IN ('High', 'Critical')
```

### Action Category Classification
```sql
CASE 
  WHEN action_name LIKE '%delete%' THEN 'Deletion'
  WHEN action_name LIKE '%permission%' THEN 'Permission Change'
  WHEN action_name LIKE '%secret%' THEN 'Secret Access'
  WHEN action_name LIKE '%token%' THEN 'Token Management'
  ELSE 'Other'
END AS event_category
```

### Success Rate Calculation
```sql
ROUND(
  SUM(CASE WHEN response_status_code < 400 THEN 1 ELSE 0 END) * 100.0 / 
  COUNT(*),
1) AS success_rate
```

### User Activity Pattern
```sql
COUNT(DISTINCT service_name) AS services_accessed,
MAX(event_date) AS last_activity,
MIN(event_date) AS first_activity
```

---

## 🛡️ Security Event Categories

### High-Risk Actions
- `deleteClusters` - Cluster deletion
- `updatePermissions` - Permission changes
- `getSecret` - Secret access
- `createToken` - Token creation
- `deleteWorkspace` - Workspace deletion

### Compliance-Relevant Actions
- `createNotebook` - Code creation
- `runCommand` - Command execution
- `createJob` - Job creation
- `exportNotebook` - Data exfiltration risk

### Authentication Actions
- `login` - User login
- `logout` - User logout
- `generateToken` - Token generation
- `revokeToken` - Token revocation

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-06 | 1.0 | Initial documentation |

