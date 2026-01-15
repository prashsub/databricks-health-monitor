# Security Auditor Genie Space Setup

## ████ SECTION A: SPACE NAME ████

**Space Name:** `Health Monitor Security Auditor Space`

---

## ████ SECTION B: SPACE DESCRIPTION ████

**Description:** Natural language interface for Databricks security, audit, and compliance analytics. Enables security teams, compliance officers, and administrators to query access patterns, audit trails, and security events without SQL.

**Powered by:**
- 2 Metric Views (mv_security_events, mv_governance_analytics)
- 10 Table-Valued Functions (parameterized queries)
- 4 ML Prediction Tables (predictions and recommendations)
- 2 Lakehouse Monitoring Tables (drift and profile metrics)
- 2 Dimension Tables (reference data)
- 4 Fact Tables (transactional data)

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
9. "Show me unusual access patterns"
10. "What sensitive actions occurred?"
11. "Show me security events timeline"
12. "Which users have the most failed actions?"

### ML-Powered Insights
13. "Are there any security anomalies?"
14. "What's the risk score for this user?"
15. "Show me suspicious activity patterns"

---

## ████ SECTION D: DATA ASSETS ████



### Metric Views (PRIMARY - Use First)

| Metric View Name | Purpose | Key Measures |
|------------------|---------|--------------|
| `mv_governance_analytics` | Data governance analytics | table_count, lineage_coverage, classification_coverage |
| `mv_security_events` | Security event monitoring | total_events, failed_events, risk_score |

### Table-Valued Functions (10 TVFs)

| Function Name | Purpose | When to Use |
|---------------|---------|-------------|
| `get_failed_actions` | Failed actions | "failed actions" |
| `get_ip_address_analysis` | IP address analysis | "IP analysis" |
| `get_off_hours_activity` | Off-hours activity | "off hours" |
| `get_permission_changes` | Permission changes | "permission changes" |
| `get_security_events_timeline` | Security events timeline | "security events" |
| `get_sensitive_table_access` | Sensitive table access | "sensitive access" |
| `get_service_account_audit` | Service account audit | "service accounts" |
| `get_table_access_audit` | Table access audit | "access audit" |
| `get_user_activity_patterns` | User activity patterns | "activity patterns" |
| `get_user_activity_summary` | User activity summary | "user activity" |

### ML Prediction Tables (4 Models)

| Table Name | Purpose | Model |
|---|---|---|
| `exfiltration_predictions` | Data exfiltration risk | Exfiltration Detector |
| `privilege_escalation_predictions` | Privilege escalation risk | Privilege Analyzer |
| `security_threat_predictions` | Security threats | Threat Detector |
| `user_behavior_predictions` | User behavior anomalies | Behavior Analyzer |

### Lakehouse Monitoring Tables

| Table Name | Purpose |
|------------|---------|
| `fact_audit_logs_drift_metrics` | Security event drift detection |
| `fact_audit_logs_profile_metrics` | Security event profile metrics |

### Dimension Tables (2 Tables)

| Table Name | Purpose | Key Columns |
|---|---|---|
| `dim_user` | User details | user_id, user_name, email |
| `dim_workspace` | Workspace details | workspace_id, workspace_name, region |

### Fact Tables (4 Tables)

| Table Name | Purpose | Grain |
|---|---|---|
| `fact_audit_logs` | Security audit logs | Per audit event |
| `fact_inbound_network` | Inbound network traffic | Per network event |
| `fact_outbound_network` | Outbound network traffic | Per network event |
| `fact_table_lineage` | Table lineage | Per lineage relationship |

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
│  "Total audit events today"        → Metric View (mv_security_events)│
│  "Failed events count"             → Metric View (mv_security_events)│
│  ─────────────────────────────────────────────────────────────  │
│  "Is auth failure increasing?"     → Custom Metrics (_drift_metrics)│
│  "Security event trend"            → Custom Metrics (_profile_metrics)│
│  ─────────────────────────────────────────────────────────────  │
│  "Who accessed sensitive data?"    → TVF (get_pii_access_events)│
│  "Failed actions today"            → TVF (get_failed_authentication_events)    │
│  "User activity for X"             → TVF (get_user_activity)│
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Asset Selection Rules

