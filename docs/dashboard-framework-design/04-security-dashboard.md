# Security Dashboard Specification

## Overview

**Purpose:** Security analytics, threat detection, access pattern analysis, and compliance monitoring for the Databricks platform.

**Existing Dashboards to Consolidate:**
- `security_audit.lvdash.json` (25 datasets)
- Security-related elements from `governance_hub.lvdash.json`

**Target Dataset Count:** ~60 datasets (within 100 limit after enrichment)

---

## Page Structure

### Page 1: Security Overview (Overview Page for Unified)
**Purpose:** Executive summary of security health

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Total Events (24h) | KPI | ds_kpi_events | Monitor: total_events |
| Unique Users | KPI | ds_kpi_users | Monitor: distinct_users |
| High Risk Events | KPI | ds_kpi_high_risk | ML: security_threat_detector |
| Failed Auth Count | KPI | ds_kpi_failed_auth | Monitor: failed_auth_count |
| Event Trend | Line | ds_event_trend | - |
| Threat Alerts | Table | ds_ml_threats | ML: security_threat_detector |

### Page 2: Event Analysis
**Purpose:** Deep dive into security events

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Events by Action | Pie | ds_events_by_action | - |
| Events by Service | Bar | ds_events_by_service | - |
| Event Timeline | Line | ds_event_timeline | - |
| Top Users by Activity | Table | ds_top_users | - |
| Admin Actions | Table | ds_admin_actions | Monitor: admin_actions |
| Event Details | Table | ds_event_detail | - |

### Page 3: Access Control
**Purpose:** Authentication and access monitoring

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Failed Auth Trend | Line | ds_failed_auth_trend | Monitor: failed_auth_count |
| Failed Auth Rate | Gauge | ds_failed_auth_rate | Monitor: failed_auth_rate |
| Access Patterns | Table | ds_ml_access_patterns | ML: access_pattern_analyzer |
| Anomalous Access | Table | ds_anomalous_access | ML: access_pattern_analyzer |
| User Sessions | Table | ds_user_sessions | - |
| Permission Changes | Table | ds_perm_changes | - |

### Page 4: Threat Detection
**Purpose:** ML-based threat identification

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Threat Score Distribution | Histogram | ds_threat_dist | ML: security_threat_detector |
| Active Threats | Table | ds_ml_active_threats | ML: security_threat_detector |
| Threat Trend | Line | ds_threat_trend | - |
| Threat by Category | Pie | ds_threat_category | ML: security_threat_detector |
| Compromised Accounts | Table | ds_compromised | ML: security_threat_detector |
| Insider Threats | Table | ds_insider_threats | ML: access_pattern_analyzer |

### Page 5: Compliance & Audit
**Purpose:** Compliance monitoring and audit trails

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Compliance Risk Score | Gauge | ds_compliance_risk | ML: compliance_risk_classifier |
| High Risk Resources | Table | ds_ml_compliance_risk | ML: compliance_risk_classifier |
| Sensitive Actions | Table | ds_sensitive_actions | Monitor: sensitive_actions |
| Data Access Events | Table | ds_data_access | Monitor: data_access_events |
| Audit Trail | Table | ds_audit_trail | - |
| Permission Recommendations | Table | ds_ml_perm_recs | ML: permission_recommender |

### Page 6: Security Drift
**Purpose:** Monitor-based security drift detection

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Auth Failure Drift | KPI | ds_auth_drift | Monitor: auth_failure_drift |
| Event Volume Drift | KPI | ds_event_drift | - |
| Security Profile | Table | ds_security_profile | Monitor: profile metrics |
| Drift Trend | Line | ds_security_drift_trend | Monitor: drift metrics |
| Monitor Alerts | Table | ds_security_alerts | - |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_events
SELECT COUNT(*) AS total_events
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAY

-- ds_kpi_users
SELECT COUNT(DISTINCT user_identity_email) AS unique_users
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAY

-- ds_failed_auth_trend
SELECT 
    event_date,
    SUM(CASE WHEN action_name LIKE '%AuthFail%' OR action_name LIKE '%LoginFail%' THEN 1 ELSE 0 END) AS failed_auth
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY event_date
ORDER BY event_date
```

### ML Datasets

```sql
-- ds_ml_threats
SELECT 
    detection_date,
    user_id,
    threat_type,
    threat_score,
    is_threat,
    risk_factors,
    recommended_actions
FROM ${catalog}.${gold_schema}.security_threat_predictions
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND threat_score > 0.7
ORDER BY threat_score DESC
LIMIT 20

-- ds_ml_access_patterns
SELECT 
    user_id,
    anomaly_probability,
    access_pattern_type,
    baseline_pattern,
    deviation_score,
    detection_date
FROM ${catalog}.${gold_schema}.access_pattern_predictions
WHERE detection_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND anomaly_probability > 0.7
ORDER BY anomaly_probability DESC
LIMIT 20

-- ds_ml_compliance_risk
SELECT 
    resource_id,
    resource_type,
    risk_category,
    risk_score,
    risk_factors,
    recommended_remediation,
    classification_date
FROM ${catalog}.${gold_schema}.compliance_risk_predictions
WHERE classification_date = CURRENT_DATE()
  AND risk_category IN ('HIGH', 'CRITICAL')
ORDER BY risk_score DESC
LIMIT 20

-- ds_ml_perm_recs
SELECT 
    user_id,
    current_permissions,
    recommended_permissions,
    permission_change_type,
    justification,
    risk_reduction_pct,
    recommendation_date
FROM ${catalog}.${gold_schema}.permission_recommendations
WHERE recommendation_date = CURRENT_DATE()
ORDER BY risk_reduction_pct DESC
LIMIT 20
```

### Monitor Datasets

```sql
-- ds_security_profile
SELECT 
    window.start AS period_start,
    total_events,
    distinct_users,
    failed_auth_count,
    failed_auth_rate * 100 AS failed_auth_rate_pct,
    sensitive_actions,
    admin_actions,
    data_access_events
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_security_drift
SELECT 
    window.start AS period_start,
    auth_failure_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 30
```

---

## Global Filter Integration

All datasets must include:
```sql
WHERE 
  (CASE 
    WHEN :time_window = 'Last 7 Days' THEN event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
    WHEN :time_window = 'Last 30 Days' THEN event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
    -- ... other time windows
  END)
  AND (:workspace_filter = 'All' OR CAST(workspace_id AS STRING) = :workspace_filter)
```

---

## ML Model Integration Summary (4 Models)

> **Source of Truth:** [07-model-catalog.md](../ml-framework-design/07-model-catalog.md)

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| security_threat_detector | Threat detection, risk alerts | security_threat_predictions |
| access_pattern_analyzer | Anomalous access detection | access_pattern_predictions |
| compliance_risk_classifier | Compliance risk scoring | compliance_risk_predictions |
| permission_recommender | Permission optimization | permission_recommendations |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_audit_logs_profile_metrics | total_events, distinct_users, failed_auth_count, failed_auth_rate, sensitive_actions, admin_actions, data_access_events |
| fact_audit_logs_drift_metrics | auth_failure_drift |

