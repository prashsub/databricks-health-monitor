# Security Auditor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Security Auditor Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks security, audit, and compliance analytics. Enables security teams, compliance officers, and administrators to query access patterns, audit trails, and security events without SQL.

**Powered by:**
- 2 Metric Views (security_events, governance_analytics)
- 10 Table-Valued Functions (user activity, sensitive access, audit queries)
- 4 ML Prediction Tables (threat detection, risk scoring, access classification)
- 2 Lakehouse Monitoring Tables (security drift and profile metrics)
- 3 Dimension Tables (workspace, user, date)
- 6 Fact Tables (audit logs, lineage, network traffic, clean rooms)

---

## ████ SECTION C: SAMPLE QUESTIONS ████

### Access Monitoring
1. "Who accessed this table?"
2. "Show me user activity for john@company.com"
3. "Which tables are most frequently accessed?"
4. "Who accessed sensitive data this week?"

### Audit Analysis
5. "Show me failed access attempts"
6. "What permission changes happened today?"
7. "Show me off-hours activity"
8. "Which service accounts are most active?"

### Security Patterns
9. "Show me bursty user activity"
10. "What sensitive actions occurred?"
11. "Show me security events timeline"
12. "Which users have the most failed actions?"

### ML-Powered Insights 🤖
13. "Are there any security anomalies?"
14. "What's the risk score for this user?"
15. "Show me suspicious activity patterns"

---

## ████ SECTION D: DATA ASSETS ████

### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `security_events` | Audit event metrics | total_events, failed_events, success_rate, unique_users, high_risk_events |
| `governance_analytics` | Data lineage metrics | read_events, write_events, active_table_count, unique_data_consumers |

### Table-Valued Functions (10 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_user_activity_summary` | User activity with risk scoring | "user activity" |
| `get_sensitive_table_access` | Sensitive data access | "sensitive data access" |
| `get_failed_actions` | Failed operations | "failed actions" |
| `get_permission_changes` | Permission modifications | "permission changes" |
| `get_off_hours_activity` | Off-hours access | "off-hours activity" |
| `get_security_events_timeline` | Chronological timeline | "security timeline" |
| `get_ip_address_analysis` | IP address patterns | "IP analysis" |
| `get_table_access_audit` | Table access trail | "table access" |
| `get_user_activity_patterns` | Temporal patterns | "activity patterns" |
| `get_service_account_audit` | Service account activity | "service accounts" |

### ML Prediction Tables 🤖 (4 Models)

| Table Name | Purpose | Model | Key Columns |
|---|---|---|---|
| `access_anomaly_predictions` | Unusual access pattern detection | Security Threat Detector | `threat_score`, `is_threat`, `threat_indicators`, `user_identity` |
| `user_risk_scores` | User risk assessment (0-100) | Compliance Risk Classifier | `risk_score`, `risk_level`, `risk_category`, `risk_factors` |
| `access_classifications` | Normal vs suspicious access classification | Access Pattern Analyzer | `pattern_class`, `probability`, `pattern_description` |
| `off_hours_baseline_predictions` | Expected off-hours activity baseline | Off-Hours Baseline Predictor | `expected_activity_level`, `baseline_deviation`, `alert_threshold` |

**Training Source:** `src/ml/security/` | **Inference:** `src/ml/inference/batch_inference_all_models.py`

### Lakehouse Monitoring Tables 📊

| Table Name | Purpose |
|------------|---------|
| `fact_audit_logs_profile_metrics` | Custom security metrics (sensitive_access_rate, failure_rate, off_hours_rate) |
| `fact_audit_logs_drift_metrics` | Security drift (event_volume_drift, sensitive_action_drift) |

#### ⚠️ CRITICAL: Custom Metrics Query Patterns

**Always include these filters when querying Lakehouse Monitoring tables:**

```sql
-- ✅ CORRECT: Get security metrics
SELECT 
  window.start AS window_start,
  total_events,
  sensitive_access_rate,
  failure_rate,
  off_hours_rate
FROM ${catalog}.${gold_schema}.fact_audit_logs_profile_metrics
WHERE column_name = ':table'     -- REQUIRED: Table-level custom metrics
  AND log_type = 'INPUT'         -- REQUIRED: Input data statistics
  AND slice_key IS NULL          -- For overall metrics
ORDER BY window.start DESC;

-- ✅ CORRECT: Get events by user (sliced)
SELECT 
  slice_value AS user_identity,
  SUM(total_events) AS event_count
FROM ${catalog}.${gold_schema}.fact_audit_logs_profile_metrics
WHERE column_name = ':table'
  AND log_type = 'INPUT'
  AND slice_key = 'user_identity_email'
GROUP BY slice_value
ORDER BY event_count DESC;

-- ✅ CORRECT: Get security drift
SELECT 
  window.start AS window_start,
  event_volume_drift,
  sensitive_action_drift
FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
ORDER BY window.start DESC;
```