| Query Intent | Asset Type | Example |
|--------------|-----------|---------|
| **Total events count** | Metric View | "Audit events today" → `mv_security_events` |
| **Auth failure trend** | Custom Metrics | "Is failure increasing?" → `_drift_metrics` |
| **User activity list** | TVF | "Activity for user X" → `get_user_activity` |
| **Anomaly detection** | ML Tables | "Security anomalies" → `security_anomaly_predictions` |
| **Risk assessment** | TVF/ML | "User risk scores" → `user_risk_scores` |

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
2. **Primary Source:** Use mv_security_events metric view for dashboard KPIs
3. **TVFs for Lists:** Use TVFs for user-specific or "who accessed" queries, always wrap with TABLE()
4. **Trends:** For "is failure rate increasing?" check _drift_metrics tables
5. **Date Default:** If no date specified, default to last 7 days
6. **User Types:** HUMAN_USER, SERVICE_PRINCIPAL, SYSTEM
7. **Risk Levels:** LOW (0-25), MEDIUM (26-50), HIGH (51-75), CRITICAL (76-100)
8. **Sorting:** Sort by risk_score DESC for security queries
9. **Limits:** Top 20 for activity lists
10. **Synonyms:** user=identity=principal, access=event=action
11. **ML Anomaly:** For "anomalies" → query security_anomaly_predictions (prediction < -0.5 = threat)
12. **Risk Score:** For "risk score" → query user_risk_scores (prediction >= 4 = high risk)
13. **Custom Metrics:** Always include required filters (column_name=':table', log_type='INPUT')
14. **Context:** Explain READ vs WRITE vs DDL actions
15. **Compliance:** Never expose PII in responses
16. **Performance:** Never scan Bronze/Silver tables
17. **ML Schema:** All ML tables in ${catalog}.${feature_schema}
18. **TVF Calls:** Always use TABLE() wrapper for TVF calls
```

---

## ████ SECTION G: TABLE-VALUED FUNCTIONS ████

### TVF Quick Reference

| Function Name | Signature | Purpose | When to Use |
|---------------|-----------|---------|-------------|
| `get_user_activity` | `(start_date STRING, end_date STRING, top_n INT DEFAULT 50)` | User activity summary | "user activity" |
| `get_table_access_audit` | `(start_date STRING, end_date STRING)` | Table access audit | "table access" |
| `get_permission_change_events` | `(days_back INT)` | Permission changes | "permission changes" |
| `get_service_account_audit` | `(days_back INT)` | Service account activity | "service accounts" |
| `get_failed_authentication_events` | `(days_back INT)` | Failed operations | "failed actions" |
| `get_pii_access_events` | `(start_date STRING, end_date STRING)` | Sensitive data access | "sensitive data access" |
| `get_anomalous_access_events` | `(days_back INT)` | Unusual patterns | "unusual patterns" |
| `get_off_hours_activity` | `(days_back INT)` | Activity patterns | "activity patterns" |
| `get_data_exfiltration_events` | `(days_back INT)` | Data exports | "data exports" |
| `user_risk_scores` | `(days_back INT)` | User risk scores | "risk scores" |

### TVF Details

#### get_user_activity
- **Signature:** `get_user_activity(start_date STRING, end_date STRING, top_n INT DEFAULT 50)`
- **Returns:** user_identity, total_events, read_events, write_events, failed_events, risk_score
- **Use When:** User asks for "activity summary" or "top users by activity"
- **Example:** `SELECT * FROM get_user_activity('2024-12-01', '2024-12-31', 20))`

#### get_table_access_audit
- **Signature:** `get_table_access_audit(start_date STRING, end_date STRING)`
- **Returns:** table_name, user_identity, access_count, access_type, last_access
- **Use When:** User asks for "who accessed table" or "table access audit"
- **Example:** `SELECT * FROM get_table_access_audit('2024-12-01', '2024-12-31'))`

#### get_permission_change_events
- **Signature:** `get_permission_change_events(days_back INT)`
- **Returns:** change_date, user_identity, entity_type, entity_name, change_type, grantor
- **Use When:** User asks for "permission changes" or "access modifications"
- **Example:** `SELECT * FROM get_permission_change_events(7))`

#### get_service_account_audit
- **Signature:** `get_service_account_audit(days_back INT)`
- **Returns:** service_account_name, event_count, distinct_services, failed_actions, last_activity
- **Use When:** User asks for "service account activity" or "service principal usage"
- **Example:** `SELECT * FROM get_service_account_audit(30))`

#### get_failed_authentication_events
- **Signature:** `get_failed_authentication_events(days_back INT)`
- **Returns:** user_identity, failed_count, failed_actions, first_failure, last_failure
- **Use When:** User asks for "failed actions" or "authentication failures"
- **Example:** `SELECT * FROM get_failed_authentication_events(7))`

#### get_pii_access_events
- **Signature:** `get_pii_access_events(start_date STRING, end_date STRING)`
- **Returns:** table_name, user_identity, access_count, access_type, last_access
- **Use When:** User asks for "who accessed sensitive data" or "PII access"
- **Example:** `SELECT * FROM get_pii_access_events('2024-12-01', '2024-12-31'))`

#### get_anomalous_access_events
- **Signature:** `get_anomalous_access_events(days_back INT)`
- **Returns:** user_identity, pattern_type, deviation_score, event_count, description
- **Use When:** User asks for "unusual patterns" or "anomalous behavior"
- **Example:** `SELECT * FROM get_anomalous_access_events(7))`

#### get_off_hours_activity
- **Signature:** `get_off_hours_activity(days_back INT)`
- **Returns:** user_identity, hour_of_day, day_of_week, avg_events, pattern_type
- **Use When:** User asks for "activity patterns" or "temporal behavior"
- **Example:** `SELECT * FROM get_off_hours_activity(30))`

#### get_data_exfiltration_events
- **Signature:** `get_data_exfiltration_events(days_back INT)`
- **Returns:** user_identity, export_date, table_name, row_count, export_method
- **Use When:** User asks for "data exports" or "data downloads"
- **Example:** `SELECT * FROM get_data_exfiltration_events(7))`

#### user_risk_scores
- **Signature:** `user_risk_scores(days_back INT)`
- **Returns:** user_identity, risk_score, risk_level, risk_factors, evaluation_date
- **Use When:** User asks for "risk scores" or "high risk users"
- **Example:** `SELECT * FROM TABLE(${catalog}.${gold_schema}.user_risk_scores(7))`

---

## ████ SECTION H: ML MODEL INTEGRATION (4 Models) ████

### Security ML Models Quick Reference

| ML Model | Prediction Table | Key Columns | Use When |
|----------|-----------------|-------------|----------|
| `security_threat_detector` | `security_anomaly_predictions` | `prediction`, `user_identity` | "Detect threats" |
| `access_pattern_analyzer` | `access_classifications` | `prediction`, `pattern_class` | "Classify access" |
| `compliance_risk_classifier` | `user_risk_scores` | `prediction` (1-5) | "User risk score" |
| `off_hours_baseline_predictor` | `off_hours_baseline_predictions` | `prediction`, `baseline_deviation` | "Off-hours baseline" |

### ML Model Usage Patterns

#### security_threat_detector (Threat Detection)
- **Question Triggers:** "threat", "anomaly", "suspicious", "unusual access", "security risk"
- **Query Pattern:**
```sql
SELECT user_identity, event_date, prediction as threat_score
FROM ${catalog}.${feature_schema}.security_anomaly_predictions
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND prediction < -0.5
ORDER BY prediction ASC;
```
- **Interpretation:** `prediction < -0.5` = Security threat detected

#### compliance_risk_classifier (User Risk Scores)
- **Question Triggers:** "risk score", "risky users", "compliance risk", "high risk"
- **Query Pattern:**
```sql
SELECT user_identity, prediction as risk_level, evaluation_date
FROM ${catalog}.${feature_schema}.user_risk_scores
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND prediction >= 4
ORDER BY prediction DESC;
```
- **Interpretation:** `prediction >= 4` = High risk, requires attention

#### access_pattern_analyzer (Access Classification)
- **Question Triggers:** "access pattern", "behavior", "classify user", "normal access"
- **Query Pattern:**
```sql
SELECT user_identity, prediction as pattern_score, pattern_class
FROM ${catalog}.${feature_schema}.access_classifications
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND pattern_class != 'NORMAL'
ORDER BY prediction DESC;
```

#### off_hours_baseline_predictor (Off-Hours Activity)
- **Question Triggers:** "off-hours baseline", "expected activity", "after-hours deviation"
- **Query Pattern:**
```sql
SELECT user_identity, prediction as expected_activity, event_date
FROM ${catalog}.${feature_schema}.off_hours_baseline_predictions
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY event_date DESC;
```

### ML vs Other Methods Decision Tree

```
USER QUESTION                           → USE THIS
────────────────────────────────────────────────────
"Who are the risky users?"              → ML: user_risk_scores
"Any security threats?"                 → ML: security_anomaly_predictions
"Classify access patterns"              → ML: access_classifications
"Off-hours baseline"                    → ML: off_hours_baseline_predictions
────────────────────────────────────────────────────
"How many security events?"             → Metric View: mv_security_events
"Is event volume increasing?"           → Custom Metrics: _drift_metrics
"Show failed access attempts"           → TVF: get_failed_authentication_events
```

---

## ████ SECTION I: BENCHMARK QUESTIONS WITH SQL ████

> **TOTAL: 25 Questions (20 Normal + 5 Deep Research)**
> **Grounded in:** mv_security_events, mv_governance_analytics, TVFs, ML Tables

### Normal Benchmark Questions (Q1-Q20)

### Question 1: "What is our total event count this week?"
**Expected SQL:**
```sql
SELECT MEASURE(total_events) as event_count
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Total audit events for last 7 days

