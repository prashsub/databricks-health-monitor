# Security Dashboard Specification

## Overview

**Purpose:** Security event monitoring, audit analysis, threat detection, and compliance tracking.

**Existing Dashboards to Consolidate:**
- `security_audit.lvdash.json` (25 datasets)
- `governance_hub.lvdash.json` (16 datasets) - security aspects

**Target Dataset Count:** ~60 datasets (within 100 limit after enrichment)

---

## Page Structure

### Page 1: Security Overview (Overview Page for Unified)
**Purpose:** Executive summary of security posture

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Total Events (24h) | KPI | ds_kpi_events | Monitor: total_events |
| High Risk Events | KPI | ds_kpi_high_risk | Monitor: sensitive_action_count |
| Denied Access | KPI | ds_kpi_denied | Monitor: unauthorized_count |
| Unique Users | KPI | ds_kpi_users | Monitor: distinct_users |
| Event Trend | Line | ds_event_trend | - |
| Recent Threats | Table | ds_ml_threats | ML: threat_detector |

### Page 2: Event Analysis
**Purpose:** Detailed event breakdown

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Events by Service | Pie | ds_events_service | - |
| Events by Action | Bar | ds_events_action | - |
| Human vs Service Principal | Pie | ds_user_type | Monitor: human_user_events, service_principal_events |
| Event Volume Trend | Line | ds_volume_trend | Monitor: total_events |
| Top Users by Activity | Table | ds_top_users | - |
| Hourly Activity Pattern | Heatmap | ds_hourly_pattern | - |

### Page 3: Threat Detection
**Purpose:** ML-based threat identification

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Active Threats | KPI | ds_active_threats | ML: security_threat_detector |
| Threat Trend | Line | ds_threat_trend | - |
| Threats by Type | Pie | ds_threat_types | ML: threat_detector |
| Data Exfiltration Alerts | Table | ds_ml_exfiltration | ML: exfiltration_detector |
| Privilege Escalation | Table | ds_ml_privilege | ML: privilege_escalation |
| User Behavior Anomalies | Table | ds_ml_behavior | ML: user_behavior_baseline |

### Page 4: Access Control
**Purpose:** Access patterns and denied requests

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Denied Requests (24h) | KPI | ds_denied_24h | Monitor: failed_action_count |
| Denied by Service | Bar | ds_denied_service | - |
| Denied by User | Table | ds_denied_user | - |
| Permission Changes | Table | ds_permission_changes | Monitor: permission_change_count |
| Admin Actions | Table | ds_admin_actions | - |
| Access Pattern Anomalies | Table | ds_ml_access | ML: access_pattern_analyzer |

### Page 5: Compliance & Audit
**Purpose:** Compliance monitoring and audit trail

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Sensitive Actions | KPI | ds_sensitive | Monitor: sensitive_action_rate |
| Off-Hours Activity | KPI | ds_off_hours | Monitor: off_hours_events |
| Compliance Risk Score | Gauge | ds_ml_compliance | ML: compliance_risk_classifier |
| Sensitive Actions Trend | Line | ds_sensitive_trend | - |
| Audit Trail | Table | ds_audit_trail | - |
| Permission Recommendations | Table | ds_ml_permissions | ML: permission_recommender |

### Page 6: Security Drift
**Purpose:** Monitor-based security drift

**Widgets:**
| Widget | Type | Dataset | ML/Monitor |
|--------|------|---------|------------|
| Event Volume Drift | KPI | ds_volume_drift | Monitor: event_volume_drift_pct |
| Sensitive Action Drift | KPI | ds_sensitive_drift | Monitor: sensitive_action_drift |
| Security Profile Metrics | Table | ds_security_profile | Monitor: profile metrics |
| Drift Trend | Line | ds_security_drift_trend | Monitor: drift metrics |
| Monitor Alerts | Table | ds_monitor_alerts | - |

---

## Datasets Specification

### Core Datasets

```sql
-- ds_kpi_events
SELECT COUNT(*) AS total_events
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 1 DAYS

-- ds_events_service
SELECT 
    service_name,
    COUNT(*) AS event_count
FROM ${catalog}.${gold_schema}.fact_audit_logs
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY service_name
ORDER BY event_count DESC
LIMIT 10
```

### ML Datasets

```sql
-- ds_ml_threats
SELECT 
    detection_time,
    threat_type,
    risk_score,
    user_identity_email,
    service_name,
    action_name,
    recommended_action
FROM ${catalog}.${gold_schema}.security_threats
WHERE detection_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND risk_score > 0.7
ORDER BY risk_score DESC
LIMIT 20

-- ds_ml_exfiltration
SELECT 
    detection_time,
    user_identity_email,
    data_volume_bytes,
    destination,
    risk_score,
    alert_status
FROM ${catalog}.${gold_schema}.exfiltration_alerts
WHERE detection_time >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY risk_score DESC
LIMIT 20

-- ds_ml_privilege
SELECT 
    detection_time,
    user_identity_email,
    escalation_type,
    from_role,
    to_role,
    risk_score
FROM ${catalog}.${gold_schema}.privilege_escalation_alerts
WHERE detection_time >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY risk_score DESC
LIMIT 20

-- ds_ml_behavior
SELECT 
    user_identity_email,
    behavior_score,
    anomaly_type,
    normal_pattern,
    observed_pattern,
    detection_time
FROM ${catalog}.${gold_schema}.user_behavior_scores
WHERE detection_time >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND behavior_score < 0.5
ORDER BY behavior_score ASC
LIMIT 20

-- ds_ml_compliance
SELECT 
    risk_category,
    risk_score,
    affected_resources,
    recommended_action
FROM ${catalog}.${gold_schema}.compliance_risk_scores
WHERE assessment_date = CURRENT_DATE()
ORDER BY risk_score DESC
```

### Monitor Datasets

```sql
-- ds_security_profile
SELECT 
    window.start AS period_start,
    total_events,
    distinct_users,
    sensitive_action_count,
    sensitive_action_rate * 100 AS sensitive_rate_pct,
    failed_action_count,
    permission_change_count,
    human_user_events,
    service_principal_events,
    off_hours_events
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
ORDER BY window.start DESC
LIMIT 30

-- ds_security_drift
SELECT 
    window.start AS period_start,
    event_volume_drift_pct * 100 AS volume_drift_pct,
    sensitive_action_drift
FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_drift_metrics
WHERE column_name = ':table'
  AND drift_type = 'CONSECUTIVE'
ORDER BY window.start DESC
LIMIT 30
```

---

## ML Model Integration Summary

| Model | Dashboard Use | Output Table |
|-------|---------------|--------------|
| threat_detector | Threat alerts table | threat_detection_results |
| security_threat_detector | Combined threat view | security_threats |
| privilege_escalation | Escalation alerts | privilege_escalation_alerts |
| exfiltration_detector | Data exfiltration alerts | exfiltration_alerts |
| permission_recommender | Permission optimization | permission_recommendations |
| compliance_risk_classifier | Risk classification | compliance_risk_scores |
| access_pattern_analyzer | Access anomalies | access_pattern_anomalies |
| user_behavior_baseline | Behavior anomalies | user_behavior_scores |

---

## Monitor Metrics Used

| Monitor | Metrics Used |
|---------|--------------|
| fact_audit_logs_profile_metrics | total_events, distinct_users, sensitive_action_count, sensitive_action_rate, failed_action_count, permission_change_count, human_user_events, service_principal_events, off_hours_events, unauthorized_count |
| fact_audit_logs_drift_metrics | event_volume_drift_pct, sensitive_action_drift |