#### Available Slicing Dimensions (Security Monitor)

| Slice Key | Use Case |
|-----------|----------|
| `workspace_id` | Events by workspace |
| `service_name` | Events by service |
| `audit_level` | By audit level |
| `action_name` | By action type |
| `user_identity_email` | Events by user |

### Dimension Tables (3 Tables)

**Sources:** `gold_layer_design/yaml/shared/`

| Table Name | Purpose | Key Columns | YAML Source |
|---|---|---|---|
| `dim_workspace` | Workspace reference | `workspace_id`, `workspace_name`, `region`, `cloud_provider` | shared/dim_workspace.yaml |
| `dim_user` | User information for access analysis | `user_id`, `user_name`, `email`, `department_tag`, `is_service_principal` | shared/dim_user.yaml |
| `dim_date` | Date dimension for time analysis | `date_key`, `day_of_week`, `month`, `quarter`, `year`, `is_weekend`, `is_business_hours` | shared/dim_date.yaml |

### Fact Tables (from gold_layer_design/yaml/security/, governance/)

| Table Name | Purpose | Grain | YAML Source |
|------------|---------|-------|-------------|
| `fact_audit_logs` | Audit event log | Per event | security/fact_audit_logs.yaml |
| `fact_table_lineage` | Data lineage | Per access event | governance/fact_table_lineage.yaml |
| `fact_assistant_events` | AI assistant interactions | Per assistant call | security/fact_assistant_events.yaml |
| `fact_clean_room_events` | Clean room operations | Per operation | security/fact_clean_room_events.yaml |
| `fact_inbound_network` | Inbound network traffic | Per connection | security/fact_inbound_network.yaml |
| `fact_outbound_network` | Outbound network traffic | Per connection | security/fact_outbound_network.yaml |

---

## ████ SECTION E: ASSET SELECTION FRAMEWORK ████

### Semantic Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASSET SELECTION DECISION TREE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER QUERY PATTERN                → USE THIS ASSET             │
│  ─────────────────────────────────────────────────────────────  │
│  "Total audit events today"        → Metric View (security_events)│
│  "Failed events count"             → Metric View (security_events)│
│  ─────────────────────────────────────────────────────────────  │
│  "Is auth failure increasing?"     → Custom Metrics (_drift_metrics)│
│  "Security event trend"            → Custom Metrics (_profile_metrics)│
│  ─────────────────────────────────────────────────────────────  │
│  "Who accessed sensitive data?"    → TVF (get_sensitive_table_access)│
│  "Failed actions today"            → TVF (get_failed_actions)    │
│  "User activity for X"             → TVF (get_user_activity_summary)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Total events count** | Metric View | "Audit events today" → `security_events` |
| **Auth failure trend** | Custom Metrics | "Is failure increasing?" → `_drift_metrics` |
| **User activity list** | TVF | "Activity for user X" → `get_user_activity_summary` |
| **Anomaly detection** | ML Tables | "Security anomalies" → `access_anomaly_predictions` |
| **Risk assessment** | TVF/ML | "User risk scores" → `get_user_risk_scores` |

### Priority Order

1. **If user asks for a LIST** → TVF
2. **If user asks about TREND** → Custom Metrics
3. **If user asks for CURRENT VALUE** → Metric View
4. **If user asks for ANOMALY/RISK** → ML Tables

---

## ████ SECTION F: GENERAL INSTRUCTIONS (≤20 Lines) ████