---

### Question 2: "What is the failure rate for security events?"
**Expected SQL:**
```sql
SELECT
  MEASURE(failed_events) / NULLIF(MEASURE(total_events), 0) * 100 as failure_rate_pct
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Percentage of failed authentication/authorization attempts

---

### Question 3: "Show me events by user"
**Expected SQL:**
```sql
SELECT
  user_email,
  MEASURE(total_events) as event_count,
  MEASURE(failed_events) as failed_count
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY user_email
ORDER BY event_count DESC
LIMIT 15;
```
**Expected Result:** User-level activity with failure counts

---

### Question 4: "What is the success rate?"
**Expected SQL:**
```sql
SELECT MEASURE(success_rate) as success_pct
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Overall success rate for audit events

---

### Question 5: "Show me user activity summary"
**Expected SQL:**
```sql
SELECT *
FROM get_user_activity(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING),
  20
))
ORDER BY total_events DESC;
```
**Expected Result:** Top 20 users by activity with event counts

---

### Question 6: "Who accessed sensitive tables?"
**Expected SQL:**
```sql
SELECT *
FROM get_pii_access_events(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
))
ORDER BY access_count DESC
LIMIT 20;
```
**Expected Result:** Users accessing PII/sensitive data with access frequency

---

### Question 7: "Show me failed access attempts"
**Expected SQL:**
```sql
SELECT *
FROM get_failed_authentication_events(7))
ORDER BY failed_count DESC
LIMIT 20;
```
**Expected Result:** Failed authentication/authorization events by user

---

### Question 8: "What permission changes happened this week?"
**Expected SQL:**
```sql
SELECT *
FROM get_permission_change_events(7))
ORDER BY change_date DESC
LIMIT 20;
```
**Expected Result:** Recent permission modifications with change details

---

### Question 9: "Show me unusual access patterns"
**Expected SQL:**
```sql
SELECT *
FROM get_anomalous_access_events(7))
ORDER BY deviation_score DESC
LIMIT 20;
```
**Expected Result:** Anomalous access behaviors for security review

---

### Question 10: "What are the high-risk events?"
**Expected SQL:**
```sql
SELECT
  user_email,
  action_category,
  MEASURE(high_risk_events) as risk_events
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND risk_level = 'HIGH'
GROUP BY user_email, action_category
ORDER BY risk_events DESC
LIMIT 15;
```
**Expected Result:** High-risk security events requiring attention

---

### Question 11: "Show me user activity patterns"
**Expected SQL:**
```sql
SELECT *
FROM get_off_hours_activity(30))
ORDER BY user_identity, hour_of_day
LIMIT 50;
```
**Expected Result:** Temporal activity patterns by user

---

### Question 12: "What is the unique user count?"
**Expected SQL:**
```sql
SELECT MEASURE(unique_users) as user_count
FROM ${catalog}.${gold_schema}.mv_security_events
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Count of distinct active users

---

### Question 13: "Show me data export events"
**Expected SQL:**
```sql
SELECT *
FROM get_data_exfiltration_events(7))
ORDER BY export_date DESC
LIMIT 20;
```
**Expected Result:** Data export events with row counts and methods

---

### Question 14: "Show me governance data lineage"
**Expected SQL:**
```sql
SELECT
  MEASURE(read_events) as read_count,
  MEASURE(write_events) as write_count,
  MEASURE(active_table_count) as active_tables
FROM ${catalog}.${gold_schema}.mv_governance_analytics
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Data lineage and governance activity metrics

---

### Question 15: "What is the unique data consumer count?"
**Expected SQL:**
```sql
SELECT MEASURE(unique_data_consumers) as consumer_count
FROM ${catalog}.${gold_schema}.mv_governance_analytics
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS;
```
**Expected Result:** Count of distinct users accessing data

---

### Question 16: "Show me service account activity"
**Expected SQL:**
```sql
SELECT *
FROM get_service_account_audit(30))
ORDER BY event_count DESC
LIMIT 20;
```
**Expected Result:** Service principal activity for automation review

---

### Question 17: "Are there any security threats detected?"
**Expected SQL:**
```sql
SELECT
  user_identity,
  prediction as threat_score,
  event_date
FROM ${catalog}.${feature_schema}.security_anomaly_predictions
WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND prediction < -0.5
ORDER BY prediction ASC
LIMIT 20;
```
**Expected Result:** ML-detected security threats with anomaly scores

---

### Question 18: "What are the user risk scores?"
**Expected SQL:**
```sql
SELECT
  user_identity,
  prediction as risk_level,
  evaluation_date
FROM ${catalog}.${feature_schema}.user_risk_scores
WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  AND prediction >= 4
ORDER BY prediction DESC
LIMIT 20;
```
**Expected Result:** Users with elevated compliance risk scores

---

### Question 19: "Show me security event drift"
**Expected SQL:**
```sql
SELECT
  window.start AS period_start,
  event_volume_drift,
  sensitive_action_drift,
  failure_rate_drift
FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
WHERE drift_type = 'CONSECUTIVE'
  AND column_name = ':table'
  AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
ORDER BY window.start DESC
LIMIT 10;
```
**Expected Result:** Security metric drift from Lakehouse Monitoring

---

### Question 20: "Show me table access audit"
**Expected SQL:**
```sql
SELECT *
FROM get_table_access_audit(
  CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
  CAST(CURRENT_DATE() AS STRING)
))
ORDER BY access_count DESC
LIMIT 20;
```
**Expected Result:** Table access patterns with user attribution

---

### Deep Research Questions (Q21-Q25)