```
You are a Databricks security and compliance analyst. Follow these rules:

1. **Asset Selection:** Use Metric View for current state, TVFs for lists, Custom Metrics for trends
2. **Primary Source:** Use security_events metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for user-specific or "who accessed" queries
4. **Trends:** For "is failure rate increasing?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 24 hours
6. **User Types:** HUMAN_USER, SERVICE_PRINCIPAL, SYSTEM
7. **Risk Levels:** LOW (0-25), MEDIUM (26-50), HIGH (51-75), CRITICAL (76-100)
8. **Sorting:** Sort by risk_score DESC for security queries
9. **Limits:** Top 20 for activity lists
10. **Synonyms:** user=identity=principal, access=event=action
11. **ML Anomaly:** For "anomalies" → query access_anomaly_predictions
12. **Risk Score:** For "risk score" → query user_risk_scores
13. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
14. **Context:** Explain READ vs WRITE vs DDL actions
15. **Compliance:** Never expose PII in responses
16. **Performance:** Never scan Bronze/Silver tables
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_user_activity_summary` | `(user_email STRING, start_date STRING, end_date STRING)` | User activity | "activity for user X" |
| `get_sensitive_table_access` | `(start_date STRING, end_date STRING)` | PII table access | "sensitive data access" |
| `get_failed_actions` | `(start_date STRING, end_date STRING)` | Failed ops | "failed actions" |
| `get_permission_changes` | `(start_date STRING, end_date STRING)` | Perm changes | "permission changes" |
| `get_off_hours_activity` | `(start_date STRING, end_date STRING)` | Off-hours | "off-hours activity" |

### TVF Details

#### get_user_activity_summary
- **Signature:** `get_user_activity_summary(user_email STRING, start_date STRING, end_date STRING)`
- **Returns:** user_identity, total_events, read_events, write_events, failed_events, risk_score
- **Use When:** User asks for "activity for john@company.com"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_user_activity_summary('john@company.com', '2024-12-01', '2024-12-31')`

#### get_sensitive_table_access
- **Signature:** `get_sensitive_table_access(start_date STRING, end_date STRING)`
- **Returns:** table_name, user_identity, access_count, access_type, last_access
- **Use When:** User asks for "who accessed sensitive data"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_sensitive_table_access('2024-12-01', '2024-12-31')`

#### get_off_hours_activity
- **Signature:** `get_off_hours_activity(start_date STRING, end_date STRING)`
- **Returns:** user_identity, event_date, event_hour, event_count, action_types
- **Use When:** User asks for "off-hours access" or "after-hours activity"
- **Example:** `SELECT * FROM ${catalog}.${gold_schema}.get_off_hours_activity('2024-12-01', '2024-12-31')`

---

## ████ SECTION G: ML MODEL INTEGRATION (4 Models) ████

### Security ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `security_threat_detector` | `access_anomaly_predictions` | `threat_score`, `is_threat` | "Detect threats" |
| `access_pattern_analyzer` | `access_classifications` | `pattern_class`, `probability` | "Classify access" |
| `compliance_risk_classifier` | `user_risk_scores` | `risk_level` (1-5) | "User risk score" |
| `permission_recommender` | — | `recommended_action` | "Permission changes" |

### ML Model Usage Patterns

#### security_threat_detector (Threat Detection)
- **Question Triggers:** "threat", "anomaly", "suspicious", "unusual access", "security risk"
- **Query Pattern:**
```sql
SELECT user_identity, event_date, threat_score, is_threat, threat_indicators
FROM ${catalog}.${gold_schema}.access_anomaly_predictions
WHERE prediction_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND is_threat = TRUE
ORDER BY threat_score ASC;
```
- **Interpretation:** `is_threat = TRUE` or `threat_score < -0.5` = Security concern

#### compliance_risk_classifier (User Risk Scores)
- **Question Triggers:** "risk score", "risky users", "compliance risk", "high risk"
- **Query Pattern:**
```sql
SELECT user_identity, risk_level, risk_category, risk_factors
FROM ${catalog}.${gold_schema}.user_risk_scores
WHERE risk_level >= 4
ORDER BY risk_level DESC, last_activity DESC;
```
- **Interpretation:** `risk_level >= 4` = High risk, requires attention

#### access_pattern_analyzer (Access Classification)
- **Question Triggers:** "access pattern", "behavior", "classify user", "normal access"
- **Query Pattern:**
```sql
SELECT user_identity, pattern_class, probability, pattern_description
FROM ${catalog}.${gold_schema}.access_classifications
WHERE pattern_class != 'NORMAL'
ORDER BY probability DESC;
```

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Who are the risky users?"              → ML: user_risk_scores
"Any security threats?"                 → ML: access_anomaly_predictions
"Classify access patterns"              → ML: access_classifications
"Permission recommendations"            → ML: permission_recommender
────────────────────────────────────────────────────
"How many security events?"             → Metric View: security_events
"Is event volume increasing?"           → Custom Metrics: _drift_metrics
"Show failed access attempts"           → TVF: get_failed_access_attempts
```

---

## ████ SECTION H: BENCHMARK QUESTIONS WITH SQL ████

### Question 1: "Who are the most active users this week?"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  MEASURE(total_events) as event_count
FROM ${catalog}.${gold_schema}.security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_identity
ORDER BY event_count DESC
LIMIT 10;
```
**Expected Result:** Top 10 users by event count