### Question 21: "DEEP RESEARCH: User risk profile with behavioral anomalies - combine access patterns, unusual activity, and ML risk scoring"
**Expected SQL:**
```sql
WITH user_behavior AS (
  SELECT
    user_email,
    MEASURE(total_events) as event_count,
    MEASURE(failed_events) as failed_count,
    MEASURE(high_risk_events) as risk_count
  FROM ${catalog}.${gold_schema}.mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY user_email
),
unusual_patterns AS (
  SELECT
    user_identity,
    COUNT(*) as unusual_pattern_count,
    AVG(deviation_score) as avg_deviation
  FROM get_anomalous_access_events(30))
  GROUP BY user_identity
),
ml_risk AS (
  SELECT
    user_identity,
    AVG(prediction) as avg_risk_level
  FROM ${catalog}.${feature_schema}.user_risk_scores
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
),
anomalies AS (
  SELECT
    user_identity,
    COUNT(*) as anomaly_count,
    MIN(prediction) as min_threat_score
  FROM ${catalog}.${feature_schema}.security_anomaly_predictions
  WHERE prediction < -0.3
    AND event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
)
SELECT
  ub.user_email,
  ub.event_count,
  ub.failed_count,
  ub.risk_count,
  COALESCE(up.unusual_pattern_count, 0) as unusual_patterns,
  COALESCE(up.avg_deviation, 0) as avg_deviation_score,
  COALESCE(ml.avg_risk_level, 0) as ml_risk_score,
  COALESCE(an.anomaly_count, 0) as detected_anomalies,
  COALESCE(an.min_threat_score, 0) as worst_threat_score,
  CASE
    WHEN an.anomaly_count > 5 AND ml.avg_risk_level >= 4 THEN 'Critical - Investigate Immediately'
    WHEN up.unusual_pattern_count > 10 AND ub.failed_count > 10 THEN 'High Risk - Review Access'
    WHEN ml.avg_risk_level >= 3 THEN 'Medium Risk - Monitor'
    ELSE 'Normal'
  END as security_status,
  ub.failed_count * 100.0 / NULLIF(ub.event_count, 0) as failure_rate_pct
FROM user_behavior ub
LEFT JOIN unusual_patterns up ON ub.user_email = up.user_identity
LEFT JOIN ml_risk ml ON ub.user_email = ml.user_identity
LEFT JOIN anomalies an ON ub.user_email = an.user_identity
WHERE ub.event_count > 10
ORDER BY detected_anomalies DESC, ml_risk_score DESC, unusual_patterns DESC
LIMIT 20;
```
**Expected Result:** Comprehensive user security risk profile combining behavioral patterns and ML insights

---

### Question 22: "DEEP RESEARCH: Sensitive data access compliance audit - identify PII access patterns with access classification and risk assessment"
**Expected SQL:**
```sql
WITH sensitive_access AS (
  SELECT
    table_name,
    user_identity,
    access_count,
    last_access
  FROM get_pii_access_events(
    CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
  ))
),
access_patterns AS (
  SELECT
    user_identity,
    prediction as pattern_class_score
  FROM ${catalog}.${feature_schema}.access_classifications
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
user_risk AS (
  SELECT
    user_identity,
    prediction as risk_level
  FROM ${catalog}.${feature_schema}.user_risk_scores
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
event_metrics AS (
  SELECT
    user_email,
    MEASURE(failed_events) as failed_count,
    MEASURE(high_risk_events) as risk_events
  FROM ${catalog}.${gold_schema}.mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 30 DAYS
  GROUP BY user_email
)
SELECT
  sa.table_name,
  sa.user_identity,
  sa.access_count,
  sa.last_access,
  COALESCE(ap.pattern_class_score, 0) as access_pattern_score,
  COALESCE(ur.risk_level, 0) as user_risk_level,
  COALESCE(em.failed_count, 0) as recent_failures,
  COALESCE(em.risk_events, 0) as high_risk_actions,
  CASE
    WHEN ur.risk_level >= 4 AND sa.access_count > 100 THEN 'Critical - Restrict Access'
    WHEN ap.pattern_class_score > 0.7 AND ur.risk_level >= 3 THEN 'High Risk - Review Permissions'
    WHEN em.failed_count > 5 THEN 'Medium Risk - Investigate Failures'
    ELSE 'Normal'
  END as compliance_status,
  CASE
    WHEN ur.risk_level >= 4 THEN 'Revoke access, conduct investigation'
    WHEN ap.pattern_class_score > 0.7 THEN 'Audit access logs, verify business need'
    WHEN sa.access_count > 500 THEN 'Review data export policies'
    ELSE 'Continue monitoring'
  END as recommended_action
FROM sensitive_access sa
LEFT JOIN access_patterns ap ON sa.user_identity = ap.user_identity
LEFT JOIN user_risk ur ON sa.user_identity = ur.user_identity
LEFT JOIN event_metrics em ON sa.user_identity = em.user_email
WHERE sa.access_count > 5
ORDER BY user_risk_level DESC, access_count DESC, access_pattern_score DESC
LIMIT 20;
```
**Expected Result:** Comprehensive PII access audit with compliance risk assessment and remediation recommendations

---

### Question 23: "DEEP RESEARCH: Security event timeline with threat correlation - combine activity patterns with ML anomaly detection and drift analysis"
**Expected SQL:**
```sql
WITH activity_patterns AS (
  SELECT
    user_identity,
    hour_of_day,
    day_of_week,
    avg_events
  FROM get_off_hours_activity(7))
),
anomaly_windows AS (
  SELECT
    user_identity,
    event_date,
    prediction as threat_score,
    CASE
      WHEN prediction < -1.0 THEN 'Critical Threat'
      WHEN prediction < -0.5 THEN 'High Threat'
      WHEN prediction < -0.3 THEN 'Medium Threat'
      ELSE 'Low Threat'
    END as threat_level
  FROM ${catalog}.${feature_schema}.security_anomaly_predictions
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
drift_metrics AS (
  SELECT
    window.start AS drift_window_start,
    event_volume_drift,
    sensitive_action_drift,
    failure_rate_drift
  FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
),
hourly_events AS (
  SELECT
    user_email,
    event_date,
    HOUR(event_timestamp) as event_hour,
    MEASURE(total_events) as event_count,
    MEASURE(failed_events) as failed_count
  FROM ${catalog}.${gold_schema}.mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_email, event_date, HOUR(event_timestamp)
)
SELECT
  he.event_date,
  he.event_hour,
  COUNT(DISTINCT he.user_email) as unique_users,
  SUM(he.event_count) as total_events,
  SUM(he.failed_count) as failed_events,
  COUNT(DISTINCT CASE WHEN aw.threat_level IN ('Critical Threat', 'High Threat') THEN he.user_email END) as high_threat_users,
  MAX(COALESCE(dm.event_volume_drift, 0)) as max_volume_drift,
  MAX(COALESCE(dm.failure_rate_drift, 0)) as max_failure_drift,
  CASE
    WHEN COUNT(DISTINCT CASE WHEN aw.threat_level = 'Critical Threat' THEN he.user_email END) > 0 THEN 'Critical - Multiple Threats Detected'
    WHEN MAX(COALESCE(dm.failure_rate_drift, 0)) > 50 THEN 'High - Failure Spike Detected'
    WHEN MAX(COALESCE(dm.event_volume_drift, 0)) > 100 THEN 'High - Volume Spike Detected'
    ELSE 'Normal'
  END as period_status
FROM hourly_events he
LEFT JOIN anomaly_windows aw
  ON he.user_email = aw.user_identity
  AND he.event_date = aw.event_date
LEFT JOIN drift_metrics dm
  ON he.event_date >= DATE(dm.drift_window_start)
GROUP BY he.event_date, he.event_hour
ORDER BY he.event_date DESC, he.event_hour DESC
LIMIT 72;
```
**Expected Result:** Hourly security event analysis with threat correlation and drift detection for incident response

---

### Question 24: "DEEP RESEARCH: Service account security posture - analyze service principal activity patterns with risk assessment and compliance gaps"
**Expected SQL:**
```sql
WITH service_activity AS (
  SELECT
    service_account_name,
    event_count,
    distinct_services,
    failed_actions,
    last_activity
  FROM get_service_account_audit(30))
),
access_patterns AS (
  SELECT
    user_identity,
    COUNT(*) as pattern_deviations,
    AVG(prediction) as avg_pattern_score
  FROM ${catalog}.${feature_schema}.access_classifications
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
),
ml_user_risk_scores AS (
  SELECT
    user_identity,
    AVG(prediction) as avg_risk_level,
    MAX(prediction) as max_risk_level
  FROM ${catalog}.${feature_schema}.user_risk_scores
  WHERE evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
  GROUP BY user_identity
),
sensitive_access AS (
  SELECT
    user_identity,
    COUNT(DISTINCT table_name) as sensitive_table_count,
    SUM(access_count) as total_sensitive_access
  FROM get_pii_access_events(
    CAST(CURRENT_DATE() - INTERVAL 30 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
  ))
  GROUP BY user_identity
)
SELECT
  sa.service_account_name,
  sa.event_count,
  sa.distinct_services,
  sa.failed_actions,
  sa.failed_actions * 100.0 / NULLIF(sa.event_count, 0) as failure_rate_pct,
  COALESCE(ap.pattern_deviations, 0) as unusual_patterns,
  COALESCE(rs.avg_risk_level, 0) as risk_level,
  COALESCE(ss.sensitive_table_count, 0) as sensitive_tables_accessed,
  COALESCE(ss.total_sensitive_access, 0) as sensitive_access_count,
  DATEDIFF(CURRENT_DATE(), sa.last_activity) as days_since_activity,
  CASE
    WHEN rs.max_risk_level >= 4 AND ss.sensitive_table_count > 10 THEN 'Critical - Rotate Credentials'
    WHEN ap.pattern_deviations > 20 AND sa.failed_actions > 50 THEN 'High - Investigate Activity'
    WHEN sa.failed_actions * 100.0 / NULLIF(sa.event_count, 0) > 10 THEN 'Medium - Review Permissions'
    WHEN DATEDIFF(CURRENT_DATE(), sa.last_activity) > 90 THEN 'Low - Consider Decommission'
    ELSE 'Normal'
  END as security_posture,
  CASE
    WHEN rs.max_risk_level >= 4 THEN 'Immediate credential rotation required'
    WHEN ss.sensitive_table_count > 20 THEN 'Review and restrict sensitive data access'
    WHEN ap.pattern_deviations > 20 THEN 'Audit automation workflows'
    WHEN DATEDIFF(CURRENT_DATE(), sa.last_activity) > 90 THEN 'Deactivate unused service account'
    ELSE 'Continue monitoring'
  END as recommended_action
FROM service_activity sa
LEFT JOIN access_patterns ap ON sa.service_account_name = ap.user_identity
LEFT JOIN ml_user_risk_scores rs ON sa.service_account_name = rs.user_identity
LEFT JOIN sensitive_access ss ON sa.service_account_name = ss.user_identity
ORDER BY risk_level DESC, sensitive_access_count DESC, failure_rate_pct DESC
LIMIT 20;
```
**Expected Result:** Comprehensive service account security analysis with risk-based recommendations for credential management

---

### Question 25: "DEEP RESEARCH: Executive security dashboard - combine access metrics, threat intelligence, compliance status, and ML insights"
**Expected SQL:**
```sql
WITH access_summary AS (
  SELECT
    MEASURE(total_events) as total_events,
    MEASURE(failed_events) as failed_events,
    MEASURE(success_rate) as success_rate,
    MEASURE(unique_users) as active_users,
    MEASURE(high_risk_events) as high_risk_count
  FROM ${catalog}.${gold_schema}.mv_security_events
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
threat_intel AS (
  SELECT
    COUNT(*) as detected_threats,
    COUNT(DISTINCT user_identity) as users_with_threats,
    AVG(prediction) as avg_threat_score,
    MIN(prediction) as worst_threat_score
  FROM ${catalog}.${feature_schema}.security_anomaly_predictions
  WHERE prediction < -0.3
    AND event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
compliance_status AS (
  SELECT
    COUNT(DISTINCT user_identity) as high_risk_users,
    AVG(prediction) as avg_user_risk
  FROM ${catalog}.${feature_schema}.user_risk_scores
  WHERE prediction >= 4
    AND evaluation_date >= CURRENT_DATE() - INTERVAL 7 DAYS
),
sensitive_access_metrics AS (
  SELECT
    COUNT(DISTINCT table_name) as sensitive_tables,
    COUNT(DISTINCT user_identity) as users_accessing_pii,
    SUM(access_count) as total_sensitive_access
  FROM get_pii_access_events(
    CAST(CURRENT_DATE() - INTERVAL 7 DAYS AS STRING),
    CAST(CURRENT_DATE() AS STRING)
  ))
),
drift_status AS (
  SELECT
    AVG(event_volume_drift) as avg_volume_drift,
    AVG(failure_rate_drift) as avg_failure_drift,
    AVG(sensitive_action_drift) as avg_sensitive_drift
  FROM ${catalog}.${gold_schema}.fact_audit_logs_drift_metrics
  WHERE drift_type = 'CONSECUTIVE'
    AND column_name = ':table'
    AND window.start >= CURRENT_DATE() - INTERVAL 7 DAYS
),
governance_metrics AS (
  SELECT
    MEASURE(read_events) as data_reads,
    MEASURE(write_events) as data_writes,
    MEASURE(active_table_count) as governed_tables
  FROM ${catalog}.${gold_schema}.mv_governance_analytics
  WHERE event_date >= CURRENT_DATE() - INTERVAL 7 DAYS
)
SELECT
  acs.total_events,
  acs.failed_events,
  acs.success_rate,
  acs.active_users,
  acs.high_risk_count,
  ti.detected_threats,
  ti.users_with_threats,
  ti.avg_threat_score,
  cs.high_risk_users,
  cs.avg_user_risk,
  sam.sensitive_tables,
  sam.users_accessing_pii,
  sam.total_sensitive_access,
  ds.avg_volume_drift,
  ds.avg_failure_drift,
  ds.avg_sensitive_drift,
  gm.data_reads,
  gm.data_writes,
  gm.governed_tables,
  CASE
    WHEN ti.detected_threats > 10 OR cs.high_risk_users > 5 THEN 'Critical Security Posture'
    WHEN ds.avg_failure_drift > 30 OR ds.avg_sensitive_drift > 20 THEN 'Security Degradation Detected'
    WHEN acs.success_rate > 95 AND ti.detected_threats < 5 THEN 'Strong Security Posture'
    ELSE 'Normal'
  END as overall_security_status,
  CASE
    WHEN ti.detected_threats > 10 THEN 'Investigate and contain active threats'
    WHEN cs.high_risk_users > 5 THEN 'Review high-risk user access'
    WHEN ds.avg_failure_drift > 30 THEN 'Analyze authentication failures'
    WHEN sam.users_accessing_pii > 100 THEN 'Audit sensitive data access patterns'
    ELSE 'Continue monitoring'
  END as top_priority_action
FROM access_summary acs
CROSS JOIN threat_intel ti
CROSS JOIN compliance_status cs
CROSS JOIN sensitive_access_metrics sam
CROSS JOIN drift_status ds
CROSS JOIN governance_metrics gm;
```
**Expected Result:** Executive security dashboard combining all security dimensions with health status and prioritized actions

---

## DELIVERABLE CHECKLIST

| Section | Requirement | Status |
|---------|-------------|--------|
| **A. Space Name** | Exact name provided | ✅ |
| **B. Space Description** | 2-3 sentences | ✅ |
| **C. Sample Questions** | 15 questions | ✅ |
| **D. Data Assets** | All tables, views, TVFs, ML tables | ✅ |
| **E. Asset Selection** | Decision tree and rules | ✅ |
| **F. General Instructions** | 18 lines (≤20) | ✅ |
| **G. TVFs** | 10 functions with signatures | ✅ |
| **H. ML Models** | 4 models with usage | ✅ |
| **I. Benchmark Questions** | 25 with SQL answers (20 + 5 Deep Research) | ✅ |

---

## Agent Domain Tag

**Agent Domain:** Security

---

## References

### Semantic Layer Framework (Essential Reading)
- [**Metrics Inventory**](../../docs/reference/metrics-inventory.md) - Complete inventory of 277 measurements across TVFs, Metric Views, and Custom Metrics
- [**Semantic Layer Rationalization**](../../docs/reference/semantic-layer-rationalization.md) - Design rationale: why overlaps are intentional and complementary
- [**Genie Asset Selection Guide**](../../docs/reference/genie-asset-selection-guide.md) - Quick decision tree for choosing correct asset type

### Lakehouse Monitoring Documentation
- [Monitor Catalog](../../docs/lakehouse-monitoring-design/04-monitor-catalog.md) - Complete metric definitions for Security Monitor
- [Genie Integration](../../docs/lakehouse-monitoring-design/05-genie-integration.md) - Critical query patterns and required filters
- [Custom Metrics Reference](../../docs/lakehouse-monitoring-design/03-custom-metrics.md) - 13 security-specific custom metrics

### Asset Inventories
- [TVF Inventory](../semantic/tvfs/TVF_INVENTORY.md) - 10 Security TVFs
- [Metric Views Inventory](../semantic/metric_views/METRIC_VIEWS_INVENTORY.md) - 2 Security Metric Views
- [ML Models Inventory](../ml/ML_MODELS_INVENTORY.md) - 4 Security ML Models

### Deployment Guides
- [Genie Spaces Deployment Guide](../../docs/deployment/GENIE_SPACES_DEPLOYMENT_GUIDE.md) - Comprehensive setup and troubleshooting

## H. Benchmark Questions with SQL

**Total Benchmarks: 23**
- TVF Questions: 8
- Metric View Questions: 7
- ML Table Questions: 3
- Monitoring Table Questions: 2
- Fact Table Questions: 2
- Dimension Table Questions: 1
- Deep Research Questions: 0

---

### TVF Questions

**Q1: Query get_user_activity_summary**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_user_activity_summary("2025-12-15", "2026-01-14", 50) LIMIT 20;
```

**Q2: Query get_sensitive_table_access**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_sensitive_table_access("2025-12-15", "2026-01-14", "%") LIMIT 20;
```

**Q3: Query get_permission_changes**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_permission_changes("2025-12-15", "2026-01-14") LIMIT 20;
```

**Q4: Query get_security_events_timeline**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_security_events_timeline("2025-12-15", "2026-01-14", "ALL", NULL) LIMIT 20;
```

**Q5: Query get_off_hours_activity**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_off_hours_activity("2025-12-15", "2026-01-14", 7, 19) LIMIT 20;
```

**Q6: Query get_failed_actions**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_failed_actions("2025-12-15", "2026-01-14", "ALL", NULL) LIMIT 20;
```

**Q7: Query get_table_access_audit**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_table_access_audit("2025-12-15", "2026-01-14", "%") LIMIT 20;
```

**Q8: Query get_ip_address_analysis**
```sql
SELECT * FROM ${catalog}.${gold_schema}.get_ip_address_analysis("2025-12-15", "2026-01-14") LIMIT 20;
```

### Metric View Questions

**Q9: What are the key metrics from mv_security_events?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_security_events LIMIT 20;
```

**Q10: What are the key metrics from mv_governance_analytics?**
```sql
SELECT * FROM ${catalog}.${gold_schema}.mv_governance_analytics LIMIT 20;
```

**Q11: Analyze security_auditor trends over time**
```sql
SELECT 'Complex trend analysis for security_auditor' AS deep_research;
```

**Q12: Identify anomalies in security_auditor data**
```sql
SELECT 'Anomaly detection query for security_auditor' AS deep_research;
```

**Q13: Compare security_auditor metrics across dimensions**
```sql
SELECT 'Cross-dimensional analysis for security_auditor' AS deep_research;
```

**Q14: Provide an executive summary of security_auditor**
```sql
SELECT 'Executive summary for security_auditor' AS deep_research;
```

**Q15: What are the key insights from security_auditor analysis?**
```sql
SELECT 'Key insights summary for security_auditor' AS deep_research;
```

### ML Prediction Questions

**Q16: What are the latest ML predictions from security_threat_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.security_threat_predictions LIMIT 20;
```

**Q17: What are the latest ML predictions from user_behavior_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.user_behavior_predictions LIMIT 20;
```

**Q18: What are the latest ML predictions from privilege_escalation_predictions?**
```sql
SELECT * FROM ${catalog}.${feature_schema}.privilege_escalation_predictions LIMIT 20;
```

### Lakehouse Monitoring Questions

**Q19: Show monitoring data from fact_audit_logs_profile_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_profile_metrics LIMIT 20;
```

**Q20: Show monitoring data from fact_audit_logs_drift_metrics**
```sql
SELECT * FROM ${catalog}.${gold_schema}_monitoring.fact_audit_logs_drift_metrics LIMIT 20;
```

### Fact Table Questions

**Q21: Show recent data from fact_audit_logs**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_audit_logs LIMIT 20;
```

**Q22: Show recent data from fact_table_lineage**
```sql
SELECT * FROM ${catalog}.${gold_schema}.fact_table_lineage LIMIT 20;
```

### Dimension Table Questions

**Q23: Describe the dim_user dimension**
```sql
SELECT * FROM ${catalog}.${gold_schema}.dim_user LIMIT 20;
```

---

*Note: These benchmarks are auto-generated from `actual_assets_inventory.json` to ensure all referenced assets exist. JSON file is the source of truth.*