---

### Question 2: "Show me failed access attempts today"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_failed_actions(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_timestamp DESC;
```
**Expected Result:** Table of failed actions

---

### Question 3: "Who accessed sensitive data this week?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_sensitive_table_access(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY access_count DESC;
```
**Expected Result:** Users who accessed PII/sensitive tables

---

### Question 4: "Show me off-hours activity"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_off_hours_activity(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Activity outside business hours

---

### Question 5: "What permission changes happened today?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_permission_changes(
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_timestamp DESC;
```
**Expected Result:** Permission modification events

---

### Question 6: "Are there any security anomalies?"
**Expected SQL:**
```sql
SELECT 
  user_identity,
  anomaly_score,
  is_anomaly,
  reason
FROM ${catalog}.${gold_schema}.access_anomaly_predictions
WHERE prediction_date = CURRENT_DATE()
  AND is_anomaly = TRUE
ORDER BY anomaly_score DESC;
```
**Expected Result:** Detected anomalous access patterns

---

### Question 7: "What's the risk score for users?"
**Expected SQL:**
```sql
SELECT 
  user_id,
  risk_score,
  risk_factors,
  CASE 
    WHEN risk_score >= 76 THEN 'CRITICAL'
    WHEN risk_score >= 51 THEN 'HIGH'
    WHEN risk_score >= 26 THEN 'MEDIUM'
    ELSE 'LOW'
  END as risk_level
FROM ${catalog}.${gold_schema}.user_risk_scores
ORDER BY risk_score DESC
LIMIT 20;
```
**Expected Result:** Users with risk classifications

---

### Question 8: "Which service accounts are most active?"
**Expected SQL:**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_service_account_audit(
  DATE_FORMAT(CURRENT_DATE() - INTERVAL 7 DAYS, 'yyyy-MM-dd'),
  DATE_FORMAT(CURRENT_DATE(), 'yyyy-MM-dd')
)
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Service principal activity summary

---

### Question 9: "Show me security event trends"
**Expected SQL:**
```sql
SELECT 
  event_date,
  MEASURE(total_events) as total_events,
  MEASURE(failed_events) as failed_events,
  MEASURE(high_risk_events) as high_risk_events
FROM ${catalog}.${gold_schema}.security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY event_date
ORDER BY event_date;
```
**Expected Result:** Daily security event trends

---

### Question 10: "Is there unusual activity volume?"
**Expected SQL:**
```sql
SELECT 
  window_start,
  event_volume_drift,
  sensitive_action_drift
FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
WHERE column_name = ':table'
  AND (ABS(event_volume_drift) > 50 OR ABS(sensitive_action_drift) > 20)
ORDER BY window_start DESC
LIMIT 10;
```
**Expected Result:** Significant security drift alerts

---

## ✅ DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. General Instructions** | 18 lines (≤20) | ✅ |
| **F. TVFs** | 10 functions with signatures | ✅ |
| **G. Benchmark Questions** | 10 with SQL answers | ✅ |

---

## Agent Domain Tag

**Agent Domain:** 🔒 **Security**

---

## References

### 📊 Semantic Layer Framework (Essential Reading)
- [**Metrics Inventory**](../../docs/reference/metrics-inventory.md) - **START HERE**: Complete inventory of 277 measurements across TVFs, Metric Views, and Custom Metrics
- [**Semantic Layer Rationalization**](../../docs/reference/semantic-layer-rationalization.md) - Design rationale: why overlaps are intentional and complementary
- [**Genie Asset Selection Guide**](../../docs/reference/genie-asset-selection-guide.md) - Quick decision tree for choosing correct asset type

### 📈 Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions for Security Monitor
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns and required filters
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md) - 13 security-specific custom metrics

### 📁 Asset Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 10 Security TVFs
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 2 Security Metric Views
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 4 Security ML Models

### 🚀 Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting

